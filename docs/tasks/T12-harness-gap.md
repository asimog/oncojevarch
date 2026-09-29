# T12 — Formalize HarnessGap routing

Status: COMPLETE
Dependencies: T11
Verdict: KEEP — route exists (`GapKind.HARNESS → HARNESS_ENGINEERING`). Formalize the route and
the boundary that harness work does not mutate scientific methods.

## Scope

Edit `docs/CAPABILITY_EVOLUTION.md`:

- HarnessGap definition: the research agent/runtime lacks an operational capability required for
  reliable execution (workspace operation, recovery primitive, context retrieval, persistence,
  tool integration, runtime ability);
- route: bounded harness engineering → verification → versioned engineering capability;
- restate: harness deficiencies must not silently mutate scientific methods or evidence rules.

## Acceptance

- Harness route documented and bounded by engineering verification.
- Explicit statement separating runtime reliability from scientific validity
  (constitution #10).

## Verification

`python scripts/verify.py`; `tests/test_gap_routing_experiment.py` unchanged and passing.
