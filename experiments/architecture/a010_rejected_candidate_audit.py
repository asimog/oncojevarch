from __future__ import annotations

from dataclasses import asdict
from time import perf_counter

from discovery.rejection_audit import (
    CandidateDecision,
    DecisionDisposition,
    RejectionReason,
    RejectionStage,
    ResolvedOutcome,
    classify_rejection_sample,
    freeze_decision_log,
    freeze_outcomes,
    stratified_rejection_sample,
)
from evaluation.rejection import evaluate_rejection_audit
from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A010")
SAMPLE_SEED = "a010-v1"
PER_STAGE = 2


def _accepted(decision_id: str) -> CandidateDecision:
    return CandidateDecision(
        decision_id=decision_id,
        candidate_id=f"candidate-{decision_id}",
        disposition=DecisionDisposition.ACCEPTED,
    )


def _rejected(
    decision_id: str, stage: RejectionStage, reason: RejectionReason
) -> CandidateDecision:
    return CandidateDecision(
        decision_id=decision_id,
        candidate_id=f"candidate-{decision_id}",
        disposition=DecisionDisposition.REJECTED,
        stage=stage,
        reason=reason,
    )


DECISIONS = (
    _accepted("a1"),
    _accepted("a2"),
    _accepted("a3"),
    _accepted("a4"),
    _rejected("r1", RejectionStage.RETRIEVAL, RejectionReason.LOW_PROMISE),
    _rejected("r2", RejectionStage.RETRIEVAL, RejectionReason.LOW_PROMISE),
    _rejected("r3", RejectionStage.RETRIEVAL, RejectionReason.MISSING_REPRESENTATION),
    _rejected("r4", RejectionStage.RETRIEVAL, RejectionReason.DUPLICATE),
    _rejected("k1", RejectionStage.RERANKING, RejectionReason.RELATIVE_RANK),
    _rejected("k2", RejectionStage.RERANKING, RejectionReason.RELATIVE_RANK),
    _rejected("k3", RejectionStage.RERANKING, RejectionReason.RELATIVE_RANK),
    _rejected("k4", RejectionStage.RERANKING, RejectionReason.UNCERTAINTY_PENALTY),
    _rejected("v1", RejectionStage.VIABILITY_GATE, RejectionReason.ABSOLUTE_GATE),
    _rejected("v2", RejectionStage.VIABILITY_GATE, RejectionReason.ABSOLUTE_GATE),
    _rejected("v3", RejectionStage.VIABILITY_GATE, RejectionReason.DUPLICATE),
    _rejected("v4", RejectionStage.VIABILITY_GATE, RejectionReason.ABSOLUTE_GATE),
)

USEFUL = {
    "a1": True,
    "a2": True,
    "a3": True,
    "a4": False,
    "r1": True,
    "r2": False,
    "r3": True,
    "r4": False,
    "k1": False,
    "k2": True,
    "k3": False,
    "k4": True,
    "v1": False,
    "v2": True,
    "v3": False,
    "v4": True,
}

OUTCOMES = tuple(
    ResolvedOutcome(
        candidate_id=f"candidate-{decision_id}",
        useful=useful,
        source="locked-a010-outcome-v1",
    )
    for decision_id, useful in USEFUL.items()
)


def _execute() -> tuple[dict[str, object], float]:
    started = perf_counter()
    log = freeze_decision_log(DECISIONS)
    outcomes = freeze_outcomes(OUTCOMES)
    sample = stratified_rejection_sample(log, seed=SAMPLE_SEED, per_stage=PER_STAGE)
    findings = classify_rejection_sample(sample, outcomes)
    metrics = evaluate_rejection_audit(
        log=log,
        sample=sample,
        outcomes=outcomes,
        findings=findings,
    )
    wall_time_ms = (perf_counter() - started) * 1000
    return {
        "decision_log": asdict(log),
        "outcome_ledger": asdict(outcomes),
        "sample": asdict(sample),
        "findings": [asdict(finding) for finding in findings],
        "metrics": asdict(metrics),
    }, wall_time_ms


def run(*, settings: Settings, live: bool = False) -> str:
    del live
    frozen = FrozenExperiment.freeze(SPEC)
    first, wall_time_ms = _execute()
    replay, _ = _execute()
    reproducible = first == replay
    metrics = first["metrics"]
    if not isinstance(metrics, dict):  # pragma: no cover
        raise TypeError("audit metrics must be a dictionary")
    success = (
        metrics["outcome_resolution_coverage"] == 1.0
        and metrics["max_stage_proportion_delta"] == 0.0
        and metrics["useful_misses"] >= 2
        and metrics["actionable_miss_fraction"] >= 0.5
        and metrics["sampled_stage_count"] == len(RejectionStage)
        and reproducible
    )

    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "success_criteria_met": success,
            "audit": first,
            "wall_time_ms": wall_time_ms,
            "deterministic_replay_equal": reproducible,
        },
        observations=(
            (
                "The rejection audit met the frozen coverage and recoverability criteria."
                if success
                else "The rejection audit did not meet the frozen criteria."
            ),
            "Audit findings append a new view; historical accept/reject records remain unchanged.",
        ),
        limitations=(
            (
                "Synthetic later outcomes validate audit mechanics, "
                "not biological false-negative rates."
            ),
            (
                "Stage balance prevents stage undercoverage but does not prove "
                "within-stage randomness."
            ),
            (
                "Recoverability labels propose follow-up classes; "
                "they do not authorize policy changes."
            ),
        ),
    )
    AppendOnlyJsonlStore(settings.store_dir / "events.jsonl").append(
        "architecture_experiment_result", asdict(result)
    )
    return str(asdict(result))
