from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class SurvivalReason(StrEnum):
    PROMISE = "promise"
    UNCERTAINTY = "uncertainty"
    NOVELTY = "novelty"
    CONTRADICTION = "contradiction"
    REPLICATION = "replication"
    EXPLORATION = "exploration"


@dataclass(frozen=True, slots=True)
class FrontierEntry:
    candidate_id: str
    state_ref: str
    reasons: tuple[SurvivalReason, ...]
    relative_rank: float | None = None
    absolute_viability: float | None = None
    uncertainty: float | None = None
    next_information_need: str | None = None


class SearchFrontier:
    def __init__(self) -> None:
        self._entries: dict[str, FrontierEntry] = {}

    def upsert(self, entry: FrontierEntry) -> None:
        if not entry.reasons:
            raise ValueError("a frontier entry must survive for at least one explicit reason")
        self._entries[entry.candidate_id] = entry

    def entries(self) -> tuple[FrontierEntry, ...]:
        return tuple(self._entries.values())
