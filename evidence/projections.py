from __future__ import annotations

import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from hashlib import sha256
from typing import Any

from evidence.models import ScientificEvidence


@dataclass(frozen=True, slots=True)
class SemanticProjection:
    projection_id: str
    version: str
    question_id: str
    source_evidence_ids: tuple[str, ...]
    payload: dict[str, Any]
    fingerprint: str


ProjectionFn = Callable[[tuple[ScientificEvidence, ...]], dict[str, Any]]


def build_projection(
    *,
    projection_id: str,
    version: str,
    question_id: str,
    evidence: Iterable[ScientificEvidence],
    projector: ProjectionFn,
) -> SemanticProjection:
    source = tuple(evidence)
    payload = projector(source)
    return freeze_projection(
        projection_id=projection_id,
        version=version,
        question_id=question_id,
        source_evidence_ids=tuple(e.evidence_id for e in source),
        payload=payload,
    )


def freeze_projection(
    *,
    projection_id: str,
    version: str,
    question_id: str,
    source_evidence_ids: tuple[str, ...],
    payload: dict[str, Any],
) -> SemanticProjection:
    """Freeze an already-derived payload with deterministic identity and provenance."""

    canonical = json.dumps(
        {
            "projection_id": projection_id,
            "version": version,
            "question_id": question_id,
            "source_evidence_ids": list(source_evidence_ids),
            "payload": payload,
        },
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return SemanticProjection(
        projection_id=projection_id,
        version=version,
        question_id=question_id,
        source_evidence_ids=source_evidence_ids,
        payload=payload,
        fingerprint=sha256(canonical.encode("utf-8")).hexdigest(),
    )
