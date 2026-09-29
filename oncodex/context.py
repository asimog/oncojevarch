from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from oncolab.capabilities import CapabilityRegistry
from store.jsonl import AppendOnlyJsonlStore


@dataclass(slots=True)
class OnCodexContext:
    """Local application context; it is not automatically model-visible scientific state."""

    repo_root: Path
    event_store: AppendOnlyJsonlStore
    capabilities: CapabilityRegistry
