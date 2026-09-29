import pytest

from evaluation.projection import ProjectionArmResult, compare_projection_arms


def _arm(
    arm_id: str,
    decisions: dict[str, str],
    *,
    serialized_bytes: int,
) -> ProjectionArmResult:
    return ProjectionArmResult(
        arm_id=arm_id,
        decisions=decisions,
        probabilities={case_id: {decision: 1.0} for case_id, decision in decisions.items()},
        serialized_bytes=serialized_bytes,
        latency_ms=10.0,
        usage={"input_tokens": serialized_bytes // 10, "output_tokens": len(decisions)},
    )


def test_paired_projection_evaluation_reports_quality_and_resource_change() -> None:
    expected = {"a": "advance", "b": "stop"}
    full = _arm("full", {"a": "advance", "b": "stop"}, serialized_bytes=1000)
    projected = _arm("projected", {"a": "advance", "b": "stop"}, serialized_bytes=400)

    result = compare_projection_arms(
        expected=expected,
        full_state=full,
        projected_state=projected,
    )

    assert result.metrics["full_accuracy"] == 1.0
    assert result.metrics["projected_accuracy"] == 1.0
    assert result.metrics["arm_agreement"] == 1.0
    assert result.metrics["serialized_byte_reduction"] == pytest.approx(0.6)
    assert result.metrics["projected_input_tokens"] == 40.0


def test_paired_projection_evaluation_rejects_unaligned_cases() -> None:
    expected = {"a": "advance", "b": "stop"}
    full = _arm("full", {"a": "advance", "b": "stop"}, serialized_bytes=1000)
    projected = _arm("projected", {"a": "advance"}, serialized_bytes=400)

    with pytest.raises(ValueError, match="frozen case set"):
        compare_projection_arms(
            expected=expected,
            full_state=full,
            projected_state=projected,
        )
