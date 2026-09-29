from __future__ import annotations

from oncodex.agent import build_oncodex_agent
from oncodex.config import Settings


async def run_architecture_smoke(settings: Settings, task: str) -> str:
    try:
        from agents import Runner, set_tracing_disabled
    except ImportError as exc:
        raise RuntimeError("install the agents extra: pip install -e '.[agents]'") from exc

    set_tracing_disabled(settings.disable_tracing)
    agent = build_oncodex_agent(settings)
    result = await Runner.run(agent, task)
    return str(result.final_output)
