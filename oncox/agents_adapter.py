from __future__ import annotations

import asyncio
import json
from time import perf_counter
from typing import Any

from oncox.ports import ReasoningOutput, ReasoningRequest, ReasoningResult

ONCOX_INSTRUCTIONS = """You are OncoX, the selective deep scientific reasoner of OncoJev.

Reason only over the structured state supplied in the request.
- Never invent measurements, statistics, effect sizes, sample counts, or file counts.
- Never claim that a measurement was performed. You do not measure and you create no
  ScientificEvidence.
- Treat missing, absent, or unreported state as unknown, never as zero and never as a
  biological negative.
- Ground each hypothesis in the supplied state and name the unmeasured quantity that would
  discriminate it.
- If the recorded structured evidence already resolves the material question, say so briefly and
  leave the remaining fields empty instead of inventing considerations."""

_OUTPUT_MODEL: type[Any] | None = None


def reasoning_output_model() -> type[Any]:
    """Build the bounded structured output schema at the adapter boundary."""

    global _OUTPUT_MODEL
    if _OUTPUT_MODEL is None:
        from pydantic import BaseModel, Field

        class ReasoningOutputModel(BaseModel):
            """Bounded OncoX reasoning output."""

            interpretation: str = Field(
                description="Concise reading of the supplied structured state."
            )
            hypotheses: list[str] = Field(
                default_factory=list,
                description="Grounded hypotheses that the supplied state can support.",
            )
            alternative_explanations: list[str] = Field(
                default_factory=list,
                description="Alternative explanations not excluded by the supplied state.",
            )
            proposed_tests: list[str] = Field(
                default_factory=list,
                description="Discriminating tests or acquisitions, not claimed results.",
            )
            unresolved_uncertainty: list[str] = Field(
                default_factory=list,
                description="What remains unknown, including unmeasured quantities.",
            )

        _OUTPUT_MODEL = ReasoningOutputModel
    return _OUTPUT_MODEL


def _text_field(raw: Any, name: str) -> str:
    value = getattr(raw, name, None)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"OncoX structured output requires a non-empty {name}")
    return value.strip()


def _text_tuple(raw: Any, name: str) -> tuple[str, ...]:
    value = getattr(raw, name, None)
    if value is None:
        raise ValueError(f"OncoX structured output is missing {name}")
    if isinstance(value, str) or not isinstance(value, (list, tuple)):
        raise ValueError(f"OncoX structured output field {name} must be a list of strings")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"OncoX structured output field {name} must contain only text")
        items.append(item.strip())
    return tuple(items)


def to_reasoning_output(raw: Any) -> ReasoningOutput:
    """Convert a structured response into the dependency-free port type."""

    if raw is None or isinstance(raw, str):
        raise ValueError("OncoX returned unstructured output instead of the required schema")
    return ReasoningOutput(
        interpretation=_text_field(raw, "interpretation"),
        hypotheses=_text_tuple(raw, "hypotheses"),
        alternative_explanations=_text_tuple(raw, "alternative_explanations"),
        proposed_tests=_text_tuple(raw, "proposed_tests"),
        unresolved_uncertainty=_text_tuple(raw, "unresolved_uncertainty"),
    )


def usage_snapshot(result: Any) -> dict[str, Any]:
    """Record SDK usage as measured; never invent provider cost."""

    usage = getattr(getattr(result, "context_wrapper", None), "usage", None)
    if usage is None:
        return {}
    return {
        "requests": getattr(usage, "requests", None),
        "input_tokens": getattr(usage, "input_tokens", None),
        "output_tokens": getattr(usage, "output_tokens", None),
        "total_tokens": getattr(usage, "total_tokens", None),
    }


def reasoning_prompt(request: ReasoningRequest) -> str:
    """Render the frozen reasoning prompt for one investigation state."""

    evidence = ", ".join(request.evidence_ids) or "(none)"
    state = json.dumps(request.structured_state, indent=2, sort_keys=True, default=str)
    return "\n".join(
        (
            f"INVESTIGATION: {request.investigation_id}",
            f"EVIDENCE IDS: {evidence}",
            f"QUESTION: {request.question}",
            "STRUCTURED STATE (JSON):",
            state,
        )
    )


def _model_id(model: Any) -> str:
    if model is None:
        return "agents-sdk-default"
    if isinstance(model, str):
        return model
    name = getattr(model, "model", None)
    if isinstance(name, str) and name:
        return name
    return type(model).__name__


class AgentsOncoXReasoner:
    """Agents SDK adapter for one bounded deep-reasoning call.

    Provider and model choice stay at this integration edge. Reasoning output is interpretation
    only and is never admitted as ScientificEvidence.

    A bounded retry absorbs provider-side structured-output failures. Attempts and error types are
    recorded so that repeated failures stay visible instead of silently degrading the arm.
    """

    def __init__(
        self,
        *,
        model: Any | None = None,
        max_turns: int = 1,
        max_attempts: int = 2,
        max_tokens: int | None = None,
        reasoning_effort: str | None = None,
        retry_delay_seconds: float = 0.5,
        instructions: str = ONCOX_INSTRUCTIONS,
    ) -> None:
        if max_turns < 1:
            raise ValueError("OncoX requires at least one bounded turn")
        if max_attempts < 1:
            raise ValueError("OncoX requires at least one bounded attempt")
        self.model = model
        self.max_turns = max_turns
        self.max_attempts = max_attempts
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.retry_delay_seconds = retry_delay_seconds
        self.instructions = instructions
        self.model_id = _model_id(model)

    def _model_settings(self) -> Any:
        from agents import ModelSettings

        kwargs: dict[str, Any] = {"max_tokens": self.max_tokens, "store": False}
        if self.reasoning_effort:
            # OpenRouter's documented reasoning control, passed through unchanged.
            kwargs["extra_body"] = {"reasoning": {"effort": self.reasoning_effort}}
        return ModelSettings(**kwargs)

    def build_agent(self) -> Any:
        try:
            from agents import Agent
        except ImportError as exc:
            raise RuntimeError("install the agents extra: pip install -e '.[agents]'") from exc

        kwargs: dict[str, Any] = {
            "name": "OncoX",
            "instructions": self.instructions,
            "output_type": reasoning_output_model(),
            "model_settings": self._model_settings(),
        }
        if self.model is not None:
            kwargs["model"] = self.model
        return Agent(**kwargs)

    async def reason(self, request: ReasoningRequest) -> ReasoningResult:
        errors: list[str] = []
        for attempt in range(1, self.max_attempts + 1):
            if attempt > 1:
                await asyncio.sleep(self.retry_delay_seconds * (attempt - 1))
            started = perf_counter()
            try:
                result = await self._run_once(request)
            except Exception as exc:  # provider/parse failures are heterogeneous
                errors.append(f"{type(exc).__name__}: {exc}")
                continue
            latency_ms = (perf_counter() - started) * 1000
            return ReasoningResult(
                output=to_reasoning_output(result.final_output),
                model_id=self.model_id,
                usage=usage_snapshot(result),
                latency_ms=latency_ms,
                attempts=attempt,
                errors=tuple(errors),
            )
        raise RuntimeError(
            f"OncoX failed after {self.max_attempts} attempts: {'; '.join(errors)}"
        )

    async def _run_once(self, request: ReasoningRequest) -> Any:
        try:
            from agents import Runner
        except ImportError as exc:
            raise RuntimeError("install the agents extra: pip install -e '.[agents]'") from exc

        agent = self.build_agent()
        return await Runner.run(agent, reasoning_prompt(request), max_turns=self.max_turns)
