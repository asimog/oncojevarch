# A014 — offline feature discovery and locked-case generalization

Date: 2026-09-30
Class: architecture, synthetic
Status: completed; frozen failure branch taken — no feature promoted

## Question

Do semantic features discovered offline on a development split generalize to validation and locked
test splits, or does bounded semantic endorsement have to reject them?

## Frozen design

- Sixty synthetic case records with a planted family-conditional signal, a fixed one-in-seven label
  noise rate, and three frozen splits: development (30), validation (15), locked test (15).
- Feature language: word n-grams seen in at least eight cases, plus conjunctions of a claim-family
  marker with a missing-item phrase.
- Discovery: positive-minus-negative presence rate on the development split only, at most six
  features at a minimum score of 0.25, deterministic tie-break.
- Jev endorsement: one batched Noul call, threshold 0.5, over the discovered features only.
- Downstream model: deterministic Laplace-smoothed log-odds weights fitted on the development
  split, cutoff fitted on the validation split over a frozen grid.
- Frozen arms: a hand-frozen baseline feature set versus discovered-then-endorsed features.
- Frozen failure: no locked-test gain, or any split-integrity finding.

## Evidence

- Full gate green; 9 focused tests.
- Split-integrity findings: none; development discovery reproduced exactly under a
  locked-label permutation.
- Discovered on development: `treatment response outcomes.` (0.344), `claim: tcga-lusc` (0.316),
  `compared with tcga-kirc.` (0.316), `observed: tcga-lusc` (0.316), and two similar positional
  n-grams.
- Reconfirmed on validation: only the two "response outcomes" phrases survived (stability 0.20).
- Jev endorsement probabilities: 0.11, 0.15, 0.20, 0.14, 0.23, 0.14 — **no feature endorsed**.
- Locked test: baseline arm accuracy 0.533 (recall 1.00, specificity 0.00, Brier 0.339);
  discovered arm accuracy 0.533 (Brier 0.250) with zero promoted features.
- Locked-test accuracy gain: 0.00. Jev cost: 895 input, 124 output tokens, 824 ms.

## Decision

No feature is promoted. The frozen failure branch applies: the discovered features did not
generalize, so they are discarded rather than promoted into any capability. The bounded endorsement
gate behaved as designed and rejected every candidate.

The reason is visible in the record: the corpus ties labels to index arithmetic that also selects
the project and item slots, so the development split's most discriminative phrases were positional
artifacts such as `claim: tcga-lusc`, not the intended family-conditional pairings. Discovery found
corpus structure instead of the planted semantics, and stability between splits was 0.20.

## Limits

- The corpus is synthetic with an implanted signal; this is a mechanics result, not cancer biology.
- The corpus generator confounded the planted signal with positional project and item slots, so the
  run cannot show whether family-conditional features would generalize on a corrected corpus. A
  corrected corpus is a new experiment identity.
- The downstream model is a lexical scorer, and the locked test holds fifteen cases.
- Jev endorsement is a bounded judgment about phrase wording, not permission to promote.

## Follow-up

A corrected corpus with label assignment independent of positional slots would test the intended
question: whether family-conditional semantic features generalize. That is a new experiment, not an
edit to A014.
