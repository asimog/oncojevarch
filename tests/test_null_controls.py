import pytest

from evaluation.null_controls import cyclic_derangement, evaluate_null_controls


def test_cyclic_derangement_has_no_fixed_points() -> None:
    items = ("a", "b", "c", "d")
    mapping = cyclic_derangement(items, offset=1)

    assert set(mapping) == set(items)
    assert set(mapping.values()) == set(items)
    assert all(source != target for source, target in mapping.items())


def test_null_control_evaluation_requires_aligned_case_sets() -> None:
    with pytest.raises(ValueError, match="same cases"):
        evaluate_null_controls(
            probabilities={"valid": {"a": 0.9}, "null": {"b": 0.1}},
            valid_arm_id="valid",
            null_arm_ids=("null",),
            threshold=0.5,
        )
