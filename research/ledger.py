from __future__ import annotations

from dataclasses import asdict
from typing import Any

from evidence.models import (
    Coverage,
    EntityLevel,
    Missingness,
    PopulationSpec,
    Provenance,
    ScientificEvidence,
)
from research.models import Investigation, InvestigationStatus
from store.jsonl import AppendOnlyJsonlStore, StoredEvent

INVESTIGATION_EVENT = "investigation_revision"
EVIDENCE_EVENT = "scientific_evidence"


def investigation_payload(investigation: Investigation) -> dict[str, Any]:
    return {
        "investigation_id": investigation.investigation_id,
        "question_id": investigation.question_id,
        "candidate_id": investigation.candidate_id,
        "population_id": investigation.population_id,
        "status": investigation.status.value,
        "evidence_ids": list(investigation.evidence_ids),
        "jev_decision_ids": list(investigation.jev_decision_ids),
        "hypothesis_ids": list(investigation.hypothesis_ids),
        "unresolved_uncertainty": list(investigation.unresolved_uncertainty),
        "next_action": investigation.next_action,
    }


def investigation_from_payload(payload: dict[str, Any]) -> Investigation:
    return Investigation(
        investigation_id=str(payload["investigation_id"]),
        question_id=str(payload["question_id"]),
        candidate_id=str(payload["candidate_id"]),
        population_id=str(payload["population_id"]),
        status=InvestigationStatus(str(payload["status"])),
        evidence_ids=tuple(str(item) for item in payload.get("evidence_ids") or ()),
        jev_decision_ids=tuple(str(item) for item in payload.get("jev_decision_ids") or ()),
        hypothesis_ids=tuple(str(item) for item in payload.get("hypothesis_ids") or ()),
        unresolved_uncertainty=tuple(
            str(item) for item in payload.get("unresolved_uncertainty") or ()
        ),
        next_action=(
            str(payload["next_action"]) if payload.get("next_action") is not None else None
        ),
    )


def evidence_payload(evidence: ScientificEvidence) -> dict[str, Any]:
    payload = asdict(evidence)
    payload["population"]["entity_level"] = evidence.population.entity_level.value
    return payload


def evidence_from_payload(payload: dict[str, Any]) -> ScientificEvidence:
    population = payload["population"]
    provenance = payload["provenance"]
    coverage = payload["coverage"]
    missingness = payload["missingness"]
    return ScientificEvidence(
        evidence_id=str(payload["evidence_id"]),
        population=PopulationSpec(
            population_id=str(population["population_id"]),
            definition=str(population["definition"]),
            entity_level=EntityLevel(str(population["entity_level"])),
            expected_count=(
                int(population["expected_count"])
                if population.get("expected_count") is not None
                else None
            ),
        ),
        measurement=str(payload["measurement"]),
        value=payload.get("value"),
        uncertainty=payload.get("uncertainty"),
        coverage=Coverage(
            requested=_optional_int(coverage.get("requested")),
            retrieved=_optional_int(coverage.get("retrieved")),
            assayed=_optional_int(coverage.get("assayed")),
        ),
        missingness=Missingness(
            unknown=int(missingness.get("unknown") or 0),
            unavailable_assay=int(missingness.get("unavailable_assay") or 0),
            retrieval_failure=int(missingness.get("retrieval_failure") or 0),
            biological_absence=int(missingness.get("biological_absence") or 0),
        ),
        provenance=Provenance(
            source=str(provenance["source"]),
            source_version=str(provenance["source_version"]),
            method_id=str(provenance["method_id"]),
            method_version=str(provenance["method_version"]),
            code_identity=str(provenance["code_identity"]),
        ),
        metadata=dict(payload.get("metadata") or {}),
    )


def _optional_int(value: Any) -> int | None:
    return int(value) if value is not None else None


class InvestigationLedger:
    """Append-only investigation revisions; the study state survives session loss."""

    def __init__(self, store: AppendOnlyJsonlStore) -> None:
        self.store = store

    def record(self, investigation: Investigation) -> StoredEvent:
        return self.store.append(INVESTIGATION_EVENT, investigation_payload(investigation))

    def latest(self, investigation_id: str) -> Investigation | None:
        latest: Investigation | None = None
        for event in self.store.read_all():
            if event.event_type != INVESTIGATION_EVENT:
                continue
            if event.payload.get("investigation_id") != investigation_id:
                continue
            latest = investigation_from_payload(event.payload)
        return latest

    def revisions(self, investigation_id: str) -> tuple[Investigation, ...]:
        return tuple(
            investigation_from_payload(event.payload)
            for event in self.store.read_all()
            if event.event_type == INVESTIGATION_EVENT
            and event.payload.get("investigation_id") == investigation_id
        )


class EvidenceLedger:
    """Append-only admitted scientific evidence."""

    def __init__(self, store: AppendOnlyJsonlStore) -> None:
        self.store = store

    def record(self, evidence: ScientificEvidence) -> StoredEvent:
        return self.store.append(EVIDENCE_EVENT, evidence_payload(evidence))

    def get(self, evidence_id: str) -> ScientificEvidence | None:
        found: ScientificEvidence | None = None
        for event in self.store.read_all():
            if event.event_type != EVIDENCE_EVENT:
                continue
            if event.payload.get("evidence_id") != evidence_id:
                continue
            found = evidence_from_payload(event.payload)
        return found

    def all(self) -> tuple[ScientificEvidence, ...]:
        return tuple(
            evidence_from_payload(event.payload)
            for event in self.store.read_all()
            if event.event_type == EVIDENCE_EVENT
        )
