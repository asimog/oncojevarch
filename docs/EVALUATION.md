# Evaluation strategy

## Scope

Evaluation answers two different questions and must not conflate them:

- **architecture evaluation** — does OncoJev work as designed (mechanics, reliability, cost)?
- **scientific evaluation** — does it produce useful cancer discovery (real biological signal)?

Architecture success is not scientific validation. Synthetic success validates mechanics only.

## Current coverage

| Level | Meaning | Experiments | Status |
|---|---|---|---|
| 0 | synthetic | A001-A010, A013-A018 | executed; mechanics and component ablations only |
| 1 | semi-synthetic | A011, A012 | executed; A012 negative (triage escalated every case, no OncoX saved) |
| 2 | retrospective real data | A019, A020 | executed; A019 missed its frozen target (no leakage), A020 moved no frontier |
| 3 | independent real-data validation | none | declared in `evaluation/models.py`; no frozen protocol or runner |
| 4 | temporal/prospective | none | declared in `evaluation/models.py`; no frozen protocol or runner |

Executed coverage reaches Level 2. Levels 3 and 4 are named but not covered: nothing above
retrospective real data has a protocol, runner, or recorded result.

### Executed level is not scientific readiness

- The evaluation machinery has exercised L0-L2. That is not scientific readiness.
- OncoJev has **not** demonstrated successful scientific cancer-discovery validation through L2.
- A019 is a retrospective-real architecture evaluation that missed its frozen rediscovery target.
- A020 is a frontier analysis over recorded experiment results, not a new prospective run.
- L3/L4 remain unexecuted; no compatibility contract or temporal protocol has been frozen.

## Synthetic is not scientific validation

Synthetic data can test contracts, missingness propagation, recovery, projection fingerprinting, search mechanics, failure modes, and deliberately planted signals. It cannot establish that Jev recognizes useful cancer biology or improves real candidate discovery.

## Evaluation ladder

Each level is an entry gate for the next. A level's result is recorded before the next level
starts, and a level's failures produce a new experiment identity rather than an edit of the old one.

### Level 0 — synthetic

Engineering/architecture validation only. Entry: the mechanism can be tested without biological
claims.

Exit gate:

- frozen fixtures;
- success cases and failure cases (not only success paths);
- deterministic replay reproduces decisions and metrics;
- recorded metrics;
- resource accounting where appropriate;
- mechanical invariants (architecture checks/tests).

L0 cannot validate cancer biology.

### Level 1 — semi-synthetic

Real biological background with controlled implanted signal, null, or corruption.

Relevant dimensions may include: signal strength; noise; missingness; subgroup size; ambiguity;
broken associations; negative controls. L1 is not defined by any required modality: the scientific
question determines what data are relevant.

Exit gate: planted signal is recovered at the frozen rate; null/shuffled controls fall to the
frozen null rate; planted-label leakage is audited.

### Level 2 — retrospective real-data rediscovery

First meaningful scientific A/B/C level. Use historical real data; keep historical known findings
out of the research inputs and freeze arm outputs before unblinding the evaluation set.

Requirements:

- real scientific question;
- explicit population;
- source and version;
- identity semantics;
- frozen candidate/search universe;
- methods and capabilities;
- assumptions;
- labels/outcomes;
- leakage control;
- null/control design;
- false-negative accounting;
- multiplicity policy;
- frozen thresholds and budgets;
- reproducibility;
- full resource accounting.

L2 is defined epistemically, not by dataset type: mutation, expression, CNV, or any other modality
is neither required nor implied.

Exit gate: identifiers masked (or leakage otherwise excluded); null control at chance; no leakage
finding; prespecified target met. A missed target is a recorded negative result that narrows the
thesis; a retest with a different representation or relationship is a new experiment identity
(as A019 requires).

### Level 3 — independent validation

Freeze candidates from discovery data and test in an independent scientifically compatible
dataset. Compatibility of populations, assays, measurements, normalization, and methods must be
explicit (see the compatibility contract below).

Gate: the independent evaluation completes with the frozen metric set, thresholds, and arm
definitions; metric or arm changes after result exposure create a new experiment identity. The
independent validation set must not tune the discovery policy.

### Level 4 — temporal/prospective

Require a frozen T1 state:

```text
scientific question
candidate/prediction
source cutoff
capabilities/models
policy
evaluation criteria
outcome definition
```

Then evaluate using genuinely later T2 information. T1/T2 cutoffs are fixed by data versions, not
analyst choice, and candidates are frozen before T2 data is examined.

Prospective shadow mode is allowed: T1 frozen decision -> no research intervention -> future
outcome arrives -> immutable join -> evaluation.

## Compatibility contract (Level 3)

A dataset is "compatible" only relative to a declared contract. Review, where relevant:

- scientific population; disease/question definition; inclusion/exclusion;
- entity identity;
- measurement definition; assay/platform;
- preprocessing/normalization; feature availability;
- covariates;
- missingness;
- endpoints; follow-up;
- statistical estimand; method;
- multiplicity policy;
- source/version;
- batch/site/distribution shifts;
- capability applicability.

Any mismatch is declared and carried as a bounded limitation; unstated compatibility is a claim,
not a finding.

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

### Fair comparison under capability evolution

