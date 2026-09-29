# A017 — interrupted work, resume, and duplicated evidence

Date: 2026-09-30
Class: architecture, synthetic
Status: completed; frozen criteria met

## Question

Can interrupted work resume without writing duplicate evidence or changing the scientific result?

## Frozen design

A six-step deterministic operation over the append-only store, where each step would write one
artifact. Artifact identity is `sha256(operation_id::step::payload)`, so the same operation step can
never produce two artifacts, and a changed payload becomes a different identity instead of rewriting
history.

Arms: uninterrupted; interrupted after step 4 then resumed; interrupted after step 2, again after
step 4, then resumed to completion. Frozen criteria: zero duplicate artifact writes, equal final
digests, every arm complete, and completed steps reused rather than re-executed.

## Results

| Metric | Value |
|---|---:|
| Duplicate artifact writes | 0 |
| Duplicate evidence count | 0 |
| Result equality (final digest) | 1.00 |
| Incomplete arms | 0 |
| Executed steps, uninterrupted arm | 6 |
| Executed steps, interrupted-after-4 arm | 1 (5 reused) |
| Executed steps, interrupted-twice arm | 3 + 2 + 1 (8 reused across attempts) |
| Artifact events per arm | 6 |

All three arms produced the same final digest
`66ed17fc186d12fbcde75c996a315f632413781ee67f80269cf4ca699d88a162`, and no arm wrote a second
artifact for any step.

## Decision

Idempotent resume is adopted for this operation shape. The runner journals completed steps in the
durable store and reuses them, so a restart is a resume rather than a rewrite. The material-change
rule is kept explicit: a different payload is a different artifact identity, never an overwrite.

## Limits

- Fault injection is in-process, not a real crash, power loss, or partial write.
- The operation is deterministic; real steps may have external side effects that identity cannot
  undo.
- Artifact identity covers step payloads, not provider or source state.
- This architecture task cannot create ScientificEvidence.
