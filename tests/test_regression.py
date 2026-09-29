import pytest

from evaluation.regression import (
    ModelRegressionEvaluation,
    RegressionObservation,
    compare_model_versions,
)


def _observation(
    model_id: str, probabilities: dict[str, float], *, latency_ms: float = 100.0
) -> RegressionObservation:
    return RegressionObservation(
        model_id=model_id,
        probabilities=probabilities,
        usage={"input_tokens": 10, "output_tokens": 5},
        latency_ms=latency_ms,
    )


LABELS = {"valid__a": True, "valid__b": True, "null__a": False, "null__b": False}
GROUPS = {"valid__a": "valid", "valid__b": "valid", "null__a": "null_1", "null__b": "null_2"}
BASELINE_PROBABILITIES = {"valid__a": 0.95, "valid__b": 0.9, "null__a": 0.05, "null__b": 0.1}


def _compare(
    candidate: RegressionObservation,
    control: RegressionObservation | None = None,
    **overrides: float,
) -> ModelRegressionEvaluation:
    return compare_model_versions(
        labels=LABELS,
        baseline=_observation("jev-1.13.0", BASELINE_PROBABILITIES),
        candidate=candidate,
        control=control,
        threshold=0.5,
        groups=GROUPS,
        **overrides,
    )


def test_identical_candidate_is_approved() -> None:
    evaluation = compare_model_versions(
        labels=LABELS,
        baseline=_observation("jev-1.13.0", BASELINE_PROBABILITIES),
        candidate=_observation("jev-preview", dict(BASELINE_PROBABILITIES)),
        control=_observation(
            "jev-1.13.0", {"valid__a": 0.94, "valid__b": 0.88, "null__a": 0.06, "null__b": 0.11}
        ),
        threshold=0.5,
        groups=GROUPS,
    )

    assert evaluation.failures == ()
    assert evaluation.metrics["candidate_decision_agreement"] == 1.0
    assert evaluation.metrics["candidate_mean_abs_drift"] == 0.0
    assert evaluation.metrics["candidate_brier"] == evaluation.metrics["baseline_brier"]
    assert evaluation.metrics["candidate_drift_excess_over_control"] < 0.05


def test_candidate_that_flips_a_null_claim_reports_every_frozen_failure() -> None:
    evaluation = _compare(
        _observation(
            "jev-preview", {"valid__a": 0.95, "valid__b": 0.9, "null__a": 0.8, "null__b": 0.1}
        ),
        _observation("jev-1.13.0", dict(BASELINE_PROBABILITIES)),
    )

    failures = " | ".join(evaluation.failures)
    assert "candidate decision agreement below the frozen minimum" in failures
    assert "a negative group claim rate exceeds the frozen maximum" in failures
    assert "candidate calibration is worse than the frozen allowance" in failures
    assert evaluation.metrics["candidate_negative_agreement"] == 0.5
    assert evaluation.metrics["candidate_null_1_mean_abs_drift"] == pytest.approx(0.75)


def test_control_separates_provider_noise_from_model_drift() -> None:
    evaluation = _compare(
        _observation(
            "jev-preview", {"valid__a": 0.95, "valid__b": 0.85, "null__a": 0.05, "null__b": 0.1}
        ),
        _observation(
            "jev-1.13.0", {"valid__a": 0.93, "valid__b": 0.85, "null__a": 0.05, "null__b": 0.1}
        ),
    )

    assert evaluation.failures == ()
    assert evaluation.metrics["candidate_mean_abs_drift"] == pytest.approx(0.0125)
    assert evaluation.metrics["control_mean_abs_drift"] == pytest.approx(0.0175)
    assert evaluation.metrics["candidate_drift_excess_over_control"] == pytest.approx(-0.005)


def test_threshold_crossing_is_exact_at_the_frozen_boundary() -> None:
    evaluation = _compare(
        _observation(
            "jev-preview", {"valid__a": 0.5, "valid__b": 0.5, "null__a": 0.5, "null__b": 0.5}
        ),
        _observation(
            "jev-1.13.0", {"valid__a": 0.5, "valid__b": 0.5, "null__a": 0.4999, "null__b": 0.4999}
        ),
    )

    assert evaluation.metrics["candidate_decision_agreement"] == 0.5
    assert evaluation.metrics["candidate_positive_claim_rate"] == 1.0
    assert evaluation.metrics["candidate_negative_mean_claim_rate"] == 1.0


def test_answers_must_match_the_frozen_question_set() -> None:
    with pytest.raises(ValueError, match="frozen question set"):
        _compare(_observation("jev-preview", {"valid__a": 0.9}))


def test_probabilities_must_be_bounded() -> None:
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        _compare(
            _observation(
                "jev-preview", {"valid__a": 1.5, "valid__b": 0.9, "null__a": 0.05, "null__b": 0.1}
            )
        )


def test_groups_must_match_the_frozen_question_set() -> None:
    with pytest.raises(ValueError, match="groups do not match"):
        compare_model_versions(
            labels=LABELS,
            baseline=_observation("jev-1.13.0", BASELINE_PROBABILITIES),
            candidate=_observation("jev-preview", BASELINE_PROBABILITIES),
            threshold=0.5,
            groups={"valid__a": "valid"},
        )
