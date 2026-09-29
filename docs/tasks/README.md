# Task program — adaptive harness and capability search

Created: 2026-09-30. This folder is the working task record. It is not canonical
architecture knowledge; canonical docs remain `THESIS.md`, `ARCHITECTURE.md`,
`docs/CONCEPT_BOOK.md`, `docs/CAPABILITY_EVOLUTION.md`, `docs/EVALUATION.md`, and
`docs/EXPERIMENT_CATALOG.md`.

Execution record: `docs/exec-plans/active/0001-adaptive-harness-capability-search.md`.

## Baseline (T00)

- Starting HEAD: `2ec39eb222c1fe9dc31314f689c9543be8e0c22c` ("Record A019 and A020 execution plans").
- Working tree at start: four modified docs from the prior evaluation-strategy session
  (`README.md`, `docs/CONCEPT_BOOK.md`, `docs/EVALUATION.md`, `docs/EXPERIMENT_CATALOG.md`).
- Baseline verification: architecture checks OK; compileall OK; pytest 110 passed / 3 skipped;
  ruff OK; mypy OK (108 source files).
- No code changed before this record.

## Independent review of the incoming plan

The 40-task plan is directionally consistent with the repository, but it was written from an
assumed state that differs from the actual state. Adjustments made:

1. **T1 shape changed** (user instruction): per-task files here plus one active execution plan,
   instead of a single monolithic plan only.
2. **Already-satisfied tasks** are marked so: T0 complete; T35 currently green; T39 partially
   done in the prior session; T33 partially (dead contract confirmed by code audit).
3. **Fingerprint safety rule**: `ExperimentSpec` is fingerprinted and A001-A020 results are frozen
   records. No new spec fields are added. `evaluation_level` is wired to `EvaluationLevel` only as
   a value-preserving annotation change, verified by comparing catalog fingerprints before/after.
4. **Executed experiments are immutable records**: A001-A020 runners and specs are not materially
   edited. New code goes into new modules/tests; T16 adds a research agent builder that leaves the
   A001 smoke agent unchanged.
5. **No speculative machinery**: the capability layer gets the smallest search/contract/ledger
   additions that satisfy T6-T8; no service, no store schema, no Jev in capability search.
6. **Evidence admission stays an explicit remaining gap** unless the next milestone requires it;
   the constitution forbids improvising it. T40 answers it honestly.
7. **T5 diagram** is published as target architecture with the implemented subset stated; it must
   not imply that unimplemented components (admission, OncoX wiring) already exist.
8. **T33 resolved by deletion**: `ABCTestPlan`, `SystemArm`, `MetricRecord` are unreferenced;
   `EvaluationLevel` survives by being wired. Dead contracts are removed, not preserved.
9. **T34 stays small**: two dependency-direction rules plus one catalog level-contract test; no
   bespoke static-analysis system.
10. **T36 defines, does not start, the next scientific milestone**; starting it is a separate
    decision with its own experiment identity.

Everything else is kept as written, with acceptance criteria tied to `python scripts/verify.py`.

## Reviewed task set

| Task | File | Verdict | Status |
|---|---|---|---|
| T00 | [T00-baseline.md](T00-baseline.md) | KEEP | COMPLETE |
| T01 | [T01-execution-plan.md](T01-execution-plan.md) | MODIFIED (per-task files + one active plan) | COMPLETE |
| T02 | [T02-thesis.md](T02-thesis.md) | KEEP | COMPLETE |
| T03 | [T03-architecture-search.md](T03-architecture-search.md) | KEEP | COMPLETE |
| T04 | [T04-five-search-problems.md](T04-five-search-problems.md) | KEEP | COMPLETE |
| T05 | [T05-flowchart.md](T05-flowchart.md) | MODIFIED (label target vs implemented) | COMPLETE |
| T06 | [T06-capability-search.md](T06-capability-search.md) | KEEP (deterministic only) | COMPLETE |
| T07 | [T07-capability-contract.md](T07-capability-contract.md) | MODIFIED (minimum fields) | COMPLETE |
| T08 | [T08-gap-explicit.md](T08-gap-explicit.md) | MODIFIED (provenance + ledger) | COMPLETE |
| T09 | [T09-method-gap.md](T09-method-gap.md) | KEEP | COMPLETE |
| T10 | [T10-capability-gap.md](T10-capability-gap.md) | KEEP | COMPLETE |
| T11 | [T11-decision-gap.md](T11-decision-gap.md) | KEEP | COMPLETE |
| T12 | [T12-harness-gap.md](T12-harness-gap.md) | KEEP | COMPLETE |
| T13 | [T13-lifecycle.md](T13-lifecycle.md) | KEEP | COMPLETE |
| T14 | [T14-oncodex.md](T14-oncodex.md) | KEEP | COMPLETE |
| T15 | [T15-oncolab.md](T15-oncolab.md) | KEEP | COMPLETE |
| T16 | [T16-orchestration.md](T16-orchestration.md) | MODIFIED (research builder; pure tools) | COMPLETE |
| T17 | [T17-codex-boundary.md](T17-codex-boundary.md) | KEEP | COMPLETE |
| T18 | [T18-source-independence.md](T18-source-independence.md) | KEEP | COMPLETE |
| T19 | [T19-type-erosion.md](T19-type-erosion.md) | MODIFIED (minimal fixes + inventory) | COMPLETE |
| T20 | [T20-concept-book.md](T20-concept-book.md) | KEEP | COMPLETE |
| T21 | [T21-readme.md](T21-readme.md) | KEEP | COMPLETE |
| T22 | [T22-lessons.md](T22-lessons.md) | KEEP | COMPLETE |
| T23 | [T23-levels.md](T23-levels.md) | KEEP | COMPLETE |
| T24 | [T24-l0.md](T24-l0.md) | KEEP | COMPLETE |
| T25 | [T25-l1.md](T25-l1.md) | KEEP | COMPLETE |
| T26 | [T26-l2.md](T26-l2.md) | KEEP | COMPLETE |
| T27 | [T27-l3.md](T27-l3.md) | KEEP | COMPLETE |
| T28 | [T28-l4.md](T28-l4.md) | KEEP | COMPLETE |
| T29 | [T29-abc-accounting.md](T29-abc-accounting.md) | MODIFIED (verify existing test; docs) | COMPLETE |
| T30 | [T30-controls-leakage.md](T30-controls-leakage.md) | KEEP | COMPLETE |
| T31 | [T31-multiplicity.md](T31-multiplicity.md) | KEEP (docs; no spec schema change) | COMPLETE |
| T32 | [T32-identity.md](T32-identity.md) | KEEP (docs; no spec schema change) | COMPLETE |
| T33 | [T33-abctestplan.md](T33-abctestplan.md) | MODIFIED (delete dead contracts; wire enum) | COMPLETE |
| T34 | [T34-checks.md](T34-checks.md) | MODIFIED (two import rules + level test) | COMPLETE |
| T35 | [T35-verification.md](T35-verification.md) | MODIFIED (extras in CI) | COMPLETE |
| T36 | [T36-milestone.md](T36-milestone.md) | MODIFIED (define, do not start) | COMPLETE |
| T37 | [T37-fair-abc.md](T37-fair-abc.md) | KEEP | COMPLETE |
| T38 | [T38-mental-model.md](T38-mental-model.md) | KEEP | COMPLETE |
| T39 | [T39-cleanup.md](T39-cleanup.md) | KEEP | COMPLETE |
| T40 | [T40-final-audit.md](T40-final-audit.md) | KEEP | COMPLETE |
