import json
from pathlib import Path

from experiments.architecture.a021_scientific_nucleus import run as run_a021
from experiments.architecture.a022_capability_search_evaluation import run as run_a022
from experiments.architecture.a023_gap_loop import run as run_a023
from experiments.architecture.a024_research_control_loop import run as run_a024
from experiments.architecture.a025_repaired_capability_search import run as run_a025
from oncodex.config import Settings


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


def test_nucleus_admits_evidence_and_refuses_a_value_less_measurement(tmp_path: Path) -> None:
    payload = json.loads(run_a021(settings=_settings(tmp_path)))

    measurements = payload["measurements"]
    assert measurements["admitted"] is True
    assert measurements["refusal_reasons"] == ["unrepresentable_value"]
    assert measurements["persisted_evidence"] is True
    assert measurements["investigation_revisions"] == 2
    assert measurements["latest_evidence_ids"] == ["ev-a021-direct"]


def test_search_evaluation_is_deterministic_and_keeps_the_mechanism(tmp_path: Path) -> None:
    first = json.loads(run_a022(settings=_settings(tmp_path / "one")))
    second = json.loads(run_a022(settings=_settings(tmp_path / "two")))

    assert first["measurements"]["arms"] == second["measurements"]["arms"]
    assert first["measurements"]["decision"] == "reopen capability retrieval"
    assert first["measurements"]["arms"]["raw_token_overlap"]["top1_correct"] == 6
    assert first["measurements"]["arms"]["raw_token_overlap"]["false_hits"] == 1
    assert first["measurements"]["arms"]["raw_token_overlap"]["false_hit_needs"] == [
        "call structural variants in a tumor normal pair"
    ]


def test_gap_loop_routes_all_kinds_and_blocks_unsafe_promotion(tmp_path: Path) -> None:
    payload = json.loads(run_a023(settings=_settings(tmp_path)))

    measurements = payload["measurements"]
    assert measurements["routes_correct"] == 4
    assert measurements["unsafe_promotions_blocked"] == 2
    assert measurements["activation_outcome"] == "evidence"
    assert measurements["reasoning_refusal_reasons"] == ["missing_provenance"]
    assert measurements["loop_gap_outcome"] == "gap"


def test_repaired_search_meets_the_rule_a022_failed(tmp_path: Path) -> None:
    payload = json.loads(run_a025(settings=_settings(tmp_path)))

    measurements = payload["measurements"]
    assert measurements["predecessor"] == "A022"
    assert measurements["decision"] == (
        "keep the repaired deterministic search as the initial mechanism"
    )
    assert measurements["arms"]["repaired_token_overlap"]["top1_correct"] == 6
    assert measurements["arms"]["repaired_token_overlap"]["false_hits"] == 0
    assert measurements["arms"]["repaired_token_overlap"]["misses_detected"] == 2


def test_control_loop_is_session_independent(tmp_path: Path) -> None:
    payload = json.loads(run_a024(settings=_settings(tmp_path)))

    measurements = payload["measurements"]
    assert measurements["step_1_outcome"] == "evidence"
    assert measurements["step_2_outcome"] == "gap"
    assert measurements["persisted_evidence"] is True
    assert measurements["persisted_gap"] is True
    assert measurements["session_independent"] is True
    assert measurements["revisions"] == 3
