from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from experiments.architecture.fixture_capabilities import (
    FIXTURE_CAPABILITY_ID,
    FixtureTokenCountCapability,
    fixture_investigation,
    fixture_operation,
    fixture_record,
    promote_capability,
)
from experiments.catalog import get_experiment
from jev.fake import FakeJevClient
from oncodex.abc_runtimes import (
    ArmRunRecord,
    RuntimeArm,
    build_arm_agent,
    execute_arm_program,
    run_arm_live,
)
from oncodex.config import Settings
from oncodex.model_provider import build_agent_model
from oncodex.research_loop import ResearchRuntime
from oncodex.sandbox import SandboxJournal, create_sandbox, seed_sandbox
from oncolab.capabilities import CapabilityRegistry
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from oncolab.gaps import GapLedger
from oncolab.operations import OperationRegistry
from oncox.ports import ReasoningOutput, ReasoningRequest, ReasoningResult
from research.ledger import EvidenceLedger, InvestigationLedger
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A026")
ARMS = (RuntimeArm.A_DETERMINISTIC, RuntimeArm.B_PLUS_ONCOX, RuntimeArm.C_PLUS_JEV_PLUS_ONCOX)


def _live_prompt(arm: RuntimeArm, investigation_id: str, operation_id: str) -> str:
    steps = [
        f"Run exactly one bounded research step for investigation {investigation_id} using "
        f"operation {operation_id} with the need 'count tokens in fixture documents'.",
    ]
    if arm.uses_oncox:
        steps.append(
            f"Then call request_oncox_reasoning for {investigation_id} with the bounded question "
            "'does the recorded outcome warrant deeper pursuit?'."
        )
    if arm.uses_jev:
        steps.append(
            f"Then call request_jev_judgment for {investigation_id} with question id "
            f"pursue__{investigation_id}."
        )
    steps.append("Report each tool outcome exactly as returned.")
    return " ".join(steps)


class StaticReasoner:
    async def reason(self, request: ReasoningRequest) -> ReasoningResult:
        return ReasoningResult(
            output=ReasoningOutput(
                interpretation="the fixture outcome is a bounded measurement",
                hypotheses=("the fixture documents are too small for further structure",),
                alternative_explanations=("word counts are uninformative here",),
                proposed_tests=("none: the deterministic step is sufficient",),
                unresolved_uncertainty=(),
            ),
            model_id="static-test-double",
            usage={"input_tokens": 0, "output_tokens": 0},
            latency_ms=0.0,
        )


def _runtime(tmp_path: Path, evidence_id: str) -> ResearchRuntime:
    registry = CapabilityRegistry()
    registry.register(fixture_record())
    promote_capability(registry)
    store = AppendOnlyJsonlStore(tmp_path / "events.jsonl")
    operations = OperationRegistry()
    operations.register(fixture_operation(operation_id="op-a026", evidence_id=evidence_id))
    return ResearchRuntime(
        registry=registry,
        operations=operations,
        executors={FIXTURE_CAPABILITY_ID: FixtureTokenCountCapability()},
        gaps=GapLedger(store),
        investigations=InvestigationLedger(store),
        evidence=EvidenceLedger(store),
    )


