from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from hashlib import sha256

from store.jsonl import AppendOnlyJsonlStore, StoredEvent

GAP_EVENT = "gap_recorded"


class GapKind(StrEnum):
    METHOD = "method"
    CAPABILITY = "capability"
    DECISION = "decision"
    HARNESS = "harness"


class GapRoute(StrEnum):
    SCIENTIFIC_RESEARCH = "scientific_research"
    ENGINEERING = "engineering"
    JEV_DESIGN_EVAL = "jev_design_eval"
    HARNESS_ENGINEERING = "harness_engineering"


ROUTES: dict[GapKind, GapRoute] = {
    GapKind.METHOD: GapRoute.SCIENTIFIC_RESEARCH,
    GapKind.CAPABILITY: GapRoute.ENGINEERING,
    GapKind.DECISION: GapRoute.JEV_DESIGN_EVAL,
    GapKind.HARNESS: GapRoute.HARNESS_ENGINEERING,
}


@dataclass(frozen=True, slots=True)
class Gap:
    gap_id: str
    kind: GapKind
    need: str
    evidence: tuple[str, ...] = ()
    unmet_requirements: tuple[str, ...] = ()
    attempted: tuple[str, ...] = ()
    origin: str = ""

    @property
    def route(self) -> GapRoute:
        return ROUTES[self.kind]


def gap_identity(*, need: str, kind: GapKind, origin: str = "") -> str:
    """Deterministic gap identity: the same need and origin cannot produce two gaps."""

    return sha256(f"{origin}::{kind.value}::{need}".encode()).hexdigest()[:12]


class GapLedger:
    """Append-only record of explicit capability gaps.

    A missing capability must become an inspectable durable state, not a silent fallback. The
    ledger records what was needed, what was attempted, why it was insufficient, and the owning
    route; it makes no scientific decisions.
    """

    def __init__(self, store: AppendOnlyJsonlStore) -> None:
        self.store = store

    def record(self, gap: Gap) -> StoredEvent:
        if not gap.need.strip():
            raise ValueError("gap need must not be empty")
        return self.store.append(
            GAP_EVENT,
            {
                "gap_id": gap.gap_id,
                "kind": gap.kind.value,
                "need": gap.need,
                "evidence": list(gap.evidence),
                "unmet_requirements": list(gap.unmet_requirements),
                "attempted": list(gap.attempted),
                "origin": gap.origin,
                "route": gap.route.value,
            },
        )

    def recorded(self) -> tuple[Gap, ...]:
        gaps: list[Gap] = []
        for event in self.store.read_all():
            if event.event_type != GAP_EVENT:
                continue
            payload = event.payload
            gaps.append(
                Gap(
                    gap_id=str(payload["gap_id"]),
                    kind=GapKind(str(payload["kind"])),
                    need=str(payload["need"]),
                    evidence=tuple(str(item) for item in payload.get("evidence") or ()),
                    unmet_requirements=tuple(
                        str(item) for item in payload.get("unmet_requirements") or ()
                    ),
                    attempted=tuple(str(item) for item in payload.get("attempted") or ()),
                    origin=str(payload.get("origin", "")),
                )
            )
        return tuple(gaps)
