from __future__ import annotations

from dataclasses import dataclass

from evidence.projections import SemanticProjection
from jev.contracts import JevDecision


@dataclass(frozen=True, slots=True)
class ProjectionCaseResult:
    case_id: str
    projection: SemanticProjection
    decision: JevDecision
    expected: object
    correct: bool


def exact_match(actual: object, expected: object) -> bool:
    return actual == expected
