from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import Any

from evidence.models import Coverage, EntityLevel, Missingness, PopulationSpec, Provenance
from execution.ports import MeasuredResult
from oncolab.admission import AdmissionContext
from oncolab.capabilities import (
    CapabilityKind,
    CapabilityRecord,
    CapabilityRegistry,
    EngineeringReadiness,
    ScientificReadiness,
)
from oncolab.operations import ScientificOperation
from research.models import Investigation

FIXTURE_CAPABILITY_ID = "fixture_token_count"
FIXTURE_CAPABILITY_VERSION = "1"
FIXTURE_POPULATION = PopulationSpec(
    population_id="fixture-documents",
    definition="two frozen inline documents used as a deterministic measurement fixture",
    entity_level=EntityLevel.OTHER,
    expected_count=2,
)
FIXTURE_DOCUMENTS = (
    "alpha beta gamma delta",
    "epsilon zeta eta theta iota",
)


def code_identity() -> str:
    return "module:" + sha256(Path(__file__).read_bytes()).hexdigest()[:16]


class FixtureTokenCountCapability:
    capability_id = FIXTURE_CAPABILITY_ID
    version = FIXTURE_CAPABILITY_VERSION

    def execute(self, *, operation_id: str, inputs: dict[str, Any]) -> MeasuredResult:
        documents = tuple(str(item) for item in inputs.get("documents") or FIXTURE_DOCUMENTS)
        counts = tuple(len(document.split()) for document in documents)
        mean = sum(counts) / len(counts) if counts else None
        return MeasuredResult(
            operation_id=operation_id,
            method_id=self.capability_id,
            population_id=FIXTURE_POPULATION.population_id,
            measurements={"mean_document_tokens": mean},
            provenance={"source": "frozen inline fixture", "source_version": "fixture-1"},
        )


class FixtureMissingValueCapability(FixtureTokenCountCapability):
    def execute(self, *, operation_id: str, inputs: dict[str, Any]) -> MeasuredResult:
        result = super().execute(operation_id=operation_id, inputs=inputs)
        return replace(result, measurements={"mean_document_tokens": None})


def fixture_context(
    *,
    evidence_id: str,
    measurement: str = "mean_document_tokens",
) -> AdmissionContext:
    return AdmissionContext(
        evidence_id=evidence_id,
        measurement=measurement,
        population=FIXTURE_POPULATION,
        coverage=Coverage(requested=2, retrieved=2, assayed=2),
        missingness=Missingness(),
        provenance=Provenance(
            source="frozen inline fixture",
            source_version="fixture-1",
            method_id=FIXTURE_CAPABILITY_ID,
            method_version=FIXTURE_CAPABILITY_VERSION,
            code_identity=code_identity(),
        ),
        metadata={"fixture": True},
    )


def fixture_operation(*, operation_id: str, evidence_id: str) -> ScientificOperation:
    return ScientificOperation(
        operation_id=operation_id,
        capability_id=FIXTURE_CAPABILITY_ID,
        version=FIXTURE_CAPABILITY_VERSION,
        inputs={"documents": list(FIXTURE_DOCUMENTS)},
        context=fixture_context(evidence_id=evidence_id),
    )


def fixture_record() -> CapabilityRecord:
    return CapabilityRecord(
        capability_id=FIXTURE_CAPABILITY_ID,
        kind=CapabilityKind.EXECUTION,
        version=FIXTURE_CAPABILITY_VERSION,
        source_identity=code_identity(),
        applicability=("fixture documents", "token counting"),
        purpose="count tokens in frozen fixture documents",
        domain_owner="nucleus-fixture",
        inputs=("documents",),
        outputs=("mean_document_tokens",),
        evaluated_domain="frozen inline fixture",
    )


def fixture_investigation(*, investigation_id: str) -> Investigation:
    return Investigation(
        investigation_id=investigation_id,
        question_id="q-fixture",
        candidate_id="c-fixture",
        population_id=FIXTURE_POPULATION.population_id,
        unresolved_uncertainty=("the fixture measurement has not been taken",),
    )


def promote_capability(
    registry: CapabilityRegistry,
    *,
    scientific: ScientificReadiness = ScientificReadiness.VALIDATED_FOR_REPLAY,
) -> CapabilityRecord:
    for target in (
        EngineeringReadiness.TESTED,
        EngineeringReadiness.VERIFIED,
        EngineeringReadiness.PROMOTED,
    ):
        registry.advance_engineering(FIXTURE_CAPABILITY_ID, FIXTURE_CAPABILITY_VERSION, target)
    return registry.set_scientific_readiness(
        FIXTURE_CAPABILITY_ID,
        FIXTURE_CAPABILITY_VERSION,
        scientific,
    )
