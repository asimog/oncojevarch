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
| A012 | OncoX on all cases vs Jev-screened selective OncoX | executable OncoX/Jev cascade; cascade not supported |
| A013 | Jev model-version regression | executable recorded-baseline regression; candidate approved for one contract |
| A014 | Offline semantic feature discovery generalization | executable; nothing promoted |
| A015 | Gap routing and no-self-promotion | executable scenario audit; routing supported |
| A016 | Full history vs bounded/progressive OnCodex context | executable; bounded context not adopted |
| A017 | Crash/recovery/idempotency | executable; idempotent resume supported |
| A018 | Can architecture results justify small reviewable repo changes? | executable; bounded proposal accepted for review |
| A019 | Leakage-resistant masked real-data rediscovery | executed; frozen negative result (recall@1 0.273 vs 0.50 target; no leakage) |
| A020 | Full system A/B/C science-efficiency frontier | executed; arm C moved no recorded frontier; central hypothesis narrowed |

The executable source of truth is `experiments/catalog.py`. Each protocol specifies a
hypothesis, required data and capabilities, comparison arms, metrics, failure criteria,
architecture consequences, resource ceiling, and evaluation level. Use
`python -m oncodex plan A###` to inspect the exact frozen input before implementation or run.

Evaluation coverage currently ends at `retrospective_real`; `independent_real` and
`temporal_prospective` have no frozen protocols yet. `docs/EVALUATION.md` owns coverage, level
gates, compatibility, controls, and resource-accounting rules.

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
