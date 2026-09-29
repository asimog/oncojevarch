from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any, Protocol

from evidence.projections import freeze_projection
from jev.contracts import JevCapability, JevDecision, JevPrimitive, JevQuestion
from oncodex.capability_tools import (
    build_capability_tools,
    build_research_tools,
)
from oncodex.research_loop import ResearchRuntime, run_research_step
from oncodex.sandbox import SandboxJournal, SandboxPolicy
from oncox.ports import ReasoningRequest, ReasoningResult, ScientificReasoner

ABC_INSTRUCTIONS = """You are OnCodex operating one bounded A/B/C runtime arm inside a sandbox.
Work only through the provided tools. Never invent a scientific method: when no activated
capability satisfies a need, record an explicit gap. Reasoning output and semantic judgments
are never measurements and never become ScientificEvidence. Stay inside the sandbox workspace
and respect the call budget."""

PURSUE_THRESHOLD = 0.5


def pursuit_policy(value: float) -> str:
    """Deterministic policy over a bounded Jev probability. Jev informs; Python decides."""

    return "pursue" if value >= PURSUE_THRESHOLD else "defer"


class RuntimeArm(StrEnum):
    A_DETERMINISTIC = "a_deterministic"
    B_PLUS_ONCOX = "b_deterministic_plus_oncox"
    C_PLUS_JEV_PLUS_ONCOX = "c_deterministic_plus_jev_plus_oncox"

    @property
    def uses_oncox(self) -> bool:
        return self is not RuntimeArm.A_DETERMINISTIC

    @property
    def uses_jev(self) -> bool:
        return self is RuntimeArm.C_PLUS_JEV_PLUS_ONCOX


class BudgetExceeded(RuntimeError):
    pass


@dataclass(slots=True)
class CallBudget:
    max_jev_calls: int = 0
    max_oncox_calls: int = 0
    jev_calls: int = 0
    oncox_calls: int = 0

    def spend_jev(self) -> None:
        if self.jev_calls + 1 > self.max_jev_calls:
            raise BudgetExceeded("Jev call budget exceeded")
        self.jev_calls += 1

    def spend_oncox(self) -> None:
        if self.oncox_calls + 1 > self.max_oncox_calls:
            raise BudgetExceeded("OncoX call budget exceeded")
        self.oncox_calls += 1

    @property
    def account(self) -> dict[str, int]:
        return {
            "jev_calls": self.jev_calls,
            "oncox_calls": self.oncox_calls,
            "max_jev_calls": self.max_jev_calls,
            "max_oncox_calls": self.max_oncox_calls,
        }


class JevClient(Protocol):
    def evaluate(self, projection: Any, capability: JevCapability) -> JevDecision: ...


@dataclass(frozen=True, slots=True)
class ArmRunRecord:
    arm: RuntimeArm
    investigation_id: str
    outcome: str
    evidence_id: str
    gap_id: str
    oncox_record: dict[str, Any] | None
    jev_record: dict[str, Any] | None
    budget: dict[str, int]
    sandbox_actions: tuple[str, ...]


def decision_capability(*, question_id: str) -> JevCapability:
    return JevCapability(
        capability_id="abc-pursuit-gate",
        version="1",
        domain_owner="abc-runtime",
        semantic_purpose=(
            "Bounded policy judgment: does the recorded outcome warrant deeper pursuit "
            "or should the investigation defer?"
        ),
        projection_id="abc-decision-projection",
        projection_version="1",
        questions=(
            JevQuestion(
                question_id=question_id,
                primitive=JevPrimitive.NOUL,
                instructions=(
                    "Would one bounded next step materially reduce the recorded uncertainty? "
                    "Answer true only if a resolvable uncertainty remains that a bounded step "
                    "could address."
                ),
                criteria={
                    "true": "a bounded next step could reduce the uncertainty",
                    "false": "no resolvable uncertainty remains for policy",
                },
            ),
        ),
        applicability=("bounded pursuit decisions",),
        exclusions=("measurement", "evidence creation"),
    )


