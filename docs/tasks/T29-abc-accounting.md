# T29 — Fix A/B/C resource accounting

Status: COMPLETE
Dependencies: T23
Verdict: MODIFIED — the docs already carry accounting rules from the prior session; verify the
existing frontier test protects the A020 lesson, and extend only if the rule is not covered.

## Scope

- `docs/EVALUATION.md`: A/B/C arms charged for every stage they execute; C includes its Jev screen
  and triage overhead. Record list: source bytes/records; deterministic compute; wall time;
  storage; Jev calls/tokens/latency; OncoX calls/tokens/latency; retries; repetitions. Monetary
  cost only when measured or reproducibly derived (never invented from tokens).
- Verify `tests/test_frontier.py` covers "arm C includes its Jev screen" (per A020 exec plan it
  does: no-savings cascade doesn't move frontier). If the rule is expressible in the existing
  frontier API, add an explicit regression case; otherwise record that the test already protects
  it and do not invent a test-only seam.

## Acceptance

- Accounting rules documented and consistent with A020's recorded correction.
- A regression case or an explicit recorded statement that existing coverage protects the rule.

## Verification

`python -m pytest tests/test_frontier.py -q` + `python scripts/verify.py`.

## Findings (2026-09-30)

- `tests/test_frontier.py::test_cascade_that_saves_nothing_does_not_move_the_frontier` already
  protects the A020 accounting rule (C at 1100 tokens does not dominate B at 1000). No new
  test-only seam was added; `docs/EVALUATION.md` now states the rule.
