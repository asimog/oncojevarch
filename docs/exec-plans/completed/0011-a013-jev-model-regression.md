# A013 — Jev model-version regression

Status: complete (candidate approved for one contract)

## Objective

Decide whether a candidate Jev model version preserves the evaluated behavior of a frozen
capability, using recorded baseline responses rather than a fresh comparison invented after the
fact.

## Frozen design

- Rebuild the A011 coherence capability exactly and refuse to run if the projection fingerprint
  differs from the recorded one.
- Baseline: immutable recorded A011 repetition for `jev-1.13.0`, read from the append-only store.
- Control: `jev-1.13.0` re-run live in a fresh session.
- Candidate: `jev-preview`.
- Frozen tolerances for claim rates, decision agreement, drift over control, and Brier.

## Implementation

- `evaluation/regression.py`: model-version regression evaluator (agreement, drift, calibration,
  grouped strata, frozen failure list).
- `experiments/architecture/a013_jev_model_regression.py`: frozen evaluation set, recorded-baseline
  lookup, control and candidate runs, and the decision record.
- `tests/test_regression.py`: 7 focused tests, including control separation and boundary crossings.

## Evidence

- Full gate green; 7 new focused tests.
- Rebuilt projection fingerprint matched the recorded A011 value.
- Candidate decision agreement 1.00; drift 0.0070 versus control 0.0095; Brier 0.00391 versus
  baseline 0.00433; no frozen failure.
- Latency 328 ms (candidate) versus 806 ms (control).

## Outcome

The candidate is approved for this contract and evaluation set only. The harness is retained for
future upgrades; a preview model must be re-evaluated before any broader scope.
