from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class ReasoningRequest:
    investigation_id: str
    evidence_ids: tuple[str, ...]
    question: str


@dataclass(frozen=True, slots=True)
class ReasoningOutput:
    interpretation: str
    hypotheses: tuple[str, ...]
    alternative_explanations: tuple[str, ...]
    proposed_tests: tuple[str, ...]
    unresolved_uncertainty: tuple[str, ...]


class ScientificReasoner(Protocol):
    async def reason(self, request: ReasoningRequest) -> ReasoningOutput: ...
