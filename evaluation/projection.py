from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from evidence.projections import SemanticProjection
from jev.contracts import JevDecision


@dataclass(frozen=True, slots=True)
class ProjectionCaseResult:
    case_id: str
    projection: SemanticProjection
    decision: JevDecision
    expected: object
    correct: bool


def exact_match(actual: object, expected: object) -> bool:
    return actual == expected


@dataclass(frozen=True, slots=True)
class ProjectionArmResult:
    arm_id: str
    decisions: dict[str, str]
    probabilities: dict[str, dict[str, float]]
    serialized_bytes: int
    latency_ms: float
    usage: dict[str, Any]


@dataclass(frozen=True, slots=True)
class PairedProjectionEvaluation:
    case_ids: tuple[str, ...]
    expected: dict[str, str]
    full_state: ProjectionArmResult
    projected_state: ProjectionArmResult
    metrics: dict[str, float]


def compare_projection_arms(
    *,
    expected: dict[str, str],
    full_state: ProjectionArmResult,
    projected_state: ProjectionArmResult,
) -> PairedProjectionEvaluation:
    """Compare aligned full/projected decisions without hiding raw arm results."""

    case_ids = tuple(expected)
    required = set(case_ids)
    for arm in (full_state, projected_state):
        if set(arm.decisions) != required:
            raise ValueError(f"{arm.arm_id} decisions do not match the frozen case set")
        if set(arm.probabilities) != required:
            raise ValueError(f"{arm.arm_id} probabilities do not match the frozen case set")

    count = len(case_ids)
    if count == 0:
        raise ValueError("paired projection evaluation requires at least one case")

    full_correct = sum(full_state.decisions[case_id] == expected[case_id] for case_id in case_ids)
    projected_correct = sum(
        projected_state.decisions[case_id] == expected[case_id] for case_id in case_ids
    )
    agreements = sum(
        full_state.decisions[case_id] == projected_state.decisions[case_id] for case_id in case_ids
    )
    regressions = sum(
        full_state.decisions[case_id] == expected[case_id]
        and projected_state.decisions[case_id] != expected[case_id]
        for case_id in case_ids
    )
    byte_reduction = 1.0 - (projected_state.serialized_bytes / full_state.serialized_bytes)

    metrics = {
        "full_accuracy": full_correct / count,
        "projected_accuracy": projected_correct / count,
        "accuracy_delta": (projected_correct - full_correct) / count,
        "arm_agreement": agreements / count,
        "full_correct_to_projected_incorrect": float(regressions),
        "serialized_byte_reduction": byte_reduction,
        "full_latency_ms": full_state.latency_ms,
        "projected_latency_ms": projected_state.latency_ms,
        "full_input_tokens": float(full_state.usage.get("input_tokens") or 0),
        "projected_input_tokens": float(projected_state.usage.get("input_tokens") or 0),
        "full_output_tokens": float(full_state.usage.get("output_tokens") or 0),
        "projected_output_tokens": float(projected_state.usage.get("output_tokens") or 0),
    }
    return PairedProjectionEvaluation(
        case_ids=case_ids,
        expected=expected,
        full_state=full_state,
        projected_state=projected_state,
        metrics=metrics,
    )
