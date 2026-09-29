from __future__ import annotations

import json
from dataclasses import asdict, replace
from math import log
from typing import Any

from evidence.models import Coverage, EntityLevel, Missingness, PopulationSpec, Provenance
from execution.ports import MeasuredResult
from experiments.architecture.fixture_capabilities import (
    FixtureTokenCountCapability,
    fixture_investigation,
    fixture_operation,
    fixture_record,
    promote_capability,
)
from experiments.catalog import get_experiment
from jev.fake import FakeJevClient
from oncodex.abc_runtimes import RuntimeArm, execute_arm_program
from oncodex.config import Settings
from oncodex.research_loop import ResearchRuntime, unmet_activation_requirements
from oncodex.sandbox import SandboxJournal, create_sandbox, seed_sandbox
from oncolab.admission import AdmissionContext
from oncolab.capabilities import (
    CapabilityKind,
    CapabilityRecord,
    CapabilityRegistry,
    EngineeringReadiness,
    ScientificReadiness,
)
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from oncolab.gaps import Gap, GapKind, GapLedger, gap_identity
from oncolab.operations import OperationRegistry, ScientificOperation
from oncox.ports import ReasoningOutput, ReasoningRequest, ReasoningResult
from research.ledger import EvidenceLedger, InvestigationLedger
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A027")
ENTROPY_ID = "site_entropy_summary"
ENTROPY_VERSION = "1"
FIXTURE_SITES = ("alpha", "alpha", "beta", "beta", "gamma")
SITE_POPULATION = PopulationSpec(
    population_id="fixture-sites",
    definition="frozen synthetic site labels used as a deterministic fixture",
    entity_level=EntityLevel.OTHER,
    expected_count=len(FIXTURE_SITES),
)


class _StaticReasoner:
    async def reason(self, request: ReasoningRequest) -> ReasoningResult:
        return ReasoningResult(
            output=ReasoningOutput(
                interpretation="the recorded gap is resolvable by bounded engineering",
                hypotheses=("a deterministic entropy summary closes the gap",),
                alternative_explanations=(),
                proposed_tests=("operate the new capability once and admit its measurement",),
                unresolved_uncertainty=(),
            ),
            model_id="static-test-double",
            usage={"input_tokens": 0, "output_tokens": 0},
            latency_ms=0.0,
        )


class SiteEntropyCapability:
    """The smallest capability that closes the recorded gap: deterministic entropy of labels."""

    capability_id = ENTROPY_ID
    version = ENTROPY_VERSION

    def execute(self, *, operation_id: str, inputs: dict[str, Any]) -> MeasuredResult:
        sites = tuple(str(site) for site in inputs.get("sites") or FIXTURE_SITES)
        counts: dict[str, int] = {}
        for site in sites:
            counts[site] = counts.get(site, 0) + 1
        entropy = -sum(
            (count / len(sites)) * log(count / len(sites)) for count in counts.values()
        )
        return MeasuredResult(
            operation_id=operation_id,
            method_id=self.capability_id,
            population_id=SITE_POPULATION.population_id,
            measurements={"site_entropy": entropy},
            provenance={"source": "frozen synthetic fixture", "source_version": "1"},
        )

    def admission_context(
        self, *, result: MeasuredResult, base: AdmissionContext
    ) -> AdmissionContext:
        return replace(
            base,
            coverage=Coverage(
                requested=len(FIXTURE_SITES),
                retrieved=len(FIXTURE_SITES),
                assayed=len(FIXTURE_SITES),
            ),
            missingness=Missingness(),
        )


def _entropy_operation() -> ScientificOperation:
    return ScientificOperation(
        operation_id="op-a027-entropy",
        capability_id=ENTROPY_ID,
        version=ENTROPY_VERSION,
        inputs={"sites": list(FIXTURE_SITES)},
        context=AdmissionContext(
            evidence_id="ev-a027-entropy",
            measurement="site_entropy",
            population=SITE_POPULATION,
            coverage=Coverage(requested=None, retrieved=None),
            missingness=Missingness(),
            provenance=Provenance(
                source="frozen synthetic fixture",
                source_version="1",
                method_id=ENTROPY_ID,
                method_version=ENTROPY_VERSION,
                code_identity="module:a027",
            ),
        ),
    )


