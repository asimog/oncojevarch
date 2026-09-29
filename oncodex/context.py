from __future__ import annotations

from dataclasses import dataclass

FACT_PREFIX = "FACT:"
CORRECTION_PREFIX = "CORRECTION:"


@dataclass(frozen=True, slots=True)
class HistoryMessage:
    message_id: str
    role: str
    content: str


@dataclass(frozen=True, slots=True)
class BoundedContextView:
    view_id: str
    messages: tuple[HistoryMessage, ...]
    pinned_facts: dict[str, str]
    superseded_fact_keys: tuple[str, ...]
    dropped_message_ids: tuple[str, ...]
    character_count: int


def facts_in(message: HistoryMessage) -> dict[str, str]:
    facts: dict[str, str] = {}
    for line in message.content.splitlines():
        stripped = line.strip()
        for prefix in (FACT_PREFIX, CORRECTION_PREFIX):
            if stripped.startswith(prefix):
                body = stripped[len(prefix) :].strip()
                if "=" in body:
                    key, _, value = body.partition("=")
                    facts[key.strip()] = value.strip()
    return facts


def _is_fact_only(message: HistoryMessage) -> bool:
    lines = [line.strip() for line in message.content.splitlines() if line.strip()]
    if not lines:
        return False
    return all(line.startswith((FACT_PREFIX, CORRECTION_PREFIX)) for line in lines)


def _render(message: HistoryMessage) -> str:
    return f"[{message.message_id}] {message.role}: {message.content}"


def build_bounded_view(
    history: tuple[HistoryMessage, ...],
    *,
    view_id: str,
    recency_window: int,
    budget_chars: int,
) -> BoundedContextView:
    """Deterministic progressive context: latest facts pinned, fact-only messages pruned.

    The pinned header carries the latest value per fact key, so a superseded value can never
    re-enter through the window. Remaining messages keep recency order, and the oldest are dropped
    until the view fits the character budget. Everything dropped is recorded.
    """

    if recency_window < 1:
        raise ValueError("bounded context requires a positive recency window")
    if budget_chars < 1:
        raise ValueError("bounded context requires a positive character budget")

    values: dict[str, set[str]] = {}
    latest: dict[str, str] = {}
    for message in history:
        for key, value in facts_in(message).items():
            values.setdefault(key, set()).add(value)
            latest[key] = value
    superseded_keys = tuple(sorted(key for key, seen in values.items() if len(seen) > 1))

    dropped: list[str] = []
    window: list[HistoryMessage] = []
    for message in history[-recency_window:]:
        if _is_fact_only(message):
            dropped.append(message.message_id)
            continue
        window.append(message)

    while window:
        size = sum(
            len(line) + 1 for line in [*_pinned_lines(latest), *(_render(item) for item in window)]
        )
        if size <= budget_chars:
            break
        dropped.append(window.pop(0).message_id)
    return BoundedContextView(
        view_id=view_id,
        messages=tuple(window),
        pinned_facts=latest,
        superseded_fact_keys=superseded_keys,
        dropped_message_ids=tuple(dropped),
        character_count=sum(
            len(line) + 1 for line in [*_pinned_lines(latest), *(_render(item) for item in window)]
        ),
    )


def _pinned_lines(facts: dict[str, str]) -> list[str]:
    return [f"PINNED FACTS: {key} = {value}" for key, value in sorted(facts.items())]


def render_view(view: BoundedContextView) -> str:
    return "\n".join(
        [*_pinned_lines(view.pinned_facts), *(_render(item) for item in view.messages)]
    )


def render_full_history(history: tuple[HistoryMessage, ...]) -> str:
    return "\n".join(_render(message) for message in history)
