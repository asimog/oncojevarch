# A017 — interrupted work, resume, and duplicated evidence

Status: complete (frozen criteria met)

## Objective

Verify that interrupted operations resume without duplicating evidence and without changing the
scientific result.

## Frozen design

- Six-step deterministic operation, artifact identity `sha256(operation_id::step::payload)`.
- Arms: uninterrupted, interrupted after step 4, interrupted after steps 2 and 4 then resumed.
- Criteria: zero duplicate writes, equal final digests, complete arms, completed steps reused.

## Implementation

- `oncolab/recovery.py`: artifact identity, resumable runner over the append-only store, and resume
  comparison.
- `experiments/architecture/a017_resumable_operations.py`: frozen operation, three arms, and the
  decision record.
- `tests/test_recovery.py`: 6 focused tests, including the changed-payload identity rule.

## Evidence

- Duplicate artifact writes 0; duplicate evidence count 0; result equality 1.00; incomplete arms 0.
- The interrupted-twice arm executed 3 + 2 + 1 steps and reused 8, writing exactly six artifacts.
- All arms ended on digest `66ed17fc…`, identical to the uninterrupted run.

## Outcome

Idempotent resume is adopted for this operation shape; the material-change rule (a different payload
is a different identity, never an overwrite) is kept explicit.
