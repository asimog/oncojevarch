from __future__ import annotations

import re
from dataclasses import dataclass, replace
from enum import StrEnum


class CapabilityKind(StrEnum):
    AGENT = "agent"
    SOURCE = "source"
    METHOD = "method"
    EXECUTION = "execution"
    JEV = "jev"
    HARNESS = "harness"


class EngineeringReadiness(StrEnum):
    DRAFT = "draft"
    TESTED = "tested"
    VERIFIED = "verified"
    PROMOTED = "promoted"


class ScientificReadiness(StrEnum):
    EXPERIMENTAL = "experimental"
    VALIDATED_FOR_REPLAY = "validated_for_replay"
    VALIDATED_FOR_EXPLORATION = "validated_for_exploration"
    VALIDATED_FOR_DEFINED_DOMAIN = "validated_for_defined_domain"


@dataclass(frozen=True, slots=True)
class CapabilityRecord:
    capability_id: str
    kind: CapabilityKind
    version: str
    source_identity: str
    engineering_readiness: EngineeringReadiness = EngineeringReadiness.DRAFT
    scientific_readiness: ScientificReadiness = ScientificReadiness.EXPERIMENTAL
    applicability: tuple[str, ...] = ()
    purpose: str = ""
    domain_owner: str = ""
    inputs: tuple[str, ...] = ()
    outputs: tuple[str, ...] = ()
    prerequisites: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()
    evaluated_domain: str = ""


@dataclass(frozen=True, slots=True)
class CapabilitySummary:
    capability_id: str
    version: str
    kind: CapabilityKind
    purpose: str
    engineering_readiness: EngineeringReadiness
    scientific_readiness: ScientificReadiness
    applicability: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ApplicabilityCheck:
    capability_id: str
    version: str
    unmet: tuple[str, ...]

    @property
    def eligible(self) -> bool:
        return not self.unmet


_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    {
        "a",
        "across",
        "an",
        "and",
        "at",
        "between",
        "by",
        "for",
        "from",
        "in",
        "of",
        "on",
        "over",
        "per",
        "the",
        "to",
        "with",
    }
)


def _tokens(text: str) -> frozenset[str]:
    return frozenset(
        token for token in _TOKEN.findall(text.lower()) if token not in _STOPWORDS
    )


def _summary(record: CapabilityRecord) -> CapabilitySummary:
    return CapabilitySummary(
        capability_id=record.capability_id,
        version=record.version,
        kind=record.kind,
        purpose=record.purpose,
        engineering_readiness=record.engineering_readiness,
        scientific_readiness=record.scientific_readiness,
        applicability=record.applicability,
    )


class CapabilityRegistry:
    """Small in-memory registry; persistence is intentionally separate.

    Search is deterministic over typed summaries: no Jev, no network. A search miss returns an
    empty tuple, which callers must treat as an explicit capability gap rather than a fallback.
    """

    def __init__(self) -> None:
        self._records: dict[tuple[str, str], CapabilityRecord] = {}

    def register(self, record: CapabilityRecord) -> None:
        key = (record.capability_id, record.version)
        if key in self._records:
            raise ValueError(f"capability already registered: {key}")
        self._records[key] = record

    def get(self, capability_id: str, version: str) -> CapabilityRecord:
        return self._records[(capability_id, version)]

    def advance_engineering(
        self,
        capability_id: str,
        version: str,
        target: EngineeringReadiness,
    ) -> CapabilityRecord:
        current = self.get(capability_id, version)
        order = list(EngineeringReadiness)
        if order.index(target) != order.index(current.engineering_readiness) + 1:
            raise ValueError("engineering readiness must advance one verified step at a time")
        updated = replace(current, engineering_readiness=target)
        self._records[(capability_id, version)] = updated
        return updated

    def set_scientific_readiness(
        self,
        capability_id: str,
        version: str,
        target: ScientificReadiness,
    ) -> CapabilityRecord:
        current = self.get(capability_id, version)
        if current.engineering_readiness not in {
            EngineeringReadiness.VERIFIED,
            EngineeringReadiness.PROMOTED,
        }:
            raise ValueError("scientific readiness cannot advance before engineering verification")
        updated = replace(current, scientific_readiness=target)
        self._records[(capability_id, version)] = updated
        return updated

    def list_summaries(self) -> tuple[CapabilitySummary, ...]:
        return tuple(
            sorted(
                (_summary(record) for record in self._records.values()),
                key=lambda summary: (summary.capability_id, summary.version),
            )
        )

    def search(
        self,
        need: str,
        *,
        kind: CapabilityKind | None = None,
        min_engineering: EngineeringReadiness | None = None,
        min_scientific: ScientificReadiness | None = None,
        limit: int = 5,
    ) -> tuple[CapabilitySummary, ...]:
        """Bounded deterministic candidate search by token overlap; empty result is explicit."""

        if not need.strip():
            raise ValueError("capability search need must not be empty")
        if limit < 1:
            raise ValueError("capability search limit must be positive")

        need_tokens = _tokens(need)
        engineering_order = list(EngineeringReadiness)
        scientific_order = list(ScientificReadiness)
        scored: list[tuple[int, str, str, CapabilitySummary]] = []
        for record in self._records.values():
            if kind is not None and record.kind != kind:
                continue
            if (
                min_engineering is not None
                and engineering_order.index(record.engineering_readiness)
                < engineering_order.index(min_engineering)
            ):
                continue
            if (
                min_scientific is not None
                and scientific_order.index(record.scientific_readiness)
                < scientific_order.index(min_scientific)
            ):
                continue
            searchable = _tokens(
                " ".join((record.capability_id, record.purpose, *record.applicability))
            )
            overlap = len(need_tokens & searchable)
            if overlap == 0:
                continue
            scored.append((-overlap, record.capability_id, record.version, _summary(record)))
        scored.sort(key=lambda item: (item[0], item[1], item[2]))
        return tuple(item[3] for item in scored[:limit])

    def check_applicability(
        self,
        capability_id: str,
        version: str,
        required: tuple[str, ...],
    ) -> ApplicabilityCheck:
        record = self.get(capability_id, version)
        unmet = tuple(tag for tag in required if tag not in record.applicability)
        return ApplicabilityCheck(capability_id=capability_id, version=version, unmet=unmet)
