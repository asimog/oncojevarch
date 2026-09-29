# A013 — Jev model-version regression

Date: 2026-09-30
Class: architecture, semi-synthetic
Status: completed; frozen tolerances met — candidate approved for this contract only

## Question

Does a candidate Jev model version preserve the evaluated behavior of a frozen capability, so that
a model upgrade can be approved, scoped, or rejected on recorded evidence instead of by default?

## Frozen comparison

The A011 task-description-coherence capability was rebuilt byte-for-byte (projection fingerprint
checked against the recorded value) over five public GDC project descriptions: five valid pairs and
three no-fixed-point derangements, twenty Noul questions, threshold 0.5.

- Baseline: the immutable recorded A011 repetition for `jev-1.13.0`, read back from the append-only
  store.
- Control: the same baseline model re-run in a fresh session, to separate provider noise from model
  drift.
- Candidate: `jev-preview`, the only alternative model offered by the account.

Frozen tolerances: positive claim rate at least 0.80, negative mean claim rate at most 0.20, no
negative arm above 0.40, candidate decision agreement at least 0.90, candidate drift no more than
0.05 above the control, and candidate Brier no more than 0.05 worse than the baseline.

## Source receipt

- GDC release: Data Release 46.0 - August 10, 2026; API tag 8.5.0; project response 1,105 bytes
- Rebuilt projection fingerprint: `b97d616b1b137326ca5a3d40ff8e18be750b4863387fe66d50af2261b9dcf86e`
  (matches the recorded A011 value)
- Baseline record: A011 live event, repetition 1, `jev-1.13.0`
- Recorded A011 repetition drift: 0.00675 mean absolute probability

## Results

| Metric | Baseline (recorded) | Control (`jev-1.13.0`) | Candidate (`jev-preview`) |
|---|---:|---:|---:|
| Decision agreement with baseline | 1.00 | 1.00 | 1.00 |
| Mean absolute drift | — | 0.0095 | 0.0070 |
| Brier score | 0.00433 | 0.00393 | 0.00391 |
| Positive claim rate | 1.00 | 1.00 | 1.00 |
| Negative mean claim rate | 0.00 | 0.00 | 0.00 |
| Max negative-arm claim rate | 0.00 | 0.00 | 0.00 |
| Latency | 785 ms | 806 ms | 328 ms |
| Tokens | 3,630 in / 469 out | 3,630 in / 469 out | 3,630 in / 469 out |

Per-case agreement was 1.00 for all five cases, with per-case drift between 0.0025 and 0.0100.
Candidate drift minus control drift was -0.0025. No frozen failure was reported.

## Decision

`jev-preview` is approved **for this contract, model pair, and evaluation set only**. The
regression harness, the recorded-baseline lookup, and the same-model control are retained. Nothing
here validates Jev semantics in general, and a capability regression result is not scientific
validation.

## Limits

- One twenty-question coherence set cannot represent Jev behavior across capabilities.
- The recorded baseline and the candidate ran in different sessions and moments.
- The candidate is a preview model; approved behavior may change without a new evaluation.
- Three derangements and five valid pairs are a small calibration sample.
