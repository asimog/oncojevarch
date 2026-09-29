from __future__ import annotations

import asyncio
import importlib.util
from collections.abc import Coroutine
from dataclasses import asdict
from typing import Any

from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncodex.runner import run_architecture_smoke
from oncolab.experiments import (
    ExperimentResult,
    ExperimentStatus,
    FrozenExperiment,
)
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A001")


def _preflight() -> dict[str, object]:
    return {
        "agents_installed": importlib.util.find_spec("agents") is not None,
        "openai_codex_installed": importlib.util.find_spec("openai_codex") is not None,
        "note": "live run uses the Agents SDK experimental codex_tool adapter",
    }


async def _live(settings: Settings, frozen: FrozenExperiment) -> ExperimentResult:
    task = (
        "Inspect only README.md, AGENTS.md, THESIS.md, and ARCHITECTURE.md. "
        "Return four bullets: project thesis, role of OncoLab, role of Jev, and the mandatory "
        "verification command. Do not modify files."
    )
    output = await run_architecture_smoke(settings, task)
    return ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={"final_output": output},
        limitations=("This tests harness/workspace integration, not scientific validity.",),
    )


def run(*, settings: Settings, live: bool = False) -> str | Coroutine[Any, Any, str]:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    if not live:
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.COMPLETED,
            frozen_fingerprint=frozen.fingerprint,
            measurements=_preflight(),
            limitations=("Preflight only; no model or Codex workspace task was executed.",),
        )
        store.append("architecture_experiment_result", asdict(result))
        return str(asdict(result))

    async def execute() -> str:
        try:
            result = await _live(settings, frozen)
        except Exception as exc:
            result = ExperimentResult(
                experiment_id=SPEC.experiment_id,
                experiment_class=SPEC.experiment_class,
                status=ExperimentStatus.FAILED,
                frozen_fingerprint=frozen.fingerprint,
                measurements={"error": f"{type(exc).__name__}: {exc}"},
                limitations=(
                    "Live external integration failed; no architecture decision is implied.",
                ),
            )
        store.append("architecture_experiment_result", asdict(result))
        return str(asdict(result))

    return execute()


if __name__ == "__main__":
    live_run = run(settings=Settings.from_env(), live=True)
    if isinstance(live_run, str):
        print(live_run)
    else:
        print(asyncio.run(live_run))
