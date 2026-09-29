from __future__ import annotations

import json
from dataclasses import asdict

from experiments.architecture.fixture_capabilities import (
    FIXTURE_CAPABILITY_ID,
    FIXTURE_CAPABILITY_VERSION,
    FixtureMissingValueCapability,
    FixtureTokenCountCapability,
    fixture_context,
    fixture_investigation,
    fixture_record,
    promote_capability,
)
from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.admission import admit_measured_result
from oncolab.capabilities import CapabilityRegistry
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from research.ledger import EvidenceLedger, InvestigationLedger
from research.models import Investigation
from research.state import revise_investigation
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A021")


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")

    registry = CapabilityRegistry()
    registry.register(fixture_record())
    promoted = promote_capability(registry)

    capability = FixtureTokenCountCapability()
    measured = capability.execute(operation_id="op-a021-direct", inputs={})
    admitted = admit_measured_result(
        measured,
        context=fixture_context(evidence_id="ev-a021-direct"),
    )

    missing = FixtureMissingValueCapability().execute(operation_id="op-a021-missing", inputs={})
    refused = admit_measured_result(
        missing,
        context=fixture_context(evidence_id="ev-a021-missing"),
    )

    investigation_ledger = InvestigationLedger(store)
    evidence_ledger = EvidenceLedger(store)
    investigation = fixture_investigation(investigation_id="inv-a021")
    investigation_ledger.record(investigation)

    evidence = admitted.evidence
    revision: Investigation | None = None
    if evidence is not None:
        evidence_ledger.record(evidence)
        revision = revise_investigation(
            investigation,
            evidence_ids=(evidence.evidence_id,),
            unresolved_uncertainty=(),
        )
        investigation_ledger.record(revision)

    refusal_reasons = (
        tuple(reason.value for reason in refused.refusal.reasons) if refused.refusal else ()
    )
    persisted_evidence = (
        evidence_ledger.get(evidence.evidence_id) is not None if evidence is not None else False
    )
    latest = investigation_ledger.latest("inv-a021")
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": False,
            "admitted": admitted.admitted,
            "admitted_measurement": evidence.measurement if evidence else "",
            "admitted_value": evidence.value if evidence else None,
            "refusal_reasons": list(refusal_reasons),
            "engineering_readiness": promoted.engineering_readiness.value,
            "scientific_readiness": promoted.scientific_readiness.value,
            "investigation_revisions": len(investigation_ledger.revisions("inv-a021")),
            "persisted_evidence": persisted_evidence,
            "latest_evidence_ids": list(latest.evidence_ids) if latest else [],
            "latest_unresolved_uncertainty": list(latest.unresolved_uncertainty) if latest else [],
            "capability": f"{FIXTURE_CAPABILITY_ID}:{FIXTURE_CAPABILITY_VERSION}",
        },
        observations=(
            (
                "A measured result with method, matching population, provenance, and a present "
                "value became ScientificEvidence; a value-less measurement was refused and never "
                "became evidence."
            ),
            (
                "The investigation revision appended the admitted evidence id, cleared the "
                "answered uncertainty, and survives through the append-only ledger."
            ),
        ),
        limitations=(
            "The nucleus is exercised with a deterministic synthetic fixture, not cancer data; "
            "it establishes the admission boundary and revision mechanics only.",
            "The admission context is supplied by deterministic caller code; typed capability "
            "output contracts are not yet earned.",
            "No Jev and no OncoX participate in this experiment by design.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
