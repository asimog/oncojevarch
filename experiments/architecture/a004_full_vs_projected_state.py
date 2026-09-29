from __future__ import annotations

import json
from dataclasses import asdict
from time import perf_counter
from typing import Any

from evaluation.projection import ProjectionArmResult, compare_projection_arms
from evidence.projections import SemanticProjection, freeze_projection
from experiments.catalog import get_experiment
from jev.contracts import JevCapability, JevDecision, JevPrimitive, JevQuestion
from jev.typesafe_adapter import TypeSafeJevClient
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A004")

EXPECTED = {
    "replicated_signal": "advance",
    "replication_conflict": "inspect",
    "underpowered_signal": "acquire_more",
    "replicated_null": "stop",
}

FULL_CASES: dict[str, dict[str, Any]] = {
    "replicated_signal": {
        "population": {"id": "synthetic-p1", "entity_level": "case", "n": 120},
        "measurement": {"direction": "positive", "strength": "moderate"},
        "coverage": {"requested": 120, "retrieved": 120, "assayed": 118},
        "missingness": {"unknown": 2, "retrieval_failure": 0},
        "uncertainty": "narrow",
        "replication": "confirmed in an independent synthetic replay",
        "contradiction": "none observed",
        "provenance": {"source": "synthetic-a004", "version": "1"},
        "workflow_metadata": {"queue": "blue", "display_color": "amber", "analyst": "R7"},
        "ingestion_notes": "Loaded on a Tuesday after an unrelated maintenance window.",
    },
    "replication_conflict": {
        "population": {"id": "synthetic-p2", "entity_level": "case", "n": 110},
        "measurement": {"direction": "positive", "strength": "strong"},
        "coverage": {"requested": 110, "retrieved": 108, "assayed": 106},
        "missingness": {"unknown": 2, "retrieval_failure": 2},
        "uncertainty": "moderate",
        "replication": "failed in an independent synthetic replay",
        "contradiction": "discovery and replay directions conflict",
        "provenance": {"source": "synthetic-a004", "version": "1"},
        "workflow_metadata": {"queue": "green", "display_color": "violet", "analyst": "R2"},
        "ingestion_notes": "The archive filename contains the word final twice.",
    },
    "underpowered_signal": {
        "population": {"id": "synthetic-p3", "entity_level": "case", "n": 34},
        "measurement": {"direction": "positive", "strength": "weak"},
        "coverage": {"requested": 100, "retrieved": 61, "assayed": 34},
        "missingness": {"unknown": 39, "unavailable_assay": 27},
        "uncertainty": "wide",
        "replication": "not attempted",
        "contradiction": "none established",
        "provenance": {"source": "synthetic-a004", "version": "1"},
        "workflow_metadata": {"queue": "red", "display_color": "teal", "analyst": "R4"},
        "ingestion_notes": "The dashboard card was viewed three times.",
    },
    "replicated_null": {
        "population": {"id": "synthetic-p4", "entity_level": "case", "n": 140},
        "measurement": {"direction": "none", "strength": "negligible"},
        "coverage": {"requested": 140, "retrieved": 140, "assayed": 138},
        "missingness": {"unknown": 2, "retrieval_failure": 0},
        "uncertainty": "narrow",
        "replication": "independent synthetic replay also found no signal",
        "contradiction": "none observed",
        "provenance": {"source": "synthetic-a004", "version": "1"},
        "workflow_metadata": {"queue": "gold", "display_color": "blue", "analyst": "R1"},
        "ingestion_notes": "The source table was alphabetically sorted.",
    },
}

PROTECTED_FIELDS = (
    "population",
    "measurement",
    "coverage",
    "missingness",
    "uncertainty",
    "replication",
    "contradiction",
    "provenance",
)


def _project_cases() -> dict[str, dict[str, Any]]:
    return {
        case_id: {field: state[field] for field in PROTECTED_FIELDS}
        for case_id, state in FULL_CASES.items()
    }


def _freeze_arm(arm_id: str, cases: dict[str, dict[str, Any]]) -> SemanticProjection:
    return freeze_projection(
        projection_id=f"a004-{arm_id}",
        version="1",
        question_id="next-bounded-action",
        source_evidence_ids=tuple(f"a004:{case_id}" for case_id in cases),
        payload={"cases": cases},
    )


FULL_STATE = _freeze_arm("full-state", FULL_CASES)
PROJECTED_STATE = _freeze_arm("question-projection", _project_cases())

