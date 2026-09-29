import pytest

from evaluation.rediscovery import (
    MaskedProject,
    RankedCandidate,
    ambiguous_cases,
    apply_overrides,
    build_features,
    evaluate_rankings,
    leakage_findings,
    leave_one_out_ranking,
    mask_id_for,
    permuted_labels,
)


def _projects() -> tuple[MaskedProject, ...]:
    return (
        MaskedProject("p1", "A", {"x": 0.9, "y": 0.1}),
        MaskedProject("p2", "A", {"x": 0.8, "y": 0.2}),
        MaskedProject("p3", "B", {"x": 0.1, "y": 0.9}),
        MaskedProject("p4", "B", {"x": 0.2, "y": 0.8}),
    )


def test_mask_identifier_does_not_reveal_the_source() -> None:
    first = mask_id_for("TCGA-KIRC")

    assert first.startswith("p")
    assert "kirc" not in first.lower()
    assert first == mask_id_for("TCGA-KIRC")


def test_features_are_shares_of_the_recorded_file_total() -> None:
    features = build_features(case_count=100, file_count=1000, profile={"a": 250.0, "b": 750.0})

    assert features["a"] == pytest.approx(0.25)
    assert features["b"] == pytest.approx(0.75)
    assert features["files_per_case"] == pytest.approx(10.0)
    with pytest.raises(ValueError, match="positive counts"):
        build_features(case_count=0, file_count=1, profile={"a": 1.0})


def test_leave_one_out_ranking_recovers_the_grouped_label() -> None:
    rankings = leave_one_out_ranking(_projects())
    labels = {project.mask_id: project.label for project in _projects()}
    metrics = evaluate_rankings(rankings=rankings, labels=labels, k_values=(1, 2))

    assert metrics.metrics["recall@1"] == 1.0
    assert metrics.metrics["mean_reciprocal_rank"] == 1.0


def test_ranking_requires_at_least_three_projects_and_two_labels() -> None:
    with pytest.raises(ValueError, match="at least three projects"):
        leave_one_out_ranking(_projects()[:2])
    with pytest.raises(ValueError, match="at least two candidate labels"):
        leave_one_out_ranking(
            tuple(
                MaskedProject(project.mask_id, "A", project.features)
                for project in _projects()
            )
        )


def test_ambiguity_margin_selects_only_close_rankings() -> None:
    rankings = (
        RankedCandidate(mask_id="p1", ranked_labels=("A", "B"), distances=(1.0, 1.01)),
        RankedCandidate(mask_id="p2", ranked_labels=("A", "B"), distances=(1.0, 3.0)),
    )

    assert ambiguous_cases(rankings, relative_margin=0.05) == ("p1",)


def test_overrides_must_permute_the_existing_candidates() -> None:
    rankings = leave_one_out_ranking(_projects())

    updated = apply_overrides(rankings, {"p1": ("B", "A")})
    overridden = next(ranking for ranking in updated if ranking.mask_id == "p1")

    assert overridden.ranked_labels == ("B", "A")
    with pytest.raises(ValueError, match="unknown label"):
        apply_overrides(rankings, {"p1": ("C", "A")})
    with pytest.raises(ValueError, match="permutation"):
        apply_overrides(rankings, {"p1": ("A",)})


def test_permuted_labels_is_a_derangement() -> None:
    labels = {"p1": "A", "p2": "A", "p3": "B", "p4": "B", "p5": "C"}

    permuted = permuted_labels(labels)

    assert all(permuted[mask_id] != labels[mask_id] for mask_id in labels)
    assert sorted(permuted.values()) == sorted(labels.values())


def test_leakage_findings_flag_masked_identifiers_and_null_success() -> None:
    clean = leakage_findings(
        masked_text="p1 profile only",
        secrets=("TCGA-KIRC",),
        null_recall_at_1=0.2,
        chance_recall_at_1=0.2,
        margin=0.15,
    )
    leaked = leakage_findings(
        masked_text="TCGA-KIRC profile",
        secrets=("TCGA-KIRC",),
        null_recall_at_1=0.6,
        chance_recall_at_1=0.2,
        margin=0.15,
    )

    assert clean == ()
    assert len(leaked) == 2
