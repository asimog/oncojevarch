# Adaptive harness and capability search

Status: COMPLETE (superseded)
Created: 2026-09-30
Completed: 2026-09-30
Base HEAD: `2ec39eb222c1fe9dc31314f689c9543be8e0c22c`
Superseded by: `docs/tasks/README.md` (9 evidence-gated tasks) and
`docs/exec-plans/completed/0002-evidence-gated-nine-task-program.md`

## What this plan was

The first implementation pass took a 41-task prompt literally and turned document sections into
pseudo-independent tasks. An assessment found the decomposition wrong: one architectural change
had produced 16 tasks, and several "COMPLETE" labels were stronger than the evidence. This record
keeps the surviving decisions and honest status; the decorative 41-task files were deleted after
extraction, per the assessment.

## What survived (still current)

- THESIS/ARCHITECTURE separation of scientific thesis vs harness strategy; five search problems;
  canonical adaptive flowchart; explicit rejection of fixed modality sequencing.
- `CapabilityRecord` discovery metadata (purpose, inputs/outputs, prerequisites, exclusions,
  evaluated_domain) and deterministic token-overlap search.
- `Gap` provenance plus the append-only `GapLedger`; gap routing table.
- `EvaluationLevel` wired into `ExperimentSpec`; catalog fingerprints of A001-A020 verified
  byte-identical (20 entries) before/after.
- Dead `ABCTestPlan`/`SystemArm`/`MetricRecord` deleted.
- Architecture checks: `oncolab` dependency rule; `execution.gdc` containment; unit-tested
  `forbid_import_directions(root)`; catalog level-contract tests.
- CI installs `.[agents,jev,dev]`.
- Canonical doc cleanup: README framing, AGENTS.md experiment line, SCAFFOLD_MANIFEST status note,
  EVALUATION gates and contracts.

## Where the labels were too strong (corrected by 0002)

- `CapabilityRegistry.search()` is an initial experimental mechanism; A022 recorded it failing its
  own frozen rule (a stopword false hit), A025 re-evaluated the repaired mechanism after a minimal
  fix — a new identity, not an edit.
- `CapabilityRecord.inputs/outputs` are discovery metadata, not typed scientific contracts.
- The OnCodex research agent demonstrated capability-registry and research-step operations; it did
  not demonstrate the full scientific control loop.
- Evidence admission had no owner; now implemented and exercised (A021-A024, S002).

## Unique decisions extracted from the deleted T00-T40 files

- Baseline: HEAD `2ec39eb2...`, verify green (110 passed / 3 skipped at that time); failures since
  are attributable to that program.
- No `ExperimentSpec` schema changes; catalog fingerprints must stay byte-identical.
- Executed experiment runners and specs are frozen records; new work lands in new modules.
- T33 resolved by deletion; T16 scoped to a separate research builder with Jev/OncoX deferred.
- T29 accounting rule already protected by `tests/test_frontier.py`; no test-only seam added.
- T35: CI extras change unverified until the next push (no push performed in this program).

## Verification at close of this plan

architecture OK; compileall OK; 130 passed / 4 skipped; ruff OK; mypy OK (113 files).

## Verification after 0002 (superseding)

architecture OK; compileall OK; 153 passed / 4 skipped; ruff OK; mypy OK (131 files); live runs
S001 (failed: frozen minimum) and S002 (completed: first admitted scientific evidence `ev-s002`).