CAPABILITY = JevCapability(
    capability_id="a004-next-action-semantics",
    version="0.1.0",
    domain_owner="evaluation",
    semantic_purpose=(
        "Compare full and question-specific synthetic states for one bounded next-action judgment."
    ),
    projection_id="a004-paired-state",
    projection_version="1",
    questions=tuple(
        JevQuestion(
            question_id=case_id,
            primitive=JevPrimitive.CHOICE,
            instructions=(
                f"Given only `cases.{case_id}`, which bounded next action is best justified?"
            ),
            criteria={
                "advance": "The signal is sufficiently supported and independently replicated.",
                "inspect": "A material contradiction requires focused inspection.",
                "acquire_more": "Insufficient coverage or uncertainty requires more information.",
                "stop": "Adequate evidence supports no material signal and no further action.",
            },
        )
        for case_id in EXPECTED
    ),
)


def _serialized_bytes(projection: SemanticProjection) -> int:
    return len(
        json.dumps(projection.payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    )


def _arm_result(
    arm_id: str,
    projection: SemanticProjection,
    decision: JevDecision,
    latency_ms: float,
) -> ProjectionArmResult:
    return ProjectionArmResult(
        arm_id=arm_id,
        decisions={answer.question_id: str(answer.value) for answer in decision.answers},
        probabilities={answer.question_id: answer.probabilities for answer in decision.answers},
        serialized_bytes=_serialized_bytes(projection),
        latency_ms=latency_ms,
        usage=decision.usage,
    )


def _evaluate_arm(
    client: TypeSafeJevClient, arm_id: str, projection: SemanticProjection
) -> ProjectionArmResult:
    started = perf_counter()
    decision = client.evaluate(projection, CAPABILITY)
    latency_ms = (perf_counter() - started) * 1000
    return _arm_result(arm_id, projection, decision, latency_ms)


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")

    if not live:
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.FROZEN,
            frozen_fingerprint=frozen.fingerprint,
            measurements={
                "live": False,
                "case_ids": tuple(EXPECTED),
                "expected": EXPECTED,
                "full_state_fingerprint": FULL_STATE.fingerprint,
                "projected_state_fingerprint": PROJECTED_STATE.fingerprint,
                "full_serialized_bytes": _serialized_bytes(FULL_STATE),
                "projected_serialized_bytes": _serialized_bytes(PROJECTED_STATE),
            },
            limitations=(
                "Inputs are frozen, but no Jev call was made.",
                "Synthetic cases test architecture mechanics, not cancer-domain validity.",
            ),
        )
    else:
        try:
            client = TypeSafeJevClient(
                api_key=settings.typesafe_api_key,
                model=settings.jev_model,
            )
            full = _evaluate_arm(client, "full_state", FULL_STATE)
            projected = _evaluate_arm(client, "projected_state", PROJECTED_STATE)
            evaluation = compare_projection_arms(
                expected=EXPECTED,
                full_state=full,
                projected_state=projected,
            )
            criteria_met = (
                evaluation.metrics["projected_accuracy"] >= evaluation.metrics["full_accuracy"]
                and evaluation.metrics["full_correct_to_projected_incorrect"] == 0
                and evaluation.metrics["serialized_byte_reduction"] > 0
            )
            result = ExperimentResult(
                experiment_id=SPEC.experiment_id,
                experiment_class=SPEC.experiment_class,
                status=ExperimentStatus.COMPLETED,
                frozen_fingerprint=frozen.fingerprint,
                measurements={
                    "live": True,
                    "success_criteria_met": criteria_met,
                    "evaluation": asdict(evaluation),
                },
                observations=(
                    (
                        "The projected arm met the frozen A004 success criteria."
                        if criteria_met
                        else "The projected arm did not meet the frozen A004 success criteria."
                    ),
                ),
                limitations=(
                    "The four cases are synthetic architecture fixtures.",
                    "One live run estimates neither stability nor scientific generalization.",
                ),
            )
        except Exception as exc:
            result = ExperimentResult(
                experiment_id=SPEC.experiment_id,
                experiment_class=SPEC.experiment_class,
                status=ExperimentStatus.FAILED,
                frozen_fingerprint=frozen.fingerprint,
                measurements={"live": True, "error": f"{type(exc).__name__}: {exc}"},
                limitations=("External failure does not establish projection quality.",),
            )

    store.append("architecture_experiment_result", asdict(result))
    return str(asdict(result))
