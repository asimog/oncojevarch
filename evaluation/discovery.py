from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class FeatureCase:
    case_id: str
    text: str
    label: bool
    split: str


@dataclass(frozen=True, slots=True)
class DiscoveredPhrase:
    phrase: str
    dev_positive_rate: float
    dev_negative_rate: float
    score: float


def normalize(text: str) -> str:
    return " ".join(text.lower().split())


def phrase_present(text: str, phrase: str) -> bool:
    """A feature is one phrase, or several phrases conjoined with `&&`."""

    normalized = normalize(text)
    return all(part in normalized for part in normalize(phrase).split("&&"))


def readable_feature(feature: str) -> str:
    return " together with ".join(part.strip() for part in feature.split("&&") if part.strip())


def candidate_phrases(
    cases: tuple[FeatureCase, ...], *, n_min: int, n_max: int, min_cases: int
) -> tuple[str, ...]:
    """Frozen candidate pool: word n-grams seen in at least `min_cases` of the given cases."""

    counts: dict[str, int] = {}
    for case in cases:
        tokens = normalize(case.text).split()
        seen: set[str] = set()
        for size in range(n_min, n_max + 1):
            for start in range(len(tokens) - size + 1):
                seen.add(" ".join(tokens[start : start + size]))
        for phrase in seen:
            counts[phrase] = counts.get(phrase, 0) + 1
    return tuple(
        sorted(
            (phrase for phrase, count in counts.items() if count >= min_cases),
            key=lambda phrase: (len(phrase.split()), phrase),
        )
    )


def discover_phrases(
    cases: tuple[FeatureCase, ...],
    *,
    phrases: tuple[str, ...],
    max_features: int,
    min_score: float,
    expected_split: str = "development",
) -> tuple[DiscoveredPhrase, ...]:
    """Select discriminative phrases from one declared split only.

    Scoring may be repeated on a later split to test stability, but the split must always be
    declared explicitly so that locked cases can never enter discovery silently.
    """

    if not cases:
        raise ValueError("feature discovery requires cases")
    if any(case.split != expected_split for case in cases):
        raise ValueError(f"feature discovery must only see {expected_split} cases")
    if max_features < 1:
        raise ValueError("feature discovery requires a positive feature budget")
    positives = [case for case in cases if case.label]
    negatives = [case for case in cases if not case.label]
    if not positives or not negatives:
        raise ValueError("feature discovery requires labeled positives and negatives")

    discovered: list[DiscoveredPhrase] = []
    for phrase in phrases:
        positive_rate = sum(phrase_present(case.text, phrase) for case in positives) / len(
            positives
        )
        negative_rate = sum(phrase_present(case.text, phrase) for case in negatives) / len(
            negatives
        )
        score = positive_rate - negative_rate
        if score >= min_score:
            discovered.append(
                DiscoveredPhrase(
                    phrase=phrase,
                    dev_positive_rate=positive_rate,
                    dev_negative_rate=negative_rate,
                    score=score,
                )
            )
    discovered.sort(key=lambda item: (-item.score, item.phrase))
    return tuple(discovered[:max_features])


def log_odds(feature: str, dev_cases: tuple[FeatureCase, ...]) -> float:
    """Deterministic weight with Laplace smoothing, fitted on the given split only."""

    positives = sum(case.label and phrase_present(case.text, feature) for case in dev_cases)
    negatives = sum(not case.label and phrase_present(case.text, feature) for case in dev_cases)
    return math.log((positives + 1) / (negatives + 1))


def case_scores(
    cases: tuple[FeatureCase, ...], *, features: tuple[str, ...], weights: dict[str, float]
) -> dict[str, float]:
    return {
        case.case_id: sum(
            weights[feature] for feature in features if phrase_present(case.text, feature)
        )
        for case in cases
    }


def fit_threshold(
    cases: tuple[FeatureCase, ...],
    *,
    features: tuple[str, ...],
    weights: dict[str, float],
    grid: tuple[float, ...],
) -> float:
    """Choose the cutoff on the validation split only, maximizing balanced accuracy."""

    if not cases or any(case.split != "validation" for case in cases):
        raise ValueError("threshold fitting must only see validation cases")
    scores = case_scores(cases, features=features, weights=weights)
    best_threshold = grid[0]
    best_balanced = -1.0
    for threshold in grid:
        positives = [case for case in cases if case.label]
        negatives = [case for case in cases if not case.label]
        positive_recall = (
            sum(scores[case.case_id] >= threshold for case in positives) / len(positives)
            if positives
            else 0.0
        )
        negative_recall = (
            sum(scores[case.case_id] < threshold for case in negatives) / len(negatives)
            if negatives
            else 0.0
        )
        balanced = (positive_recall + negative_recall) / 2
        if balanced > best_balanced:
            best_balanced = balanced
            best_threshold = threshold
    return best_threshold


@dataclass(frozen=True, slots=True)
class FeatureArmEvaluation:
    metrics: dict[str, float]
    per_case: tuple[dict[str, Any], ...]


def evaluate_features(
    cases: tuple[FeatureCase, ...],
    *,
    features: tuple[str, ...],
    weights: dict[str, float],
    threshold: float,
) -> FeatureArmEvaluation:
    if not cases:
        raise ValueError("feature evaluation requires cases")
    scores = case_scores(cases, features=features, weights=weights)
    predictions = {case_id: score >= threshold for case_id, score in scores.items()}
    positives = [case for case in cases if case.label]
    negatives = [case for case in cases if not case.label]
    true_positives = sum(predictions[case.case_id] for case in positives)
    true_negatives = sum(not predictions[case.case_id] for case in negatives)
    accuracy = sum(predictions[case.case_id] == case.label for case in cases) / len(cases)
    brier = sum(
        ((1.0 / (1.0 + math.exp(-scores[case.case_id]))) - float(case.label)) ** 2 for case in cases
    ) / len(cases)
    metrics = {
        "case_count": float(len(cases)),
        "accuracy": accuracy,
        "positive_recall": (true_positives / len(positives)) if positives else 0.0,
        "negative_specificity": (true_negatives / len(negatives)) if negatives else 0.0,
        "brier_score": brier,
        "feature_count": float(len(features)),
    }
    per_case = tuple(
        {
            "case_id": case.case_id,
            "label": case.label,
            "score": scores[case.case_id],
            "prediction": predictions[case.case_id],
        }
        for case in cases
    )
    return FeatureArmEvaluation(metrics=metrics, per_case=per_case)


def phrase_stability(
    first: tuple[DiscoveredPhrase, ...], second: tuple[DiscoveredPhrase, ...]
) -> float:
    first_set = {item.phrase for item in first}
    second_set = {item.phrase for item in second}
    if not first_set and not second_set:
        return 1.0
    return len(first_set & second_set) / len(first_set | second_set)


def split_integrity_findings(
    cases: tuple[FeatureCase, ...], *, label_tokens: tuple[str, ...]
) -> tuple[str, ...]:
    """Cheap mechanical leakage checks for a frozen three-split corpus."""

    findings: list[str] = []
    splits = {case.split for case in cases}
    if splits != {"development", "validation", "locked_test"}:
        findings.append(f"unexpected split names: {sorted(splits)}")
    if len({case.case_id for case in cases}) != len(cases):
        findings.append("case identities are not unique")
    for case in cases:
        for token in label_tokens:
            if normalize(token) in normalize(case.text):
                findings.append(f"case {case.case_id} text contains the label token {token!r}")
    return tuple(findings)
