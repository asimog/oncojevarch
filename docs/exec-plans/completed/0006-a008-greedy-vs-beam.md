# A008 — greedy versus bounded beam search

Status: complete

## Objective

Determine whether a small beam recovers useful terminal branches lost by greedy search at an
acceptable evaluation cost using replayable, locked traces.

## Frozen design

- Six depth-two traces with fixed edge distributions and expected terminal paths.
- Widths 1, 2, and 3 ranked by length-normalized geometric-mean path probability.
- Width 2 success: at least +0.25 recall, at most 1.75 times greedy evaluated edges, and exact
  deterministic replay.

## Evidence

- Focused beam/catalog tests: 5 passed.
- Frozen fingerprint: `f2011fbd52b0ce6d47a17581c14477118cdffd14782f16aef6ac61a785c5250e`.
- Terminal recall: width 1 = 0.333, width 2 = 0.833, width 3 = 1.000.
- Mean evaluated edges: 4.167, 6.167, and 6.500 respectively.
- Width 2 recall gain: 0.50; evaluation ratio: 1.48.
- Two complete executions produced identical decisions and metrics.

## Outcome

The scoped criteria were met. The repository now contains a generic validated replay beam
primitive, but no width is promoted as a permanent scientific-search default. Representative
Jev-backed and biological traces remain future evaluation work.
