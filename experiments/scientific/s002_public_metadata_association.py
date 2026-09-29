from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from evidence.models import Coverage, Missingness, Provenance
from execution.gdc import GdcClient
from experiments.scientific.catalog import get_scientific_experiment
from experiments.scientific.s001_public_metadata_association import (
    CAPABILITY_VERSION,
    ITERATIONS,
    MEASUREMENT,
    METHOD_ID,
    POPULATION,
    SEED,
    SOURCE_ID,
    AssayCoavailabilityCapability,
    code_identity,
)
from oncodex.config import Settings
from oncodex.research_loop import ResearchRuntime, run_research_step
from oncolab.admission import AdmissionContext
from oncolab.capabilities import (
    CapabilityKind,
    CapabilityRecord,
    CapabilityRegistry,
    EngineeringReadiness,
    ScientificReadiness,
)
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from oncolab.gaps import GapLedger
from oncolab.operations import OperationRegistry, ScientificOperation
from research.ledger import EvidenceLedger, InvestigationLedger
from research.models import Investigation
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_scientific_experiment("S002")
MIN_PROJECTS = 30


def _register(registry: CapabilityRegistry) -> None:
    identity = code_identity()
    registry.register(
        CapabilityRecord(
            capability_id=SOURCE_ID,
            kind=CapabilityKind.SOURCE,
            version=CAPABILITY_VERSION,
            source_identity=identity,
            applicability=("public metadata", "project aggregates"),
            purpose="read public GDC project metadata with experimental-strategy file counts",
            domain_owner="gdc-source",
            inputs=("program filter",),
            outputs=("project assay profiles",),
            evaluated_domain="GDC public projects endpoint, TCGA program",
        )
    )
    registry.register(
        CapabilityRecord(
            capability_id=METHOD_ID,
            kind=CapabilityKind.METHOD,
            version=CAPABILITY_VERSION,
            source_identity=identity,
            applicability=("association tests", "null models", "project aggregates"),
            purpose="seeded permutation statistic for assay co-availability concentration",
            domain_owner="s002",
            inputs=("project assay profiles",),
            outputs=(MEASUREMENT,),
            evaluated_domain="GDC project metadata, TCGA program",
        )
    )
    for capability_id in (SOURCE_ID, METHOD_ID):
        for target in (
            EngineeringReadiness.TESTED,
            EngineeringReadiness.VERIFIED,
            EngineeringReadiness.PROMOTED,
        ):
            registry.advance_engineering(capability_id, CAPABILITY_VERSION, target)
    registry.set_scientific_readiness(
        SOURCE_ID, CAPABILITY_VERSION, ScientificReadiness.VALIDATED_FOR_REPLAY
    )
    registry.set_scientific_readiness(
        METHOD_ID, CAPABILITY_VERSION, ScientificReadiness.VALIDATED_FOR_DEFINED_DOMAIN
    )


