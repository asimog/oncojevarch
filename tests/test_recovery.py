from pathlib import Path

import pytest

from oncolab.recovery import (
    OperationStep,
    OperationSummary,
    ResumableRunner,
    artifact_identity,
    compare_resume_arms,
)
from store.jsonl import AppendOnlyJsonlStore


def _steps() -> tuple[OperationStep, ...]:
    return (
        OperationStep("first", lambda: {"value": 1}),
        OperationStep("second", lambda: {"value": 2}),
        OperationStep("third", lambda: {"value": 3}),
    )


def _runner(tmp_path: Path) -> ResumableRunner:
    return ResumableRunner(
        store=AppendOnlyJsonlStore(tmp_path / "events.jsonl"), operation_id="op-1"
    )


def _summary(status: str, *, executed: int, reused: int) -> OperationSummary:
    return OperationSummary(
        operation_id="op-1",
        status=status,
        outcomes=(),
        executed_steps=executed,
        reused_steps=reused,
        duplicate_artifacts=0,
        final_digest="digest",
    )


def test_uninterrupted_run_executes_every_step(tmp_path: Path) -> None:
    summary = _runner(tmp_path).run(_steps())

    assert summary.complete
    assert summary.executed_steps == 3
    assert summary.reused_steps == 0
    assert summary.duplicate_artifacts == 0


def test_resume_reuses_completed_steps_and_keeps_the_result(tmp_path: Path) -> None:
    runner = _runner(tmp_path)

    interrupted = runner.run(_steps(), interrupt_after=1)
    resumed = runner.run(_steps())

    assert interrupted.status == "interrupted"
    assert interrupted.executed_steps == 2
    assert resumed.complete
    assert resumed.executed_steps == 1
    assert resumed.reused_steps == 2
    assert resumed.duplicate_artifacts == 0
    assert resumed.final_digest == runner.run(_steps()).final_digest


def test_repeated_identical_runs_never_write_a_second_artifact(tmp_path: Path) -> None:
    runner = _runner(tmp_path)

    first = runner.run(_steps())
    second = runner.run(_steps())

    assert first.final_digest == second.final_digest
    assert second.executed_steps == 0
    assert second.reused_steps == 3
    assert second.duplicate_artifacts == 0
    stored = [
        event for event in runner.store.read_all() if event.event_type == "operation_artifact"
    ]
    assert len(stored) == 3


def test_changed_step_payload_becomes_a_new_artifact_identity(tmp_path: Path) -> None:
    runner = _runner(tmp_path)
    runner.run(_steps()[:1])
    changed = (OperationStep("first", lambda: {"value": 99}),)

    summary = runner.run(changed)

    assert summary.executed_steps == 1
    assert summary.reused_steps == 0
    assert artifact_identity(
        operation_id="op-1", step="first", payload={"value": 1}
    ) != artifact_identity(operation_id="op-1", step="first", payload={"value": 99})


def test_step_names_must_be_unique(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unique"):
        _runner(tmp_path).run(
            (OperationStep("same", lambda: {"v": 1}), OperationStep("same", lambda: {"v": 2}))
        )


def test_resume_comparison_reports_equality_and_incompleteness() -> None:
    comparison = compare_resume_arms(
        {
            "uninterrupted": _summary("complete", executed=3, reused=0),
            "resumed": _summary("complete", executed=1, reused=2),
        }
    )
    incomplete = compare_resume_arms(
        {
            "uninterrupted": _summary("complete", executed=3, reused=0),
            "abandoned": _summary("interrupted", executed=2, reused=0),
        }
    )

    assert comparison.metrics["result_equality"] == 1.0
    assert comparison.metrics["duplicate_evidence_count"] == 0.0
    assert comparison.metrics["incomplete_arm_count"] == 0.0
    assert comparison.metrics["total_reused_steps"] == 2.0
    assert incomplete.metrics["incomplete_arm_count"] == 1.0
