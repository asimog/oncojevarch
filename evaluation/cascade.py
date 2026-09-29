from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from oncox.ports import ReasoningOutput


def normalize_text(text: str) -> str:
    """Lowercase and collapse whitespace for frozen lexical rubric matching."""

    return " ".join(text.lower().split())


@dataclass(frozen=True, slots=True)
class ReasoningConsideration:
    """One frozen rubric item for a case.

    `recorded_in_state` marks considerations already present in the structured state. A
    consideration that is not recorded is what bounded screening may prevent reasoning from adding.
    """

    consideration_id: str
    description: str
    markers: tuple[str, ...]
    recorded_in_state: bool

    def matched_in(self, normalized_text: str) -> bool:
        return any(normalize_text(marker) in normalized_text for marker in self.markers)


@dataclass(frozen=True, slots=True)
class CascadeCase:
    case_id: str
    claim: str
    question: str
    state: dict[str, Any]
    considerations: tuple[ReasoningConsideration, ...]

    def recorded(self) -> tuple[ReasoningConsideration, ...]:
        return tuple(item for item in self.considerations if item.recorded_in_state)

    def novel(self) -> tuple[ReasoningConsideration, ...]:
        return tuple(item for item in self.considerations if not item.recorded_in_state)


def serialize_reasoning_text(output: ReasoningOutput) -> str:
    parts = (
        output.interpretation,
        *output.hypotheses,
        *output.alternative_explanations,
        *output.proposed_tests,
        *output.unresolved_uncertainty,
    )
    return normalize_text(" \n ".join(parts))


def serialize_state(case: CascadeCase) -> str:
    return normalize_text(json.dumps(case.state, sort_keys=True, default=str))


def validate_case_set(cases: tuple[CascadeCase, ...]) -> None:
    """Enforce the frozen case-set invariants before any live output is observed."""

    if not cases:
        raise ValueError("cascade evaluation requires at least one locked case")
    case_ids = [case.case_id for case in cases]
    if len(set(case_ids)) != len(case_ids):
        raise ValueError("locked case identities must be unique")
    for case in cases:
        if not case.considerations:
            raise ValueError(f"case {case.case_id} has no rubric considerations")
        state_text = serialize_state(case)
        for consideration in case.considerations:
            if not consideration.markers:
                raise ValueError(
                    f"consideration {consideration.consideration_id} has no frozen markers"
                )
            if consideration.recorded_in_state:
                continue
            for marker in consideration.markers:
                if normalize_text(marker) in state_text:
                    raise ValueError(
                        f"novel consideration {consideration.consideration_id} marker "
                        f"{marker!r} already appears in the frozen state of {case.case_id}"
                    )


@dataclass(frozen=True, slots=True)
class ReasoningAssessment:
    case_id: str
    reasoned: bool
    matched_consideration_ids: tuple[str, ...]
    novel_matched_ids: tuple[str, ...]
    knowledge: float
    output_match_ratio: float


def _build_assessment(
    case: CascadeCase, matched_in_output: tuple[str, ...], *, reasoned: bool
) -> ReasoningAssessment:
    total = len(case.considerations)
    matched = set(matched_in_output)
    available = {
        item.consideration_id
        for item in case.considerations
        if item.recorded_in_state or item.consideration_id in matched
    }
    matched_order = tuple(
        item.consideration_id
        for item in case.considerations
        if item.consideration_id in matched
    )
    novel_ids = {item.consideration_id for item in case.novel()}
    return ReasoningAssessment(
        case_id=case.case_id,
        reasoned=reasoned,
        matched_consideration_ids=matched_order,
        novel_matched_ids=tuple(
            consideration_id for consideration_id in matched_order if consideration_id in novel_ids
        ),
        knowledge=len(available) / total,
        output_match_ratio=len(matched) / total if reasoned else 0.0,
    )


def assess_reasoning(case: CascadeCase, output: ReasoningOutput) -> ReasoningAssessment:
    """Score one reasoning output against the frozen rubric."""

    text = serialize_reasoning_text(output)
    matched = tuple(
        item.consideration_id for item in case.considerations if item.matched_in(text)
    )
    return _build_assessment(case, matched, reasoned=True)


def assess_without_reasoning(case: CascadeCase) -> ReasoningAssessment:
    """Score a screened-out case: nothing is lost that the structured state already records."""

    return _build_assessment(case, (), reasoned=False)


