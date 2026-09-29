from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any


@dataclass(frozen=True, slots=True)
class MaskedProject:
    mask_id: str
    label: str
    features: dict[str, float]


@dataclass(frozen=True, slots=True)
class RankedCandidate:
    mask_id: str
    ranked_labels: tuple[str, ...]
    distances: tuple[float, ...]


def mask_id_for(secret: str) -> str:
    """Opaque identity: the mask reveals nothing about the source identifier."""

    return f"p{sha256(secret.encode()).hexdigest()[:8]}"


def build_features(
    *, case_count: int, file_count: int, profile: dict[str, float]
) -> dict[str, float]:
    if case_count <= 0 or file_count <= 0:
        raise ValueError("rediscovery features require positive counts")
    features = {key: value / file_count for key, value in profile.items()}
    features["files_per_case"] = file_count / case_count
    return features


def _standardize(
    *,
    features: dict[str, float],
    reference: tuple[dict[str, float], ...],
) -> dict[str, float]:
    """Z-score one profile against the reference projects.

    Feature keys are the union across the reference and the profile. An inventory entry that is
    absent from a project contributes a zero share of that project's recorded file total, which is
    a property of the share representation, not a biological absence claim.
    """

    keys = sorted({key for item in (features, *reference) for key in item})
    standardized: dict[str, float] = {}
    for key in keys:
        values = [item.get(key, 0.0) for item in reference]
        if not values:
            standardized[key] = 0.0
            continue
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        deviation = variance**0.5
        standardized[key] = (
            0.0 if deviation == 0 else (features.get(key, 0.0) - mean) / deviation
        )
    return standardized


def leave_one_out_ranking(projects: tuple[MaskedProject, ...]) -> tuple[RankedCandidate, ...]:
    """Deterministic nearest-centroid ranking with the evaluated project excluded everywhere."""

    if len(projects) < 3:
        raise ValueError("masked rediscovery requires at least three projects")
    labels = sorted({project.label for project in projects})
    if len(labels) < 2:
        raise ValueError("masked rediscovery requires at least two candidate labels")
    ranked: list[RankedCandidate] = []
    for target in projects:
        reference = tuple(project for project in projects if project.mask_id != target.mask_id)
        reference_features = tuple(project.features for project in reference)
        target_vector = _standardize(features=target.features, reference=reference_features)
        centroids: dict[str, dict[str, float]] = {}
        for label in labels:
            members = [
                _standardize(features=project.features, reference=reference_features)
                for project in reference
                if project.label == label
            ]
            if not members:
                continue
            centroids[label] = {
                key: sum(member[key] for member in members) / len(members) for key in target_vector
            }
        distances = {
            centroid_label: sum((target_vector[key] - vector[key]) ** 2 for key in target_vector)
            ** 0.5
            for centroid_label, vector in centroids.items()
        }
        ordered = sorted(distances.items(), key=lambda item: (item[1], item[0]))
        ranked.append(
            RankedCandidate(
                mask_id=target.mask_id,
                ranked_labels=tuple(label for label, _ in ordered),
                distances=tuple(distance for _, distance in ordered),
            )
        )
    return tuple(ranked)


@dataclass(frozen=True, slots=True)
class RediscoveryMetrics:
    metrics: dict[str, float]
    per_case: tuple[dict[str, Any], ...]


def evaluate_rankings(
    *,
    rankings: tuple[RankedCandidate, ...],
    labels: dict[str, str],
    k_values: tuple[int, ...] = (1, 2, 3),
) -> RediscoveryMetrics:
    if set(labels) != {ranking.mask_id for ranking in rankings}:
        raise ValueError("rankings do not match the locked label set")
    if not k_values or any(k < 1 for k in k_values):
        raise ValueError("recall@k requires positive k values")
    metrics: dict[str, float] = {"case_count": float(len(rankings))}
    for k in k_values:
        hits = sum(labels[ranking.mask_id] in ranking.ranked_labels[:k] for ranking in rankings)
        metrics[f"recall@{k}"] = hits / len(rankings)
    metrics["mean_reciprocal_rank"] = sum(
        1.0 / (ranking.ranked_labels.index(labels[ranking.mask_id]) + 1) for ranking in rankings
    ) / len(rankings)
    metrics["chance_recall@1"] = 1.0 / len({label for label in labels.values()})
    per_case = tuple(
        {
            "mask_id": ranking.mask_id,
            "label": labels[ranking.mask_id],
            "rank": ranking.ranked_labels.index(labels[ranking.mask_id]) + 1,
            "top_three": list(ranking.ranked_labels[:3]),
            "distances": list(ranking.distances[:3]),
        }
        for ranking in rankings
    )
    return RediscoveryMetrics(metrics=metrics, per_case=per_case)


def ambiguous_cases(
    rankings: tuple[RankedCandidate, ...], *, relative_margin: float
) -> tuple[str, ...]:
    """Cases whose top two candidates are within a frozen relative margin."""

    if relative_margin <= 0.0:
        raise ValueError("ambiguity margin must be positive")
    ambiguous: list[str] = []
    for ranking in rankings:
        if len(ranking.distances) < 2 or ranking.distances[0] <= 0.0:
            continue
        if (ranking.distances[1] - ranking.distances[0]) / ranking.distances[0] < relative_margin:
            ambiguous.append(ranking.mask_id)
    return tuple(ambiguous)


def apply_overrides(
    rankings: tuple[RankedCandidate, ...], overrides: dict[str, tuple[str, ...]]
) -> tuple[RankedCandidate, ...]:
    """Re-rank only with labels already present in the candidate set; identity is preserved."""

    known = {label for ranking in rankings for label in ranking.ranked_labels}
    updated: list[RankedCandidate] = []
    for ranking in rankings:
        override = overrides.get(ranking.mask_id)
        if override is None:
            updated.append(ranking)
            continue
        if not set(override) <= known:
            raise ValueError(f"override for {ranking.mask_id} introduces an unknown label")
        if set(override) != set(ranking.ranked_labels):
            raise ValueError(
                f"override for {ranking.mask_id} must be a permutation of the same candidates"
            )
        distances = {
            label: ranking.distances[ranking.ranked_labels.index(label)] for label in override
        }
        updated.append(
            RankedCandidate(
                mask_id=ranking.mask_id,
                ranked_labels=override,
                distances=tuple(distances[label] for label in override),
            )
        )
    return tuple(updated)


def permuted_labels(labels: dict[str, str]) -> dict[str, str]:
    """Deterministic derangement for the null control: no project keeps its own label."""

    mask_ids = sorted(labels)
    values = [labels[mask_id] for mask_id in mask_ids]
    for offset in range(1, len(mask_ids)):
        rotated = values[offset:] + values[:offset]
        candidate = dict(zip(mask_ids, rotated, strict=True))
        if all(candidate[mask_id] != labels[mask_id] for mask_id in mask_ids):
            return candidate
    raise ValueError("no derangement exists for this label multiset")


def leakage_findings(
    *,
    masked_text: str,
    secrets: tuple[str, ...],
    null_recall_at_1: float,
    chance_recall_at_1: float,
    margin: float,
) -> tuple[str, ...]:
    findings: list[str] = []
    lowered = masked_text.lower()
    for secret in secrets:
        if secret.lower() in lowered:
            findings.append(f"masked view leaks identifier {secret!r}")
    if null_recall_at_1 > chance_recall_at_1 + margin:
        findings.append("null control succeeded above the chance margin")
    return tuple(findings)
