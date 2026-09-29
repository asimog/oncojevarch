from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class StoredEvent:
    event_id: str
    event_type: str
    occurred_at: str
    payload: dict[str, Any]


class AppendOnlyJsonlStore:
    def __init__(self, path: Path) -> None:
        self.path = path

    def append(self, event_type: str, payload: dict[str, Any]) -> StoredEvent:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        event = StoredEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            occurred_at=datetime.now(UTC).isoformat(),
            payload=payload,
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(asdict(event), sort_keys=True, default=str) + "\n")
        return event

    def read_all(self) -> tuple[StoredEvent, ...]:
        if not self.path.exists():
            return ()
        events: list[StoredEvent] = []
        with self.path.open("r", encoding="utf-8") as handle:
            for line in handle:
                raw = json.loads(line)
                events.append(StoredEvent(**raw))
        return tuple(events)