def triage_escalations(
    *, probabilities: dict[str, float], case_ids: tuple[str, ...], threshold: float
) -> dict[str, bool]:
    """Apply the frozen triage threshold and keep raw probabilities separate."""

    if not 0.0 < threshold < 1.0:
        raise ValueError("triage threshold must be strictly between 0 and 1")
    if set(probabilities) != set(case_ids):
        raise ValueError("triage probabilities do not match the frozen case set")
    if any(value < 0.0 or value > 1.0 for value in probabilities.values()):
        raise ValueError("triage probabilities must be within [0, 1]")
    return {case_id: probabilities[case_id] >= threshold for case_id in case_ids}


@dataclass(frozen=True, slots=True)
class CascadeEvaluation:
    case_ids: tuple[str, ...]
    useful_case_ids: tuple[str, ...]
    escalated_case_ids: tuple[str, ...]
    false_negative_case_ids: tuple[str, ...]
    metrics: dict[str, float]
    per_case: tuple[dict[str, Any], ...]


def evaluate_cascade(
    *,
    cases: tuple[CascadeCase, ...],
    all_arm: dict[str, ReasoningAssessment],
    cascade_arm: dict[str, ReasoningAssessment],
    escalations: dict[str, bool],
) -> CascadeEvaluation:
    """Compare the all-case arm with the screened arm without hiding raw per-case results."""

    validate_case_set(cases)
    case_ids = tuple(case.case_id for case in cases)
    for arm in (all_arm, cascade_arm):
        if set(arm) != set(case_ids):
            raise ValueError("arm assessments do not match the frozen case set")
    if set(escalations) != set(case_ids):
        raise ValueError("triage decisions do not match the frozen case set")
    for case_id in case_ids:
        if not all_arm[case_id].reasoned:
            raise ValueError(f"the all-case arm must reason on every eligible case: {case_id}")
        if escalations[case_id] is not cascade_arm[case_id].reasoned:
            raise ValueError(f"screened-out cases must not call OncoX: {case_id}")

    useful = tuple(
        case_id for case_id in case_ids if all_arm[case_id].novel_matched_ids
    )
    escalated = tuple(case_id for case_id in case_ids if escalations[case_id])
    false_negatives = tuple(
        case_id for case_id in case_ids if case_id in useful and not escalations[case_id]
    )
    useless = tuple(case_id for case_id in case_ids if case_id not in useful)
    true_positives = len(set(useful) & set(escalated))

    reasoned_cascade = tuple(case_id for case_id in case_ids if escalations[case_id])
    quality_all = sum(all_arm[case_id].knowledge for case_id in case_ids) / len(case_ids)
    quality_cascade = (
        sum(cascade_arm[case_id].knowledge for case_id in case_ids) / len(case_ids)
    )
    ratio_all = sum(all_arm[case_id].output_match_ratio for case_id in case_ids) / len(case_ids)
    ratio_escalated = (
        sum(cascade_arm[case_id].output_match_ratio for case_id in reasoned_cascade)
        / len(reasoned_cascade)
        if reasoned_cascade
        else 0.0
    )

    metrics = {
        "quality_all": quality_all,
        "quality_cascade": quality_cascade,
        "quality_loss": quality_all - quality_cascade,
        "oncox_calls_all": float(sum(1 for case_id in case_ids if all_arm[case_id].reasoned)),
        "oncox_calls_cascade": float(len(reasoned_cascade)),
        "oncox_call_reduction": 1.0 - (len(reasoned_cascade) / len(case_ids)),
        "useful_case_count": float(len(useful)),
        "false_negative_count": float(len(false_negatives)),
        "false_negative_rate": (len(false_negatives) / len(useful)) if useful else 0.0,
        "triage_sensitivity": (true_positives / len(useful)) if useful else 0.0,
        "triage_false_positive_rate": (
            (len(escalated) - true_positives) / len(useless) if useless else 0.0
        ),
        "output_match_ratio_all": ratio_all,
        "output_match_ratio_escalated": ratio_escalated,
        "conditional_quality_ratio": (ratio_escalated / ratio_all) if ratio_all else 0.0,
    }
    per_case = tuple(
        {
            "case_id": case_id,
            "escalated": escalations[case_id],
            "useful": case_id in useful,
            "novel_matched_all": all_arm[case_id].novel_matched_ids,
            "novel_matched_cascade": cascade_arm[case_id].novel_matched_ids,
            "knowledge_all": all_arm[case_id].knowledge,
            "knowledge_cascade": cascade_arm[case_id].knowledge,
        }
        for case_id in case_ids
    )
    return CascadeEvaluation(
        case_ids=case_ids,
        useful_case_ids=useful,
        escalated_case_ids=escalated,
        false_negative_case_ids=false_negatives,
        metrics=metrics,
        per_case=per_case,
    )
