# T13 — Capability-evolution lifecycle

Status: COMPLETE
Dependencies: T09-T12
Verdict: KEEP — add the canonical lifecycle diagram and invariant chain to
`docs/CAPABILITY_EVOLUTION.md`.

## Scope

- Add one Mermaid lifecycle: need → capability search → exists? → use | explicit gap → classify
  (Method/Capability/Decision/Harness) → route → candidate capability → engineering verification →
  scientific/contract evaluation → versioned registration → bounded activation → use.
- Preserve the invariant chain: `generated != verified`; `engineering verified != scientifically
  validated`; `scientifically validated != universally applicable`.
- Keep existing content (dynamic composition vs evolution, two readiness axes, promotion,
  autoresearch constraints); consolidate rather than duplicate.

## Acceptance

- Diagram parses as Mermaid and matches `oncolab/gaps.py` routes and `oncolab/capabilities.py`
  promotion gates.
- The three `!=` statements appear verbatim.

## Verification

Render check + `python scripts/verify.py`.
