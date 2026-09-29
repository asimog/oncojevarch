# T01 — Execution plan

Status: COMPLETE
Dependencies: T00
Verdict: MODIFIED — user instruction replaces "one plan only" with per-task files in
`docs/tasks/` plus one active execution plan that tracks the program.

## Deliverables

- `docs/tasks/README.md` — program analysis and task index (this folder).
- `docs/tasks/T00..T40*.md` — reviewed task definitions with status, dependencies, files,
  goal, acceptance, verification, findings.
- `docs/exec-plans/active/0001-adaptive-harness-capability-search.md` — the working record,
  updated while working; moves to `completed/` when the program closes.

## Acceptance

- Every incoming task has a reviewed file with an explicit verdict
  (KEEP / MODIFIED / ALREADY_DONE / DELETE-AS-UNNECESSARY) and acceptance criteria.
- The active plan lists phases, dependencies, statuses, and verification evidence.
- Statuses are updated as work proceeds; completed slices are recorded rather than batched.

## Verification

Presence and consistency of `docs/tasks/`; the active plan matches actual statuses at each
checkpoint. No mechanical check enforces task-file content (working state, not invariants).
