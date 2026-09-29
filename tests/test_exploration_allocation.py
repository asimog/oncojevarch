import pytest

from discovery.allocation import ExplorationAllocation, allocate_frontier
from discovery.frontier import FrontierEntry, SurvivalReason


def _entry(candidate_id: str, promise: float, uncertainty: float, novelty: float) -> FrontierEntry:
    return FrontierEntry(
        candidate_id=candidate_id,
        state_ref=f"state:{candidate_id}",
        reasons=(SurvivalReason.PROMISE,),
        relative_rank=promise,
        uncertainty=uncertainty,
        novelty=novelty,
    )


def test_allocation_preserves_promise_and_adds_distinct_exploration_slots() -> None:
    selected = allocate_frontier(
        (
            _entry("promise", 0.9, 0.1, 0.1),
            _entry("uncertain", 0.5, 0.95, 0.2),
            _entry("novel", 0.4, 0.3, 0.99),
        ),
        ExplorationAllocation(promise_slots=1, uncertainty_slots=1, novelty_slots=1),
    )

    assert tuple(item.candidate_id for item in selected) == ("promise", "uncertain", "novel")
    assert tuple(item.reason for item in selected) == (
        SurvivalReason.PROMISE,
        SurvivalReason.UNCERTAINTY,
        SurvivalReason.NOVELTY,
    )


def test_allocation_rejects_missing_policy_signal() -> None:
    incomplete = FrontierEntry("candidate", "state:candidate", (SurvivalReason.PROMISE,))
    with pytest.raises(ValueError, match="relative_rank"):
        allocate_frontier(
            (incomplete,),
            ExplorationAllocation(promise_slots=1, uncertainty_slots=0, novelty_slots=0),
        )
