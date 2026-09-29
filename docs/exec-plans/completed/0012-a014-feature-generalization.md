# A014 — offline feature discovery and locked-case generalization

Status: complete (negative; no feature promoted)

## Objective

Test whether offline-discovered semantic features generalize to a locked test split, and whether
bounded semantic endorsement can act as the promotion gate.

## Frozen design

- Synthetic corpus of sixty cases with a planted family-conditional signal, one-in-seven label
  noise, and development/validation/locked-test splits of 30/15/15.
- Feature language: frequent word n-grams plus family-marker conjunctions with missing-item
  phrases; deterministic discovery on the development split only; cutoff fitted on validation only.
- One batched Noul endorsement call over the discovered features.
- Frozen failure: no locked-test gain or any split-integrity finding.

## Implementation

- `evaluation/discovery.py`: candidate generation, split-declared discovery, log-odds scoring,
  validation cutoff fitting, locked-test evaluation, feature stability, split-integrity audit.
- `experiments/architecture/a014_feature_generalization.py`: frozen corpus, arms, endorsement call,
  leakage checks, and the promotion decision.
- `tests/test_feature_generalization.py`: 9 focused tests.

## Evidence

- Split-integrity findings: none; discovery reproduced exactly under locked-label permutation.
- Discovery selected positional artifacts (`claim: tcga-lusc`, `compared with tcga-kirc.`) because
  the corpus generator confounds labels with index-derived slots; stability was 0.20.
- Jev endorsed zero of six features (probabilities 0.11–0.23).
- Locked-test accuracy gain 0.00; discovered arm Brier 0.250 versus baseline 0.339 with zero
  promoted features.

## Outcome

Failure branch taken: the discovered features are discarded and nothing is promoted. The lesson is
recorded rather than fixed inside A014: the corpus needs label assignment independent of positional
slots, which is a new experiment identity.
