# A010 — rejected-candidate audit

Status: complete

## Objective

Test whether an immutable, outcome-blind rejection audit exposes actionable false-negative modes.

## Frozen design

- Four accepted and twelve rejected historical decisions.
- Four rejections per retrieval/reranking/viability stage; sample two per stage.
- Sampling consumes only the fingerprinted decision log; outcomes join afterward.
- Success: full stage representation and resolution, at least two useful misses, at least half
  actionable, zero stage-proportion delta, and exact deterministic replay.

## Evidence

- Focused rejection/catalog tests: 6 passed.
- Experiment fingerprint: `dec3b1eddf02407475e3b0fc2086a242b7f862ea149f25201d86f813cbd021d9`.
- Accepted yield: 0.75.
- Two useful misses among six sampled rejections; miss rate 0.333.
- All three stages represented; outcome coverage 1.00; stage-proportion delta 0.00.
- Both misses received actionable follow-up classes; replay was identical.
- A regression found and fixed during execution: stage coverage had initially been computed from
  useful-miss stages instead of sampled stages. A dedicated owner-boundary test now protects it.

## Outcome

The scoped criteria were met. Audit results append a new view over immutable decisions and may
route new experiments, but they never revise historical records or self-promote policy changes.
