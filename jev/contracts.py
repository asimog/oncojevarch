from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class JevPrimitive(StrEnum):
    CHOICE = "choice"
    NOUL = "noul"
    SCORE = "score"


@dataclass(frozen=True, slots=True)
class JevQuestion:
    question_id: str
    primitive: JevPrimitive
    instructions: str
    criteria: Any


@dataclass(frozen=True, slots=True)
class JevCapability:
    capability_id: str
    version: str
    domain_owner: str
    semantic_purpose: str
    projection_id: str
    projection_version: str
    questions: tuple[JevQuestion, ...]
    applicability: tuple[str, ...] = ()
    exclusions: tuple[str, ...] = ()
    model_compatibility: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class JevAnswer:
    question_id: str
    primitive: JevPrimitive
    value: Any
    probabilities: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class JevDecision:
    capability_id: str
    capability_version: str
    projection_fingerprint: str
    model_id: str
    answers: tuple[JevAnswer, ...]
    usage: dict[str, Any] = field(default_factory=dict)