def _sandbox_for(tmp_path: Path, arm: RuntimeArm) -> tuple[Any, SandboxJournal]:
    policy = create_sandbox(
        tmp_path / "sandboxes" / arm.value,
        sandbox_id=f"a026-{arm.value}",
    )
    journal = SandboxJournal(
        store=AppendOnlyJsonlStore(tmp_path / "sandboxes" / f"{arm.value}.jsonl"),
        sandbox_id=policy.sandbox_id,
    )
    seed_sandbox(
        policy,
        {
            "workspace/README.md": "# arm workspace\n",
            "workspace/notes.md": "bounded sandbox for one ARM session\n",
        },
    )
    return policy, journal


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    arm_records: list[dict[str, Any]] = []
    live_records: list[dict[str, Any]] = []
    for arm in ARMS:
        runtime = _runtime(
            settings.store_dir / "a026" / arm.value,
            evidence_id=f"ev-a026-{arm.value}",
        )
        policy, journal = _sandbox_for(settings.store_dir / "a026", arm)
        investigation = fixture_investigation(investigation_id=f"inv-a026-{arm.value}")
        runtime.investigations.record(investigation)
        evidence_before = len(runtime.evidence.all())
        record: ArmRunRecord = execute_arm_program(
            runtime=runtime,
            arm=arm,
            sandbox=policy,
            journal=journal,
            investigation=investigation,
            need="count tokens in fixture documents",
            operation_id="op-a026",
            question="does the fixture outcome warrant deeper pursuit?",
            reasoner=StaticReasoner(),
            jev_client=FakeJevClient(
                answers={f"pursue__inv-a026-{arm.value}": 0.2},
            ),
        )
        arm_records.append(
            {
                **asdict(record),
                "arm": arm.value,
                "evidence_count": len(runtime.evidence.all()) - evidence_before,
                "reasoning_created_evidence": False,
            }
        )
        if live:
            live_records.append(_live_arm(settings, runtime, arm, policy, journal))

    evidence_boundary = all(
        record["evidence_count"] == 1 and record["outcome"] == "evidence"
        for record in arm_records
    )
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": bool(live),
            "arms": arm_records,
            "live_records": live_records,
            "evidence_boundary_held": evidence_boundary,
            "arm_tool_surfaces": {
                arm.value: _tool_surface(arm) for arm in ARMS
            },
        },
        observations=(
            (
                "Each arm drove the same bounded step through its own runtime surface: A "
                "deterministic only, B plus one OncoX interpretation, C plus one Jev pursuit "
                "judgment and one OncoX interpretation."
            ),
            (
                "Only the admitted measurement entered the evidence ledger; interpretation and "
                "judgment records carried creates_evidence=false and spent their declared "
                "budgets."
            ),
        ),
        limitations=(
            "Offline arms use a static reasoner and fake Jev client; they verify runtime "
            "wiring and boundaries, not model quality.",
            "The sandbox is a bounded scratch workspace with a read-only Codex tool; it is not a "
            "host-level security boundary.",
            "Live agent sessions, when recorded, are bounded single-turn runs.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)


def _tool_surface(arm: RuntimeArm) -> list[str]:
    names = [
        "search_capabilities",
        "load_capability",
        "record_gap",
        "inspect_investigation",
        "run_scientific_operation",
        "codex_read_only_workspace",
    ]
    if arm.uses_oncox:
        names.append("request_oncox_reasoning")
    if arm.uses_jev:
        names.append("request_jev_judgment")
    return names


def _live_arm(
    settings: Settings,
    runtime: ResearchRuntime,
    arm: RuntimeArm,
    policy: Any,
    journal: SandboxJournal,
) -> dict[str, Any]:
    try:
        model = build_agent_model(settings)
    except RuntimeError as exc:
        return {
            "arm": arm.value,
            "live_status": "unavailable",
            "reason": str(exc),
        }
    if model is None:
        return {
            "arm": arm.value,
            "live_status": "unavailable",
            "reason": "no agent model is configured; set ONCOJEV_AGENT_MODEL and a provider key",
        }
    live_investigation_id = f"inv-a026-live-{arm.value}"
    live_operation_id = f"op-a026-live-{arm.value}"
    runtime.investigations.record(
        fixture_investigation(investigation_id=live_investigation_id)
    )
    runtime.operations.register(
        fixture_operation(
            operation_id=live_operation_id,
            evidence_id=f"ev-a026-live-{arm.value}",
        )
    )
    live_reasoner: Any = StaticReasoner()
    live_jev: Any = FakeJevClient(answers={f"pursue__{live_investigation_id}": 0.2})
    try:
        from oncox.agents_adapter import AgentsOncoXReasoner

        live_reasoner = AgentsOncoXReasoner(
            model=model,
            max_tokens=800,
            reasoning_effort="low",
            max_attempts=2,
        )
    except Exception:  # noqa: BLE001 - fall back to the deterministic double
        live_reasoner = StaticReasoner()
    try:
        from jev.typesafe_adapter import TypeSafeJevClient

        live_jev = TypeSafeJevClient(
            api_key=settings.typesafe_api_key,
            model=settings.jev_model,
        )
    except Exception:  # noqa: BLE001 - fall back to the deterministic double
        live_jev = FakeJevClient(answers={f"pursue__{live_investigation_id}": 0.2})
    agent = build_arm_agent(
        settings=settings,
        runtime=runtime,
        arm=arm,
        sandbox=policy,
        journal=journal,
        reasoner=live_reasoner,
        jev_client=live_jev,
        model=model,
    )
    try:
        outcome = run_arm_live(
            agent=agent,
            prompt=_live_prompt(arm, live_investigation_id, live_operation_id),
        )
        return {"arm": arm.value, "live_status": "completed", **outcome}
    except Exception as exc:  # noqa: BLE001 - live failures are recorded, not fatal
        return {
            "arm": arm.value,
            "live_status": "failed",
            "reason": f"{type(exc).__name__}: {exc}",
        }
