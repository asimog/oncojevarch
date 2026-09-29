from __future__ import annotations

from typing import Any

from oncodex.config import Settings


def build_agent_model(settings: Settings) -> Any | None:
    """Build the configured model at the OnCodex integration boundary."""

    if not settings.agent_model:
        return None
    if not settings.openrouter_api_key:
        return settings.agent_model

    try:
        from agents import OpenAIChatCompletionsModel
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise RuntimeError("install the agents extra: pip install -e '.[agents]'") from exc

    client = AsyncOpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
    )
    return OpenAIChatCompletionsModel(model=settings.agent_model, openai_client=client)
