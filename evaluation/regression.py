from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class RegressionObservation:
    """One model version's answers over a frozen capability evaluation set."""

    model_id: str
    probabilities: dict[str, float]
    usage: dict[str, Any]
    latency_ms: float


@dataclass(frozen=True, slots=True)
class ModelRegressionEvaluation:
    metrics: dict[str, float]
    per_question: tuple[dict[str, Any], ...]
    failures: tuple[str, ...]


def _validate(
    *,
    labels: dict[str, bool],
    observations: tuple[RegressionObservation, ...],
    threshold: float,
) -> tuple[str, ...]:
    if not labels:
        raise ValueError("model regression requires at least one labeled question")
    if not 0.0 < threshold < 1.0:
        raise ValueError("regression threshold must be strictly between 0 and 1")
    question_ids = tuple(labels)
    for observation in observations:
        if set(observation.probabilities) != set(question_ids):
            raise ValueError(f"{observation.model_id} answers do not match the frozen question set")
        if any(value < 0.0 or value > 1.0 for value in observation.probabilities.values()):
            raise ValueError(f"{observation.model_id} probabilities must be within [0, 1]")
    return question_ids


def _brier(observation: RegressionObservation, labels: dict[str, bool]) -> float:
    return sum((observation.probabilities[q] - float(labels[q])) ** 2 for q in labels) / len(labels)


def _claim_rate(
    observation: RegressionObservation, question_ids: tuple[str, ...], threshold: float
) -> float:
    if not question_ids:
        return 0.0
    return sum(observation.probabilities[q] >= threshold for q in question_ids) / len(question_ids)


def _max_group_claim_rate(
    observation: RegressionObservation,
    question_ids: tuple[str, ...],
    groups: dict[str, str],
    threshold: float,
) -> float:
    group_ids = sorted({groups[q] for q in question_ids})
    if not group_ids:
        return 0.0
    return max(
        _claim_rate(observation, tuple(q for q in question_ids if groups[q] == group), threshold)
        for group in group_ids
    )


