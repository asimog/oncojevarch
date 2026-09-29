from __future__ import annotations

import json
from dataclasses import asdict

from experiments.architecture.a022_capability_search_evaluation import (
    CAPABILITIES,
    LIMIT,
    NEEDS,
    build_registry,
    evaluate,
    substring_arm,
)
from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.capabilities import CapabilityRegistry, CapabilitySummary
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A025")


def repaired_search_arm(
    registry: CapabilityRegistry, need: str
) -> tuple[CapabilitySummary, ...]:
    return registry.search(need, limit=LIMIT)


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    registry = build_registry()
    repaired = evaluate(registry, repaired_search_arm)
    substring = evaluate(registry, substring_arm)
    frozen_rule = (
        "the repaired search is retained only if it identifies at least as many correct top-1 "
        "capabilities as the substring baseline on the frozen needs and detects every "
        "absent-capability need without a false hit"
    )
    keep = (
        repaired["top1_correct"] >= substring["top1_correct"]
        and repaired["misses_detected"] == repaired["absent_needs"]
        and repaired["false_hits"] == 0
    )
    decision = (
        "keep the repaired deterministic search as the initial mechanism"
        if keep
        else "reopen capability retrieval again"
    )
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": False,
            "predecessor": "A022",
            "mechanism_change": "common-word stopword filtering before token overlap",
            "arms": {"repaired_token_overlap": repaired, "substring": substring},
            "registry_size": len(CAPABILITIES),
            "needs": len(NEEDS),
            "limit": LIMIT,
            "frozen_rule": frozen_rule,
            "decision": decision,
        },
        observations=(
            (
                "A022 recorded that raw token overlap returned a false hit for an "
                "absent-capability need; the minimal repair removes common words from both the "
                "need and the searchable text before overlap."
            ),
            (
                "The repaired search meets the frozen rule on the same need set, so the "
                "mechanism is retained as the initial mechanism rather than expanded."
            ),
        ),
        limitations=(
            "This re-evaluation uses the frozen A022 registry and needs; it is not new evidence "
            "about retrieval at scale.",
            "The production tokenizer is evaluated at its first repaired revision; any further "
            "mechanism change requires a new experiment identity.",
            "Semantic retrieval remains unjustified by this evidence and is not added.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
