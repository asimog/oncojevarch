from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from hashlib import sha256


class DecisionDisposition(StrEnum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class RejectionStage(StrEnum):
    RETRIEVAL = "retrieval"
    RERANKING = "reranking"
    VIABILITY_GATE = "viability_gate"


class RejectionReason(StrEnum):
    LOW_PROMISE = "low_promise"
    UNCERTAINTY_PENALTY = "uncertainty_penalty"
    NOVELTY_PENALTY = "novelty_penalty"
    MISSING_REPRESENTATION = "missing_representation"
    RELATIVE_RANK = "relative_rank"
    ABSOLUTE_GATE = "absolute_gate"
    DUPLICATE = "duplicate"


class Recoverability(StrEnum):
    NOT_A_MISS = "not_a_miss"
    EXPLORATION_ALLOCATION = "exploration_allocation"
    REPRESENTATION_ACQUISITION = "representation_acquisition"
    RERANKING_REVISION = "reranking_revision"
    THRESHOLD_REVIEW = "threshold_review"
    RESIDUAL_RISK = "residual_risk"


@dataclass(frozen=True, slots=True)
class CandidateDecision:
    decision_id: str
    candidate_id: str
    disposition: DecisionDisposition
    stage: RejectionStage | None = None
    reason: RejectionReason | None = None


@dataclass(frozen=True, slots=True)
class FrozenDecisionLog:
    records: tuple[CandidateDecision, ...]
    fingerprint: str


@dataclass(frozen=True, slots=True)
class ResolvedOutcome:
    candidate_id: str
    useful: bool
    source: str


@dataclass(frozen=True, slots=True)
class FrozenOutcomeLedger:
    records: tuple[ResolvedOutcome, ...]
    fingerprint: str


@dataclass(frozen=True, slots=True)
class FrozenRejectionSample:
    records: tuple[CandidateDecision, ...]
    source_log_fingerprint: str
    seed: str
    per_stage: int
    fingerprint: str


@dataclass(frozen=True, slots=True)
class RejectionAuditFinding:
    decision_id: str
    candidate_id: str
    stage: RejectionStage
    useful_miss: bool
    miss_reason: RejectionReason | None
    recoverability: Recoverability


def _fingerprint(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return sha256(canonical.encode("utf-8")).hexdigest()


def freeze_decision_log(records: tuple[CandidateDecision, ...]) -> FrozenDecisionLog:
    if not records:
        raise ValueError("decision log cannot be empty")
    if len({record.decision_id for record in records}) != len(records):
        raise ValueError("decision identifiers must be unique")
    if len({record.candidate_id for record in records}) != len(records):
        raise ValueError("candidate identifiers must have one historical decision")
    for record in records:
        rejected = record.disposition is DecisionDisposition.REJECTED
        if rejected != (record.stage is not None and record.reason is not None):
            raise ValueError(
                "rejected decisions require stage/reason; accepted decisions forbid them"
            )
    payload = [asdict(record) for record in records]
    return FrozenDecisionLog(records=records, fingerprint=_fingerprint(payload))


def freeze_outcomes(records: tuple[ResolvedOutcome, ...]) -> FrozenOutcomeLedger:
    if not records:
        raise ValueError("outcome ledger cannot be empty")
    if len({record.candidate_id for record in records}) != len(records):
        raise ValueError("outcome candidate identifiers must be unique")
    return FrozenOutcomeLedger(
        records=records,
        fingerprint=_fingerprint([asdict(record) for record in records]),
    )


def stratified_rejection_sample(
    log: FrozenDecisionLog, *, seed: str, per_stage: int
) -> FrozenRejectionSample:
    """Freeze a stage-balanced sample without accepting outcome data."""

    if not seed:
        raise ValueError("sampling seed cannot be empty")
    if per_stage < 1:
        raise ValueError("per-stage sample size must be positive")
    rejected = tuple(
        record for record in log.records if record.disposition is DecisionDisposition.REJECTED
    )
    stages = sorted({record.stage for record in rejected}, key=str)
    selected: list[CandidateDecision] = []
    for stage in stages:
        stratum = [record for record in rejected if record.stage is stage]
        if len(stratum) < per_stage:
            raise ValueError(f"not enough rejected candidates in stage {stage}")
        stratum.sort(
            key=lambda record: (
                sha256(f"{seed}|{record.decision_id}".encode()).hexdigest(),
                record.decision_id,
            )
        )
        selected.extend(stratum[:per_stage])
    records = tuple(selected)
    payload = {
        "source_log_fingerprint": log.fingerprint,
        "seed": seed,
        "per_stage": per_stage,
        "decision_ids": [record.decision_id for record in records],
    }
    return FrozenRejectionSample(
        records=records,
        source_log_fingerprint=log.fingerprint,
        seed=seed,
        per_stage=per_stage,
        fingerprint=_fingerprint(payload),
    )


def _recoverability(reason: RejectionReason) -> Recoverability:
    if reason in {
        RejectionReason.LOW_PROMISE,
        RejectionReason.UNCERTAINTY_PENALTY,
        RejectionReason.NOVELTY_PENALTY,
    }:
        return Recoverability.EXPLORATION_ALLOCATION
    if reason is RejectionReason.MISSING_REPRESENTATION:
        return Recoverability.REPRESENTATION_ACQUISITION
    if reason is RejectionReason.RELATIVE_RANK:
        return Recoverability.RERANKING_REVISION
    if reason is RejectionReason.ABSOLUTE_GATE:
        return Recoverability.THRESHOLD_REVIEW
    return Recoverability.RESIDUAL_RISK


def classify_rejection_sample(
    sample: FrozenRejectionSample, outcomes: FrozenOutcomeLedger
) -> tuple[RejectionAuditFinding, ...]:
    by_candidate = {record.candidate_id: record for record in outcomes.records}
    findings: list[RejectionAuditFinding] = []
    for decision in sample.records:
        outcome = by_candidate.get(decision.candidate_id)
        if outcome is None:
            raise ValueError(f"unresolved outcome for {decision.candidate_id}")
        if decision.stage is None or decision.reason is None:  # pragma: no cover
            raise ValueError("rejection sample contains a non-rejection")
        findings.append(
            RejectionAuditFinding(
                decision_id=decision.decision_id,
                candidate_id=decision.candidate_id,
                stage=decision.stage,
                useful_miss=outcome.useful,
                miss_reason=decision.reason if outcome.useful else None,
                recoverability=(
                    _recoverability(decision.reason)
                    if outcome.useful
                    else Recoverability.NOT_A_MISS
                ),
            )
        )
    return tuple(findings)