def compare_model_versions(
    *,
    labels: dict[str, bool],
    baseline: RegressionObservation,
    candidate: RegressionObservation,
    threshold: float,
    control: RegressionObservation | None = None,
    min_decision_agreement: float = 0.9,
    max_drift_excess: float = 0.05,
    max_brier_excess: float = 0.05,
    groups: dict[str, str] | None = None,
    min_positive_claim_rate: float = 0.8,
    max_negative_mean_claim_rate: float = 0.2,
    max_negative_group_claim_rate: float = 0.4,
) -> ModelRegressionEvaluation:
    """Compare a candidate model version with an immutable recorded baseline.

    The control (normally the baseline model re-run in a fresh session) separates model drift from
    provider nondeterminism. No threshold here is a general rule: they belong to this contract.
    """

    observations = (baseline, candidate) if control is None else (baseline, candidate, control)
    question_ids = _validate(labels=labels, observations=observations, threshold=threshold)
    group_of = dict(groups or {})
    if group_of and set(group_of) != set(question_ids):
        raise ValueError("groups do not match the frozen question set")
    positive_ids = tuple(q for q in question_ids if labels[q])
    negative_ids = tuple(q for q in question_ids if not labels[q])
    if not positive_ids or not negative_ids:
        raise ValueError("model regression requires positive and negative labeled questions")

    def agreement(
        left: RegressionObservation, right: RegressionObservation, ids: tuple[str, ...]
    ) -> float:
        if not ids:
            return 0.0
        same = sum(
            (left.probabilities[q] >= threshold) == (right.probabilities[q] >= threshold)
            for q in ids
        )
        return same / len(ids)

    def drift(left: RegressionObservation, right: RegressionObservation) -> float:
        return sum(abs(left.probabilities[q] - right.probabilities[q]) for q in question_ids) / len(
            question_ids
        )

    metrics: dict[str, float] = {
        "candidate_decision_agreement": agreement(candidate, baseline, question_ids),
        "candidate_positive_agreement": agreement(candidate, baseline, positive_ids),
        "candidate_negative_agreement": agreement(candidate, baseline, negative_ids),
        "candidate_mean_abs_drift": drift(candidate, baseline),
        "baseline_brier": _brier(baseline, labels),
        "candidate_brier": _brier(candidate, labels),
        "baseline_positive_claim_rate": _claim_rate(baseline, positive_ids, threshold),
        "candidate_positive_claim_rate": _claim_rate(candidate, positive_ids, threshold),
        "baseline_negative_mean_claim_rate": _claim_rate(baseline, negative_ids, threshold),
        "candidate_negative_mean_claim_rate": _claim_rate(candidate, negative_ids, threshold),
        "baseline_negative_group_claim_rate": _max_group_claim_rate(
            baseline, negative_ids, group_of, threshold
        ),
        "candidate_negative_group_claim_rate": _max_group_claim_rate(
            candidate, negative_ids, group_of, threshold
        ),
        "baseline_latency_ms": baseline.latency_ms,
        "candidate_latency_ms": candidate.latency_ms,
        "baseline_input_tokens": float(baseline.usage.get("input_tokens") or 0),
        "candidate_input_tokens": float(candidate.usage.get("input_tokens") or 0),
        "baseline_output_tokens": float(baseline.usage.get("output_tokens") or 0),
        "candidate_output_tokens": float(candidate.usage.get("output_tokens") or 0),
    }
    for group in sorted(set(group_of.values())) if group_of else ():
        ids = tuple(q for q in question_ids if group_of[q] == group)
        metrics[f"candidate_{group}_agreement"] = agreement(candidate, baseline, ids)
        metrics[f"candidate_{group}_mean_abs_drift"] = sum(
            abs(candidate.probabilities[q] - baseline.probabilities[q]) for q in ids
        ) / len(ids)

    if control is not None:
        metrics["control_decision_agreement"] = agreement(control, baseline, question_ids)
        metrics["control_mean_abs_drift"] = drift(control, baseline)
        metrics["control_brier"] = _brier(control, labels)
        metrics["control_latency_ms"] = control.latency_ms
        metrics["candidate_drift_excess_over_control"] = (
            metrics["candidate_mean_abs_drift"] - metrics["control_mean_abs_drift"]
        )
    else:
        metrics["control_decision_agreement"] = 0.0
        metrics["control_mean_abs_drift"] = 0.0
        metrics["control_brier"] = 0.0
        metrics["control_latency_ms"] = 0.0
        metrics["candidate_drift_excess_over_control"] = 0.0

    failures: list[str] = []
    if metrics["candidate_positive_claim_rate"] < min_positive_claim_rate:
        failures.append("positive claim rate below the frozen minimum")
    if metrics["candidate_negative_mean_claim_rate"] > max_negative_mean_claim_rate:
        failures.append("negative mean claim rate above the frozen maximum")
    if metrics["candidate_negative_group_claim_rate"] > max_negative_group_claim_rate:
        failures.append("a negative group claim rate exceeds the frozen maximum")
    if metrics["candidate_decision_agreement"] < min_decision_agreement:
        failures.append("candidate decision agreement below the frozen minimum")
    if metrics["candidate_drift_excess_over_control"] > max_drift_excess:
        failures.append("candidate drift exceeds the control by more than the frozen allowance")
    if metrics["candidate_brier"] > metrics["baseline_brier"] + max_brier_excess:
        failures.append("candidate calibration is worse than the frozen allowance")

    per_question = tuple(
        {
            "question_id": question_id,
            "label": labels[question_id],
            "group": group_of.get(question_id, ""),
            "baseline": baseline.probabilities[question_id],
            "candidate": candidate.probabilities[question_id],
            "control": control.probabilities[question_id] if control is not None else None,
        }
        for question_id in question_ids
    )
    return ModelRegressionEvaluation(
        metrics=metrics, per_question=per_question, failures=tuple(failures)
    )
