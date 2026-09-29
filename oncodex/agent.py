from __future__ import annotations

from typing import Any

from oncodex.codex_workspace import build_read_only_codex_tool
from oncodex.config import Settings
from oncodex.model_provider import build_agent_model

ONCODEX_INSTRUCTIONS = """You are OnCodex, the top autonomous research agent for this repository.
Use repository-local docs as the source of architectural truth. This run is an architecture
smoke test, not a scientific experiment. Use the Codex workspace tool only for the bounded
read-only task. Do not modify files. Return a concise factual result."""


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
