from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from store.jsonl import AppendOnlyJsonlStore

SANDBOX_EVENT = "sandbox_action"


@dataclass(frozen=True, slots=True)
class SandboxPolicy:
    """A bounded filesystem root and call allowance controlled from the environment."""

    sandbox_id: str
    root: Path
    allow_write: bool = False
    max_agent_calls: int = 8


@dataclass(slots=True)
class SandboxJournal:
    """Records every sandbox action durably; agent sessions are not the record."""

    store: AppendOnlyJsonlStore
    sandbox_id: str
    actions: list[dict[str, Any]] = field(default_factory=list)

    def record(self, action: str, detail: dict[str, Any] | None = None) -> None:
        entry: dict[str, Any] = {"sandbox_id": self.sandbox_id, "action": action}
        entry.update(detail or {})
        self.actions.append(entry)
        self.store.append(SANDBOX_EVENT, entry)

    def action_names(self) -> tuple[str, ...]:
        return tuple(str(action["action"]) for action in self.actions)


def create_sandbox(root: Path, *, sandbox_id: str, allow_write: bool = False) -> SandboxPolicy:
    root.mkdir(parents=True, exist_ok=True)
    return SandboxPolicy(
        sandbox_id=sandbox_id,
        root=root.resolve(),
        allow_write=allow_write,
    )


def guard_path(policy: SandboxPolicy, path: Path) -> Path:
    candidate = path.resolve()
    if not candidate.is_relative_to(policy.root):
        raise PermissionError(f"path escapes sandbox {policy.sandbox_id}: {path}")
    return candidate


def seed_sandbox(policy: SandboxPolicy, files: dict[str, str]) -> tuple[str, ...]:
    """Write a small frozen workspace into the sandbox; always performed by the environment."""

    for name, content in files.items():
        target = guard_path(policy, policy.root / name)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return tuple(sorted(files))
