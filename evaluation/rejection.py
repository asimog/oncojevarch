from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from discovery.rejection_audit import (
    DecisionDisposition,
    FrozenDecisionLog,
    FrozenOutcomeLedger,
    FrozenRejectionSample,
    Recoverability,
    RejectionAuditFinding,
)


@dataclass(frozen=True, slots=True)
class RejectionAuditMetrics:
    accepted_count: int
    accepted_useful: int
    accepted_yield: float
    rejected_population_count: int
    rejected_sample_count: int
    sampled_stage_count: int
    useful_misses: int
    sample_miss_rate: float
    outcome_resolution_coverage: float
    actionable_miss_fraction: float
    max_stage_proportion_delta: float
    misses_by_stage: dict[str, int]
    misses_by_reason: dict[str, int]
    misses_by_recoverability: dict[str, int]


def evaluate_rejection_audit(
    *,
    log: FrozenDecisionLog,
    sample: FrozenRejectionSample,
    outcomes: FrozenOutcomeLedger,
    findings: tuple[RejectionAuditFinding, ...],
) -> RejectionAuditMetrics:
    if sample.source_log_fingerprint != log.fingerprint:
        raise ValueError("sample does not belong to the supplied decision log")
    if len(findings) != len(sample.records):
        raise ValueError("one finding is required for every sampled rejection")
    outcome_by_candidate = {record.candidate_id: record for record in outcomes.records}
    accepted = tuple(
        record for record in log.records if record.disposition is DecisionDisposition.ACCEPTED
    )
    resolved_accepted = [
        outcome_by_candidate[record.candidate_id]
        for record in accepted
        if record.candidate_id in outcome_by_candidate
    ]
    if len(resolved_accepted) != len(accepted):
        raise ValueError("all accepted candidates require resolved outcomes")

    rejected = tuple(
        record for record in log.records if record.disposition is DecisionDisposition.REJECTED
    )
    population_by_stage = Counter(str(record.stage) for record in rejected)
    sample_by_stage = Counter(str(record.stage) for record in sample.records)
    max_delta = max(
        abs(
            sample_by_stage[stage] / len(sample.records)
            - population_by_stage[stage] / len(rejected)
        )
        for stage in population_by_stage
    )
    useful = tuple(finding for finding in findings if finding.useful_miss)
    actionable = tuple(
        finding for finding in useful if finding.recoverability is not Recoverability.RESIDUAL_RISK
    )
    resolved_sample = sum(finding.candidate_id in outcome_by_candidate for finding in findings)
    return RejectionAuditMetrics(
        accepted_count=len(accepted),
        accepted_useful=sum(outcome.useful for outcome in resolved_accepted),
        accepted_yield=sum(outcome.useful for outcome in resolved_accepted) / len(accepted),
        rejected_population_count=len(rejected),
        rejected_sample_count=len(sample.records),
        sampled_stage_count=len(sample_by_stage),
        useful_misses=len(useful),
        sample_miss_rate=len(useful) / len(sample.records),
        outcome_resolution_coverage=resolved_sample / len(sample.records),
        actionable_miss_fraction=len(actionable) / len(useful) if useful else 0.0,
        max_stage_proportion_delta=max_delta,
        misses_by_stage=dict(Counter(str(finding.stage) for finding in useful)),
        misses_by_reason=dict(Counter(str(finding.miss_reason) for finding in useful)),
        misses_by_recoverability=dict(Counter(str(finding.recoverability) for finding in useful)),
    )
