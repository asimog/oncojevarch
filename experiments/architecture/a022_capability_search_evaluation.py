from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import asdict
from typing import Any

from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.capabilities import (
    CapabilityKind,
    CapabilityRecord,
    CapabilityRegistry,
    CapabilitySummary,
)
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A022")

CAPABILITIES: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "count_tokens_fixture",
        "count tokens in frozen fixture documents",
        ("fixture documents", "token counting"),
    ),
    (
        "gdc_public_metadata",
        "read public GDC project metadata and file class counts",
        ("public metadata", "project aggregates"),
    ),
    (
        "sample_identifier_join",
        "join sample identifiers across release versions",
        ("identity joins", "release comparison"),
    ),
    (
        "permutation_null_test",
        "compute a seeded permutation association null",
        ("association tests", "null models"),
    ),
    (
        "site_entropy_summary",
        "summarize primary site entropy over project aggregates",
        ("aggregate summaries", "site entropy"),
    ),
    (
        "file_share_profiles",
        "build file share profiles per project",
        ("profiles", "file shares"),
    ),
)

NEEDS: tuple[tuple[str, str | None], ...] = (
    ("count the words in the document fixture", "count_tokens_fixture"),
    ("read public cancer project aggregates from the archive", "gdc_public_metadata"),
    ("compare sample identity between releases", "sample_identifier_join"),
    ("seeded null model for association counts", "permutation_null_test"),
    ("entropy of primary site across projects", "site_entropy_summary"),
    ("file share profile per project", "file_share_profiles"),
    ("estimate tumor purity from bulk assays", None),
    ("call structural variants in a tumor normal pair", None),
)
LIMIT = 3
RAW_TOKEN = re.compile(r"[a-z0-9]+")


def build_registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    for capability_id, purpose, applicability in CAPABILITIES:
        registry.register(
            CapabilityRecord(
                capability_id=capability_id,
                kind=CapabilityKind.METHOD,
                version="1",
                source_identity="frozen:a022",
                applicability=applicability,
                purpose=purpose,
            )
        )
    return registry


def _raw_tokens(text: str) -> frozenset[str]:
    """The frozen mechanism under evaluation: plain alphanumeric token overlap."""

    return frozenset(RAW_TOKEN.findall(text.lower()))


def raw_token_arm(
    registry: CapabilityRegistry, need: str
) -> tuple[CapabilitySummary, ...]:
    need_tokens = _raw_tokens(need)
    scored: list[tuple[int, str, str, CapabilitySummary]] = []
    for summary in registry.list_summaries():
        searchable = _raw_tokens(
            f"{summary.capability_id} {summary.purpose} {' '.join(summary.applicability)}"
        )
        overlap = len(need_tokens & searchable)
        if overlap:
            scored.append((-overlap, summary.capability_id, summary.version, summary))
    scored.sort(key=lambda item: (item[0], item[1], item[2]))
    return tuple(item[3] for item in scored[:LIMIT])


def substring_arm(
    registry: CapabilityRegistry, need: str
) -> tuple[CapabilitySummary, ...]:
    text = need.lower()
    matches = tuple(
        summary
        for summary in registry.list_summaries()
        if text in f"{summary.purpose} {' '.join(summary.applicability)}".lower()
    )
    return matches[:LIMIT]


def evaluate(
    registry: CapabilityRegistry,
    retrieve: Callable[[CapabilityRegistry, str], tuple[CapabilitySummary, ...]],
) -> dict[str, Any]:
    top1_correct = 0
    misses_detected = 0
    false_hits = 0
    candidates = 0
    false_hit_needs: list[str] = []
    for need, expected in NEEDS:
        found = retrieve(registry, need)
        candidates += len(found)
        if expected is None:
            if found:
                false_hits += 1
                false_hit_needs.append(need)
            else:
                misses_detected += 1
        elif found and found[0].capability_id == expected:
            top1_correct += 1
    matching = sum(1 for _, expected in NEEDS if expected is not None)
    return {
        "top1_correct": top1_correct,
        "matching_needs": matching,
        "misses_detected": misses_detected,
        "absent_needs": len(NEEDS) - matching,
        "false_hits": false_hits,
        "false_hit_needs": false_hit_needs,
        "candidates_returned": candidates,
    }


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    registry = build_registry()
    raw = evaluate(registry, raw_token_arm)
    substring = evaluate(registry, substring_arm)
    frozen_rule = (
        "the token-overlap mechanism is retained only if it identifies at least as many correct "
        "top-1 capabilities as the substring baseline on the frozen needs and detects every "
        "absent-capability need without a false hit; otherwise retrieval is reopened"
    )
    keep = (
        raw["top1_correct"] >= substring["top1_correct"]
        and raw["misses_detected"] == raw["absent_needs"]
        and raw["false_hits"] == 0
    )
    decision = (
        "keep deterministic token search as the initial mechanism"
        if keep
        else "reopen capability retrieval"
    )
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": False,
            "arms": {"raw_token_overlap": raw, "substring": substring},
            "registry_size": len(CAPABILITIES),
            "needs": len(NEEDS),
            "limit": LIMIT,
            "frozen_rule": frozen_rule,
            "decision": decision,
        },
        observations=(
            (
                "Lexical token overlap retrieves all six matching capabilities at top-1, but it "
                "also returns a false hit for an absent-capability need because common words "
                "match, so the mechanism fails its own frozen rule and retrieval is reopened."
            ),
            (
                "The substring baseline is exact but useless for natural-language needs and "
                "silently returns nothing for needs that do express registry vocabulary "
                "differently; it is not a candidate mechanism."
            ),
        ),
        limitations=(
            "The registry is tiny and the needs are frozen by hand; this is not evidence about "
            "retrieval at scale.",
            "Only lexical mechanisms are compared; semantic ranking is not evaluated and is not "
            "assumed necessary.",
            "The evaluated mechanism is pinned inside this experiment so the recorded result "
            "stays reproducible if the production tokenizer changes; a repaired mechanism "
            "requires a new experiment identity.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
