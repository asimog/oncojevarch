from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class EntityLevel(StrEnum):
    CASE = "case"
    SAMPLE = "sample"
    ALIQUOT = "aliquot"
    FILE = "file"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class PopulationSpec:
    population_id: str
    definition: str
    entity_level: EntityLevel
    expected_count: int | None = None


@dataclass(frozen=True, slots=True)
class Coverage:
    requested: int | None
    retrieved: int | None
    assayed: int | None = None


@dataclass(frozen=True, slots=True)
class Missingness:
    unknown: int = 0
    unavailable_assay: int = 0
    retrieval_failure: int = 0
    biological_absence: int = 0


@dataclass(frozen=True, slots=True)
class Provenance:
    source: str
    source_version: str
    method_id: str
    method_version: str
    code_identity: str


@dataclass(frozen=True, slots=True)
class ScientificEvidence:
    evidence_id: str
    population: PopulationSpec
    measurement: str
    value: Any
    uncertainty: Any | None
    coverage: Coverage
    missingness: Missingness
    provenance: Provenance
    metadata: dict[str, Any] = field(default_factory=dict)
