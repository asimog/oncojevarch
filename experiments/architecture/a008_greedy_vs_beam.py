from __future__ import annotations

from dataclasses import asdict
from time import perf_counter

from discovery.beam import BranchEdge, ReplayTree, beam_search
from evaluation.search import evaluate_search_policy
from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A008")
WIDTHS = (1, 2, 3)


def _binary_trace(
    trace_id: str,
    root: tuple[tuple[str, float], tuple[str, float]],
    left: tuple[tuple[str, float], tuple[str, float]],
    right: tuple[tuple[str, float], tuple[str, float]],
) -> ReplayTree:
    return ReplayTree(
        trace_id=trace_id,
        edges_by_path={
            (): tuple(BranchEdge(*edge) for edge in root),
            (root[0][0],): tuple(BranchEdge(*edge) for edge in left),
            (root[1][0],): tuple(BranchEdge(*edge) for edge in right),
        },
    )


TRACES = (
    _binary_trace(
        "recover-1",
        (("local", 0.55), ("recoverable", 0.45)),
        (("wrong", 0.55), ("other", 0.45)),
        (("target", 0.99), ("other", 0.01)),
    ),
    _binary_trace(
        "recover-2",
        (("local", 0.60), ("recoverable", 0.40)),
        (("wrong", 0.51), ("other", 0.49)),
        (("target", 0.99), ("other", 0.01)),
    ),
    _binary_trace(
        "recover-3",
        (("local", 0.52), ("recoverable", 0.48)),
        (("wrong", 0.52), ("other", 0.48)),
        (("target", 0.90), ("other", 0.10)),
    ),
    _binary_trace(
        "clear-1",
        (("target-root", 0.80), ("noise", 0.20)),
        (("target", 0.90), ("other", 0.10)),
        (("wrong", 0.70), ("other", 0.30)),
    ),
    _binary_trace(
        "clear-2",
        (("noise", 0.25), ("target-root", 0.75)),
        (("wrong", 0.60), ("other", 0.40)),
        (("target", 0.88), ("other", 0.12)),
    ),
    ReplayTree(
        trace_id="requires-width-3",
        edges_by_path={
            (): (
                BranchEdge("alpha", 0.34),
                BranchEdge("beta", 0.33),
                BranchEdge("gamma", 0.33),
            ),
            ("alpha",): (BranchEdge("wrong", 0.55), BranchEdge("other", 0.45)),
            ("beta",): (BranchEdge("wrong", 0.60), BranchEdge("other", 0.40)),
            ("gamma",): (BranchEdge("target", 0.99), BranchEdge("other", 0.01)),
        },
    ),
)

EXPECTED: dict[str, tuple[str, ...]] = {
    "recover-1": ("recoverable", "target"),
    "recover-2": ("recoverable", "target"),
    "recover-3": ("recoverable", "target"),
    "clear-1": ("target-root", "target"),
    "clear-2": ("target-root", "target"),
    "requires-width-3": ("gamma", "target"),
}


def _execute() -> tuple[dict[int, dict[str, object]], dict[int, float]]:
    by_width: dict[int, dict[str, object]] = {}
    wall_time_ms: dict[int, float] = {}
    for width in WIDTHS:
        started = perf_counter()
        results = tuple(beam_search(trace, width=width) for trace in TRACES)
        wall_time_ms[width] = (perf_counter() - started) * 1000
        by_width[width] = {
            "metrics": asdict(evaluate_search_policy(expected=EXPECTED, results=results)),
            "traces": [asdict(result) for result in results],
        }
    return by_width, wall_time_ms


def run(*, settings: Settings, live: bool = False) -> str:
    del live
    frozen = FrozenExperiment.freeze(SPEC)
    first, wall_time_ms = _execute()
    replay, _ = _execute()
    reproducible = first == replay

    greedy = first[1]["metrics"]
    width_two = first[2]["metrics"]
    if not isinstance(greedy, dict) or not isinstance(width_two, dict):  # pragma: no cover
        raise TypeError("search metrics must be dictionaries")
    recall_gain = float(width_two["terminal_recall"]) - float(greedy["terminal_recall"])
    evaluation_ratio = float(width_two["mean_evaluated_edges"]) / float(
        greedy["mean_evaluated_edges"]
    )
    success = recall_gain >= 0.25 and evaluation_ratio <= 1.75 and reproducible

    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "success_criteria_met": success,
            "expected": EXPECTED,
            "widths": first,
            "wall_time_ms": wall_time_ms,
            "width_2_recall_gain": recall_gain,
            "width_2_evaluation_ratio": evaluation_ratio,
            "deterministic_replay_equal": reproducible,
        },
        observations=(
            (
                "Width 2 met the frozen recall/cost criteria."
                if success
                else "Width 2 did not meet the frozen recall/cost criteria."
            ),
            "Width 3 remains an explicitly costed comparison rather than an automatic default.",
        ),
        limitations=(
            "Frozen synthetic probabilities isolate search mechanics from Jev model quality.",
            "Six depth-two traces do not estimate performance on a biological search space.",
            "Wall time at this scale is descriptive; evaluated-edge count is the useful cost.",
        ),
    )
    AppendOnlyJsonlStore(settings.store_dir / "events.jsonl").append(
        "architecture_experiment_result", asdict(result)
    )
    return str(asdict(result))
