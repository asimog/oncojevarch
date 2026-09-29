from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from store.jsonl import AppendOnlyJsonlStore

OPERATION_EVENT = "operation_artifact"


@dataclass(frozen=True, slots=True)
class OperationStep:
    name: str
    produce: Callable[[], dict[str, Any]]


@dataclass(frozen=True, slots=True)
class StepOutcome:
    step: str
    artifact_id: str
    digest: str
    reused: bool


@dataclass(frozen=True, slots=True)
class OperationSummary:
    operation_id: str
    status: str
    outcomes: tuple[StepOutcome, ...]
    executed_steps: int
    reused_steps: int
    duplicate_artifacts: int
    final_digest: str
    error: str = ""

    @property
    def complete(self) -> bool:
        return self.status == "complete"


def artifact_identity(*, operation_id: str, step: str, payload: dict[str, Any]) -> str:
    """Stable artifact identity: the same operation and step cannot produce two artifacts."""

    canonical = repr(sorted(payload.items()))
    return sha256(f"{operation_id}::{step}::{canonical}".encode()).hexdigest()


def _digest(payload: dict[str, Any]) -> str:
    return sha256(repr(sorted(payload.items())).encode("utf-8")).hexdigest()


class ResumableRunner:
    """Deterministic resumable operation over the append-only store.

    Completed steps are journaled by artifact identity, so a resumed run reuses them instead of
    writing a second artifact, and a changed step payload becomes a different operation identity
    rather than silently rewriting history.
    """

    def __init__(self, *, store: AppendOnlyJsonlStore, operation_id: str) -> None:
        self.store = store
        self.operation_id = operation_id

    def journal(self) -> dict[str, dict[str, Any]]:
        entries: dict[str, dict[str, Any]] = {}
        for event in self.store.read_all():
            if event.event_type != OPERATION_EVENT:
                continue
            payload = event.payload
            if payload.get("operation_id") != self.operation_id:
                continue
            entries[str(payload["step"])] = payload
        return entries

    def run(
        self,
        steps: tuple[OperationStep, ...],
        *,
        interrupt_after: int | None = None,
    ) -> OperationSummary:
        if not steps:
            raise ValueError("a resumable operation requires at least one step")
        if len({step.name for step in steps}) != len(steps):
            raise ValueError("operation step names must be unique")
        journal = self.journal()
        outcomes: list[StepOutcome] = []
        executed = 0
        reused = 0
        duplicates = 0

        for index, step in enumerate(steps):
            if interrupt_after is not None and index > interrupt_after:
                return OperationSummary(
                    operation_id=self.operation_id,
                    status="interrupted",
                    outcomes=tuple(outcomes),
                    executed_steps=executed,
                    reused_steps=reused,
                    duplicate_artifacts=duplicates,
                    final_digest=outcomes[-1].digest if outcomes else "",
                    error=f"interrupted after step {interrupt_after}",
                )
            payload = step.produce()
            identity = artifact_identity(
                operation_id=self.operation_id, step=step.name, payload=payload
            )
            known = journal.get(step.name)
            if known is not None and known.get("artifact_id") == identity:
                outcomes.append(
                    StepOutcome(
                        step=step.name,
                        artifact_id=identity,
                        digest=str(known["digest"]),
                        reused=True,
                    )
                )
                reused += 1
                continue
            existing = [
                event
                for event in self.store.read_all()
                if event.event_type == OPERATION_EVENT
                and event.payload.get("artifact_id") == identity
            ]
            if existing:
                duplicates += 1
            self.store.append(
                OPERATION_EVENT,
                {
                    "operation_id": self.operation_id,
                    "step": step.name,
                    "artifact_id": identity,
                    "digest": _digest(payload),
                    "payload": payload,
                },
            )
            outcomes.append(
                StepOutcome(
                    step=step.name, artifact_id=identity, digest=_digest(payload), reused=False
                )
            )
            executed += 1

        return OperationSummary(
            operation_id=self.operation_id,
            status="complete",
            outcomes=tuple(outcomes),
            executed_steps=executed,
            reused_steps=reused,
            duplicate_artifacts=duplicates,
            final_digest=outcomes[-1].digest if outcomes else "",
        )


@dataclass(frozen=True, slots=True)
class ResumeComparison:
    metrics: dict[str, float]
    per_arm: tuple[dict[str, Any], ...]


def compare_resume_arms(arms: dict[str, OperationSummary]) -> ResumeComparison:
    if not arms:
        raise ValueError("resume comparison requires at least one arm")
    reference = arms[next(iter(arms))]
    digests = {arm_id: summary.final_digest for arm_id, summary in arms.items()}
    duplicates = sum(summary.duplicate_artifacts for summary in arms.values())
    incomplete = sum(1 for summary in arms.values() if not summary.complete)
    executed = {arm_id: summary.executed_steps for arm_id, summary in arms.items()}
    metrics = {
        "arm_count": float(len(arms)),
        "duplicate_evidence_count": float(duplicates),
        "incomplete_arm_count": float(incomplete),
        "result_equality": float(len(set(digests.values())) == 1),
        "reference_final_digest_matches": float(
            all(digest == reference.final_digest for digest in digests.values())
        ),
        "total_executed_steps": float(sum(executed.values())),
        "total_reused_steps": float(sum(summary.reused_steps for summary in arms.values())),
    }
    per_arm = tuple(
        {
            "arm_id": arm_id,
            "status": summary.status,
            "executed_steps": summary.executed_steps,
            "reused_steps": summary.reused_steps,
            "duplicate_artifacts": summary.duplicate_artifacts,
            "final_digest": summary.final_digest,
            "error": summary.error,
        }
        for arm_id, summary in arms.items()
    )
    return ResumeComparison(metrics=metrics, per_arm=per_arm)
