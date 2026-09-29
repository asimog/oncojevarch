from __future__ import annotations

from typing import Any

from oncodex.capability_tools import build_capability_tools
from oncodex.codex_workspace import build_read_only_codex_tool
from oncodex.config import Settings
from oncodex.model_provider import build_agent_model
from oncolab.capabilities import CapabilityRegistry
from oncolab.gaps import GapLedger
from store.jsonl import AppendOnlyJsonlStore

ONCODEX_INSTRUCTIONS = """You are OnCodex, the top autonomous research agent for this repository.
Use repository-local docs as the source of architectural truth. This run is an architecture
smoke test, not a scientific experiment. Use the Codex workspace tool only for the bounded
read-only task. Do not modify files. Return a concise factual result."""

ONCODEX_RESEARCH_INSTRUCTIONS = """You are OnCodex, the top autonomous research agent for this
repository. Work from the scientific state: identify unresolved uncertainty, decide what
information is missing, search capabilities before improvising, load their contracts, and verify
applicability. When no applicable capability exists, record an explicit gap instead of inventing
a method. Never treat reasoning as measured evidence. Use the read-only Codex workspace tool only
for bounded inspection or engineering tasks. Use repository-local docs as the source of
architectural truth."""


def build_oncodex_agent(settings: Settings) -> Any:
    try:
        from agents import Agent
    except ImportError as exc:
        raise RuntimeError("install the agents extra: pip install -e '.[agents]'") from exc

    tool = build_read_only_codex_tool(repo_root=settings.repo_root)
    kwargs: dict[str, Any] = {
        "name": "OnCodex",
        "instructions": ONCODEX_INSTRUCTIONS,
        "tools": [tool],
    }
    model = build_agent_model(settings)
    if model is not None:
        kwargs["model"] = model
    return Agent(**kwargs)


def build_oncodex_research_agent(
    settings: Settings,
    *,
    registry: CapabilityRegistry | None = None,
    gap_ledger: GapLedger | None = None,
) -> Any:
    try:
        from agents import Agent
    except ImportError as exc:
        raise RuntimeError("install the agents extra: pip install -e '.[agents]'") from exc

    resolved_registry = registry if registry is not None else CapabilityRegistry()
    resolved_ledger = (
        gap_ledger
        if gap_ledger is not None
        else GapLedger(AppendOnlyJsonlStore(settings.repo_root / ".oncojev" / "gaps.jsonl"))
    )
    tools: list[Any] = [
        *build_capability_tools(registry=resolved_registry, ledger=resolved_ledger),
        build_read_only_codex_tool(repo_root=settings.repo_root),
    ]
    kwargs: dict[str, Any] = {
        "name": "OnCodex",
        "instructions": ONCODEX_RESEARCH_INSTRUCTIONS,
        "tools": tools,
    }
    model = build_agent_model(settings)
    if model is not None:
        kwargs["model"] = model
    return Agent(**kwargs)
