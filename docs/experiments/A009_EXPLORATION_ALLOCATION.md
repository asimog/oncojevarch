# A009 — top score versus uncertainty/novelty exploration

Date: 2026-09-29
Class: architecture
Status: completed; frozen success criteria met

## Question

Can a fixed exploration allocation recover useful low-promise candidates at the same selection
budget as a top-score-only policy?

## Frozen comparison

Ten candidates have locked promise, uncertainty, novelty, and useful-outcome labels. Both arms
select four candidates. The baseline takes the four highest promise scores. The treatment takes
two by promise, then one unselected candidate by uncertainty and one by novelty. Neither policy
can read outcome labels.

Success required at least +0.25 useful recall, preservation of the top two promise candidates,
an equal four-candidate budget, and identical deterministic replay.

## Results

| Metric | Top score | 2/1/1 exploration |
|---|---:|---:|
| Selected candidates | 4 | 4 |
| Useful selected | 2 | 4 |
| Useful recall | 0.50 | 1.00 |
| Selected precision | 0.50 | 1.00 |
| False-negative burden | 2 | 0 |
| Selection-reason diversity | 1 | 3 |

The treatment retained candidates `c01` and `c02`, then recovered useful `c05` through the
uncertainty slot and useful `c07` through the novelty slot. Two executions produced identical
selections and metrics. Runtime was below 0.1 ms per arm and is not meaningful at this scale;
the selected-candidate budget was exactly equal.

- Frozen experiment fingerprint: `a6ab0d226a8d532cbd6364d8774d676d2b3c1d32cf4edf1dfcc27332fc047510`
- External data downloaded: none
- Jev calls: none; fixed signals isolate allocation mechanics

## Decision

The experiment supports keeping a generic explicit-slot exploration allocator for later replay
and real-data evaluation. It does not promote the 2/1/1 split, establish that uncertainty or
novelty predicts scientific utility, or authorize use of outcome labels during selection.

## Limits

- Synthetic outcomes establish mechanics only.
- The useful uncertain and novel candidates were deliberately planted.
- Equal candidate count does not model unequal downstream evaluation cost.
- Representative traces are required before choosing any operational allocation.
