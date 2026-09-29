# A010 — rejected-candidate audit

Date: 2026-09-29
Class: architecture
Status: completed; frozen success criteria met

## Question

Can an outcome-blind audit of historical rejections reveal useful candidates lost upstream and
identify a bounded recovery class without modifying history?

## Frozen comparison

The immutable decision log contains four accepted candidates and twelve rejected candidates,
evenly distributed across retrieval, reranking, and absolute-viability stages. A frozen SHA-256
ordering samples two rejections per stage. Later outcome labels are joined only after the sample
identity is frozen.

Success required representation of all three stages with zero proportion delta, complete outcome
resolution, at least two useful misses, at least half assigned an actionable recovery class, and
identical replay.

## Results

- Accepted candidates: 4; useful: 3; accepted yield: 0.75.
- Rejected population: 12; audited sample: 6.
- Sampled stages: 3; maximum population/sample stage-proportion delta: 0.00.
- Useful misses: 2; rejected-sample miss rate: 0.333.
- Outcome-resolution coverage: 1.00.
- Actionable-miss fraction: 1.00.
- Misses: one reranking `relative_rank` miss and one viability `absolute_gate` miss.
- Proposed follow-up classes: reranking revision and threshold review.
- Two complete executions produced identical sample identities, findings, and metrics.

Fingerprints:

- Experiment: `dec3b1eddf02407475e3b0fc2086a242b7f862ea149f25201d86f813cbd021d9`
- Decision log: `12e87dd8c41b2d38326cf75599555fa8742c68efc4ad11da2e49c806976b35e7`
- Outcome ledger: `5d7809ba51b93184c95ed50c31fe5d5e51018a6ad4033fbec8c21be04c2c2eb3`
- Rejection sample: `532edf1d31abaafa2d73ea415af06a2954c6ea31269472dc2c45ff15338d6804`

## Decision

The result supports the immutable-log, outcome-blind sampling, and append-only audit pattern. It
justifies later focused experiments on reranking and absolute-gate thresholds; it does not itself
change either policy. The absence of a useful retrieval miss in this six-item sample is not proof
that retrieval has no false negatives.

## Limits

- Outcomes and historical decisions are synthetic architecture fixtures.
- Stage balance does not prove representative reasons within each stage.
- Recovery classes are routing suggestions, not evidence that the proposed repair will work.
- No GDC request was appropriate because public metadata does not provide the required later
  counterfactual outcomes for these rejected branches.
