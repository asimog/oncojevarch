# Evaluation strategy

## Synthetic is not scientific validation

Synthetic data can test contracts, missingness propagation, recovery, projection fingerprinting, search mechanics, failure modes, and deliberately planted signals. It cannot establish that Jev recognizes useful cancer biology or improves real candidate discovery.

## Evaluation ladder

### Level 0 — synthetic
Engineering/architecture validation only.

### Level 1 — semi-synthetic
Real biological background with controlled implanted signal. Measures sensitivity to signal strength, missingness, subgroup size, and search depth while preserving realistic background structure.

### Level 2 — retrospective real-data rediscovery
First meaningful scientific A/B/C level. Use historical real data; keep historical known findings out of the research inputs and freeze arm outputs before unblinding the evaluation set.

Model-pretraining leakage is a major threat: an LLM may already know famous published findings. Mitigations/diagnostics may include masked identifiers, uncommon relationship tasks, restricted literature access, newer releases, semi-synthetic controls, and future/independent validation.

### Level 3 — independent validation
Freeze candidates from discovery data and test in an independent scientifically compatible dataset. Compatibility of populations, assays, measurements, normalization, and methods must be explicit.

### Level 4 — temporal/prospective
Where feasible, discover on information available at T1, freeze candidates, then evaluate against genuinely later data at T2.

## A/B/C

```text
A = deterministic scientific system
B = deterministic + OncoX
C = deterministic + Jev + OncoX
```

Use the same scientific population/source release, allowable methods, task, evaluation labels, and resource-accounting rules.

Run at least two resource comparisons:

1. **Equal budget:** which arm delivers better scientific outcomes for the same resource budget?
2. **Equal scientific target:** how much resource does each arm require to reach a prespecified target?

The thesis is that C may shift the quality-cost frontier. If B and C occupy essentially the same frontier, the Jev layer may not justify its complexity. If C lowers discovery recall through early semantic pruning, that is evidence against the design.

## Component ablations before full A/B/C

- deterministic ranking vs deterministic + Jev reranking;
- Choice vs Choice + absolute-viability Noul;
- greedy vs beam/frontier search;
- full state vs question-specific projection;
- no exploration vs uncertainty/novelty exploration;
- OncoX on all cases vs Jev-screened selective OncoX;
- fixed Jev questions vs offline evaluated discovered questions;
- normal vs null/shuffled controls.

## Pre-register metrics before result exposure

Candidates include scientific recall/precision, known-signal rediscovery, held-out replication, contradiction discovery, false-negative burden, candidate stability/diversity, bytes transferred, deterministic compute, Jev calls/tokens, OncoX calls/tokens, time-to-candidate, cost per viable Investigation, and reproducibility.

Do not invent the winning metric after seeing results.