def _base_context() -> AdmissionContext:
    return AdmissionContext(
        evidence_id="ev-s002",
        measurement=MEASUREMENT,
        population=POPULATION,
        coverage=Coverage(requested=None, retrieved=None),
        missingness=Missingness(),
        provenance=Provenance(
            source="GDC API",
            source_version="pending-dispatch",
            method_id=METHOD_ID,
            method_version=CAPABILITY_VERSION,
            code_identity=code_identity(),
        ),
        metadata={
            "seed": SEED,
            "iterations": ITERATIONS,
            "null": "independent RNA-Seq and WXS flag permutations preserving marginals",
            "predecessor": "S001",
        },
    )


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    if not live:
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.FROZEN,
            frozen_fingerprint=frozen.fingerprint,
            measurements={
                "live": False,
                "preflight": "protocol frozen; no measurement taken and no network contacted",
                "spec_errors": list(SPEC.validation_errors()),
                "population": POPULATION.population_id,
                "seed": SEED,
                "iterations": ITERATIONS,
                "min_projects": MIN_PROJECTS,
                "predecessor": "S001",
            },
            observations=(
                "S002 corrects S001's frozen minimum-project count, which the live S001 run "
                "failed against at 33 retrieved TCGA projects.",
            ),
            limitations=("Preflight records no scientific evidence by design.",),
        )
        store.append("scientific_experiment_result", asdict(result))
        return json.dumps(asdict(result), indent=2, default=str)

    registry = CapabilityRegistry()
    _register(registry)
    runtime = ResearchRuntime(
        registry=registry,
        operations=OperationRegistry(),
        executors={
            METHOD_ID: AssayCoavailabilityCapability(
                client=GdcClient(), min_projects=MIN_PROJECTS
            )
        },
        gaps=GapLedger(store),
        investigations=InvestigationLedger(store),
        evidence=EvidenceLedger(store),
    )
    runtime.operations.register(
        ScientificOperation(
            operation_id="op-s002",
            capability_id=METHOD_ID,
            version=CAPABILITY_VERSION,
            inputs={},
            context=_base_context(),
        )
    )
    investigation = Investigation(
        investigation_id="inv-s002",
        question_id="q-s002",
        candidate_id="c-s002",
        population_id=POPULATION.population_id,
        unresolved_uncertainty=(
            "assay co-availability structure across TCGA projects is unmeasured",
        ),
    )
    runtime.investigations.record(investigation)

    status = ExperimentStatus.FAILED
    measurements: dict[str, Any] = {"live": True}
    observations: tuple[str, ...] = ()
    failure_reason = ""
    try:
        step = run_research_step(
            runtime=runtime,
            investigation=investigation,
            need="measure assay co-availability concentration across TCGA projects",
            operation_id="op-s002",
        )
        measurements["step_outcome"] = step.outcome
        if step.outcome == "evidence":
            evidence = runtime.evidence.get(step.evidence_id)
            if evidence is None:
                raise RuntimeError("admitted evidence was not persisted")
            value = float(evidence.value)
            null_mean = float(evidence.metadata["null_mean"])
            p_value = float(evidence.metadata["permutation_p"])
            status = ExperimentStatus.COMPLETED
            measurements["evidence_id"] = evidence.evidence_id
            measurements["value"] = value
            measurements["null_mean"] = null_mean
            measurements["permutation_p"] = p_value
            measurements["projects_total"] = int(evidence.metadata["projects_total"])
            measurements["co_available_projects"] = int(
                evidence.metadata["co_available_projects"]
            )
            measurements["coverage"] = {
                "requested": evidence.coverage.requested,
                "retrieved": evidence.coverage.retrieved,
                "assayed": evidence.coverage.assayed,
            }
            measurements["missingness"] = {
                "unknown": evidence.missingness.unknown,
            }
            if p_value <= 0.05:
                statement = (
                    f"The site concentration of co-available projects exceeded the frozen "
                    f"independence null (max share {value:.4f}, null mean {null_mean:.4f}, "
                    f"p={p_value:.4f}); this is a public-metadata structure observation, not "
                    "a biological claim."
                )
            else:
                statement = (
                    f"The site concentration of co-available projects did not exceed the frozen "
                    f"independence null (max share {value:.4f}, null mean {null_mean:.4f}, "
                    f"p={p_value:.4f})."
                )
            observations = (statement,)
        else:
            failure_reason = f"step outcome was {step.outcome}"
    except Exception as exc:  # noqa: BLE001 - failure branch must record, not crash
        failure_reason = f"{type(exc).__name__}: {exc}"
    if status is ExperimentStatus.FAILED:
        measurements["failure_reason"] = failure_reason or "unknown failure"
        observations = (f"S002 did not complete: {measurements['failure_reason']}.",)
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=status,
        frozen_fingerprint=frozen.fingerprint,
        measurements=measurements,
        observations=observations,
        limitations=(
            "The question is about public metadata structure, not disease biology.",
            "One prespecified statistic and one null family; no multiplicity family is claimed.",
            "Coverage and missingness are disclosed by the capable execution and admitted "
            "together with the value.",
            "No Jev and no OncoX participate in this investigation.",
        ),
    )
    store.append("scientific_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
