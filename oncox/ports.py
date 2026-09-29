from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class ReasoningRequest:
    investigation_id: str
    evidence_ids: tuple[str, ...]
    question: str
    structured_state: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ReasoningOutput:
    interpretation: str
    hypotheses: tuple[str, ...]
    alternative_explanations: tuple[str, ...]
    proposed_tests: tuple[str, ...]
    unresolved_uncertainty: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReasoningResult:
    """Structured reasoning plus the resource account for one bounded call.

    OncoX produces interpretation and proposed investigation, never measurement.
    """

    output: ReasoningOutput
    model_id: str
    usage: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0
    attempts: int = 1
    errors: tuple[str, ...] = ()


class ScientificReasoner(Protocol):
    async def reason(self, request: ReasoningRequest) -> ReasoningResult: ...
