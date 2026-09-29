from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A020")
ARM_A = "deterministic"
ARM_B = "deterministic_plus_oncox"
ARM_C = "deterministic_plus_jev_plus_oncox"
A12_QUALITY_MAX = 1.0
A19_QUALITY_TARGET = 0.50
NARRATIVE_EVIDENCE = (
    (
        "A006: bounded Jev reranking moved top-1 recall from 0.40 to 1.00 without changing "
        "shortlist membership (recorded architecture result).",
    ),
    (
        "A007: an independent absolute-viability Noul gate moved false acceptance from 1.00 to "
        "0.00 while keeping viable recall at 1.00 (recorded architecture result).",
    ),
)


@dataclass(frozen=True, slots=True)
class FrontierPoint:
    task_id: str
    arm_id: str
    quality: float
    input_tokens: int
    output_tokens: int
    calls: int
    provenance: str

    @property
    def tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def quality_per_1k_tokens(self) -> float:
        return self.quality / (self.tokens / 1000) if self.tokens else 0.0


@dataclass(frozen=True, slots=True)
class TaskFrontier:
    task_id: str
    quality_target: str
    points: tuple[FrontierPoint, ...]
    non_dominated: tuple[str, ...]
    dominated_by: dict[str, tuple[str, ...]]
    c_moves_frontier: bool
    reasons: tuple[str, ...]


def _latest_live(store: AppendOnlyJsonlStore, experiment_id: str) -> dict[str, Any]:
    for event in reversed(store.read_all()):
        payload = event.payload
        if payload.get("experiment_id") != experiment_id:
            continue
        measurements = payload.get("measurements", {})
        if payload.get("status") == "completed" and measurements.get("live"):
            return {"event_id": event.event_id, "occurred_at": event.occurred_at, **payload}
    raise RuntimeError(f"no completed live result for {experiment_id} in the store")


def _a012_task(record: dict[str, Any], repetition: int = 1) -> tuple[FrontierPoint, ...]:
    measurements = record["measurements"]
    repetitions = measurements["repetitions"]
    selected = next(
        (item for item in repetitions if item["repetition"] == repetition), repetitions[0]
    )
    metrics = selected["evaluation"]["metrics"]
    all_arm = selected["all_arm_resources"]
    cascade_arm = selected["cascade_arm_resources"]
    triage = selected["triage"]
    quality_b = A12_QUALITY_MAX
    quality_c = 1.0 - float(metrics["false_negative_rate"])
    provenance = f"{record['event_id']} repetition {selected['repetition']}"
    return (
        FrontierPoint(
            task_id="a012_oncox_cascade",
            arm_id=ARM_B,
            quality=quality_b,
            input_tokens=int(all_arm["input_tokens"]),
            output_tokens=int(all_arm["output_tokens"]),
            calls=int(all_arm["calls"]),
            provenance=provenance,
        ),
        FrontierPoint(
            task_id="a012_oncox_cascade",
            arm_id=ARM_C,
            quality=quality_c,
            input_tokens=int(cascade_arm["input_tokens"])
            + int(triage["usage"].get("input_tokens") or 0),
            output_tokens=int(cascade_arm["output_tokens"])
            + int(triage["usage"].get("output_tokens") or 0),
            calls=int(cascade_arm["calls"]) + 1,
            provenance=provenance,
        ),
    )


def _a019_task(record: dict[str, Any]) -> tuple[FrontierPoint, ...]:
    measurements = record["measurements"]
    arms = measurements["arms"]
    provenance = str(record["event_id"])
    points: list[FrontierPoint] = []
    arm_map = {
        ARM_A: "deterministic",
        ARM_B: "deterministic_plus_jev",
        ARM_C: "deterministic_plus_jev_plus_oncox",
    }
    for arm_id, source in arm_map.items():
        arm = arms[source]
        recall = float(arm["metrics"]["recall@1"])
        input_tokens = int(arm.get("input_tokens") or 0)
        output_tokens = int(arm.get("output_tokens") or 0)
        calls = int(arm.get("jev_calls") or 0) + int(arm.get("oncox_calls") or 0)
        if arm_id == ARM_C:
            # Arm C contains the Jev screen as well as OncoX, so its cost must include both.
            jev_arm = arms["deterministic_plus_jev"]
            input_tokens += int(jev_arm.get("input_tokens") or 0)
            output_tokens += int(jev_arm.get("output_tokens") or 0)
            calls += int(jev_arm.get("jev_calls") or 0)
        points.append(
            FrontierPoint(
                task_id="a019_masked_rediscovery",
                arm_id=arm_id,
                quality=min(recall / A19_QUALITY_TARGET, 1.0),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                calls=calls,
                provenance=provenance,
            )
        )
    return tuple(points)


