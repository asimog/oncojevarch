# T07 — Strengthen capability contracts without hardcoding science

Status: COMPLETE
Dependencies: T06
Verdict: MODIFIED — add only the minimum fields needed for safe search and use; no giant schema,
no biological modality enums, no core ontology change.

## Scope

Extend `CapabilityRecord` (`oncolab/capabilities.py:30-38`) with defaulted fields:

- `purpose: str = ""` — one-line semantic purpose used by search summaries;
- `domain_owner: str = ""` — who owns the semantics;
- `inputs: tuple[str, ...] = ()`, `outputs: tuple[str, ...] = ()` — named contract surface;
- `prerequisites: tuple[str, ...] = ()`, `exclusions: tuple[str, ...] = ()` — applicability
  boundaries;
- `evaluated_domain: str = ""` — free-text evaluated scope (which data/domain it was evaluated on).

Existing registrations must remain valid (defaults). Do not add modality enums, entity-identity
fields, or population fields to the generic record; measurement-specific concepts live in
capability-owned typed contracts.

## Acceptance

- A future capability for an unforeseen scientific measurement can be registered without editing
  the generic core types (demonstrated by a test registering a capability with arbitrary
  purpose/inputs/outputs).
- Search summaries surface purpose/applicability; readiness filtering still works.
- No cancer-modality identifier enters `oncolab/`.

## Verification

Focused tests + `python scripts/verify.py` (myPy strict).
