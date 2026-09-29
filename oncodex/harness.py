from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any

from oncodex.config import Settings
from oncodex.model_provider import build_agent_model

ONCODEX_REPLAY_INSTRUCTIONS = """You are OnCodex, the autonomous research agent of OncoJev.

Answer only from the supplied investigation context.
- Use the latest recorded value of any fact, never a superseded one.
- Never invent measurements, counts, or statistics that the context does not contain.
- If the context does not settle a question, say so instead of guessing.
- Return the required structured answer only."""


@dataclass(frozen=True, slots=True)
class HarnessTurnResult:
    output: dict[str, Any]
    model_id: str
    usage: dict[str, Any]
    latency_ms: float


async def run_harness_turn(
    *,
    settings: Settings,
    prompt: str,
    output_model: type[Any],
    instructions: str = ONCODEX_REPLAY_INSTRUCTIONS,
    max_turns: int = 1,
) -> HarnessTurnResult:
    """One bounded OnCodex harness turn over supplied context, with a structured answer."""

    try:
        from agents import Agent, Runner, set_tracing_disabled
    except ImportError as exc:
        raise RuntimeError("install the agents extra: pip install -e '.[agents]'") from exc

    set_tracing_disabled(settings.disable_tracing)
    kwargs: dict[str, Any] = {
        "name": "OnCodex",
        "instructions": instructions,
        "output_type": output_model,
    }
    model = build_agent_model(settings)
    if model is not None:
        kwargs["model"] = model
    agent = Agent(**kwargs)
    started = perf_counter()
    result = await Runner.run(agent, prompt, max_turns=max_turns)
    latency_ms = (perf_counter() - started) * 1000
    final = result.final_output
    if isinstance(final, str) or final is None:
        raise ValueError("OnCodex harness turn requires structured output")
    dump = getattr(final, "model_dump", None)
    output = dict(dump()) if callable(dump) else dict(vars(final))
    usage = getattr(getattr(result, "context_wrapper", None), "usage", None)
    return HarnessTurnResult(
        output=output,
        model_id=_model_id(model),
        usage={
            "requests": getattr(usage, "requests", None),
            "input_tokens": getattr(usage, "input_tokens", None),
            "output_tokens": getattr(usage, "output_tokens", None),
            "total_tokens": getattr(usage, "total_tokens", None),
        },
        latency_ms=latency_ms,
    )


def _model_id(model: Any) -> str:
    if model is None:
        return "agents-sdk-default"
    name = getattr(model, "model", None)
    return str(name) if name else type(model).__name__
