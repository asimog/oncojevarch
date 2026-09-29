# Experiment catalog

There are only two experiment classes: architecture and scientific.

## Architecture experiments

| ID | Question | Status in scaffold |
|---|---|---|
| A001 | Can OnCodex run independently of the IDE and invoke a bounded read-only Codex workspace task? | executable preflight/live shell |
| A002 | Do Choice/Noul/Score semantics map cleanly to bounded OncoJev decisions? | executable offline/live shell |
| A003 | What is the smallest projection that preserves a target semantic judgment? | executable mechanics demo |
| A004 | Full relevant state vs projected state | executable offline freeze/live Jev evaluation |
| A005 | When does richer representation materially improve the decision? | executable GDC metadata ladder |
| A006 | Deterministic ranking vs Jev reranking | executable GDC metadata/Jev evaluation |
| A007 | Choice vs Choice + Noul | executable GDC metadata/Jev evaluation |
| A008 | Greedy vs beam search | executable deterministic replay evaluation |
| A009 | Top-score vs uncertainty/exploration frontier | executable deterministic evaluation |
| A010 | What useful candidates were rejected upstream? | executable immutable-log audit |
| A011 | Does the system produce narratives on null/shuffled data? | executable GDC/Jev controls |
| A012 | OncoX on all cases vs Jev-screened selective OncoX | frozen protocol |
| A013 | Jev model-version regression | frozen protocol |
| A014 | Offline semantic feature discovery generalization | frozen protocol |
| A015 | Gap routing and no-self-promotion | core tests + frozen protocol |
| A016 | Full history vs bounded/progressive OnCodex context | frozen protocol |
| A017 | Crash/recovery/idempotency | frozen protocol |
| A018 | Can architecture results justify small reviewable repo changes? | frozen protocol |
| A019 | Leakage-resistant masked real-data rediscovery | frozen real-data protocol |
| A020 | Full system A/B/C science-efficiency frontier | frozen real-data protocol |

The executable source of truth is `experiments/catalog.py`. Each protocol specifies a
hypothesis, required data and capabilities, comparison arms, metrics, failure criteria,
architecture consequences, resource ceiling, and evaluation level. Use
`python -m oncodex plan A###` to inspect the exact frozen input before implementation or run.

## Scientific experiments

None are implemented in the scaffold. A scientific experiment must freeze its scientific question, population, source/version, method/estimand, variables/comparisons, missingness/normalization/multiplicity policy where applicable, success/failure/stop rules, budget, and capability versions before material results are exposed.

## Experiment record template

Every future experiment should specify:

- research question;
- hypothesis;
- experiment class;
- required data;
- required capabilities;
- baseline/treatment/control;
- prespecified metrics;
- failure/falsification criteria;
- what outcome would alter architecture or scientific belief;
- resource budget;
- synthetic/semi-synthetic/retrospective/independent/prospective level.