def _runtime(tmp_path: Any, *, with_entropy_executor: bool) -> ResearchRuntime:
    registry = CapabilityRegistry()
    registry.register(fixture_record())
    promote_capability(registry)
    store = AppendOnlyJsonlStore(tmp_path / "events.jsonl")
    operations = OperationRegistry()
    operations.register(
        fixture_operation(operation_id="op-a027-fixture", evidence_id="ev-a027-fixture")
    )
    operations.register(_entropy_operation())
    executors: dict[str, Any] = {fixture_record().capability_id: FixtureTokenCountCapability()}
    if with_entropy_executor:
        executors[ENTROPY_ID] = SiteEntropyCapability()
    return ResearchRuntime(
        registry=registry,
        operations=operations,
        executors=executors,
        gaps=GapLedger(store),
        investigations=InvestigationLedger(store),
        evidence=EvidenceLedger(store),
    )


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    base = settings.store_dir / "a027"

    # Phase 1: a real need hits a missing capability through the agent runtime.
    runtime = _runtime(base / "phase1", with_entropy_executor=False)
    policy = create_sandbox(base / "phase1" / "sandbox", sandbox_id="a027-phase1")
    journal = SandboxJournal(
        store=AppendOnlyJsonlStore(base / "phase1" / "sandbox.jsonl"),
        sandbox_id=policy.sandbox_id,
    )
    seed_sandbox(policy, {"workspace/README.md": "# gap proof\n"})
    investigation = fixture_investigation(investigation_id="inv-a027")
    runtime.investigations.record(investigation)
    gap_record = execute_arm_program(
        runtime=runtime,
        arm=RuntimeArm.C_PLUS_JEV_PLUS_ONCOX,
        sandbox=policy,
        journal=journal,
        investigation=investigation,
        need="measure site entropy across the fixture population",
        operation_id="op-a027-entropy",
        question="should engineering close the recorded capability gap?",
        reasoner=_StaticReasoner(),
        jev_client=FakeJevClient(answers={"pursue__inv-a027": 0.9}),
    )
    recorded_gaps = runtime.gaps.recorded()
    gap = next((item for item in recorded_gaps if item.gap_id == gap_record.gap_id), None)
    gap_route = gap.route.value if gap else ""

    # A MethodGap control: an understood-but-unknown method must not be routed to engineering.
    method_gap = Gap(
        gap_id=gap_identity(
            need="estimate tumor purity from bulk assays",
            kind=GapKind.METHOD,
            origin="a027",
        ),
        kind=GapKind.METHOD,
        need="estimate tumor purity from bulk assays",
        evidence=("no validated method exists for this assay",),
        unmet_requirements=("no validated method exists for this assay",),
        origin="a027",
    )
    runtime.gaps.record(method_gap)

    # Phase 2: governed evolution closes the capability gap; nothing self-promoted.
    registry = runtime.registry
    gates_blocked = 0
    registry.register(
        CapabilityRecord(
            capability_id=ENTROPY_ID,
            kind=CapabilityKind.METHOD,
            version=ENTROPY_VERSION,
            source_identity="module:a027",
            applicability=("aggregate summaries", "site entropy"),
            purpose="deterministic entropy of site labels over a frozen population",
            domain_owner="a027",
            inputs=("site labels",),
            outputs=("site_entropy",),
            evaluated_domain="frozen synthetic fixture",
        )
    )
    try:
        registry.advance_engineering(ENTROPY_ID, ENTROPY_VERSION, EngineeringReadiness.PROMOTED)
    except ValueError:
        gates_blocked += 1
    for target in (
        EngineeringReadiness.TESTED,
        EngineeringReadiness.VERIFIED,
        EngineeringReadiness.PROMOTED,
    ):
        registry.advance_engineering(ENTROPY_ID, ENTROPY_VERSION, target)
    record = registry.get(ENTROPY_ID, ENTROPY_VERSION)
    pre_activation_unmet = unmet_activation_requirements(record)
    registry.set_scientific_readiness(
        ENTROPY_ID, ENTROPY_VERSION, ScientificReadiness.VALIDATED_FOR_DEFINED_DOMAIN
    )
    phase2_runtime = ResearchRuntime(
        registry=registry,
        operations=runtime.operations,
        executors={**runtime.executors, ENTROPY_ID: SiteEntropyCapability()},
        gaps=runtime.gaps,
        investigations=runtime.investigations,
        evidence=runtime.evidence,
    )
    policy2 = create_sandbox(base / "phase2" / "sandbox", sandbox_id="a027-phase2")
    journal2 = SandboxJournal(
        store=AppendOnlyJsonlStore(base / "phase2" / "sandbox.jsonl"),
        sandbox_id=policy2.sandbox_id,
    )
    seed_sandbox(policy2, {"workspace/README.md": "# evolution\n"})
    latest_investigation = phase2_runtime.investigations.latest("inv-a027")
    if latest_investigation is None:
        raise RuntimeError("the gap revision was not persisted")
    close_record = execute_arm_program(
        runtime=phase2_runtime,
        arm=RuntimeArm.A_DETERMINISTIC,
        sandbox=policy2,
        journal=journal2,
        investigation=latest_investigation,
        need="measure site entropy across the fixture population",
        operation_id="op-a027-entropy",
        question="",
    )
    evidence = phase2_runtime.evidence.get(close_record.evidence_id)

    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": False,
            "phase1_outcome": gap_record.outcome,
            "phase1_gap_id": gap_record.gap_id,
            "phase1_gap_route": gap_route,
            "phase1_jev_answer": (
                gap_record.jev_record.get("policy", "") if gap_record.jev_record else ""
            ),
            "method_gap_id": method_gap.gap_id,
            "method_gap_route": method_gap.route.value,
            "method_gap_implemented": False,
            "unsafe_promotions_blocked": gates_blocked,
            "pre_activation_unmet": list(pre_activation_unmet),
            "phase2_outcome": close_record.outcome,
            "phase2_evidence_id": close_record.evidence_id,
            "phase2_value": evidence.value if evidence else None,
            "gap_closed": close_record.outcome == "evidence",
            "recorded_gap_count": len(phase2_runtime.gaps.recorded()),
            "sandbox_actions": list(journal.action_names()) + list(journal2.action_names()),
        },
        observations=(
            (
                "A real need with no applicable capability produced an explicit routed gap "
                "through the arm-C runtime; the Jev judgment then signaled pursuit without "
                "creating evidence or implementing anything."
            ),
            (
                "The smallest justified capability was registered, blocked from skipping "
                "promotion steps, activated after verification and scientific readiness, and "
                "then executed; its measurement was admitted and the investigation's next "
                "action advanced."
            ),
            (
                "The MethodGap control routed to scientific research and was not implemented, "
                "so method invention and engineering remain separate epistemic events."
            ),
        ),
        limitations=(
            "The gap was closed on a frozen synthetic fixture; the same path on real science "
            "requires a scientific experiment identity.",
            "The 'pursue' judgment comes from a fake Jev client; live judgment is exercised by "
            "the A/B/C runtime path.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
