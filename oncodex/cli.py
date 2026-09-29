from __future__ import annotations

import argparse
import asyncio
import json
import sys
from dataclasses import asdict
from pathlib import Path

from experiments.architecture.a001_oncodex_codex_smoke import run as run_a001
from experiments.architecture.a002_jev_primitives import run as run_a002
from experiments.architecture.a003_projection_sufficiency import run as run_a003
from experiments.architecture.a004_full_vs_projected_state import run as run_a004
from experiments.architecture.a005_gdc_representation_ladder import run as run_a005
from experiments.architecture.a006_deterministic_vs_jev_reranking import run as run_a006
from experiments.architecture.a007_choice_plus_noul import run as run_a007
from experiments.architecture.a008_greedy_vs_beam import run as run_a008
from experiments.catalog import EXPERIMENTS, get_experiment
from oncodex.config import Settings

RUNNERS = {
    "A001": run_a001,
    "A002": run_a002,
    "A003": run_a003,
    "A004": run_a004,
    "A005": run_a005,
    "A006": run_a006,
    "A007": run_a007,
    "A008": run_a008,
}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="oncojev")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("status")
    sub.add_parser("experiments")
    plan = sub.add_parser("plan")
    plan.add_argument("experiment_id", choices=tuple(e.experiment_id for e in EXPERIMENTS))
    run = sub.add_parser("run")
    run.add_argument("experiment_id", choices=tuple(RUNNERS))
    run.add_argument("--live", action="store_true")
    return parser


def _status(settings: Settings) -> int:
    print("OncoJev scaffold status")
    print(f"repo_root: {settings.repo_root}")
    print(f"store_dir: {settings.store_dir}")
    print(f"agent_model: {settings.agent_model or '(not configured)'}")
    print(f"agent_provider: {'openrouter' if settings.openrouter_api_key else 'openai/default'}")
    print(f"jev_model: {settings.jev_model or '(not configured)'}")
    print(f"typesafe_configured: {bool(settings.typesafe_api_key)}")
    print("implemented experiments: A001, A002, A003, A004, A005, A006, A007, A008")
    print("scientific claims: none")
    return 0


def _list_experiments() -> int:
    for spec in EXPERIMENTS:
        marker = "implemented" if spec.experiment_id in RUNNERS else "catalog"
        print(f"{spec.experiment_id} [{spec.experiment_class.value}] {marker}: {spec.question}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    settings = Settings.from_env(Path.cwd())
    if args.command == "status":
        return _status(settings)
    if args.command == "experiments":
        return _list_experiments()
    if args.command == "plan":
        print(json.dumps(asdict(get_experiment(args.experiment_id)), indent=2, default=str))
        return 0
    runner = RUNNERS[args.experiment_id]
    result = runner(settings=settings, live=bool(args.live))
    if asyncio.iscoroutine(result):
        result = asyncio.run(result)
    print(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