def _decision_projection(*, evidence_ids: tuple[str, ...], outcome: str, next_action: str) -> Any:
    return freeze_projection(
        projection_id="abc-decision-projection",
        version="1",
        question_id=(
            "pursue__" + (evidence_ids[0].replace(":", "-") if evidence_ids else outcome)
        ),
        source_evidence_ids=evidence_ids,
        payload={"outcome": outcome, "next_action": next_action},
    )


def execute_arm_program(
    *,
    runtime: ResearchRuntime,
    arm: RuntimeArm,
    sandbox: SandboxPolicy,
    journal: SandboxJournal,
    investigation: Any,
    need: str,
    operation_id: str,
    question: str,
    reasoner: ScientificReasoner | None = None,
    jev_client: JevClient | None = None,
    budget: CallBudget | None = None,
) -> ArmRunRecord:
    """Deterministic arm program: the same step sequence the arm agent drives through tools.

    The program is used for offline end-to-end verification and as the frozen policy of each arm;
    agents may extend it live but cannot bypass the admission gate this program uses.
    """

    if arm.uses_oncox and reasoner is None:
        raise ValueError("this arm requires an OncoX reasoner")
    if arm.uses_jev and jev_client is None:
        raise ValueError("this arm requires a Jev client")
    budget = budget if budget is not None else CallBudget(
        max_jev_calls=1 if arm.uses_jev else 0,
        max_oncox_calls=1 if arm.uses_oncox else 0,
    )
    journal.record(
        "arm_start",
        {"arm": arm.value, "investigation_id": investigation.investigation_id},
    )

    step = run_research_step(
        runtime=runtime,
        investigation=investigation,
        need=need,
        operation_id=operation_id,
    )
    journal.record(
        "research_step",
        {
            "arm": arm.value,
            "outcome": step.outcome,
            "evidence_id": step.evidence_id,
            "gap_id": step.gap_id,
        },
    )

    oncox_record: dict[str, Any] | None = None
    if arm.uses_oncox:
        if reasoner is None:
            raise ValueError("this arm requires an OncoX reasoner")
        budget.spend_oncox()
        evidence_ids = (step.evidence_id,) if step.evidence_id else ()
        request = ReasoningRequest(
            investigation_id=step.investigation_id,
            evidence_ids=evidence_ids,
            question=question,
            structured_state={
                "outcome": step.outcome,
                "next_action": step.revision.next_action or "",
            },
        )
        result: ReasoningResult = asyncio.run(reasoner.reason(request))
        oncox_record = {
            "model_id": result.model_id,
            "interpretation": result.output.interpretation,
            "hypotheses": list(result.output.hypotheses),
            "proposed_tests": list(result.output.proposed_tests),
            "usage": result.usage,
            "latency_ms": result.latency_ms,
            "creates_evidence": False,
        }
        journal.record("oncox_reasoning", {"arm": arm.value, "model_id": result.model_id})

    jev_record: dict[str, Any] | None = None
    if arm.uses_jev:
        if jev_client is None:
            raise ValueError("this arm requires a Jev client")
        budget.spend_jev()
        capability = decision_capability(question_id=f"pursue__{step.investigation_id}")
        projection = _decision_projection(
            evidence_ids=(step.evidence_id,) if step.evidence_id else (),
            outcome=step.outcome,
            next_action=step.revision.next_action or "",
        )
        decision = jev_client.evaluate(projection, capability)
        answer_value = float(decision.answers[0].value) if decision.answers else 0.0
        jev_record = {
            "capability_id": decision.capability_id,
            "model_id": decision.model_id,
            "projection_fingerprint": decision.projection_fingerprint,
            "answers": [asdict(answer) for answer in decision.answers],
            "value": answer_value,
            "policy": pursuit_policy(answer_value),
            "creates_evidence": False,
        }
        journal.record("jev_judgment", {"arm": arm.value, "model_id": decision.model_id})

    journal.record("arm_end", {"arm": arm.value, "outcome": step.outcome})
    return ArmRunRecord(
        arm=arm,
        investigation_id=step.investigation_id,
        outcome=step.outcome,
        evidence_id=step.evidence_id,
        gap_id=step.gap_id,
        oncox_record=oncox_record,
        jev_record=jev_record,
        budget=budget.account,
        sandbox_actions=journal.action_names(),
    )


