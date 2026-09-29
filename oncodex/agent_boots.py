from __future__ import annotations

from enum import StrEnum
from typing import Any

from oncodex.abc_runtimes import RuntimeArm, build_arm_agent
from oncodex.capability_tools import build_capability_tools, build_research_tools
from oncodex.research_loop import ResearchRuntime
from oncodex.sandbox import SandboxJournal, SandboxPolicy


class BootTarget(StrEnum):
    ONCODEX = "oncodex"
    ONCOX = "oncox"
    ONCOLAB = "oncolab"


BOOT_CONTRACTS: dict[BootTarget, tuple[str, ...]] = {
    BootTarget.ONCODEX: (
        "search_capabilities",
        "load_capability",
        "record_gap",
        "inspect_investigation",
        "run_scientific_operation",
        "request_oncox_reasoning",
        "request_jev_judgment",
        "invoke_oncox_agent",
        "invoke_oncolab_agent",
    ),
    BootTarget.ONCOX: (),
    BootTarget.ONCOLAB: (
        "search_capabilities",
        "load_capability",
        "record_gap",
        "inspect_investigation",
    ),
}

ONCOX_BOOT_INSTRUCTIONS = """You are OncoX, a bounded deep-reasoning component. You interpret
recorded evidence, propose hypotheses and discriminating tests. You never create measured
evidence, never judge policy, and never write to the scientific store."""

ONCOLAB_BOOT_INSTRUCTIONS = """You are OnCoLab, the governance substrate. You inspect
investigations, capability contracts, and gap state. You never execute measurements, never
reason open-endedly, and never create ScientificEvidence."""

ONCODEX_BOOT_INSTRUCTIONS = """You are OnCodex, controlling independent OncoX and OnCoLab agent
runtimes through bounded tool calls. Work from scientific state, search capabilities, execute
allowed operations or expose gaps, and keep reasoning and judgment out of the evidence path."""


def _default_ports(
    model: Any | None,
) -> tuple[Any, Any]:
    from jev.fake import FakeJevClient
    from oncox.fake import StaticReasoner

    reasoner: Any = StaticReasoner()
    jev: Any = FakeJevClient(answers={})
    if model is not None:
        try:
            from oncox.agents_adapter import AgentsOncoXReasoner

            reasoner = AgentsOncoXReasoner(
                model=model, max_tokens=800, reasoning_effort="low", max_attempts=2
            )
        except Exception:  # noqa: BLE001 - deterministic fallback
            reasoner = StaticReasoner()
    try:
        from jev.typesafe_adapter import TypeSafeJevClient

        jev = TypeSafeJevClient()
    except Exception:  # noqa: BLE001 - deterministic fallback
        jev = FakeJevClient(answers={})
    return reasoner, jev


def build_boot_agent(
    target: BootTarget,
    *,
    runtime: ResearchRuntime,
    sandbox: SandboxPolicy,
    journal: SandboxJournal,
    model: Any | None = None,
    reasoner: Any | None = None,
    jev_client: Any | None = None,
) -> Any:
    """Boot one independent agent runtime; Agents SDK controllers compose them via as_tool."""

    from agents import Agent

    from oncodex.codex_workspace import build_read_only_codex_tool

    if reasoner is None or jev_client is None:
        default_reasoner, default_jev = _default_ports(model)
        reasoner = reasoner if reasoner is not None else default_reasoner
        jev_client = jev_client if jev_client is not None else default_jev

    codex_tool = build_read_only_codex_tool(repo_root=sandbox.root)
    capability_tools = build_capability_tools(registry=runtime.registry, ledger=runtime.gaps)
    research_tools = build_research_tools(runtime=runtime)

    if target is BootTarget.ONCOX:
        kwargs: dict[str, Any] = {
            "name": "OncoX",
            "instructions": ONCOX_BOOT_INSTRUCTIONS,
            "tools": [codex_tool],
        }
        if model is not None:
            kwargs["model"] = model
        return Agent(**kwargs)

    if target is BootTarget.ONCOLAB:
        inspect_only = [
            tool
            for tool in research_tools
            if getattr(tool, "name", "") == "inspect_investigation"
        ]
        kwargs = {
            "name": "OnCoLab",
            "instructions": ONCOLAB_BOOT_INSTRUCTIONS,
            "tools": [*capability_tools, *inspect_only, codex_tool],
        }
        if model is not None:
            kwargs["model"] = model
        return Agent(**kwargs)

    oncox_agent = build_boot_agent(
        BootTarget.ONCOX,
        runtime=runtime,
        sandbox=sandbox,
        journal=journal,
        model=model,
    )
    oncolab_agent = build_boot_agent(
        BootTarget.ONCOLAB,
        runtime=runtime,
        sandbox=sandbox,
        journal=journal,
        model=model,
    )
    extra_tools = (
        oncox_agent.as_tool(
            tool_name="invoke_oncox_agent",
            tool_description="Ask the independent OncoX agent for bounded interpretation.",
        ),
        oncolab_agent.as_tool(
            tool_name="invoke_oncolab_agent",
            tool_description="Ask the independent OnCoLab agent for governance state.",
        ),
    )
    return build_arm_agent(
        settings=None,
        runtime=runtime,
        arm=RuntimeArm.C_PLUS_JEV_PLUS_ONCOX,
        sandbox=sandbox,
        journal=journal,
        reasoner=reasoner,
        jev_client=jev_client,
        model=model,
        extra_tools=extra_tools,
    )
