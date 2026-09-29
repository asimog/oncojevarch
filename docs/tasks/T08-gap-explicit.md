# T08 — Make capability-search failure explicit

Status: COMPLETE
Dependencies: T06, T07
Verdict: MODIFIED — `Gap` records need + evidence only (`oncolab/gaps.py:29-38`) and nothing is
persisted. Add the minimum provenance and a durable ledger; no elaborate service, no store schema.

## Scope

- Extend `Gap` with defaults: `unmet_requirements: tuple[str, ...] = ()` (why existing
  capabilities could not satisfy the need), `attempted: tuple[str, ...] = ()` (capability ids or
  versions considered), `origin: str = ""` (what asked for it, e.g. investigation id).
- Add a small append-only gap ledger (`GapLedger`) that records gaps via the existing
  `store/jsonl.py` `AppendOnlyJsonlStore`, so a capability absence is an inspectable durable state.
- Keep routes derived from kind (existing `ROUTES`); do not add new gap kinds.

## Acceptance

- A capability-search miss can be recorded with: what was needed, what was attempted, why it was
  insufficient, the evidence, and the owning route.
- Recorded gaps survive process restart and can be read back in order.
- No new dependency direction violations (oncolab → store is already used by `recovery.py`).

## Verification

Focused tests (`tests/test_gap_ledger.py`) + `python scripts/verify.py`.
