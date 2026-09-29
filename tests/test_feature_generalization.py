import pytest

from evaluation.discovery import (
    FeatureCase,
    candidate_phrases,
    discover_phrases,
    evaluate_features,
    fit_threshold,
    phrase_stability,
    split_integrity_findings,
)
from experiments.architecture.a014_feature_generalization import (
    BASELINE_FEATURES,
    candidate_features,
    corpus,
)


def _cases() -> tuple[FeatureCase, ...]:
    return (
        FeatureCase("d1", "marker alpha missing per-case counts", True, "development"),
        FeatureCase("d2", "marker alpha missing survival follow-up", True, "development"),
        FeatureCase("d3", "marker beta missing survival follow-up", False, "development"),
        FeatureCase("d4", "marker beta missing survival follow-up", False, "development"),
        FeatureCase("v1", "marker alpha missing per-case counts", True, "validation"),
        FeatureCase("v2", "marker beta missing survival follow-up", False, "validation"),
        FeatureCase("t1", "marker alpha missing per-case counts", True, "locked_test"),
        FeatureCase("t2", "marker beta missing survival follow-up", False, "locked_test"),
    )


def test_corpus_splits_are_frozen_and_disjoint() -> None:
    cases = corpus()

    assert len(cases) == 60
    assert {case.split for case in cases} == {"development", "validation", "locked_test"}
    assert len({case.case_id for case in cases}) == 60
    assert len([case for case in cases if case.split == "development"]) == 30
    assert len([case for case in cases if case.split == "validation"]) == 15
    assert len([case for case in cases if case.split == "locked_test"]) == 15
    assert split_integrity_findings(cases, label_tokens=("needs_deeper_reasoning",)) == ()


def test_discovery_only_accepts_development_cases() -> None:
    cases = _cases()

    with pytest.raises(ValueError, match="development"):
        discover_phrases(
            tuple(case for case in cases if case.split != "development"),
            phrases=("marker alpha",),
            max_features=2,
            min_score=0.1,
        )


def test_discovery_prefers_discriminative_phrases_and_is_deterministic() -> None:
    cases = _cases()
    phrases = candidate_phrases(cases, n_min=2, n_max=2, min_cases=2)

    first = discover_phrases(
        tuple(case for case in cases if case.split == "development"),
        phrases=phrases,
        max_features=2,
        min_score=0.5,
    )
    second = discover_phrases(
        tuple(case for case in cases if case.split == "development"),
        phrases=phrases,
        max_features=2,
        min_score=0.5,
    )

    assert first == second
    assert first[0].phrase == "alpha missing"
    assert first[0].score == 1.0


def test_conjunction_features_require_every_phrase() -> None:
    cases = _cases()
    cases = cases + (
        FeatureCase("d5", "marker alpha missing per-case counts", False, "development"),
    )

    discovered = discover_phrases(
        tuple(case for case in cases if case.split == "development"),
        phrases=("marker alpha && missing per-case counts",),
        max_features=1,
        min_score=0.1,
    )

    assert [item.phrase for item in discovered] == ["marker alpha && missing per-case counts"]
    assert discovered[0].dev_negative_rate == pytest.approx(1 / 3)


def test_threshold_fitting_only_accepts_validation_cases() -> None:
    cases = _cases()

    with pytest.raises(ValueError, match="validation"):
        fit_threshold(
            tuple(case for case in cases if case.split == "development"),
            features=("marker alpha",),
            weights={"marker alpha": 1.0},
            grid=(0.5,),
        )


def test_locked_test_evaluation_separates_the_two_arms() -> None:
    cases = _cases()
    validation = tuple(case for case in cases if case.split == "validation")
    locked_test = tuple(case for case in cases if case.split == "locked_test")
    weights = {"marker alpha": 1.5}

    threshold = fit_threshold(
        validation, features=("marker alpha",), weights=weights, grid=(0.0, 1.0, 2.0)
    )
    strong = evaluate_features(
        locked_test, features=("marker alpha",), weights=weights, threshold=threshold
    )
    weak = evaluate_features(
        locked_test,
        features=BASELINE_FEATURES,
        weights={feature: 0.0 for feature in BASELINE_FEATURES},
        threshold=threshold,
    )

    assert threshold == 1.0
    assert strong.metrics["accuracy"] == 1.0
    assert strong.metrics["positive_recall"] == 1.0
    assert strong.metrics["negative_specificity"] == 1.0
    assert weak.metrics["positive_recall"] == 0.0


def test_split_integrity_flags_label_tokens_in_case_text() -> None:
    findings = split_integrity_findings(
        _cases(), label_tokens=("missing per-case counts", "marker alpha")
    )

    assert findings
    assert any("marker alpha" in finding for finding in findings)


def test_feature_stability_uses_set_overlap() -> None:
    cases = _cases()
    development = tuple(case for case in cases if case.split == "development")
    validation = tuple(case for case in cases if case.split == "validation")
    phrases = candidate_phrases(cases, n_min=2, n_max=2, min_cases=2)

    dev_features = discover_phrases(development, phrases=phrases, max_features=3, min_score=0.5)
    val_features = discover_phrases(
        validation, phrases=phrases, max_features=3, min_score=0.5, expected_split="validation"
    )

    assert phrase_stability(dev_features, val_features) == pytest.approx(1.0)


def test_frozen_candidate_language_includes_family_marker_conjunctions() -> None:
    features = candidate_features(corpus())

    assert "availability_claim && per-case sample inventories" in features
    assert "population_claim && population registry incidence rates" in features
    assert len(features) == len(set(features))
