import json
from pathlib import Path

from experiments.scientific.s001_public_metadata_association import (
    ITERATIONS,
    MIN_PROJECTS,
    ProjectAssayProfile,
    max_site_share,
    parse_profiles,
    permutation_statistic,
    run,
)
from oncodex.config import Settings

PAYLOAD = {
    "data": {
        "hits": [
            {
                "project_id": "TCGA-B",
                "primary_site": "Lung",
                "summary": {
                    "experimental_strategies": [
                        {"experimental_strategy": "RNA-Seq", "file_count": 5},
                        {"experimental_strategy": "WXS", "file_count": 2},
                    ]
                },
            },
            {
                "project_id": "TCGA-A",
                "primary_site": "Kidney",
                "summary": {
                    "experimental_strategies": [
                        {"experimental_strategy": "RNA-Seq", "file_count": 3},
                        {"experimental_strategy": "WXS", "file_count": 0},
                    ]
                },
            },
        ]
    }
}


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        repo_root=tmp_path,
        store_dir=tmp_path / "store",
        agent_model=None,
        jev_model=None,
        openrouter_api_key=None,
        typesafe_api_key=None,
        openrouter_base_url="https://openrouter.ai/api/v1",
        disable_tracing=True,
    )


def test_parse_profiles_reads_strategy_counts_and_sorts() -> None:
    profiles = parse_profiles(PAYLOAD)

    assert [profile.project_id for profile in profiles] == ["TCGA-A", "TCGA-B"]
    assert (profiles[0].rna_seq, profiles[0].wxs) == (True, False)
    assert (profiles[1].rna_seq, profiles[1].wxs) == (True, True)


def test_max_site_share_counts_only_co_available_projects() -> None:
    sites = ["Lung", "Lung", "Kidney"]
    rna = [True, True, False]
    wxs = [True, False, True]

    assert max_site_share(sites, rna, wxs) == 1.0
    assert max_site_share(sites, [False, False, False], wxs) == 0.0


def test_permutation_statistic_is_deterministic_and_bounded() -> None:
    profiles = tuple(
        ProjectAssayProfile(
            project_id=f"P{index}",
            primary_site=("Lung", "Kidney", "Brain")[index % 3],
            rna_seq=index % 2 == 0,
            wxs=index % 3 != 2,
        )
        for index in range(12)
    )

    first = permutation_statistic(profiles, iterations=50)
    second = permutation_statistic(profiles, iterations=50)

    assert first == second
    assert 0.0 < first["permutation_p"] <= 1.0
    assert 0.0 <= first["null_mean"] <= 1.0


def test_offline_preflight_records_no_measurement(tmp_path: Path) -> None:
    payload = json.loads(run(settings=_settings(tmp_path)))

    measurements = payload["measurements"]
    assert payload["status"] == "frozen"
    assert measurements["live"] is False
    assert measurements["seed"] == "s001:2026-09-30"
    assert measurements["iterations"] == ITERATIONS
    assert measurements["min_projects"] == MIN_PROJECTS
    assert measurements["spec_errors"] == []


def test_s001_spec_is_complete_and_scientific() -> None:
    from experiments.scientific.catalog import SCIENTIFIC_EXPERIMENTS
    from oncolab.experiments import ExperimentClass

    assert [experiment.experiment_id for experiment in SCIENTIFIC_EXPERIMENTS] == [
        "S001",
        "S002",
    ]
    assert all(
        experiment.experiment_class is ExperimentClass.SCIENTIFIC
        and experiment.validation_errors() == ()
        for experiment in SCIENTIFIC_EXPERIMENTS
    )


def test_s002_preflight_records_the_corrected_minimum(tmp_path: Path) -> None:
    from experiments.scientific.s002_public_metadata_association import run as run_s002

    payload = json.loads(run_s002(settings=_settings(tmp_path)))

    measurements = payload["measurements"]
    assert payload["status"] == "frozen"
    assert measurements["predecessor"] == "S001"
    assert measurements["min_projects"] == 30
