# T34 — Strengthen mechanical enforcement carefully

Status: COMPLETE
Dependencies: T06-T08, T18
Verdict: MODIFIED — add only two stable dependency rules and one catalog test; no bespoke
static-analysis system.

## Scope

`scripts/check_architecture.py`:

1. `oncolab` must not import `oncodex`, `oncox`, `discovery`, or `observatory` (registry/ledger
   belong to the substrate; orchestration depends on oncolab, never the reverse).
2. Source-adapter containment: only `execution` (its own adapter) and `experiments` may import
   `execution.gdc`; core packages must not.

`tests/test_experiment_catalog.py`:

3. Level contract: any future experiment at `independent_real` must declare a compatibility
   contract in `inputs`; any at `temporal_prospective` must declare T1/T2 cutoffs. Vacuous today
   (no such experiments), enforced when one appears.

Do not add: modality-token scanners, doc-prose matchers, or speculative checks with no current
invariant.

## Acceptance

- Existing checks unchanged; new checks pass on current code.
- A synthetic violation for each new check is rejected (fresh-repo or unit-test level).

## Verification

`python scripts/check_architecture.py` + `python scripts/verify.py`.

## Findings (2026-09-30)

- `scripts/check_architecture.py` adds `oncolab` to the forbidden-direction map and confines
  `execution.gdc` imports to `execution/` and `experiments/` via `forbid_import_directions(root)`,
  unit-tested with synthetic violations in `tests/test_architecture_checks.py`.
- Catalog level contracts are enforced by two tests in `tests/test_experiment_catalog.py`.
