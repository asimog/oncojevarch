import pytest

from discovery.frontier import FrontierEntry, SearchFrontier, SurvivalReason


def test_frontier_requires_explicit_survival_reason() -> None:
    frontier = SearchFrontier()
    with pytest.raises(ValueError):
        frontier.upsert(FrontierEntry("c1", "state:1", ()))


def test_frontier_can_preserve_uncertain_candidate() -> None:
    frontier = SearchFrontier()
    frontier.upsert(
        FrontierEntry("c1", "state:1", (SurvivalReason.UNCERTAINTY,), relative_rank=0.2)
    )
    assert frontier.entries()[0].reasons == (SurvivalReason.UNCERTAINTY,)
