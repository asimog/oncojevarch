import pytest

from experiments.architecture.a020_frontier import (
    ARM_A,
    ARM_B,
    ARM_C,
    FrontierPoint,
    evaluate_frontier,
)


def _point(arm: str, *, quality: float, tokens: int) -> FrontierPoint:
    return FrontierPoint(
        task_id="t",
        arm_id=arm,
        quality=quality,
        input_tokens=tokens,
        output_tokens=0,
        calls=1,
        provenance="test",
    )


def test_point_reports_tokens_and_quality_per_thousand_tokens() -> None:
    point = _point(ARM_A, quality=0.5, tokens=2000)

    assert point.tokens == 2000
    assert point.quality_per_1k_tokens == pytest.approx(0.25)


def test_cascade_that_saves_nothing_does_not_move_the_frontier() -> None:
    frontier = evaluate_frontier(
        task_id="t",
        quality_target="retention",
        points=(
            _point(ARM_B, quality=1.0, tokens=1000),
            _point(ARM_C, quality=1.0, tokens=1100),
        ),
    )

    assert frontier.non_dominated == (ARM_B,)
    assert frontier.dominated_by[ARM_C] == (ARM_B,)
    assert frontier.c_moves_frontier is False
    assert "C does not strictly dominate" in frontier.reasons[0]


def test_cascade_that_halves_cost_at_equal_quality_moves_the_frontier() -> None:
    frontier = evaluate_frontier(
        task_id="t",
        quality_target="retention",
        points=(
            _point(ARM_B, quality=1.0, tokens=1000),
            _point(ARM_C, quality=1.0, tokens=500),
        ),
    )

    assert frontier.non_dominated == (ARM_C,)
    assert frontier.c_moves_frontier is True


def test_cheap_arm_that_loses_quality_is_not_dominated() -> None:
    frontier = evaluate_frontier(
        task_id="t",
        quality_target="recall@1 / target",
        points=(
            _point(ARM_A, quality=0.5, tokens=0),
            _point(ARM_B, quality=0.6, tokens=100),
            _point(ARM_C, quality=0.6, tokens=130),
        ),
    )

    assert set(frontier.non_dominated) == {ARM_A, ARM_B}
    assert frontier.dominated_by[ARM_C] == (ARM_B,)
    assert frontier.c_moves_frontier is False


def test_equal_points_dominate_nothing() -> None:
    frontier = evaluate_frontier(
        task_id="t",
        quality_target="retention",
        points=(
            _point(ARM_B, quality=0.9, tokens=100),
            _point(ARM_C, quality=0.9, tokens=100),
        ),
    )

    assert set(frontier.non_dominated) == {ARM_B, ARM_C}
    assert frontier.dominated_by == {ARM_B: (), ARM_C: ()}
    assert frontier.c_moves_frontier is False


def test_frontier_requires_unique_arms() -> None:
    with pytest.raises(ValueError, match="unique"):
        evaluate_frontier(
            task_id="t",
            quality_target="retention",
            points=(
                _point(ARM_C, quality=1.0, tokens=10),
                _point(ARM_C, quality=1.0, tokens=20),
            ),
        )
