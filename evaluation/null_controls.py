from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class NullArmMetrics:
    arm_id: str
    case_count: int
    claim_count: int
    claim_rate: float
    mean_probability: float
    max_probability: float


@dataclass(frozen=True, slots=True)
class NullControlEvaluation:
    threshold: float
    valid: NullArmMetrics
    null_arms: dict[str, NullArmMetrics]
    mean_null_claim_rate: float
    maximum_null_claim_rate: float
    mean_null_probability: float
    valid_minus_null_mean_probability: float


def cyclic_derangement(items: tuple[str, ...], *, offset: int) -> dict[str, str]:
    if len(items) < 2:
        raise ValueError("derangement requires at least two items")
    if len(set(items)) != len(items):
        raise ValueError("derangement items must be unique")
    normalized = offset % len(items)
    if normalized == 0:
        raise ValueError("derangement offset must not preserve every item")
    return {item: items[(index + normalized) % len(items)] for index, item in enumerate(items)}


def _arm_metrics(arm_id: str, probabilities: dict[str, float], threshold: float) -> NullArmMetrics:
    if not probabilities:
        raise ValueError(f"arm {arm_id} has no cases")
    if any(probability < 0.0 or probability > 1.0 for probability in probabilities.values()):
        raise ValueError(f"arm {arm_id} contains a probability outside [0, 1]")
    claim_count = sum(probability >= threshold for probability in probabilities.values())
    return NullArmMetrics(
        arm_id=arm_id,
        case_count=len(probabilities),
        claim_count=claim_count,
        claim_rate=claim_count / len(probabilities),
        mean_probability=sum(probabilities.values()) / len(probabilities),
        max_probability=max(probabilities.values()),
    )


def evaluate_null_controls(
    *,
    probabilities: dict[str, dict[str, float]],
    valid_arm_id: str,
    null_arm_ids: tuple[str, ...],
    threshold: float,
) -> NullControlEvaluation:
    if not null_arm_ids:
        raise ValueError("at least one null-control arm is required")
    if threshold < 0.0 or threshold > 1.0:
        raise ValueError("claim threshold must be within [0, 1]")
    expected_arms = {valid_arm_id, *null_arm_ids}
    if set(probabilities) != expected_arms:
        raise ValueError("probability arms do not match the frozen control set")
    case_ids = set(probabilities[valid_arm_id])
    if any(set(probabilities[arm_id]) != case_ids for arm_id in expected_arms):
        raise ValueError("all null-control arms must contain the same cases")

    valid = _arm_metrics(valid_arm_id, probabilities[valid_arm_id], threshold)
    null_arms = {
        arm_id: _arm_metrics(arm_id, probabilities[arm_id], threshold) for arm_id in null_arm_ids
    }
    mean_null_claim_rate = sum(arm.claim_rate for arm in null_arms.values()) / len(null_arms)
    mean_null_probability = sum(arm.mean_probability for arm in null_arms.values()) / len(null_arms)
    return NullControlEvaluation(
        threshold=threshold,
        valid=valid,
        null_arms=null_arms,
        mean_null_claim_rate=mean_null_claim_rate,
        maximum_null_claim_rate=max(arm.claim_rate for arm in null_arms.values()),
        mean_null_probability=mean_null_probability,
        valid_minus_null_mean_probability=valid.mean_probability - mean_null_probability,
    )
