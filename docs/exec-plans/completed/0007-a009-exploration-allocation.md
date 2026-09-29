# A009 — top score versus uncertainty/novelty exploration

Status: complete

## Objective

Test whether an equal-budget frozen exploration allocation recovers useful candidates missed by
top-score-only selection.

## Frozen design

- Ten candidates; four locked useful outcomes.
- Baseline allocation: four promise slots.
- Treatment allocation: two promise, one uncertainty, one novelty slot.
- Success: at least +0.25 useful recall, preserve top two promise candidates, equal budget, and
  exact deterministic replay.

## Evidence

- Focused allocation/frontier/catalog tests: 7 passed.
- Frozen fingerprint: `a6ab0d226a8d532cbd6364d8774d676d2b3c1d32cf4edf1dfcc27332fc047510`.
- Baseline useful recall/precision: 0.50/0.50; false negatives: 2.
- Treatment useful recall/precision: 1.00/1.00; false negatives: 0.
- Both arms selected four candidates; top two promise candidates were preserved.
- Two executions produced identical selections and metrics.

## Outcome

The scoped criteria were met. The allocator is retained as a generic mechanism for future
evaluation; its frozen 2/1/1 proportions and synthetic result are not promoted as a scientific
search policy.
