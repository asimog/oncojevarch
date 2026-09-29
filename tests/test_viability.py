import pytest

from evaluation.viability import evaluate_viability


def test_viability_metrics_distinguish_false_acceptance_and_rejection() -> None:
    metrics = evaluate_viability(
        expected={"viable": True, "missed": True, "bad": False, "rejected": False},
        accepted={"viable": True, "missed": False, "bad": True, "rejected": False},
        probabilities={"viable": 0.9, "missed": 0.4, "bad": 0.8, "rejected": 0.1},
    )

    assert metrics.false_acceptance_rate == 0.5
    assert metrics.false_rejection_rate == 0.5
    assert metrics.viable_recall == 0.5
    assert metrics.accuracy == 0.5
    assert metrics.coverage == 0.5
    assert metrics.brier_score == pytest.approx(0.255)


def test_viability_evaluation_rejects_unbounded_probability() -> None:
    with pytest.raises(ValueError, match="within"):
        evaluate_viability(
            expected={"yes": True, "no": False},
            accepted={"yes": True, "no": False},
            probabilities={"yes": 1.1, "no": 0.0},
        )
