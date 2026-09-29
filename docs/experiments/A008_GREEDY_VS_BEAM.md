# A008 — greedy versus bounded beam search

Date: 2026-09-29
Class: architecture
Status: completed; frozen success criteria met

## Question

Can a small bounded beam recover useful terminal branches that greedy search permanently loses,
without multiplying semantic evaluations beyond the frozen ceiling?

## Frozen comparison

Six depth-two replay traces contain locked Choice-like edge probabilities and terminal labels.
Three traces have a recoverable early greedy error, two have a clear greedy winner, and one hides
the correct terminal behind the third-ranked root branch. Widths 1, 2, and 3 use the same
length-normalized geometric-mean path score.

Width 2 had to improve terminal recall by at least 0.25 while evaluating at most 1.75 times as
many edges as width 1. Two complete replays had to match exactly.

## Results

| Metric | Width 1 | Width 2 | Width 3 |
|---|---:|---:|---:|
| Terminal recall | 0.333 | 0.833 | 1.000 |
| Mean expanded nodes | 2.000 | 3.000 | 3.167 |
| Mean evaluated edges | 4.167 | 6.167 | 6.500 |
| Mean root-branch diversity | 1.000 | 2.000 | 2.167 |
| Evaluated-edge ratio vs greedy | 1.00 | 1.48 | 1.56 |

Width 2 gained 0.50 terminal recall and stayed below the 1.75 cost ceiling. Width 3 recovered the
single trace designed to require the third root branch. The second full replay was identical to
the first. Measured runtime was below 0.3 ms per six-trace policy run and is not meaningful at
this scale; evaluated edges are the relevant resource measure.

- Frozen experiment fingerprint: `f2011fbd52b0ce6d47a17581c14477118cdffd14782f16aef6ac61a785c5250e`
- External data downloaded: none
- Jev calls: none; frozen probabilities isolate search-policy mechanics

## Decision

The result justifies retaining a source-agnostic bounded beam primitive and testing width 2 in
later representative search traces. Width 3 is not promoted as a default from one constructed
failure. Greedy remains useful where later evidence cannot reverse an early ranking or where the
extra evaluations are not justified.

## Limits

- Synthetic probabilities establish mechanics, not Jev probability quality.
- Six shallow traces do not estimate biological-search recall.
- The frozen cost model counts evaluated edges but not provider batching or downstream work.
