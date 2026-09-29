from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from time import perf_counter
from typing import Any

from evaluation.discovery import (
    FeatureCase,
    candidate_phrases,
    discover_phrases,
    evaluate_features,
    fit_threshold,
    log_odds,
    phrase_stability,
    readable_feature,
    split_integrity_findings,
)
from evidence.projections import SemanticProjection, freeze_projection
from experiments.catalog import get_experiment
from jev.contracts import JevCapability, JevPrimitive, JevQuestion
from jev.typesafe_adapter import TypeSafeJevClient
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A014")
CASE_COUNT = 60
DEVELOPMENT_CASES = 30
VALIDATION_CASES = 45
MAX_DISCOVERED_FEATURES = 6
MIN_DEV_SCORE = 0.25
ENDORSEMENT_THRESHOLD = 0.5
THRESHOLD_GRID = (0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
SPLITS = ("development", "validation", "locked_test")
LABEL_TOKENS = ("needs_deeper_reasoning", "label=", "material_missing")
PROJECTS = ("TCGA-LUAD", "TCGA-LUSC", "TCGA-KIRC", "TCGA-KIRP", "TCGA-KICH")
IMMATERIAL_ITEMS = ("treatment response outcomes", "survival follow-up")
FAMILIES: tuple[dict[str, Any], ...] = (
    {
        "key": "count_comparison",
        "marker": "file counts per case",
        "claim": "records {na} files per case against {nb}, so it is more deeply characterized",
        "material": ("per-case aliquot counts", "sample-type composition"),
    },
    {
        "key": "platform_comparison",
        "marker": "expression platform",
        "claim": "records a different expression platform inventory, so expression differs",
        "material": ("platform-specific case counts", "assay-per-case inventory"),
    },
    {
        "key": "availability_claim",
        "marker": "assay availability",
        "claim": "records no methylation array entry, so the assay is unavailable",
        "material": ("record submission dates", "per-case sample inventories"),
    },
    {
        "key": "population_claim",
        "marker": "population incidence",
        "claim": "records {na} cases against {nb}, so the disease is more common",
        "material": ("population registry incidence rates", "enrollment-frame description"),
    },
)
BASELINE_FEATURES = (
    "observed:",
    "recorded_checks:",
    "missing:",
    "treatment response outcomes",
)


def _split_of(index: int) -> str:
    if index < DEVELOPMENT_CASES:
        return "development"
    if index < VALIDATION_CASES:
        return "validation"
    return "locked_test"


def _case_text(
    index: int, family: dict[str, Any], project_a: str, project_b: str, missing: list[str]
) -> str:
    count_a = 400 + index * 7
    count_b = 250 + index * 3
    return (
        f"case {index:02d} family: {family['key']} marker: {family['marker']}. "
        f"claim: {project_a} {family['claim'].format(na=count_a, nb=count_b)} "
        f"compared with {project_b}. "
        f"observed: {project_a} file_count={count_a} {project_b} file_count={count_b}. "
        "recorded_checks: operational cohort sizes; file identity is not assay identity. "
        f"missing: {', '.join(missing)}."
    )


def corpus() -> tuple[FeatureCase, ...]:
    """Frozen synthetic corpus with a family-conditional implanted signal and fixed label noise."""

    cases: list[FeatureCase] = []
    for index in range(CASE_COUNT):
        family = FAMILIES[index % len(FAMILIES)]
        project_a = PROJECTS[index % len(PROJECTS)]
        project_b = PROJECTS[(index + 1) % len(PROJECTS)]
        material_item = family["material"][(index // len(FAMILIES)) % len(family["material"])]
        if index % 10 < 7:
            missing = [material_item, IMMATERIAL_ITEMS[index % 2]]
            planted = True
        else:
            missing = [IMMATERIAL_ITEMS[0], IMMATERIAL_ITEMS[1]]
            planted = False
        label = planted
        if index % 7 == 3:
            label = not label
        cases.append(
            FeatureCase(
                case_id=f"f{index:02d}",
                text=_case_text(index, family, project_a, project_b, missing),
                label=label,
                split=_split_of(index),
            )
        )
    return tuple(cases)


def candidate_features(cases: tuple[FeatureCase, ...]) -> tuple[str, ...]:
    """Frozen feature language: n-grams plus family-marker conjunctions with missing items."""

    singles = candidate_phrases(cases, n_min=2, n_max=3, min_cases=8)
    items = sorted(
        {item for family in FAMILIES for item in family["material"]} | set(IMMATERIAL_ITEMS)
    )
    conjunctions = tuple(f"{family['key']} && {item}" for family in FAMILIES for item in items)
    return tuple(sorted(set(singles) | set(conjunctions)))


def _cases_by_split(cases: tuple[FeatureCase, ...], split: str) -> tuple[FeatureCase, ...]:
    return tuple(case for case in cases if case.split == split)


def _endorsement_capability(features: tuple[str, ...]) -> JevCapability:
    return JevCapability(
        capability_id="a014-discovered-feature-endorsement",
        version="0.1.0",
        domain_owner="evaluation",
        semantic_purpose=(
            "Judge whether a discovered phrase indicates a material unresolved question."
        ),
        projection_id="a014-feature-endorsement",
        projection_version="1",
        questions=tuple(
            JevQuestion(
                question_id=f"endorse__{index:02d}",
                primitive=JevPrimitive.NOUL,
                instructions=(
                    f"Using only `features.{index:02d}`, does the phrase "
                    f"'{readable_feature(feature)}' indicate that a case still leaves a material, "
                    "unresolved scientific question rather than a general or immaterial "
                    "statement? Answer true only for a materially unresolved consideration."
                ),
                criteria={
                    "true": "the phrase indicates a material unresolved consideration",
                    "false": "the phrase is general, descriptive, or immaterial",
                },
            )
            for index, feature in enumerate(features)
        ),
    )


def _endorsement_projection(features: tuple[str, ...]) -> SemanticProjection:
    return freeze_projection(
        projection_id="a014-feature-endorsement",
        version="1",
        question_id="feature-endorsement",
        source_evidence_ids=tuple(
            f"discovered-feature:{index:02d}" for index in range(len(features))
        ),
        payload={
            "features": {
                f"{index:02d}": readable_feature(feature) for index, feature in enumerate(features)
            }
        },
    )


def _arm_evaluation(
    *,
    name: str,
    features: tuple[str, ...],
    development: tuple[FeatureCase, ...],
    validation: tuple[FeatureCase, ...],
    locked_test: tuple[FeatureCase, ...],
) -> dict[str, Any]:
    weights = {feature: log_odds(feature, development) for feature in features}
    threshold = fit_threshold(validation, features=features, weights=weights, grid=THRESHOLD_GRID)
    evaluation = evaluate_features(
        locked_test, features=features, weights=weights, threshold=threshold
    )
    return {
        "arm_id": name,
        "features": list(features),
        "weights": weights,
        "threshold": threshold,
        "locked_test": asdict(evaluation),
    }


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    cases = corpus()
    development = _cases_by_split(cases, "development")
    validation = _cases_by_split(cases, "validation")
    locked_test = _cases_by_split(cases, "locked_test")
    integrity = split_integrity_findings(cases, label_tokens=LABEL_TOKENS)

    if not live:
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.FROZEN,
            frozen_fingerprint=frozen.fingerprint,
            measurements={
                "live": False,
                "corpus_fingerprint": sha256(
                    json.dumps([asdict(case) for case in cases], sort_keys=True).encode("utf-8")
                ).hexdigest(),
                "split_sizes": {split: len(_cases_by_split(cases, split)) for split in SPLITS},
                "candidate_feature_count": len(candidate_features(cases)),
                "split_integrity_findings": list(integrity),
                "protocol": {
                    "max_discovered_features": MAX_DISCOVERED_FEATURES,
                    "min_dev_score": MIN_DEV_SCORE,
                    "endorsement_threshold": ENDORSEMENT_THRESHOLD,
                    "threshold_grid": list(THRESHOLD_GRID),
                },
            },
            limitations=(
                "No model call was made; this is the frozen protocol only.",
                "This architecture task cannot create ScientificEvidence.",
            ),
        )
        store.append("architecture_experiment_result", asdict(result))
        return json.dumps(asdict(result), indent=2, default=str)

    try:
        discovered_dev = discover_phrases(
            development,
            phrases=candidate_features(cases),
            max_features=MAX_DISCOVERED_FEATURES,
            min_score=MIN_DEV_SCORE,
        )
        validated = discover_phrases(
            validation,
            phrases=candidate_features(cases),
            max_features=MAX_DISCOVERED_FEATURES,
            min_score=MIN_DEV_SCORE,
            expected_split="validation",
        )
        stability = phrase_stability(discovered_dev, validated)
        features = tuple(item.phrase for item in discovered_dev)
        capability = _endorsement_capability(features)
        projection = _endorsement_projection(features)
        client = TypeSafeJevClient(api_key=settings.typesafe_api_key, model=settings.jev_model)
        started = perf_counter()
        decision = client.evaluate(projection, capability)
        latency_ms = (perf_counter() - started) * 1000
        probabilities = {
            answer.question_id.removeprefix("endorse__"): float(answer.value)
            for answer in decision.answers
        }
        endorsed = tuple(
            feature
            for index, feature in enumerate(features)
            if probabilities[f"{index:02d}"] >= ENDORSEMENT_THRESHOLD
        )
        baseline_arm = _arm_evaluation(
            name="baseline_features",
            features=BASELINE_FEATURES,
            development=development,
            validation=validation,
            locked_test=locked_test,
        )
        discovered_arm = _arm_evaluation(
            name="discovered_features",
            features=endorsed,
            development=development,
            validation=validation,
            locked_test=locked_test,
        )
        baseline_accuracy = baseline_arm["locked_test"]["metrics"]["accuracy"]
        discovered_accuracy = discovered_arm["locked_test"]["metrics"]["accuracy"]
        permuted = tuple(
            FeatureCase(
                case_id=case.case_id,
                text=case.text,
                label=not case.label,
                split=case.split,
            )
            if case.split == "locked_test"
            else case
            for case in cases
        )
        audit = split_integrity_findings(permuted, label_tokens=LABEL_TOKENS)
        leakage_findings = list(integrity) + list(audit)
        if (
            discover_phrases(
                _cases_by_split(permuted, "development"),
                phrases=candidate_features(permuted),
                max_features=MAX_DISCOVERED_FEATURES,
                min_score=MIN_DEV_SCORE,
            )
            != discovered_dev
        ):
            leakage_findings.append("development discovery changed under locked-label permutation")
        promoted = (
            discovered_accuracy >= baseline_accuracy and not leakage_findings and len(endorsed) > 0
        )
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.COMPLETED,
            frozen_fingerprint=frozen.fingerprint,
            measurements={
                "live": True,
                "features_promoted": promoted,
                "discovered_on_development": [asdict(item) for item in discovered_dev],
                "reconfirmed_on_validation": [asdict(item) for item in validated],
                "feature_stability_jaccard": stability,
                "endorsement": {
                    "model_id": decision.model_id,
                    "capability_id": decision.capability_id,
                    "capability_version": decision.capability_version,
                    "probabilities": probabilities,
                    "endorsed_features": list(endorsed),
                    "usage": decision.usage,
                    "latency_ms": latency_ms,
                    "threshold": ENDORSEMENT_THRESHOLD,
                },
                "arms": {
                    "baseline_features": baseline_arm,
                    "discovered_features": discovered_arm,
                },
                "locked_test_accuracy_gain": discovered_accuracy - baseline_accuracy,
                "split_integrity_findings": leakage_findings,
                "corpus_fingerprint": sha256(
                    json.dumps([asdict(case) for case in cases], sort_keys=True).encode("utf-8")
                ).hexdigest(),
                "protocol": {
                    "max_discovered_features": MAX_DISCOVERED_FEATURES,
                    "min_dev_score": MIN_DEV_SCORE,
                    "endorsement_threshold": ENDORSEMENT_THRESHOLD,
                    "threshold_grid": list(THRESHOLD_GRID),
                    "split_sizes": {split: len(_cases_by_split(cases, split)) for split in SPLITS},
                },
                "cost": {
                    "measured": False,
                    "basis": "the TypeSafe SDK usage path exposes tokens only",
                },
            },
            observations=(
                (
                    "Offline-discovered features generalized to the locked split with no leakage "
                    "finding, so they are promoted for this synthetic corpus only."
                    if promoted
                    else "Discovered features are not promoted: locked-test gain, endorsement, or "
                    "split integrity failed."
                ),
            ),
            limitations=(
                "The corpus is synthetic with an implanted family-conditional signal; this is a "
                "mechanics result, not cancer biology.",
                "Feature discovery is lexical n-gram selection with conjunctions, not a general "
                "semantic learner.",
                "One Jev batch endorses features for one contract; endorsement is a bounded "
                "judgment, not permission.",
                "Locked-test performance on sixty synthetic cases is a small sample.",
            ),
        )
    except Exception as exc:
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.FAILED,
            frozen_fingerprint=frozen.fingerprint,
            measurements={"live": True, "error": f"{type(exc).__name__}: {exc}"},
            limitations=("External failure does not establish feature generalization.",),
        )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
