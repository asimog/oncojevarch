from __future__ import annotations

from typing import Any

from evidence.projections import SemanticProjection
from jev.contracts import JevAnswer, JevCapability, JevDecision, JevPrimitive


class FakeJevClient:
    """Deterministic test double. Never treat its output as model/scientific validation."""

    def __init__(self, answers: dict[str, Any]) -> None:
        self._answers = answers

    def evaluate(self, projection: SemanticProjection, capability: JevCapability) -> JevDecision:
        built: list[JevAnswer] = []
        for question in capability.questions:
            raw = self._answers[question.question_id]
            if question.primitive is JevPrimitive.NOUL:
                built.append(
                    JevAnswer(
                        question_id=question.question_id,
                        primitive=question.primitive,
                        value=float(raw),
                        probabilities={"true": float(raw), "false": 1.0 - float(raw)},
                    )
                )
            else:
                built.append(
                    JevAnswer(
                        question_id=question.question_id,
                        primitive=question.primitive,
                        value=raw,
                    )
                )
        return JevDecision(
            capability_id=capability.capability_id,
            capability_version=capability.version,
            projection_fingerprint=projection.fingerprint,
            model_id="fake-test-double",
            answers=tuple(built),
        )
