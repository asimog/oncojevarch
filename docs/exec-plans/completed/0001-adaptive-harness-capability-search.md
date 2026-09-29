# Adaptive harness and capability search

Status: COMPLETE
Created: 2026-09-30
Completed: 2026-09-30
Base HEAD: `2ec39eb222c1fe9dc31314f689c9543be8e0c22c`

Reviewed task definitions: `docs/tasks/` (one file per task, T00-T40).
No commits were made; all changes are in the working tree per instruction.

## Phase A — Documentation convergence (COMPLETE)

- THESIS.md — recorded evidence to date; harness strategy is not a fourth arm.
- ARCHITECTURE.md — adaptive scientific search, five search problems, repository mental model,
  canonical adaptive flowchart (target vs implemented), expanded OnCodex/OncoLab roles, Codex
  engineering-side boundary, source-independence path.
- docs/CONCEPT_BOOK.md — five search problems, capability search synthesis, earned lessons
  A001-A020.
- docs/CAPABILITY_EVOLUTION.md — explicit routes for Method/Capability/Decision/Harness gaps and
  the capability lifecycle diagram with the three invariant inequalities.
- README.md — mission, scientific thesis, harness strategy, current phase, corrected non-goals,
  repository map including docs/tasks; corrected stale experiment-status claims.
- AGENTS.md — executable experiment list corrected to A001-A020; docs/tasks added to read-first.
- SCAFFOLD_MANIFEST.md — stale test count corrected; superseded next-action block replaced.
- docs/EVALUATION.md — executed level vs scientific readiness, L0-L4 entry/exit gates, L3
  compatibility contract, L4 frozen-T1/shadow mode, accounting rules, controls, leakage review,
  multiplicity modes, freezing/identity, fair A/B/C under capability evolution, open gaps.

## Phase B — Code (COMPLETE)

- `oncolab/capabilities.py` — minimum contract fields (purpose, domain_owner, inputs, outputs,
  prerequisites, exclusions, evaluated_domain), `CapabilitySummary`, deterministic bounded
  `search`, `check_applicability`, explicit empty results. No Jev.
- `oncolab/gaps.py` — provenance fields (`unmet_requirements`, `attempted`, `origin`) and
  `GapLedger` append-only durable recording with deterministic `gap_identity`.
- `oncodex/capability_tools.py` — pure tool functions + Agents SDK wrappers
  (`search_capabilities`, `load_capability`, `record_gap`); no network, no global state.
- `oncodex/agent.py` — `build_oncodex_research_agent`; A001 smoke builder untouched.
- `oncolab/experiments.py` — `evaluation_level: EvaluationLevel`; catalog typed; catalog
  fingerprints verified byte-identical before/after (20 entries).
- `evaluation/models.py` — dead `ABCTestPlan`/`SystemArm`/`MetricRecord` deleted; `EvaluationLevel`
  wired and tested.
- `scripts/check_architecture.py` — `oncolab` dependency rule; source-adapter containment;
  `forbid_import_directions(root)` unit-tested.
- `.github/workflows/ci.yml` — installs `.[agents,jev,dev]`.

## Decisions and findings

- 2026-09-30: T33 resolved by deletion of dead evaluation contracts; keep and wire
  `EvaluationLevel`.
- 2026-09-30: T16 scoped to a separate research builder; Jev/OncoX agent invocation deferred
  (no evaluated per-decision Jev capability exists).
- 2026-09-30: No `ExperimentSpec` schema change; fingerprints of frozen A001-A020 records prove
  unchanged.
- 2026-09-30: T29 accounting rule was already protected by `tests/test_frontier.py`; docs updated,
  no test-only seam added.
- 2026-09-30: markdown scan of repo docs found no remaining broken fences (scratch copies under
  `.oncojev/` are not repo docs).

## Verification log

- 2026-09-30 baseline: architecture OK; compileall OK; pytest 110 passed / 3 skipped; ruff OK;
  mypy OK (108 files).
- 2026-09-30 final (global Python, no optional SDKs): architecture checks OK; compileall OK;
  pytest 130 passed / 4 skipped; ruff OK; mypy OK (113 files).
- 2026-09-30 local venv (agents installed): new capability-tool wrapper tests executed and passed
  (16/16 across test_capability_tools, test_capability_search, test_gap_ledger).
- CI workflow updated but not executed (no push performed; no remote mutations).

## Remaining gaps (also in docs/EVALUATION.md)

- no L3/L4 protocol, compatibility artifact, or temporal cutoffs frozen yet;
- evidence admission (`MeasuredResult -> ScientificEvidence`) has no implemented owner;
- no evaluated per-decision Jev instrument built since A013 (DecisionGap path untested live);
- agent-side Jev/OncoX invocation deliberately unwired;
- multiplicity mode declaration documented but not enforced by a catalog field;
- CI extras change unverified until the next push.
