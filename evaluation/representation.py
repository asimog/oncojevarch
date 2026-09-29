from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PairedCoverage:
    total_cases: int
    left_cases: int
    right_cases: int
    union_cases: int
    paired_cases: int
    paired_fraction: float


def derive_paired_coverage(
    *,
    total_cases: int,
    left_cases: int,
    right_cases: int,
    union_cases: int,
) -> PairedCoverage:
    counts = (total_cases, left_cases, right_cases, union_cases)
    if any(count < 0 for count in counts):
        raise ValueError("case counts cannot be negative")
    if union_cases > total_cases:
        raise ValueError("union cannot exceed total cases")
    if union_cases < max(left_cases, right_cases):
        raise ValueError("union cannot be smaller than either input set")

    paired_cases = left_cases + right_cases - union_cases
    if paired_cases < 0 or paired_cases > min(left_cases, right_cases):
        raise ValueError("counts imply an impossible intersection")
    paired_fraction = paired_cases / total_cases if total_cases else 0.0
    return PairedCoverage(
        total_cases=total_cases,
        left_cases=left_cases,
        right_cases=right_cases,
        union_cases=union_cases,
        paired_cases=paired_cases,
        paired_fraction=paired_fraction,
    )


def paired_feasibility_decision(
    coverage: PairedCoverage,
    *,
    minimum_cases: int,
    minimum_fraction: float,
) -> str:
    if minimum_cases < 1:
        raise ValueError("minimum_cases must be positive")
    if not 0 < minimum_fraction <= 1:
        raise ValueError("minimum_fraction must be in (0, 1]")
    if coverage.paired_cases >= minimum_cases and coverage.paired_fraction >= minimum_fraction:
        return "proceed_to_sample_compatibility_check"
    return "insufficient_paired_case_coverage"
