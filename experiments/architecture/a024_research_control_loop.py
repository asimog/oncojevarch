from __future__ import annotations

import json
from dataclasses import asdict

from experiments.architecture.fixture_capabilities import (
    FIXTURE_CAPABILITY_ID,
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
from oncolab.capabilities import CapabilityRegistry
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from oncolab.gaps import GapLedger
from oncolab.operations import OperationRegistry, ScientificOperation
from research.ledger import EvidenceLedger, InvestigationLedger
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A024")


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")

    registry = CapabilityRegistry()
    registry.register(fixture_record())
    promote_capability(registry)

    operations = OperationRegistry()
    operations.register(fixture_operation(operation_id="op-a024", evidence_id="ev-a024"))
    operations.register(
        ScientificOperation(
            operation_id="op-a024-missing",
            capability_id="no_such_capability",
            version="1",
            inputs={},
            context=fixture_context(evidence_id="ev-a024-missing"),
        )
    )
    runtime = ResearchRuntime(
        registry=registry,
        operations=operations,
        executors={FIXTURE_CAPABILITY_ID: FixtureTokenCountCapability()},
        gaps=GapLedger(store),
        investigations=InvestigationLedger(store),
        evidence=EvidenceLedger(store),
    )

    investigation = fixture_investigation(investigation_id="inv-a024")
    runtime.investigations.record(investigation)
    evidence_step = run_research_step(
        runtime=runtime,
        investigation=investigation,
        need="count tokens in fixture documents",
        operation_id="op-a024",
    )
    gap_step = run_research_step(
        runtime=runtime,
        investigation=evidence_step.revision,
        need="estimate tumor purity from bulk assays",
        operation_id="op-a024-missing",
    )

    fresh_evidence = EvidenceLedger(AppendOnlyJsonlStore(store.path))
    fresh_investigations = InvestigationLedger(AppendOnlyJsonlStore(store.path))
    fresh_gaps = GapLedger(AppendOnlyJsonlStore(store.path))
    latest = fresh_investigations.latest("inv-a024")
    gap_ids = {gap.gap_id for gap in fresh_gaps.recorded()}
    session_independent = (
        latest is not None
        and evidence_step.evidence_id in latest.evidence_ids
        and latest.next_action is not None
        and gap_step.gap_id in latest.next_action
        and fresh_evidence.get(evidence_step.evidence_id) is not None
        and gap_step.gap_id in gap_ids
    )

    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": False,
            "steps": 2,
            "step_1_outcome": evidence_step.outcome,
            "step_2_outcome": gap_step.outcome,
            "evidence_id": evidence_step.evidence_id,
            "gap_id": gap_step.gap_id,
            "revisions": len(fresh_investigations.revisions("inv-a024")),
            "persisted_evidence": fresh_evidence.get(evidence_step.evidence_id) is not None,
            "persisted_gap": gap_step.gap_id in gap_ids,
            "session_independent": session_independent,
        },
        observations=(
            (
                "One research step executed an activated capability, admitted its measurement, "
                "and persisted evidence plus the revised investigation before returning."
            ),
            (
                "A second step with no registered capability recorded an explicit gap and set "
                "the investigation's next action to the gap route."
            ),
            (
                "Rebuilding every ledger from the same append-only store reproduces the "
                "investigation, its evidence, and its gap: agent threads are not scientific "
                "memory."
            ),
        ),
        limitations=(
            "The step takes the information need as an input; identifying the next need from "
            "scientific state remains agent reasoning and is not demonstrated here.",
            "The deterministic fixture capability is not a scientific capability, and no Jev "
            "or OncoX participates.",
            "Operation and admission context are frozen by caller code; typed capability "
            "output contracts remain to be earned.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