def _dominates(left: FrontierPoint, right: FrontierPoint) -> bool:
    better_or_equal = left.tokens <= right.tokens and left.quality >= right.quality
    strictly_better = left.tokens < right.tokens or left.quality > right.quality
    return better_or_equal and strictly_better


def evaluate_frontier(
    *, task_id: str, quality_target: str, points: tuple[FrontierPoint, ...]
) -> TaskFrontier:
    if not points:
        raise ValueError("a frontier requires at least one point")
    if len({point.arm_id for point in points}) != len(points):
        raise ValueError("frontier arm ids must be unique per task")
    dominated_by: dict[str, tuple[str, ...]] = {}
    for point in points:
        dominators = tuple(
            other.arm_id
            for other in points
            if other.arm_id != point.arm_id and _dominates(other, point)
        )
        dominated_by[point.arm_id] = dominators
    non_dominated = tuple(point.arm_id for point in points if not dominated_by[point.arm_id])
    reasons: list[str] = []
    c_point = next((point for point in points if point.arm_id == ARM_C), None)
    c_moves = False
    if c_point is None:
        reasons.append("no C point was recorded for this task")
    else:
        c_moves = any(
            _dominates(c_point, other) for other in points if other.arm_id != ARM_C
        )
        if not c_moves:
            reasons.append("C does not strictly dominate any recorded arm on this task")
    return TaskFrontier(
        task_id=task_id,
        quality_target=quality_target,
        points=points,
        non_dominated=non_dominated,
        dominated_by=dominated_by,
        c_moves_frontier=c_moves,
        reasons=tuple(reasons),
    )


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    a012 = _latest_live(store, "A012")
    a019 = _latest_live(store, "A019")
    frontiers = (
        evaluate_frontier(
            task_id="a012_oncox_cascade",
            quality_target="useful-case retention (1 - cascade false-negative rate)",
            points=_a012_task(a012),
        ),
        evaluate_frontier(
            task_id="a019_masked_rediscovery",
            quality_target=f"recall@1 divided by the frozen target {A19_QUALITY_TARGET}",
            points=_a019_task(a019),
        ),
    )
    c_moves = any(frontier.c_moves_frontier for frontier in frontiers)
    c_on_frontier = any(ARM_C in frontier.non_dominated for frontier in frontiers)
    a012_metrics = a012["measurements"]["repetitions"][0]["evaluation"]["metrics"]
    resource_facts = {
        "a012_cascade_call_reduction": float(a012_metrics["oncox_call_reduction"]),
        "a012_false_negatives": float(a012_metrics["false_negative_count"]),
        "a019_jev_tokens_spent": int(
            a019["measurements"]["arms"]["deterministic_plus_jev"]["input_tokens"]
        )
        + int(a019["measurements"]["arms"]["deterministic_plus_jev"]["output_tokens"]),
        "a019_oncox_calls_spent": int(
            a019["measurements"]["arms"]["deterministic_plus_jev_plus_oncox"]["oncox_calls"]
        ),
    }
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": False,
            "arm_c_moves_frontier": c_moves,
            "arm_c_on_any_frontier": c_on_frontier,
            "frontiers": [asdict(frontier) for frontier in frontiers],
            "resource_facts": resource_facts,
            "narrative_evidence": [item[0] for item in NARRATIVE_EVIDENCE],
            "protocol": {
                "arms": [ARM_A, ARM_B, ARM_C],
                "dominance": (
                    "left dominates right when it uses no more tokens and loses no quality, and "
                    "is strictly better on at least one axis"
                ),
                "tasks": [frontier.task_id for frontier in frontiers],
                "sources": {
                    "a012_event": a012["event_id"],
                    "a019_event": a019["event_id"],
                },
                "quality_axes": {
                    frontier.task_id: frontier.quality_target for frontier in frontiers
                },
            },
            "cost": {
                "measured": False,
                "basis": "recorded-results analysis; no provider call is made",
            },
        },
        observations=(
            (
                "Arm C moved the quality-resource frontier on at least one recorded task."
                if c_moves
                else "Arm C did not move the frontier on the recorded tasks: the central "
                "hypothesis is narrowed rather than confirmed, and the Jev layer keeps its "
                "recorded value in gating and reranking rather than selective OncoX triage."
            ),
        ),
        limitations=(
            "This is a recorded-results analysis of two frozen tasks, not a new prospective "
            "comparison, and it cannot establish scientific discovery.",
            "Quality axes are task-relative: cascade retention for A012 and recall@1 against a "
            "frozen target for A019.",
            "Only A012 recorded a deterministic-plus-OncoX arm, and only A019 recorded all three.",
            "A006 and A007 are cited as recorded narrative evidence, not as frontier points.",
            "Token counts are provider-reported and no monetary cost is claimed.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
