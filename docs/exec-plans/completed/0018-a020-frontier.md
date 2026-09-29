# A020 — science-efficiency frontier

Status: complete (failure branch; central hypothesis narrowed)

## Objective

Decide whether the combined layer stack (deterministic, deterministic plus OncoX, deterministic plus
Jev plus OncoX) improves scientific utility per unit resource on frozen real-data tasks.

## Frozen design

- Recorded-results analysis over immutable stored experiment results, not a new prospective run.
- Tasks: `a012_oncox_cascade` (quality = useful-case retention) and `a019_masked_rediscovery`
  (quality = recall@1 divided by the frozen 0.50 target).
- Dominance: no more tokens, no less quality, strictly better on at least one axis. Arm C must
  strictly dominate a recorded arm to count as moving the frontier.

## Implementation

- `experiments/architecture/a020_frontier.py`: frozen point extraction from the store, per-task
  dominance, resource facts, narrative evidence, and the decision record.
- `tests/test_frontier.py`: 6 focused tests covering dominance, ties, and the bookkeeping rule that
  arm C includes its Jev screen.

## Evidence

- A012: B 13,656 tokens at quality 1.000 dominates C 15,014 tokens at quality 1.000.
- A019: deterministic 0 tokens at quality 0.545 dominates B and C at 4,580 tokens and equal quality.
- Arm C moved no frontier; the first extraction under-counted C's cost and was corrected before the
  result was recorded.
- A006 and A007 remain the recorded evidence that Jev improves gating and reranking.

## Outcome

The central hypothesis is narrowed: retain the deterministic core and bounded Jev gating/reranking;
do not claim a frontier shift from Jev-screened OncoX; keep all-case OncoX where deep reasoning is
used; and re-test any revised triage contract as a new experiment identity.
