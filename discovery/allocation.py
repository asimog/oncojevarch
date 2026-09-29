from __future__ import annotations

from dataclasses import dataclass

from discovery.frontier import FrontierEntry, SurvivalReason


@dataclass(frozen=True, slots=True)
class ExplorationAllocation:
    promise_slots: int
    uncertainty_slots: int
    novelty_slots: int

    @property
    def budget(self) -> int:
        return self.promise_slots + self.uncertainty_slots + self.novelty_slots


@dataclass(frozen=True, slots=True)
class AllocatedCandidate:
    candidate_id: str
    reason: SurvivalReason


def _signal(entry: FrontierEntry, field: str) -> float:
    value = getattr(entry, field)
    if value is None or value < 0.0 or value > 1.0:
        raise ValueError(f"{field} must be present and within [0, 1] for {entry.candidate_id}")
    return float(value)


def allocate_frontier(
    entries: tuple[FrontierEntry, ...], allocation: ExplorationAllocation
) -> tuple[AllocatedCandidate, ...]:
    """Fill frozen promise/uncertainty/novelty slots without using outcome labels."""

    if allocation.budget < 1:
        raise ValueError("exploration allocation requires a positive budget")
    if min(allocation.promise_slots, allocation.uncertainty_slots, allocation.novelty_slots) < 0:
        raise ValueError("allocation slots cannot be negative")
    if allocation.budget > len(entries):
        raise ValueError("allocation budget exceeds candidate count")
    if len({entry.candidate_id for entry in entries}) != len(entries):
        raise ValueError("candidate identifiers must be unique")

    ranked = {
        SurvivalReason.PROMISE: sorted(
            entries, key=lambda entry: (-_signal(entry, "relative_rank"), entry.candidate_id)
        ),
        SurvivalReason.UNCERTAINTY: sorted(
            entries, key=lambda entry: (-_signal(entry, "uncertainty"), entry.candidate_id)
        ),
        SurvivalReason.NOVELTY: sorted(
            entries, key=lambda entry: (-_signal(entry, "novelty"), entry.candidate_id)
        ),
    }
    requested = (
        (SurvivalReason.PROMISE, allocation.promise_slots),
        (SurvivalReason.UNCERTAINTY, allocation.uncertainty_slots),
        (SurvivalReason.NOVELTY, allocation.novelty_slots),
    )
    selected: list[AllocatedCandidate] = []
    seen: set[str] = set()
    for reason, slots in requested:
        available = (entry for entry in ranked[reason] if entry.candidate_id not in seen)
        for entry in available:
            if sum(item.reason is reason for item in selected) >= slots:
                break
            selected.append(AllocatedCandidate(entry.candidate_id, reason))
            seen.add(entry.candidate_id)

    for entry in ranked[SurvivalReason.PROMISE]:
        if len(selected) >= allocation.budget:
            break
        if entry.candidate_id not in seen:
            selected.append(AllocatedCandidate(entry.candidate_id, SurvivalReason.PROMISE))
            seen.add(entry.candidate_id)
    return tuple(selected)
