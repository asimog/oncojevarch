from __future__ import annotations

from dataclasses import dataclass

from discovery.allocation import AllocatedCandidate


@dataclass(frozen=True, slots=True)
class ExplorationMetrics:
    candidate_count: int
    selected_count: int
    useful_count: int
    useful_selected: int
    useful_recall: float
    selected_precision: float
    false_negative_burden: int
    reason_diversity: int


def evaluate_exploration(
    *, outcomes: dict[str, bool], selected: tuple[AllocatedCandidate, ...]
) -> ExplorationMetrics:
    if not outcomes or not any(outcomes.values()):
        raise ValueError("exploration evaluation requires at least one useful outcome")
    selected_ids = [item.candidate_id for item in selected]
    if len(selected_ids) != len(set(selected_ids)):
        raise ValueError("selection contains duplicate candidates")
    if not set(selected_ids) <= set(outcomes):
        raise ValueError("selection contains an unknown candidate")
    useful_count = sum(outcomes.values())
    useful_selected = sum(outcomes[candidate_id] for candidate_id in selected_ids)
    return ExplorationMetrics(
        candidate_count=len(outcomes),
        selected_count=len(selected),
        useful_count=useful_count,
        useful_selected=useful_selected,
        useful_recall=useful_selected / useful_count,
        selected_precision=useful_selected / len(selected) if selected else 0.0,
        false_negative_burden=useful_count - useful_selected,
        reason_diversity=len({item.reason for item in selected}),
    )
