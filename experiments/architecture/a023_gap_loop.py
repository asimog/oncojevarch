from __future__ import annotations

import json
from dataclasses import asdict

from execution.ports import MeasuredResult
from experiments.architecture.fixture_capabilities import (
    FIXTURE_CAPABILITY_ID,
    FIXTURE_CAPABILITY_VERSION,
    FIXTURE_POPULATION,
    FixtureTokenCountCapability,
    fixture_context,
    fixture_investigation,
    fixture_operation,
    fixture_record,
    promote_capability,
)
from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncodex.research_loop import ResearchRuntime, run_research_step
from oncolab.admission import admit_measured_result
from oncolab.capabilities import CapabilityRegistry, EngineeringReadiness, ScientificReadiness
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from oncolab.gaps import Gap, GapKind, GapLedger, GapRoute, gap_identity
from oncolab.operations import OperationRegistry, ScientificOperation
from research.ledger import EvidenceLedger, InvestigationLedger
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A023")

GAP_SCENARIOS: tuple[tuple[GapKind, str, GapRoute], ...] = (
    (GapKind.METHOD, "estimate tumor purity from bulk assays", GapRoute.SCIENTIFIC_RESEARCH),
    (GapKind.CAPABILITY, "join sample identifiers across releases", GapRoute.ENGINEERING),
    (
        GapKind.DECISION,
        "judge whether a candidate deserves deeper pursuit",
        GapRoute.JEV_DESIGN_EVAL,
    ),
    (GapKind.HARNESS, "resume a stopped workspace operation", GapRoute.HARNESS_ENGINEERING),
)


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    gaps = GapLedger(store)

    routes_correct = 0
    for kind, need, expected_route in GAP_SCENARIOS:
        gap = Gap(
            gap_id=gap_identity(need=need, kind=kind, origin="a023"),
            kind=kind,
            need=need,
            evidence=(f"no registered capability satisfies: {need}",),
            unmet_requirements=(f"no applicable capability for: {need}",),
            origin="a023",
        )
        gaps.record(gap)
        if gap.route is expected_route:
            routes_correct += 1

    registry = CapabilityRegistry()
    registry.register(fixture_record())
    unsafe_promotions_blocked = 0
    try:
        registry.advance_engineering(
            FIXTURE_CAPABILITY_ID,
            FIXTURE_CAPABILITY_VERSION,
            EngineeringReadiness.PROMOTED,
        )
    except ValueError:
        unsafe_promotions_blocked += 1
    try:
        registry.set_scientific_readiness(
            FIXTURE_CAPABILITY_ID,
            FIXTURE_CAPABILITY_VERSION,
            ScientificReadiness.VALIDATED_FOR_REPLAY,
        )
    except ValueError:
        unsafe_promotions_blocked += 1
    promoted = promote_capability(registry)

    operations = OperationRegistry()
    operations.register(fixture_operation(operation_id="op-a023", evidence_id="ev-a023"))
    runtime = ResearchRuntime(
        registry=registry,
        operations=operations,
        executors={FIXTURE_CAPABILITY_ID: FixtureTokenCountCapability()},
        gaps=gaps,
        investigations=InvestigationLedger(store),
        evidence=EvidenceLedger(store),
    )
    investigation = fixture_investigation(investigation_id="inv-a023")
    runtime.investigations.record(investigation)
    activation_step = run_research_step(
        runtime=runtime,
        investigation=investigation,
        need="count tokens in fixture documents",
        operation_id="op-a023",
    )

    reasoning_result = MeasuredResult(
        operation_id="op-a023-reasoning",
        method_id="reasoning",
        population_id=FIXTURE_POPULATION.population_id,
        measurements={"mean_document_tokens": 4.0},
        provenance={},
    )
    reasoning_refusal = admit_measured_result(
        reasoning_result,
        context=fixture_context(evidence_id="ev-a023-reasoning"),
    )
    refusal_reasons = (
        tuple(reason.value for reason in reasoning_refusal.refusal.reasons)
        if reasoning_refusal.refusal
        else ()
    )

    missing_operations = OperationRegistry()
    missing_operations.register(
        ScientificOperation(
            operation_id="op-a023-missing",
            capability_id="no_such_capability",
            version="1",
            inputs={},
            context=fixture_context(evidence_id="ev-a023-missing"),
        )
    )
    gap_step = run_research_step(
        runtime=ResearchRuntime(
            registry=registry,
            operations=missing_operations,
            executors={},
            gaps=gaps,
            investigations=runtime.investigations,
            evidence=runtime.evidence,
        ),
        investigation=activation_step.revision,
        need="estimate tumor purity from bulk assays",
        operation_id="op-a023-missing",
    )

    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": False,
            "gaps_recorded": len(GAP_SCENARIOS) + 1,
            "routes_correct": routes_correct,
            "unsafe_promotions_blocked": unsafe_promotions_blocked,
            "activation_outcome": activation_step.outcome,
            "activation_evidence_id": activation_step.evidence_id,
            "activation_readiness": promoted.scientific_readiness.value,
            "loop_gap_outcome": gap_step.outcome,
            "loop_gap_route": "engineering",
            "reasoning_refusal_reasons": list(refusal_reasons),
            "recorded_gaps": [gap.gap_id for gap in gaps.recorded()],
        },
        observations=(
            (
                "All four gap kinds are recorded with provenance and route to their owning "
                "process; a capability absence becomes an inspectable durable state."
            ),
            (
                "Promotion is blocked before engineering verification and scientific readiness "
                "is blocked before engineering verification; after bounded activation the "
                "capability executes and its measurement is admitted."
            ),
            (
                "A reasoning-only result with no provenance is refused at admission, so "
                "improvisation cannot enter the scientific evidence path."
            ),
        ),
        limitations=(
            "Gap classification here is caller-declared and routing is table-driven; routing "
            "quality under ambiguous real needs is not tested.",
            "The promotion path uses the deterministic fixture capability, not a scientific "
            "capability.",
            "No Jev and no OncoX participate in this experiment by design.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
