from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from evidence.models import Coverage, Missingness, PopulationSpec, Provenance, ScientificEvidence
from execution.ports import MeasuredResult


class AdmissionRefusalReason(StrEnum):
    MISSING_METHOD = "missing_method"
    POPULATION_MISMATCH = "population_mismatch"
    MISSING_PROVENANCE = "missing_provenance"
    MISSING_MEASUREMENT = "missing_measurement"
    UNREPRESENTABLE_VALUE = "unrepresentable_value"


@dataclass(frozen=True, slots=True)
class AdmissionRefusal:
    operation_id: str
    reasons: tuple[AdmissionRefusalReason, ...]


@dataclass(frozen=True, slots=True)
class AdmissionContext:
    evidence_id: str
    measurement: str
    population: PopulationSpec
    coverage: Coverage
    missingness: Missingness
    provenance: Provenance
    uncertainty: Any | None = None
    metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class AdmissionResult:
    evidence: ScientificEvidence | None = None
    refusal: AdmissionRefusal | None = None

    @property
    def admitted(self) -> bool:
        return self.evidence is not None


def admit_measured_result(result: MeasuredResult, *, context: AdmissionContext) -> AdmissionResult:
    """Deterministic admission gate between measurement and scientific evidence.

    Admission is an OncoLab decision, not a reasoning decision. Missing is not zero: an absent
    or explicit ``None`` measurement is refused rather than converted into a value. A result
    must carry a method identity, a matching population identity, provenance, and the declared
    measurement before it can become ScientificEvidence.
    """

    reasons: list[AdmissionRefusalReason] = []
    if not result.method_id.strip():
        reasons.append(AdmissionRefusalReason.MISSING_METHOD)
    if (
        not result.population_id.strip()
        or result.population_id != context.population.population_id
    ):
        reasons.append(AdmissionRefusalReason.POPULATION_MISMATCH)
    if not result.provenance:
        reasons.append(AdmissionRefusalReason.MISSING_PROVENANCE)
    if not context.measurement.strip() or context.measurement not in result.measurements:
        reasons.append(AdmissionRefusalReason.MISSING_MEASUREMENT)
    elif result.measurements[context.measurement] is None:
        reasons.append(AdmissionRefusalReason.UNREPRESENTABLE_VALUE)
    if reasons:
        return AdmissionResult(
            refusal=AdmissionRefusal(
                operation_id=result.operation_id,
                reasons=tuple(reasons),
            )
        )
    return AdmissionResult(
        evidence=ScientificEvidence(
            evidence_id=context.evidence_id,
            population=context.population,
            measurement=context.measurement,
            value=result.measurements[context.measurement],
            uncertainty=context.uncertainty,
            coverage=context.coverage,
            missingness=context.missingness,
            provenance=context.provenance,
            metadata=dict(context.metadata or {}),
        )
    )
