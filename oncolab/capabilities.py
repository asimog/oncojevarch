from __future__ import annotations

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


class CapabilityRegistry:
    """Small in-memory registry; persistence is intentionally separate."""

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
