from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


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

    @property
    def route(self) -> GapRoute:
        return ROUTES[self.kind]
