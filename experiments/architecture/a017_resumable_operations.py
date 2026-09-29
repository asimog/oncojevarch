from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from typing import Any

from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from oncolab.recovery import (
    OperationStep,
    OperationSummary,
    ResumableRunner,
    compare_resume_arms,
)
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A017")
OPERATION_ID = "a017-operations"
INTERRUPTS = (None, 2, 4)
PROJECTS = ("TCGA-KIRC", "TCGA-KIRP", "TCGA-KICH")


def steps() -> tuple[OperationStep, ...]:
    """Frozen deterministic operation: six steps that would each write an evidence artifact."""

    def cohort(project_id: str) -> Callable[[], dict[str, Any]]:
        return lambda: {
            "measurement": "file_count_per_case",
            "project_id": project_id,
            "case_count": {"TCGA-KIRC": 537, "TCGA-KIRP": 291, "TCGA-KICH": 113}[project_id],
            "file_count": {"TCGA-KIRC": 35031, "TCGA-KIRP": 18749, "TCGA-KICH": 6076}[project_id],
        }

    def comparison(left: str, right: str) -> Callable[[], dict[str, Any]]:
        def produce() -> dict[str, Any]:
            counts = {
                "TCGA-KIRC": (537, 35031),
                "TCGA-KIRP": (291, 18749),
                "TCGA-KICH": (113, 6076),
            }
            ratio = round(
                (counts[left][1] / counts[left][0]) / (counts[right][1] / counts[right][0]), 4
            )
            return {
                "measurement": "files_per_case_ratio",
                "left": left,
                "right": right,
                "ratio": ratio,
            }

        return produce

    return (
        OperationStep("cohort_kirc", cohort("TCGA-KIRC")),
        OperationStep("cohort_kirp", cohort("TCGA-KIRP")),
        OperationStep("cohort_kich", cohort("TCGA-KICH")),
        OperationStep("compare_kirc_kirp", comparison("TCGA-KIRC", "TCGA-KIRP")),
        OperationStep("compare_kirc_kich", comparison("TCGA-KIRC", "TCGA-KICH")),
        OperationStep("summary", lambda: {"measurement": "operation_summary", "step_count": 6}),
    )


def operation_fingerprint() -> str:
    return sha256(
        json.dumps([step.name for step in steps()], sort_keys=True).encode("utf-8")
    ).hexdigest()


def _run_arm(*, store_dir: Path, arm_id: str, interrupts: tuple[int | None, ...]) -> dict[str, Any]:
    """Run one arm: apply each interruption in order, then resume to completion."""

    path = store_dir / f"a017-{arm_id}.jsonl"
    if path.exists():
        path.unlink()
    store = AppendOnlyJsonlStore(path)
    runner = ResumableRunner(store=store, operation_id=OPERATION_ID)
    attempts: list[dict[str, Any]] = []
    final: OperationSummary | None = None
    for interruption in interrupts:
        summary = runner.run(steps(), interrupt_after=interruption)
        attempts.append(asdict(summary) | {"complete": summary.complete})
        final = summary
        if summary.complete:
            break
    if final is None:
        raise ValueError("resumable arm ran no attempts")
    if not final.complete:
        final = runner.run(steps())
        attempts.append(asdict(final) | {"complete": final.complete})
    artifact_events = [
        event for event in store.read_all() if event.event_type == "operation_artifact"
    ]
    artifact_ids = [event.payload.get("artifact_id") for event in artifact_events]
    return {
        "arm_id": arm_id,
        "attempts": attempts,
        "summary": asdict(final),
        "artifact_events": len(artifact_events),
        "distinct_artifact_ids": len(set(artifact_ids)),
        "duplicate_artifact_writes": len(artifact_ids) - len(set(artifact_ids)),
    }


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    arms = {
        "uninterrupted": _run_arm(
            store_dir=settings.store_dir, arm_id="uninterrupted", interrupts=(None,)
        ),
        "interrupted_late": _run_arm(
            store_dir=settings.store_dir, arm_id="interrupted", interrupts=(4,)
        ),
        "interrupted_twice_early": _run_arm(
            store_dir=settings.store_dir, arm_id="interrupted_early", interrupts=(2, 4)
        ),
    }
    summaries = {arm_id: OperationSummary(**arm["summary"]) for arm_id, arm in arms.items()}
    comparison = compare_resume_arms(summaries)
    duplicate_writes = sum(arm["duplicate_artifact_writes"] for arm in arms.values())
    expected_artifacts = len(steps())
    artifact_event_counts = {arm["artifact_events"] for arm in arms.values()}
    passed = (
        duplicate_writes == 0
        and comparison.metrics["result_equality"] == 1.0
        and comparison.metrics["incomplete_arm_count"] == 0.0
        and artifact_event_counts == {expected_artifacts}
        and comparison.metrics["total_reused_steps"] > 0.0
    )
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": False,
            "idempotent_resume_supported": passed,
            "operation_fingerprint": operation_fingerprint(),
            "operation_id": OPERATION_ID,
            "step_count": expected_artifacts,
            "comparison": asdict(comparison),
            "arms": {
                arm_id: {key: value for key, value in arm.items() if key != "summary"}
                for arm_id, arm in arms.items()
            },
            "duplicate_artifact_writes": duplicate_writes,
            "artifact_event_counts": sorted(artifact_event_counts),
            "protocol": {
                "arms": list(arms),
                "interrupt_points": list(INTERRUPTS),
                "artifact_identity": "sha256(operation_id::step::payload)",
                "change_rule": (
                    "a changed step payload creates a different artifact identity instead of "
                    "rewriting the previous artifact"
                ),
            },
            "cost": {
                "measured": False,
                "basis": "deterministic in-process operation; no provider call is made",
            },
        },
        observations=(
            (
                "Interrupted and resumed runs produced the same final digest as an uninterrupted "
                "run with no duplicate artifacts and completed steps reused rather than redone."
                if passed
                else "Resume behavior failed a frozen condition: duplicates, unequal results, or "
                "incomplete arms."
            ),
        ),
        limitations=(
            "Fault injection is in-process, not a real crash or power loss.",
            "The operation is deterministic; real steps may have external side effects.",
            "Artifact identity covers step payloads, not provider or source state.",
            "This architecture task cannot create ScientificEvidence.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
