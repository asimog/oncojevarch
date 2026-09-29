import asyncio
from collections import Counter

import pytest

from evaluation.cascade import (
    CascadeCase,
    ReasoningConsideration,
    assess_reasoning,
    assess_without_reasoning,
    evaluate_cascade,
    triage_escalations,
    validate_case_set,
)
from experiments.architecture.a012_jev_oncox_cascade import (
    PROJECT_IDS,
    _arm_record,
    _build_cases,
    _capability,
    _frozen_views,
    _projection,
    _run_repetition,
)
from jev.fake import FakeJevClient
from oncox.ports import ReasoningOutput, ReasoningRequest, ReasoningResult


def _cases() -> tuple[CascadeCase, ...]:
    cases = _build_cases(_frozen_views())
    validate_case_set(cases)
    return cases


def _output_for(case: CascadeCase, *, include_novel: bool) -> ReasoningOutput:
    selected = case.considerations if include_novel else case.recorded()
    markers = [marker for item in selected for marker in item.markers]
    return ReasoningOutput(
        interpretation="; ".join(markers),
        hypotheses=(),
        alternative_explanations=(),
        proposed_tests=(),
        unresolved_uncertainty=(),
    )


class _CountingReasoner:
    def __init__(self, outputs: dict[str, ReasoningOutput]) -> None:
        self.calls: list[str] = []
        self._outputs = outputs

    async def reason(self, request: ReasoningRequest) -> ReasoningResult:
        self.calls.append(request.investigation_id)
        return ReasoningResult(
            output=self._outputs[request.investigation_id],
            model_id="fake-reasoner",
            usage={"input_tokens": 11, "output_tokens": 7},
            latency_ms=2.5,
        )


def test_screened_out_cases_never_call_oncox_and_escalated_cases_call_once() -> None:
    cases = _cases()
    open_ids = tuple(case.case_id for case in cases if case.novel())
    closed_ids = tuple(case.case_id for case in cases if not case.novel())
    jev = FakeJevClient(
        {f"escalate__{case.case_id}": (1.0 if case.novel() else 0.0) for case in cases}
    )
    reasoner = _CountingReasoner(
        {case.case_id: _output_for(case, include_novel=True) for case in cases}
    )

    record = asyncio.run(
        _run_repetition(
            repetition=1,
            cases=cases,
            projection=_projection(cases),
            capability=_capability(cases),
            jev=jev,
            reasoner=reasoner,
        )
    )

    assert record["triage"]["escalated_case_ids"] == list(open_ids)
    assert Counter(reasoner.calls) == Counter(
        {case_id: 2 for case_id in open_ids} | {case_id: 1 for case_id in closed_ids}
    )
    assert record["all_arm"]["calls"] == len(cases)
    assert record["cascade_arm"]["calls"] == len(open_ids)
    assert record["cascade_arm"]["screened_out_case_ids"] == list(closed_ids)
    assert record["all_arm_resources"]["calls"] == len(cases)
    assert record["cascade_arm_resources"]["calls"] == len(open_ids)

    metrics = record["evaluation"]["metrics"]
    assert metrics["false_negative_count"] == 0
    assert metrics["triage_sensitivity"] == 1.0
    assert metrics["triage_false_positive_rate"] == 0.0
    assert metrics["oncox_call_reduction"] == pytest.approx(0.5)
    assert metrics["quality_loss"] == 0.0
    assert metrics["conditional_quality_ratio"] == pytest.approx(1.0)


def test_triage_probabilities_are_recorded_next_to_escalation_crossings() -> None:
    cases = _cases()
    jev = FakeJevClient({f"escalate__{case.case_id}": 0.5 for case in cases})
    reasoner = _CountingReasoner(
        {case.case_id: _output_for(case, include_novel=True) for case in cases}
    )

    record = asyncio.run(
        _run_repetition(
            repetition=1,
            cases=cases,
            projection=_projection(cases),
            capability=_capability(cases),
            jev=jev,
            reasoner=reasoner,
        )
    )

    assert record["triage"]["probabilities"] == {case.case_id: 0.5 for case in cases}
    assert record["triage"]["escalated_case_ids"] == [case.case_id for case in cases]


def test_false_negative_burden_is_reported_per_case_not_hidden_in_aggregates() -> None:
    cases = _cases()
    all_arm = {
        case.case_id: assess_reasoning(case, _output_for(case, include_novel=True))
        for case in cases
    }
    escalations = {case.case_id: not case.novel() for case in cases}
    cascade_arm = {
        case.case_id: (
            all_arm[case.case_id] if escalations[case.case_id] else assess_without_reasoning(case)
        )
        for case in cases
    }

    evaluation = evaluate_cascade(
        cases=cases, all_arm=all_arm, cascade_arm=cascade_arm, escalations=escalations
    )

    assert evaluation.useful_case_ids == ("c06", "c07", "c08", "c09", "c10")
    assert evaluation.false_negative_case_ids == ("c06", "c07", "c08", "c09", "c10")
    assert evaluation.metrics["false_negative_count"] == 5
    assert evaluation.metrics["false_negative_rate"] == 1.0
    assert evaluation.metrics["triage_sensitivity"] == 0.0
    assert evaluation.metrics["quality_loss"] == pytest.approx(0.3)


def test_screened_out_cases_must_not_call_oncox() -> None:
    cases = _cases()
    selected = (cases[0], cases[5])
    all_arm = {
        case.case_id: assess_reasoning(case, _output_for(case, include_novel=True))
        for case in cases
    }
    escalations = {case.case_id: case.case_id == cases[5].case_id for case in cases}
    cascade_arm = {
        case.case_id: (
            assess_reasoning(case, _output_for(case, include_novel=True))
            if escalations[case.case_id]
            else assess_without_reasoning(case)
        )
        for case in cases
    }
    cascade_arm[selected[0].case_id] = assess_reasoning(
        selected[0], _output_for(selected[0], include_novel=True)
    )

    with pytest.raises(ValueError, match="screened-out"):
        evaluate_cascade(
            cases=cases, all_arm=all_arm, cascade_arm=cascade_arm, escalations=escalations
        )


