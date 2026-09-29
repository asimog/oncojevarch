from pathlib import Path
from typing import Any

import pytest

from oncodex.agent_boots import BOOT_CONTRACTS, BootTarget, build_boot_agent
from oncodex.research_loop import ResearchRuntime
from oncodex.sandbox import SandboxJournal, create_sandbox
from oncolab.capabilities import CapabilityRegistry
from oncolab.gaps import GapLedger
from oncolab.operations import OperationRegistry
from research.ledger import EvidenceLedger, InvestigationLedger
from store.jsonl import AppendOnlyJsonlStore


def _runtime(tmp_path: Path) -> ResearchRuntime:
    store = AppendOnlyJsonlStore(tmp_path / "boot.jsonl")
    return ResearchRuntime(
        registry=CapabilityRegistry(),
        operations=OperationRegistry(),
        executors={},
        gaps=GapLedger(store),
        investigations=InvestigationLedger(store),
        evidence=EvidenceLedger(store),
    )


def test_contracts_keep_tier_boundaries() -> None:
    oncox = set(BOOT_CONTRACTS[BootTarget.ONCOX])
    oncolab = set(BOOT_CONTRACTS[BootTarget.ONCOLAB])
    oncodex = set(BOOT_CONTRACTS[BootTarget.ONCODEX])

    assert oncox == set()
    assert {"run_scientific_operation", "request_oncox_reasoning"} .isdisjoint(oncolab)
    assert {"invoke_oncox_agent", "invoke_oncolab_agent"} <= oncodex
    assert {"search_capabilities", "record_gap", "inspect_investigation"} <= oncolab


def test_boot_agents_build_with_bounded_surfaces(tmp_path: Path) -> None:
    pytest.importorskip("agents")
    runtime = _runtime(tmp_path)

    def names(agent: Any) -> set[str]:
        return {str(getattr(tool, "name", "")) for tool in agent.tools}

    def build(target: BootTarget) -> Any:
        sandbox = create_sandbox(tmp_path / target.value, sandbox_id=f"boot-{target.value}")
        journal = SandboxJournal(
            store=AppendOnlyJsonlStore(tmp_path / f"{target.value}.jsonl"),
            sandbox_id=sandbox.sandbox_id,
        )
        return build_boot_agent(target, runtime=runtime, sandbox=sandbox, journal=journal)

    oncox = build(BootTarget.ONCOX)
    oncolab = build(BootTarget.ONCOLAB)
    oncodex = build(BootTarget.ONCODEX)

    assert "run_scientific_operation" not in names(oncox)
    assert "request_oncox_reasoning" not in names(oncolab)
    assert "inspect_investigation" in names(oncolab)
    assert {"invoke_oncox_agent", "invoke_oncolab_agent"} <= names(oncodex)
    assert "run_scientific_operation" in names(oncodex)
