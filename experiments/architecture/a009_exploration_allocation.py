from __future__ import annotations

from dataclasses import asdict
from time import perf_counter

from discovery.allocation import ExplorationAllocation, allocate_frontier
from discovery.frontier import FrontierEntry, SurvivalReason
from evaluation.exploration import evaluate_exploration
from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A009")
BASELINE = ExplorationAllocation(promise_slots=4, uncertainty_slots=0, novelty_slots=0)
TREATMENT = ExplorationAllocation(promise_slots=2, uncertainty_slots=1, novelty_slots=1)


def _candidate(
    candidate_id: str, promise: float, uncertainty: float, novelty: float
) -> FrontierEntry:
    return FrontierEntry(
        candidate_id=candidate_id,
        state_ref=f"a009:{candidate_id}",
        reasons=(SurvivalReason.PROMISE,),
        relative_rank=promise,
        uncertainty=uncertainty,
        novelty=novelty,
    )


CANDIDATES = (
    _candidate("c01", 0.95, 0.10, 0.10),
    _candidate("c02", 0.90, 0.15, 0.12),
    _candidate("c03", 0.85, 0.20, 0.25),
    _candidate("c04", 0.80, 0.25, 0.20),
    _candidate("c05", 0.60, 0.98, 0.30),
    _candidate("c06", 0.55, 0.90, 0.35),
    _candidate("c07", 0.50, 0.40, 0.99),
    _candidate("c08", 0.45, 0.50, 0.92),
    _candidate("c09", 0.40, 0.60, 0.50),
    _candidate("c10", 0.35, 0.70, 0.70),
)
OUTCOMES = {
    "c01": True,
    "c02": True,
    "c03": False,
    "c04": False,
    "c05": True,
    "c06": False,
    "c07": True,
    "c08": False,
    "c09": False,
    "c10": False,
}


def _execute() -> tuple[dict[str, object], dict[str, float]]:
    results: dict[str, object] = {}
    wall_time_ms: dict[str, float] = {}
    for arm_id, allocation in (("top_score", BASELINE), ("exploration", TREATMENT)):
        started = perf_counter()
        selected = allocate_frontier(CANDIDATES, allocation)
        wall_time_ms[arm_id] = (perf_counter() - started) * 1000
        results[arm_id] = {
            "allocation": asdict(allocation),
            "selected": [asdict(item) for item in selected],
            "metrics": asdict(evaluate_exploration(outcomes=OUTCOMES, selected=selected)),
        }
    return results, wall_time_ms


def run(*, settings: Settings, live: bool = False) -> str:
    del live
    frozen = FrozenExperiment.freeze(SPEC)
    first, wall_time_ms = _execute()
    replay, _ = _execute()
    reproducible = first == replay
    baseline = first["top_score"]
    treatment = first["exploration"]
    if not isinstance(baseline, dict) or not isinstance(treatment, dict):  # pragma: no cover
        raise TypeError("exploration arms must be dictionaries")
    baseline_metrics = baseline["metrics"]
    treatment_metrics = treatment["metrics"]
    baseline_selected = baseline["selected"]
    treatment_selected = treatment["selected"]
    if not all(
        isinstance(value, (dict, list))
        for value in (baseline_metrics, treatment_metrics, baseline_selected, treatment_selected)
    ):  # pragma: no cover
        raise TypeError("exploration result has an invalid shape")
    if not isinstance(baseline_metrics, dict) or not isinstance(treatment_metrics, dict):
        raise TypeError("exploration metrics must be dictionaries")
    if not isinstance(baseline_selected, list) or not isinstance(treatment_selected, list):
        raise TypeError("exploration selections must be lists")

    recall_gain = float(treatment_metrics["useful_recall"]) - float(
        baseline_metrics["useful_recall"]
    )
    treatment_ids = {str(item["candidate_id"]) for item in treatment_selected}
    top_two_preserved = {"c01", "c02"} <= treatment_ids
    equal_budget = treatment_metrics["selected_count"] == baseline_metrics["selected_count"]
    success = recall_gain >= 0.25 and top_two_preserved and bool(equal_budget) and reproducible

    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "success_criteria_met": success,
            "candidate_signals": [asdict(candidate) for candidate in CANDIDATES],
            "locked_outcomes": OUTCOMES,
            "arms": first,
            "wall_time_ms": wall_time_ms,
            "useful_recall_gain": recall_gain,
            "top_two_promise_preserved": top_two_preserved,
            "equal_budget": equal_budget,
            "deterministic_replay_equal": reproducible,
        },
        observations=(
            (
                "The exploration allocation met the frozen equal-budget criteria."
                if success
                else "The exploration allocation did not meet the frozen criteria."
            ),
        ),
        limitations=(
            "Synthetic outcomes isolate allocation behavior from scientific validity.",
            "The 2/1/1 slot split is prespecified for this fixture, not a permanent policy.",
            "Useful labels were locked for evaluation and are unavailable to selection code.",
        ),
    )
    AppendOnlyJsonlStore(settings.store_dir / "events.jsonl").append(
        "architecture_experiment_result", asdict(result)
    )
    return str(asdict(result))