def test_all_case_arm_must_reason_on_every_eligible_case() -> None:
    cases = _cases()
    selected = (cases[0], cases[5])
    all_arm = {case.case_id: assess_without_reasoning(case) for case in cases}
    escalations = {case.case_id: False for case in cases}
    cascade_arm = {case.case_id: assess_without_reasoning(case) for case in cases}

    with pytest.raises(ValueError, match="all-case arm"):
        evaluate_cascade(
            cases=cases, all_arm=all_arm, cascade_arm=cascade_arm, escalations=escalations
        )

    assert {case.case_id for case in selected} <= set(all_arm)


def test_case_order_cannot_change_evaluation_labels() -> None:
    cases = _cases()
    all_arm = {
        case.case_id: assess_reasoning(case, _output_for(case, include_novel=True))
        for case in cases
    }
    escalations = {case.case_id: bool(case.novel()) for case in cases}
    cascade_arm = {
        case.case_id: (
            all_arm[case.case_id] if escalations[case.case_id] else assess_without_reasoning(case)
        )
        for case in cases
    }

    forward = evaluate_cascade(
        cases=cases, all_arm=all_arm, cascade_arm=cascade_arm, escalations=escalations
    )
    reversed_order = evaluate_cascade(
        cases=tuple(reversed(cases)),
        all_arm=all_arm,
        cascade_arm=cascade_arm,
        escalations=escalations,
    )

    assert forward.metrics == reversed_order.metrics
    assert set(forward.false_negative_case_ids) == set(reversed_order.false_negative_case_ids)
    assert set(forward.useful_case_ids) == set(reversed_order.useful_case_ids)
    assert set(forward.escalated_case_ids) == set(reversed_order.escalated_case_ids)


def test_assessment_requires_the_frozen_case_identity() -> None:
    cases = _cases()

    with pytest.raises(ValueError, match="frozen case set"):
        evaluate_cascade(
            cases=cases,
            all_arm={
                case.case_id: assess_reasoning(case, _output_for(case, include_novel=True))
                for case in cases[:-1]
            },
            cascade_arm={
                case.case_id: assess_without_reasoning(case) for case in cases
            },
            escalations={case.case_id: False for case in cases},
        )


def test_triage_threshold_crossings_are_separate_from_raw_probabilities() -> None:
    probabilities = {"c01": 0.5, "c06": 0.4999}

    escalations = triage_escalations(
        probabilities=probabilities, case_ids=("c01", "c06"), threshold=0.5
    )

    assert escalations == {"c01": True, "c06": False}
    assert probabilities == {"c01": 0.5, "c06": 0.4999}

    with pytest.raises(ValueError, match="frozen case set"):
        triage_escalations(probabilities={"c01": 0.5}, case_ids=("c01", "c06"), threshold=0.5)
    with pytest.raises(ValueError, match="between 0 and 1"):
        triage_escalations(probabilities={"c01": 0.5}, case_ids=("c01",), threshold=0.0)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        triage_escalations(probabilities={"c01": 1.5}, case_ids=("c01",), threshold=0.5)


def test_screened_out_assessment_keeps_only_recorded_knowledge() -> None:
    case = next(case for case in _cases() if case.novel())

    assessment = assess_without_reasoning(case)

    assert assessment.reasoned is False
    assert assessment.novel_matched_ids == ()
    assert assessment.output_match_ratio == 0.0
    assert assessment.knowledge == pytest.approx(
        len(case.recorded()) / len(case.considerations)
    )


def test_case_validation_rejects_novel_considerations_already_present_in_state() -> None:
    case = CascadeCase(
        case_id="x",
        claim="the difference is caused by batch effects",
        question="q",
        state={"observed": {"note": "batch effects are possible"}},
        considerations=(ReasoningConsideration("k1", "novel", ("batch effects",), False),),
    )

    with pytest.raises(ValueError, match="already appears"):
        validate_case_set((case,))


def test_usage_is_recorded_separately_per_arm() -> None:
    all_arm = _arm_record(
        "all",
        [
            {
                "usage": {"input_tokens": 10, "output_tokens": 4},
                "latency_ms": 3.0,
                "attempts": 1,
            },
            {
                "usage": {"input_tokens": 20, "output_tokens": 6},
                "latency_ms": 5.0,
                "attempts": 2,
            },
        ],
    )
    cascade_arm = _arm_record(
        "cascade",
        [
            {
                "usage": {"input_tokens": 10, "output_tokens": 4},
                "latency_ms": 3.0,
                "attempts": 1,
            }
        ],
    )

    assert all_arm["arm_id"] == "all"
    assert all_arm["calls"] == 2
    assert all_arm["attempts"] == 3
    assert all_arm["input_tokens"] == 30
    assert all_arm["output_tokens"] == 10
    assert all_arm["wall_ms"] == 8.0
    assert cascade_arm["arm_id"] == "cascade"
    assert cascade_arm["calls"] == 1
    assert cascade_arm["input_tokens"] == 10


def test_frozen_snapshot_covers_the_locked_project_set() -> None:
    views = _frozen_views()

    assert set(views) == set(PROJECT_IDS)
    assert all(view["case_count"] > 0 for view in views.values())
    assert all(view["file_count"] > view["case_count"] for view in views.values())
    assert "ATAC-Seq" not in views["TCGA-KICH"]["experimental_strategies"]