Capability evolution is a potential confound. A/B/C comparisons must not give one arm better
scientific tools because that arm triggered more capability evolution. For a mature frozen
comparison keep constant: scientific task; population; data access; source versions; deterministic
scientific capabilities; candidate universe; validated capability registry; resource-accounting
rules; outcome labels. Vary only the decision architecture of A, B, and C.

If capability evolution itself is being evaluated, that is a separate experiment with its own
identity. Do not mix the two hypotheses.

### Resource accounting

- count every arm-specific cost; arm C includes its Jev screen and any triage overhead (A020's
  first extraction under-counted exactly this and was corrected before the result was recorded);
- record, where available: source bytes/records; deterministic compute; wall time; storage;
  Jev calls, input/output tokens, latency; OncoX calls, input/output tokens, latency; retries;
  repetitions;
- monetary cost is reported only when measured or reproducibly derived; never invented from token
  counts;
- extract frontier points from immutable recorded results, per task, never in aggregate;
- dominance requires no more resource, no less quality, and a strict gain on at least one axis.

## Component ablations before full A/B/C

- deterministic ranking vs deterministic + Jev reranking;
- Choice vs Choice + absolute-viability Noul;
- greedy vs beam/frontier search;
- full state vs question-specific projection;
- no exploration vs uncertainty/novelty exploration;
- OncoX on all cases vs Jev-screened selective OncoX;
- fixed Jev questions vs offline evaluated discovered questions;
- normal vs null/shuffled controls.

## Controls

Consequential semantic/scientific evaluations declare applicable controls:

- null control;
- shuffled/permuted labels;
- broken associations;
- randomized candidate identities;
- negative-control populations/features;
- deterministic-only baseline;
- semantic-layer ablation.

Controls are required from Level 1 upward. A null arm above the frozen null rate is a failure, not
a metric. Each null family uses fixed seeds; instability across seeds is itself a recorded finding.
Null outputs that remain persuasive count against the system.

## Leakage

Model-pretraining leakage is a major threat: an LLM may already know famous published findings. Mitigations/diagnostics may include masked identifiers, uncommon relationship tasks, restricted literature access, newer releases, semi-synthetic controls, and future/independent validation.

Leakage review considers: identifiers; outcomes; future data; literature; model training
familiarity; prompt/context; derived target-encoding features; adaptive modifications after result
exposure.

Operational audit for any Level 2+ rediscovery claim:

- mask identifiers, names, sites, and disease types from every arm input;
- audit every arm input for label tokens and near-duplicates;
- run a deranged-label null control;
- prefer uncommon or held-out relationships over famous published ones;
- freeze literature access where the claim depends on literature-derived targets;
- confirm survivors on a newer release or independent dataset.

## Multiplicity and adaptive-search claims

Scientific discovery that searches many candidates, variables, subgroups, hypotheses, endpoints,
or semantic features creates adaptive-selection/multiplicity problems.

Declare at freeze time whether the experiment is:

```text
CONFIRMATORY        prespecified multiplicity handling required
EXPLORATORY         held-out/independent confirmation required before confirmatory language
ADAPTIVE_DISCOVERY  must retain search history and the tested universe
```

When the object is novel discovery rather than rediscovery, precision depends on how many
candidates the search examined; report per-stage candidate counts so any claim can be discounted
for search size. Jev confidence is not a p-value; OncoX plausibility is not multiplicity
correction.

Future experiments declare the mode inside the existing `inputs` field of `ExperimentSpec`; no
spec schema change is made retroactively.

## Pre-register metrics before result exposure

Candidates include scientific recall/precision, known-signal rediscovery, held-out replication, contradiction discovery, false-negative burden, candidate stability/diversity, bytes transferred, deterministic compute, Jev calls/tokens, OncoX calls/tokens, time-to-candidate, cost per viable Investigation, and reproducibility.

Do not invent the winning metric after seeing results.

## Freezing and identity

Freeze and fingerprint where applicable: question; hypothesis; experiment class; evaluation level;
population; source/version; capabilities; methods; candidate universe; projections; Jev
model/capability; OncoX configuration; thresholds; budgets; controls; metrics; multiplicity;
failure/stop rules.

- freeze protocol, arms, metrics, and thresholds before material results are exposed;
- freeze arm outputs before unblinding the evaluation set at Level 2+;
- record immutable results; no history rewriting;
- corrections are appended with provenance; material post-result changes create a new experiment
  identity (epistemic constitution #12);
- state in every recorded result whether it is rediscovery, replication, or novel discovery.

## Next step

The next scientific milestone is capability-neutral: use the autonomous harness on a scientifically
meaningful investigation in which OnCodex determines what information is required, searches for
applicable capabilities, exposes gaps, and evolves only justified capabilities (see README
"Current phase"). No level beyond L2 may be claimed until its protocol is frozen and executed.

## Open gaps

- no Level 3 or Level 4 protocol exists; the level names in `evaluation/models.py` are declarative
  until a frozen protocol exists;
- no compatibility-contract artifact exists yet for a Level 3 dataset;
- the multiplicity mode declaration is documented but not yet enforced by a catalog field;
- level entry/exit gates are reviewed by reading, not mechanically enforced end-to-end;
- evidence admission (`MeasuredResult -> ScientificEvidence`) has no implemented owner yet; the
  next milestone will need it.
