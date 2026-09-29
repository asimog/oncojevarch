import pytest

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


def _rejected(decision_id: str, stage: RejectionStage) -> CandidateDecision:
    return CandidateDecision(
        decision_id=decision_id,
        candidate_id=f"candidate-{decision_id}",
        disposition=DecisionDisposition.REJECTED,
        stage=stage,
        reason=RejectionReason.LOW_PROMISE,
    )


def test_rejection_sample_is_stage_balanced_and_input_order_invariant() -> None:
    records = tuple(
        _rejected(f"{stage.value}-{index}", stage) for stage in RejectionStage for index in range(3)
    )
    forward = stratified_rejection_sample(freeze_decision_log(records), seed="fixed", per_stage=2)
    reversed_sample = stratified_rejection_sample(
        freeze_decision_log(tuple(reversed(records))), seed="fixed", per_stage=2
    )

    assert {record.decision_id for record in forward.records} == {
        record.decision_id for record in reversed_sample.records
    }
    assert all(
        sum(record.stage is stage for record in forward.records) == 2 for stage in RejectionStage
    )


def test_rejection_audit_rejects_unresolved_sample_outcome() -> None:
    log = freeze_decision_log((_rejected("r1", RejectionStage.RETRIEVAL),))
    sample = stratified_rejection_sample(log, seed="fixed", per_stage=1)
    unrelated = freeze_outcomes((ResolvedOutcome("other", False, "locked"),))

    with pytest.raises(ValueError, match="unresolved outcome"):
        classify_rejection_sample(sample, unrelated)


def test_stage_representation_does_not_require_a_useful_miss_in_every_stage() -> None:
    accepted = CandidateDecision("a1", "candidate-a1", DecisionDisposition.ACCEPTED)
    rejected = tuple(_rejected(f"r-{stage.value}", stage) for stage in RejectionStage)
    log = freeze_decision_log((accepted, *rejected))
    sample = stratified_rejection_sample(log, seed="fixed", per_stage=1)
    outcomes = freeze_outcomes(
        (
            ResolvedOutcome("candidate-a1", True, "locked"),
            *(ResolvedOutcome(record.candidate_id, False, "locked") for record in rejected),
        )
    )
    findings = classify_rejection_sample(sample, outcomes)

    metrics = evaluate_rejection_audit(
        log=log,
        sample=sample,
        outcomes=outcomes,
        findings=findings,
    )
    assert metrics.sampled_stage_count == len(RejectionStage)
    assert metrics.useful_misses == 0
