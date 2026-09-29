from pathlib import Path
from typing import Any

import pytest

from evidence.projections import SemanticProjection
from experiments.architecture.fixture_capabilities import (
    FIXTURE_CAPABILITY_ID,
    FixtureTokenCountCapability,
    fixture_investigation,
    fixture_operation,
    fixture_record,
    promote_capability,
)
from jev.contracts import JevCapability, JevDecision, JevPrimitive
from jev.fake import FakeJevClient
from oncodex.abc_runtimes import (
    ArmRunRecord,
    BudgetExceeded,
    CallBudget,
    RuntimeArm,
    build_arm_agent,
    execute_arm_program,
)
from oncodex.research_loop import ResearchRuntime
from oncodex.sandbox import SandboxJournal, SandboxPolicy, create_sandbox, guard_path, seed_sandbox
from oncolab.capabilities import CapabilityRegistry
from oncolab.gaps import GapLedger
from oncolab.operations import OperationRegistry
from oncox.ports import ReasoningOutput, ReasoningRequest, ReasoningResult
from research.ledger import EvidenceLedger, InvestigationLedger
from store.jsonl import AppendOnlyJsonlStore


class StaticReasoner:
    async def reason(self, request: ReasoningRequest) -> ReasoningResult:
        return ReasoningResult(
            output=ReasoningOutput(
                interpretation="the recorded outcome leaves one bounded question open",
                hypotheses=("assay design invariance explains the null",),
                alternative_explanations=("site aggregation hides structure",),
                proposed_tests=("measure with a variant assay pair",),
                unresolved_uncertainty=("variance is absent in the frozen population",),
            ),
            model_id="static-test-double",
            usage={"input_tokens": 0, "output_tokens": 0},
            latency_ms=0.0,
        )


def _runtime(tmp_path: Path) -> ResearchRuntime:
    registry = CapabilityRegistry()
    registry.register(fixture_record())
    promote_capability(registry)
    store = AppendOnlyJsonlStore(tmp_path / "events.jsonl")
    operations = OperationRegistry()
    operations.register(fixture_operation(operation_id="op-abc", evidence_id="ev-abc"))
    return ResearchRuntime(
        registry=registry,
        operations=operations,
        executors={FIXTURE_CAPABILITY_ID: FixtureTokenCountCapability()},
        gaps=GapLedger(store),
        investigations=InvestigationLedger(store),
        evidence=EvidenceLedger(store),
    )


def _sandbox(tmp_path: Path, arm: RuntimeArm) -> tuple[SandboxPolicy, SandboxJournal]:
    store = AppendOnlyJsonlStore(tmp_path / "sandbox.jsonl")
    policy = create_sandbox(tmp_path / "sandboxes" / arm.value, sandbox_id=f"sb-{arm.value}")
    journal = SandboxJournal(store=store, sandbox_id=policy.sandbox_id)
    seed_sandbox(policy, {"workspace/README.md": "# sandbox\n", "workspace/fixture.txt": "a b c\n"})
    return policy, journal


def _run_arm(tmp_path: Path, arm: RuntimeArm, *, budget: CallBudget | None = None) -> ArmRunRecord:
    runtime = _runtime(tmp_path / arm.value)
    policy, journal = _sandbox(tmp_path, arm)
    investigation = fixture_investigation(investigation_id=f"inv-{arm.value}")
    runtime.investigations.record(investigation)
    jev = FakeJevClient(answers={f"pursue__inv-{arm.value}": 0.2})
    return execute_arm_program(
        runtime=runtime,
        arm=arm,
        sandbox=policy,
        journal=journal,
        investigation=investigation,
        need="count tokens in fixture documents",
        operation_id="op-abc",
        question="does the outcome warrant deeper pursuit?",
        reasoner=StaticReasoner(),
        jev_client=jev,
        budget=budget,
    )


def test_arm_a_is_deterministic_only(tmp_path: Path) -> None:
    record = _run_arm(tmp_path, RuntimeArm.A_DETERMINISTIC)

    assert record.outcome == "evidence"
    assert record.oncox_record is None
    assert record.jev_record is None
    assert record.budget == {
        "jev_calls": 0,
        "oncox_calls": 0,
        "max_jev_calls": 0,
        "max_oncox_calls": 0,
        "enforced": False,
    }


def test_arm_b_adds_interpretation_only(tmp_path: Path) -> None:
    record = _run_arm(tmp_path, RuntimeArm.B_PLUS_ONCOX)

    assert record.outcome == "evidence"
    assert record.oncox_record is not None
    assert record.oncox_record["creates_evidence"] is False
    assert record.jev_record is None
    assert record.budget["oncox_calls"] == 1


