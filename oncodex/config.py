from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _read_env_file(path: Path) -> dict[str, str]:
    """Read simple KEY=VALUE settings without mutating the process environment."""

    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0:1] == value[-1:] and value.startswith(("'", '"')):
            value = value[1:-1]
        values[key] = value
    return values


@dataclass(frozen=True, slots=True)
class Settings:
    repo_root: Path
    store_dir: Path
    agent_model: str | None
    jev_model: str | None
    openrouter_api_key: str | None
    typesafe_api_key: str | None
    openrouter_base_url: str
    disable_tracing: bool

    @classmethod
    def from_env(cls, repo_root: Path | None = None) -> Settings:
        root = (repo_root or Path.cwd()).resolve()
        local = _read_env_file(root / ".env.local")

        def setting(name: str, *aliases: str, default: str | None = None) -> str | None:
            for key in (name, *aliases):
                if key in os.environ:
                    return os.environ[key]
            for key in (name, *aliases):
                if key in local:
                    return local[key]
            return default

        raw_store = setting("ONCOJEV_STORE_DIR", default=".oncojev") or ".oncojev"
        store = Path(raw_store)
        if not store.is_absolute():
            store = root / store
        return cls(
            repo_root=root,
            store_dir=store,
            agent_model=setting("ONCOJEV_AGENT_MODEL", "LLM_MODEL") or None,
            jev_model=setting("ONCOJEV_JEV_MODEL", "JEV_MODEL") or None,
            openrouter_api_key=setting("OPENROUTER_API_KEY") or None,
            typesafe_api_key=setting("TYPESAFE_API_KEY") or None,
            openrouter_base_url=setting(
                "OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1"
            )
            or "https://openrouter.ai/api/v1",
            disable_tracing=(setting("OPENAI_AGENTS_DISABLE_TRACING", default="1") or "1").lower()
            in {"1", "true", "yes"},
        )
