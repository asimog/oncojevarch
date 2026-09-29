import pytest

from evaluation.representation import derive_paired_coverage, paired_feasibility_decision


def test_paired_coverage_drives_feasibility_from_consistent_counts() -> None:
    coverage = derive_paired_coverage(
        total_cases=585,
        left_cases=518,
        right_cases=582,
        union_cases=583,
    )

    assert coverage.paired_cases == 517
    assert coverage.paired_fraction == pytest.approx(517 / 585)
    assert (
        paired_feasibility_decision(
            coverage,
            minimum_cases=100,
            minimum_fraction=0.5,
        )
        == "proceed_to_sample_compatibility_check"
    )


@pytest.mark.parametrize(
    ("left", "right", "union"),
    ((10, 20, 9), (10, 20, 40)),
)
def test_paired_coverage_rejects_impossible_counts(left: int, right: int, union: int) -> None:
    with pytest.raises(ValueError):
        derive_paired_coverage(
            total_cases=30,
            left_cases=left,
            right_cases=right,
            union_cases=union,
        )
