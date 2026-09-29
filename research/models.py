from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class InvestigationStatus(StrEnum):
    OPEN = "open"
    DEFERRED = "deferred"
    EXHAUSTED = "exhausted"
    FINALIZED = "finalized"


@dataclass(frozen=True, slots=True)
class ResearchQuestion:
    question_id: str
    text: str


@dataclass(frozen=True, slots=True)
class Candidate:
    candidate_id: str
    label: str
    origin: str


@dataclass(frozen=True, slots=True)
class Hypothesis:
    hypothesis_id: str
    investigation_id: str
    statement: str
    predictions: tuple[str, ...] = ()
    discriminating_tests: tuple[str, ...] = ()
    supporting_evidence_ids: tuple[str, ...] = ()
    conflicting_evidence_ids: tuple[str, ...] = ()
    alternative_hypothesis_ids: tuple[str, ...] = ()
    revision: int = 1


@dataclass(frozen=True, slots=True)
class Investigation:
    investigation_id: str
    question_id: str
    candidate_id: str
    population_id: str
    status: InvestigationStatus = InvestigationStatus.OPEN
    evidence_ids: tuple[str, ...] = ()
    jev_decision_ids: tuple[str, ...] = ()
    hypothesis_ids: tuple[str, ...] = ()
    unresolved_uncertainty: tuple[str, ...] = ()
    next_action: str | None = None


@dataclass(frozen=True, slots=True)
class Dossier:
    dossier_id: str
    investigation_id: str
    evidence_ids: tuple[str, ...]
    hypothesis_ids: tuple[str, ...]
    limitations: tuple[str, ...]
    synthesis: str
    provenance: dict[str, str] = field(default_factory=dict)
