from __future__ import annotations

from collections import Counter

from store.jsonl import AppendOnlyJsonlStore


def event_counts(store: AppendOnlyJsonlStore) -> dict[str, int]:
    return dict(Counter(event.event_type for event in store.read_all()))
