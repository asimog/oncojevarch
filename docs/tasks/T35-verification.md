# T35 — Verify CI/dependency correctness

Status: COMPLETE
Dependencies: T19, T33
Verdict: MODIFIED — baseline verification is green locally (with extras installed); CI installs
only `.[dev]`, so adapter tests skip there. Improve the check by installing the optional extras in
CI; do not suppress valid mypy errors.

## Scope

- `.github/workflows/ci.yml`: install `.[agents,jev,dev]` so the Agents/TypeSafe adapter tests
  actually execute in CI instead of skipping (they remain import-guarded locally).
- Confirm mypy stays strict and green with optional SDKs present locally (it already is);
  no new `ignore_missing_imports` overrides.
- Record exact final counts: architecture checks, compile, tests passed/skipped, ruff, mypy.

## Acceptance

- CI config installs extras; verify.py unchanged in behavior.
- Any failure surfaced by extras is fixed, not muted.

## Verification

`python scripts/verify.py` locally + review of the workflow diff. CI itself runs on push (not
executed here; no remote mutations).

## Findings (2026-09-30)

- CI now installs `.[agents,jev,dev]`.
- Global Python (no optional SDKs): 130 passed / 4 skipped; ruff OK; mypy OK (113 files).
- Local venv (agents installed): the new capability-tool wrapper tests executed rather than
  skipped (16/16 across `test_capability_tools`, `test_capability_search`, `test_gap_ledger`).
- The CI workflow change itself is local and unexecuted until a push (not performed here).