def test_arm_c_adds_judgment_and_interpretation(tmp_path: Path) -> None:
    record = _run_arm(tmp_path, RuntimeArm.C_PLUS_JEV_PLUS_ONCOX)

    assert record.outcome == "evidence"
    assert record.jev_record is not None
    assert record.jev_record["creates_evidence"] is False
    answer = record.jev_record["answers"][0]
    assert answer["primitive"] == JevPrimitive.NOUL.value
    assert float(answer["value"]) == 0.2
    assert record.jev_record["policy"] == "defer"
    assert record.jev_record["raw"] == {"test_double": True}
    assert record.budget["jev_calls"] == 1


def test_budget_accounting_records_by_default_and_blocks_when_enforced(tmp_path: Path) -> None:
    record = _run_arm(
        tmp_path / "unforced",
        RuntimeArm.C_PLUS_JEV_PLUS_ONCOX,
        budget=CallBudget(max_jev_calls=0, max_oncox_calls=0),
    )
    assert record.budget["jev_calls"] == 1
    assert record.budget["enforced"] is False

    with pytest.raises(BudgetExceeded):
        _run_arm(
            tmp_path / "enforced",
            RuntimeArm.C_PLUS_JEV_PLUS_ONCOX,
            budget=CallBudget(max_jev_calls=0, max_oncox_calls=0, enforce=True),
        )


def test_sandbox_guards_paths_and_journals_actions(tmp_path: Path) -> None:
    policy, journal = _sandbox(tmp_path, RuntimeArm.A_DETERMINISTIC)

    with pytest.raises(PermissionError):
        guard_path(policy, tmp_path / "outside.txt")

    assert (policy.root / "workspace" / "fixture.txt").exists()
    assert journal.action_names() == ()


def test_journal_records_arm_actions(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path / "journal")
    policy, journal = _sandbox(tmp_path / "journal", RuntimeArm.B_PLUS_ONCOX)
    investigation = fixture_investigation(investigation_id="inv-journal")
    runtime.investigations.record(investigation)

    execute_arm_program(
        runtime=runtime,
        arm=RuntimeArm.B_PLUS_ONCOX,
        sandbox=policy,
        journal=journal,
        investigation=investigation,
        need="count tokens in fixture documents",
        operation_id="op-abc",
        question="q",
        reasoner=StaticReasoner(),
    )

    assert journal.action_names() == (
        "arm_start",
        "research_step",
        "oncox_reasoning",
        "arm_end",
    )


def test_agent_runtimes_build_with_distinct_tool_surfaces(tmp_path: Path) -> None:
    pytest.importorskip("agents")
    runtime = _runtime(tmp_path / "agents")

    def names(agent: Any) -> set[str]:
        return {str(getattr(tool, "name", "")) for tool in agent.tools}

    arm_a = build_arm_agent(
        settings=None,
        runtime=runtime,
        arm=RuntimeArm.A_DETERMINISTIC,
        sandbox=create_sandbox(tmp_path / "agents" / "a", sandbox_id="a"),
        journal=SandboxJournal(store=AppendOnlyJsonlStore(tmp_path / "a.jsonl"), sandbox_id="a"),
    )
    arm_b = build_arm_agent(
        settings=None,
        runtime=runtime,
        arm=RuntimeArm.B_PLUS_ONCOX,
        sandbox=create_sandbox(tmp_path / "agents" / "b", sandbox_id="b"),
        journal=SandboxJournal(store=AppendOnlyJsonlStore(tmp_path / "b.jsonl"), sandbox_id="b"),
        reasoner=StaticReasoner(),
    )
    arm_c = build_arm_agent(
        settings=None,
        runtime=runtime,
        arm=RuntimeArm.C_PLUS_JEV_PLUS_ONCOX,
        sandbox=create_sandbox(tmp_path / "agents" / "c", sandbox_id="c"),
        journal=SandboxJournal(store=AppendOnlyJsonlStore(tmp_path / "c.jsonl"), sandbox_id="c"),
        reasoner=StaticReasoner(),
        jev_client=FakeJevClient(answers={"pursue__inv": 0.2}),
    )

    assert "request_oncox_reasoning" not in names(arm_a)
    assert "request_jev_judgment" not in names(arm_a)
    assert "request_oncox_reasoning" in names(arm_b)
    assert "request_jev_judgment" not in names(arm_b)
    assert {"request_oncox_reasoning", "request_jev_judgment"} <= names(arm_c)
    assert {"search_capabilities", "record_gap", "inspect_investigation"} <= names(arm_c)


def test_jev_decision_is_typed_and_projection_bound() -> None:
    from oncodex.abc_runtimes import _decision_projection, decision_capability

    capability = decision_capability(question_id="pursue__inv-1")
    projection = _decision_projection(evidence_ids=("ev-1",), outcome="evidence", next_action="")
    decision: JevDecision = FakeJevClient(answers={"pursue__inv-1": 0.7}).evaluate(
        projection, capability
    )

    assert isinstance(projection, SemanticProjection)
    assert decision.projection_fingerprint == projection.fingerprint
    assert float(decision.answers[0].value) == 0.7
    assert isinstance(capability, JevCapability)
