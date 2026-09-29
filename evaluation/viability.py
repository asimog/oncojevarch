from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ViabilityMetrics:
    case_count: int
    false_acceptance_rate: float
    false_rejection_rate: float
    viable_recall: float
    accuracy: float
    coverage: float
    brier_score: float


def evaluate_viability(
    *, expected: dict[str, bool], accepted: dict[str, bool], probabilities: dict[str, float]
) -> ViabilityMetrics:
    if not expected:
        raise ValueError("viability evaluation requires at least one case")
    if set(accepted) != set(expected) or set(probabilities) != set(expected):
        raise ValueError("viability outputs do not match the frozen case set")
    if any(probability < 0.0 or probability > 1.0 for probability in probabilities.values()):
        raise ValueError("viability probabilities must be within [0, 1]")

    positives = sum(expected.values())
    negatives = len(expected) - positives
    if positives == 0 or negatives == 0:
        raise ValueError("viability evaluation requires viable and no-match cases")

    false_acceptances = sum(accepted[case_id] and not label for case_id, label in expected.items())
    false_rejections = sum(not accepted[case_id] and label for case_id, label in expected.items())
    correct = sum(accepted[case_id] == label for case_id, label in expected.items())
    brier = sum(
        (probabilities[case_id] - float(label)) ** 2 for case_id, label in expected.items()
    ) / len(expected)
    return ViabilityMetrics(
        case_count=len(expected),
        false_acceptance_rate=false_acceptances / negatives,
        false_rejection_rate=false_rejections / positives,
        viable_recall=1.0 - (false_rejections / positives),
        accuracy=correct / len(expected),
        coverage=sum(accepted.values()) / len(expected),
        brier_score=brier,
    )
