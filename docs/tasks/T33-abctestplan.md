# T33 — Resolve ABCTestPlan

Status: COMPLETE
Dependencies: T19
Verdict: MODIFIED — recon proves `ABCTestPlan`, `SystemArm`, and `MetricRecord`
(`evaluation/models.py:15-35`) are referenced nowhere outside their own definitions and docs.
Resolution: delete the dead contracts; keep `EvaluationLevel` by wiring it (T19). Do not preserve
decorative architecture.

## Scope

- `evaluation/models.py`: remove `ABCTestPlan`, `SystemArm`, `MetricRecord`; keep
  `EvaluationLevel` (now used by `oncolab/experiments.py` and the catalog).
- Update `docs/EVALUATION.md` "Open gaps": remove the dead-contract line; replace with the
  resolved state.
- Do not touch A020's frontier analysis (recorded result); its accounting rule is protected by
  `tests/test_frontier.py`.

## Acceptance

- No unreferenced evaluation contract remains in `evaluation/models.py`.
- `EvaluationLevel` has real consumers (`oncolab.experiments.ExperimentSpec`, catalog, tests).
- Import direction stays legal: `oncolab → evaluation` (evaluation imports nothing from oncolab).

## Verification

`python scripts/verify.py` (ruff F401 will catch unused imports) + grep for removed names.

## Findings (2026-09-30)

- `ABCTestPlan`, `SystemArm`, and `MetricRecord` deleted from `evaluation/models.py`; repo-wide grep
  finds no remaining code references. `EvaluationLevel` survives and is consumed by
  `oncolab/experiments.py`, `experiments/catalog.py`, and the catalog tests.
