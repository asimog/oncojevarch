# Evidence-gated nine-task program

Status: COMPLETE through the evidence boundary
Created: 2026-09-30
Completed: 2026-09-30
Base commit: `711824f`
Task definitions: `docs/tasks/README.md`

## Purpose

Replace the 41-task specification-of-the-answer program with nine evidence-gated tasks, and
deliver the missing executable nucleus (evidence admission) plus the first scientific
investigation. Gated tasks that were not triggered are recorded with triggers, not marked done.

## Phase 1 — Cleanup and honesty (COMPLETE)

- Deleted `docs/tasks/T00-T40` after extracting unique decisions into
  `completed/0001-adaptive-harness-capability-search.md`.
- Rewrote 0001 as an honest transition record (implemented vs experimentally demonstrated vs
  target; corrections applied here).
- Canonical wording corrected: capability search is an initial evaluated mechanism;
  `CapabilityRecord` metadata is discovery metadata; evidence admission is implemented and
  exercised; agent-side Jev/OncoX invocation remains a target contract.

## Phase 2 — Tasks 1-4 (COMPLETE)

- T1 nucleus: `oncolab/admission.py`, `research/state.py`, `research/ledger.py`,
  `oncolab/operations.py`; experiment A021.
- T2 search evaluation: A022 recorded the raw mechanism failing its frozen rule (stopword false
  hit, decision "reopen"); stopword repair in `oncolab/capabilities.py`; A025 re-evaluated the
  repaired mechanism under a new identity (decision "keep").
- T3 gap loop: A023 (4/4 routes correct, 2 unsafe promotions blocked, reasoning-only result
  refused at admission).
- T4 control loop: `oncodex/research_loop.py`; tools `inspect_investigation` and
  `run_scientific_operation`; A024 (session_independent true over rebuilt ledgers).

## Phase 3 — Tasks 5-9 (COMPLETE to their evidence gates)

- T5: S001 failed live against its frozen minimum-project count (33 retrieved vs 40); S002
  (new identity, minimum 30) completed live: 33 projects, 33 co-available, max site share
  0.0909 == null mean, p=1.0; first admitted scientific evidence `ev-s002`; the degenerate null
  is the substantive finding.
- T6: no DecisionGap exposed by S002; Jev remains unwired with a recorded trigger.
- T7: no explanation need exposed; OncoX remains unwired with a recorded trigger.
- T8: deferred by design dependency — B and C have no evidence-backed components, so an A/B/C run
  would compare identical arms; A020 machinery retained; trigger recorded.
- T9: not earned — no candidate/prediction exists to validate; L3/L4 protocols deliberately not
  created.

## Decisions and findings

- 2026-09-30: negative results get new identities, not edits (A022→A025, S001→S002).
- 2026-09-30: admission context is frozen for identity (population, provenance, measurement) and
  completed for measurement facts (coverage, missingness, source version) through the typed
  `AdmissionContextDisclosure` protocol implemented by the scientific capability.
- 2026-09-30: no Jev/OncoX/A/B/C/L3/L4 work proceeds without its evidence trigger.

## Verification log

- Final: architecture checks OK; compileall OK; 153 passed / 4 skipped; ruff OK; mypy OK
  (131 source files).
- Local venv (agents installed): capability-tool and research-tool wrappers exercised.
- Live: `python -m oncodex run S002 --live` completed and recorded `ev-s002`;
  `python -m oncodex run S001 --live` recorded a failed identity.
- No commit or push was performed for this program (not requested).

## Remaining gaps (updated)

- typed capability output contracts (`CapabilityRecord` metadata is discovery metadata);
- OnCodex need-identification from scientific state (step takes the need as input);
- no DecisionGap or explanation need has been exposed yet;
- A/B/C, L3, L4 await their triggers;
- CI extras change from 0001 still unverified until a push.
