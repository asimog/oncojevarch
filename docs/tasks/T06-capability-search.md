# T06 — Make capability search first-class

Status: COMPLETE
Dependencies: T01, T07
Verdict: KEEP — real gap. Recon: `CapabilityRegistry` has only `register`/`get`/
`advance_engineering`/`set_scientific_readiness` (`oncolab/capabilities.py:41-84`); a miss raises a
bare `KeyError`; no summary/search/eligibility mechanism exists repo-wide. Tightened scope:
deterministic search only — no Jev ranking (applicability here does not require semantic judgment).

## Scope

Edit `oncolab/capabilities.py` (+ exports, focused tests):

- `CapabilitySummary` value type (id, version, kind, purpose, readiness pair, applicability);
- `CapabilityRegistry.list_summaries()` and a bounded deterministic `search(need, *, kind=None,
  limit=...)` using token overlap over purpose/applicability, stable ordering;
- explicit negative outcome: search returns an empty tuple, never raises;
- applicability check: `check_applicability(...)` returning required tags that are unmet;
- no Jev, no network, no store coupling.

## Acceptance

- A need can be resolved to a bounded candidate summary set without loading full records.
- Absence of an applicable capability is an explicit return value.
- Search is deterministic across runs and bounded by `limit`.
- No applicable-capability path directs the caller to record a gap (T08).

## Verification

New focused tests (`tests/test_capability_search.py`) + `python scripts/verify.py`.
