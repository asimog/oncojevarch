import pytest

from evaluation.ranking import evaluate_rankings, promote_choice


def test_ranking_metrics_capture_top_k_and_reciprocal_rank() -> None:
    metrics = evaluate_rankings(
        expected={"q1": "a", "q2": "d"},
        rankings={"q1": ("a", "b"), "q2": ("c", "d")},
        k=2,
    )

    assert metrics.recall_at_1 == 0.5
    assert metrics.recall_at_k == 1.0
    assert metrics.precision_at_1 == 0.5
    assert metrics.mean_reciprocal_rank == 0.75


def test_promote_choice_preserves_shortlist_membership() -> None:
    assert promote_choice(("a", "b", "c"), "c") == ("c", "a", "b")


def test_promote_choice_rejects_candidate_outside_shortlist() -> None:
    with pytest.raises(ValueError, match="outside shortlist"):
        promote_choice(("a", "b"), "c")
