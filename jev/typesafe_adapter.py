from __future__ import annotations

import os
from typing import Any

from evidence.projections import SemanticProjection
from jev.contracts import JevAnswer, JevCapability, JevDecision, JevPrimitive


class TypeSafeJevClient:
    """Thin adapter over typesafe-sdk.

    Revalidate this adapter against the live TypeSafe docs before scientific use.
    """

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        selected_api_key = api_key or os.getenv("TYPESAFE_API_KEY")
        selected_model = model or os.getenv("ONCOJEV_JEV_MODEL") or os.getenv("JEV_MODEL")
        self.base_url = base_url or os.getenv("TYPESAFE_BASE_URL")
        if not selected_api_key:
            raise RuntimeError("TYPESAFE_API_KEY is required for live Jev calls")
        if not selected_model:
            raise RuntimeError(
                "ONCOJEV_JEV_MODEL is required; pin the model used by the experiment"
            )
        self.api_key: str = selected_api_key
        self.model: str = selected_model

    def evaluate(self, projection: SemanticProjection, capability: JevCapability) -> JevDecision:
        try:
            from typesafe_sdk import Choice, Noul, Score, TypeSafeClient
        except ImportError as exc:
            raise RuntimeError("install the jev extra: pip install -e '.[jev]'") from exc

        questions: dict[str, Any] = {}
        for question in capability.questions:
            if question.primitive is JevPrimitive.CHOICE:
                questions[question.question_id] = Choice(
                    instructions=question.instructions,
                    criteria=question.criteria,
                )
            elif question.primitive is JevPrimitive.NOUL:
                questions[question.question_id] = Noul(
                    instructions=question.instructions,
                    criteria=question.criteria,
                )
            elif question.primitive is JevPrimitive.SCORE:
                questions[question.question_id] = Score(
                    instructions=question.instructions,
                    criteria=question.criteria,
                )
            else:  # pragma: no cover
                raise ValueError(f"unsupported primitive: {question.primitive}")

        client_kwargs: dict[str, Any] = {"api_key": self.api_key, "model": self.model}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        with TypeSafeClient(**client_kwargs) as client:
            response = client.system_one(state=projection.payload, questions=questions)

        answers: list[JevAnswer] = []
        for question in capability.questions:
            got: Any = response.answers[question.question_id]
            if question.primitive is JevPrimitive.CHOICE:
                value = got.choice
                probs = {str(k): float(v) for k, v in got.probabilities.items()}
            elif question.primitive is JevPrimitive.NOUL:
                value = float(got.noul)
                probs = {"true": value, "false": 1.0 - value}
            else:
                value = got.score
                probs = {str(k): float(v) for k, v in got.probabilities.items()}
            answers.append(
                JevAnswer(
                    question_id=question.question_id,
                    primitive=question.primitive,
                    value=value,
                    probabilities=probs,
                )
            )

        usage = {
            "input_tokens": getattr(response.usage, "input_tokens", None),
            "output_tokens": getattr(response.usage, "output_tokens", None),
        }
        return JevDecision(
            capability_id=capability.capability_id,
            capability_version=capability.version,
            projection_fingerprint=projection.fingerprint,
            model_id=self.model,
            answers=tuple(answers),
            usage=usage,
        )
