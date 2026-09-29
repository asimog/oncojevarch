from pathlib import Path

from store.jsonl import AppendOnlyJsonlStore


def test_append_only_store_records_events(tmp_path: Path) -> None:
    store = AppendOnlyJsonlStore(tmp_path / "events.jsonl")
    a = store.append("one", {"x": 1})
    b = store.append("two", {"x": 2})
    events = store.read_all()
    assert [event.event_id for event in events] == [a.event_id, b.event_id]
    assert [event.event_type for event in events] == ["one", "two"]
