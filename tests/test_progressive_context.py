import pytest

from evaluation.context import (
    ContextArmScore,
    ContextTask,
    compare_context_arms,
    evaluate_context_arm,
    score_answer,
)
from oncodex.context import (
    HistoryMessage,
    build_bounded_view,
    render_full_history,
    render_view,
)


def _history() -> tuple[HistoryMessage, ...]:
    return (
        HistoryMessage("m01", "user", "open the investigation"),
        HistoryMessage("m02", "tool", "FACT: cases = 537"),
        HistoryMessage("m03", "assistant", "recorded"),
        HistoryMessage("m04", "tool", "CORRECTION: cases = 531"),
        HistoryMessage("m05", "tool", "FACT: files = 35031"),
        HistoryMessage("m06", "assistant", "ready"),
    )


def test_bounded_view_pins_latest_values_and_marks_superseded_keys() -> None:
    view = build_bounded_view(_history(), view_id="v1", recency_window=6, budget_chars=10000)

    assert view.pinned_facts == {"cases": "531", "files": "35031"}
    assert view.superseded_fact_keys == ("cases",)
    assert "537" not in render_view(view)
    assert "m02" in view.dropped_message_ids
    assert "m04" in view.dropped_message_ids
    assert [message.message_id for message in view.messages] == ["m01", "m03", "m06"]


def test_bounded_view_drops_oldest_messages_until_it_fits_the_budget() -> None:
    view = build_bounded_view(_history(), view_id="v2", recency_window=6, budget_chars=120)

    assert view.character_count <= 120
    assert "m01" in view.dropped_message_ids
    assert view.pinned_facts == {"cases": "531", "files": "35031"}


def test_bounded_view_requires_positive_parameters() -> None:
    with pytest.raises(ValueError, match="recency window"):
        build_bounded_view(_history(), view_id="v3", recency_window=0, budget_chars=100)
    with pytest.raises(ValueError, match="character budget"):
        build_bounded_view(_history(), view_id="v4", recency_window=6, budget_chars=0)


def test_full_history_keeps_superseded_values() -> None:
    text = render_full_history(_history())

    assert "537" in text
    assert "CORRECTION" in text


def test_answer_scoring_requires_latest_values_and_rejects_superseded_ones() -> None:
    task = ContextTask(
        task_id="t01",
        question="state the case count",
        required_facts={"cases": "531"},
        contradicted_values=("537",),
    )

    good = score_answer(task, {"answers": ["the corrected count is 531"]})
    stale = score_answer(task, {"answers": ["the count is 537"]})
    incomplete = score_answer(task, {"answers": ["no value recorded"]})

    assert good.success and good.contradicted is False
    assert stale.success is False and stale.contradicted_present == ("537",)
    assert incomplete.success is False and incomplete.missing_required == ("cases",)


def test_arm_evaluation_requires_the_frozen_task_set() -> None:
    task = ContextTask("t01", "q", {"cases": "531"}, ("537",))

    with pytest.raises(ValueError, match="frozen task set"):
        evaluate_context_arm(arm_id="arm", tasks=(task,), answers={}, resources={})


def test_paired_comparison_reports_success_and_token_deltas() -> None:
    full = ContextArmScore(
        arm_id="full_history",
        metrics={
            "task_count": 3.0,
            "success_rate": 0.667,
            "contradiction_rate": 0.333,
            "input_tokens": 1000.0,
            "output_tokens": 100.0,
            "mean_latency_ms": 200.0,
            "character_count": 6000.0,
        },
        per_task=(),
    )
    bounded = ContextArmScore(
        arm_id="bounded_progressive",
        metrics={
            "task_count": 3.0,
            "success_rate": 1.0,
            "contradiction_rate": 0.0,
            "input_tokens": 600.0,
            "output_tokens": 90.0,
            "mean_latency_ms": 180.0,
            "character_count": 3600.0,
        },
        per_task=(),
    )

    metrics = compare_context_arms(full_history=full, bounded=bounded)

    assert metrics["success_delta"] == pytest.approx(0.333)
    assert metrics["contradiction_delta"] == pytest.approx(-0.333)
    assert metrics["input_token_reduction"] == pytest.approx(0.4)
    assert metrics["latency_delta_ms"] == pytest.approx(-20.0)


def test_paired_comparison_requires_matching_task_counts() -> None:
    full = ContextArmScore("full_history", {"task_count": 3.0}, ())
    bounded = ContextArmScore("bounded_progressive", {"task_count": 2.0}, ())

    with pytest.raises(ValueError, match="same frozen task set"):
        compare_context_arms(full_history=full, bounded=bounded)