def build_arm_agent(
    *,
    settings: Any,
    runtime: ResearchRuntime,
    arm: RuntimeArm,
    sandbox: SandboxPolicy,
    journal: SandboxJournal,
    reasoner: ScientificReasoner | None = None,
    jev_client: JevClient | None = None,
    budget: CallBudget | None = None,
    model: Any | None = None,
) -> Any:
    """Build the Agents SDK agent for one arm with a bounded, sandboxed tool surface."""

    from agents import Agent, function_tool

    from oncodex.codex_workspace import build_read_only_codex_tool

    budget = budget if budget is not None else CallBudget(
        max_jev_calls=1 if arm.uses_jev else 0,
        max_oncox_calls=1 if arm.uses_oncox else 0,
    )
    tools: list[Any] = [
        *build_capability_tools(registry=runtime.registry, ledger=runtime.gaps),
        *build_research_tools(runtime=runtime),
        build_read_only_codex_tool(repo_root=sandbox.root),
    ]

    if arm.uses_oncox:

        async def request_oncox_reasoning(investigation_id: str, question: str) -> str:
            """Request one bounded OncoX interpretation; never creates ScientificEvidence.

            Args:
                investigation_id: Investigation the reasoning belongs to.
                question: The bounded reasoning question.
            """
            active_reasoner = reasoner
            if active_reasoner is None:
                raise RuntimeError("arm requires an OncoX reasoner")
            budget.spend_oncox()
            latest = runtime.investigations.latest(investigation_id)
            evidence_ids = tuple(latest.evidence_ids) if latest else ()
            request = ReasoningRequest(
                investigation_id=investigation_id,
                evidence_ids=evidence_ids,
                question=question,
                structured_state={"next_action": (latest.next_action or "") if latest else ""},
            )
            result = await active_reasoner.reason(request)
            journal.record("oncox_reasoning", {"model_id": result.model_id})
            return json.dumps(
                {
                    "model_id": result.model_id,
                    "interpretation": result.output.interpretation,
                    "hypotheses": list(result.output.hypotheses),
                    "creates_evidence": False,
                },
                sort_keys=True,
            )

        tools.append(function_tool(name_override="request_oncox_reasoning")(request_oncox_reasoning))

    if arm.uses_jev:

        def request_jev_judgment(investigation_id: str, question_id: str) -> str:
            """Request one bounded Jev judgment; never creates ScientificEvidence or policy.

            Args:
                investigation_id: Investigation the judgment belongs to.
                question_id: Question identity for the frozen decision capability.
            """
            active_jev = jev_client
            if active_jev is None:
                raise RuntimeError("arm requires a Jev client")
            budget.spend_jev()
            latest = runtime.investigations.latest(investigation_id)
            evidence_ids = tuple(latest.evidence_ids) if latest else ()
            capability = decision_capability(question_id=question_id)
            projection = _decision_projection(
                evidence_ids=evidence_ids,
                outcome="recorded",
                next_action=(latest.next_action or "") if latest else "",
            )
            decision = active_jev.evaluate(projection, capability)
            journal.record("jev_judgment", {"model_id": decision.model_id})
            answer_value = float(decision.answers[0].value) if decision.answers else 0.0
            return json.dumps(
                {
                    "model_id": decision.model_id,
                    "projection_fingerprint": decision.projection_fingerprint,
                    "answers": [asdict(answer) for answer in decision.answers],
                    "policy": pursuit_policy(answer_value),
                    "creates_evidence": False,
                },
                sort_keys=True,
                default=str,
            )

        tools.append(function_tool(name_override="request_jev_judgment")(request_jev_judgment))

    agent_kwargs: dict[str, Any] = {
        "name": f"OnCodex-{arm.value}",
        "instructions": ABC_INSTRUCTIONS,
        "tools": tools,
    }
    if model is not None:
        agent_kwargs["model"] = model
    return Agent(**agent_kwargs)


def run_arm_live(*, agent: Any, prompt: str) -> dict[str, Any]:
    """Run one bounded Agents SDK session; the scientific state stays in OncoLab/store."""

    from agents import Runner

    result = asyncio.run(Runner.run(agent, prompt))
    return {"final_output": str(result.final_output)}
