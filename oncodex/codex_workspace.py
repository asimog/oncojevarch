from __future__ import annotations

from pathlib import Path
from typing import Any


class CodexWorkspaceUnavailable(RuntimeError):
    pass


def build_read_only_codex_tool(*, repo_root: Path, idle_timeout_seconds: int = 60) -> Any:
    """Create the experimental Agents SDK Codex tool behind one narrow adapter.

    Keep imports local so core tests do not require external SDKs. Revalidate this
    adapter whenever openai-agents changes its experimental Codex surface.
    """

    try:
        from agents.extensions.experimental.codex import ThreadOptions, TurnOptions, codex_tool
    except ImportError as exc:
        raise CodexWorkspaceUnavailable(
            "install the agents extra: pip install -e '.[agents]'"
        ) from exc

    return codex_tool(
        sandbox_mode="read-only",
        working_directory=str(repo_root),
        default_thread_options=ThreadOptions(),
        default_turn_options=TurnOptions(idle_timeout_seconds=idle_timeout_seconds),
    )
