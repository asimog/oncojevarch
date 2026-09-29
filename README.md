# OncoJev

OncoJev is an experiment-driven autonomous computational cancer-discovery system.

**Status:** architecture-experiment harness with A001-A020 executed. This is deliberately not a complete autonomous lab and makes no scientific discovery claims.

## Scientific thesis

Can deterministic scientific computation + high-throughput typed semantic judgment (Jev) + selective deep scientific reasoning (OncoX) improve scientifically useful discovery per unit compute, data transfer, wall-clock time, and expensive reasoning?

```text
A = deterministic scientific system
B = deterministic + selective OncoX
C = deterministic + bounded evaluated Jev + selective OncoX
```

The main question is whether C shifts the science-efficiency frontier. This is a falsifiable hypothesis, not a premise the architecture may guarantee. See `THESIS.md`.

## Harness strategy

```text
scientific uncertainty
  -> what information would reduce it?
  -> what representation is sufficient?
  -> what capability can produce or evaluate it?
  -> capability search
  -> applicable validated capability?
       yes -> execute -> new ScientificEvidence
       no  -> explicit gap -> classify -> evaluated capability evolution -> versioned capability
```

Capability evolution is infrastructure around the three scientific tiers, never a fourth tier. The architecture should not need modification merely because a new scientific measurement type becomes useful. See `ARCHITECTURE.md` and `docs/CAPABILITY_EVOLUTION.md`.

## Current phase

A001-A020 tested architecture hypotheses and are recorded in `docs/EXPERIMENT_CATALOG.md`; several narrowed or rejected their candidate capabilities (A012, A014, A016, A019, A020). The next phase is not "build a fixed cancer pipeline." It is:

> Use the autonomous harness on scientifically meaningful investigations in which OnCodex determines what information is required, searches for applicable capabilities, exposes gaps where capabilities are absent, evolves only justified capabilities, and uses the three-tier intelligence system where appropriate.

The scientific question determines the source, measurements, methods, capabilities, semantic questions, and follow-up reasoning. The architecture does not. The reviewed task program for this phase is tracked in `docs/tasks/`.

## Mental model

```text
OncoJev = whole system

OnCodex   = autonomous research agent / evolving harness
OncoLab   = durable scientific substrate and constraints
Discovery = search
Execution = measurement
Jev       = bounded typed semantic judgment
OncoX     = selective deep scientific reasoning
Store     = durable scientific memory
Observatory = read-only view
```

The scaffold implements the boundaries, durable experiment records, capability/gap lifecycle,
semantic projection contract, minimal search frontier, append-only store, and the architecture
mechanisms exercised by A001-A020. Several candidate capabilities were rejected or narrowed by
those experiments; see `docs/EXPERIMENT_CATALOG.md` for recorded outcomes.

## Why it is small

The repository follows an experiment-driven rule:

```text
experiment -> limitation -> capability need -> smallest justified implementation -> verification
```

Do not prebuild the mature architecture.

## Quick start

Python 3.11+ is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python scripts/verify.py
python -m oncodex status
python -m oncodex experiments
python -m oncodex plan A001
```

Optional integrations:

```powershell
python -m pip install -e ".[agents,jev,dev]"
```

Copy `.env.example` to `.env.local` and fill it locally. OnCodex reads that file without
overwriting process environment variables and never prints credential values.

## Initial experiments

### A001 — OnCodex / Codex workspace smoke

Preflight only:

```powershell
python -m oncodex run A001
```

Live mode (requires Agents SDK/provider/Codex configuration):

```powershell
python -m oncodex run A001 --live
```

A001 keeps the experimental Agents SDK `codex_tool` behind a narrow adapter. Its workspace sandbox is read-only by default.

### A002 — Jev primitive semantics

Offline contract smoke:

```powershell
python -m oncodex run A002
```

Live TypeSafe call:

```powershell
python -m oncodex run A002 --live
```

A002 is an architecture experiment. Its demo fixture does not validate cancer biology.

### A003 — semantic projection sufficiency

```powershell
python -m oncodex run A003
```

The included cases are synthetic and test only projection mechanics. Real labeled biological cases are required before scientific conclusions.

### A004 — full state versus question-specific projection

Freeze and inspect the paired synthetic evaluation:

```powershell
python -m oncodex run A004
```

Execute both arms against the pinned Jev model:

```powershell
python -m oncodex run A004 --live
```

A004 records raw paired decisions and probabilities plus accuracy, arm agreement, serialized
bytes, tokens, and latency. One synthetic run is an architecture measurement, not validation.

### A005 — cheapest sufficient GDC representation

Freeze the acquisition ladder:

```powershell
python -m oncodex run A005
```

Query only public GDC metadata, facets, and `size=0` counts:

```powershell
python -m oncodex run A005 --live
```

A005 uses deterministic set arithmetic to decide whether a richer representation resolves paired
case availability. It does not download case records or molecular files and does not use Jev for
exact counting.

### A006 — deterministic ranking versus Jev reranking

Freeze the project-metadata ranking task:

```powershell
python -m oncodex run A006
```

Run three repetitions against one small public GDC metadata slice and the pinned Jev model:

```powershell
python -m oncodex run A006 --live
```

A006 fixes shortlist membership with deterministic retrieval. Jev may select only the first-ranked
candidate; it cannot introduce a project omitted upstream. The task evaluates metadata matching,
not cancer biology.

### A007 — Choice plus absolute-viability Noul

```powershell
python -m oncodex run A007
python -m oncodex run A007 --live
```

A007 compares forced relative selection with a separate absolute adequacy gate over viable and
best-of-bad-options GDC project-description tasks. The gate is evaluated independently; it does
not turn a semantic judgment into scientific evidence.

### A008 — greedy versus bounded beam search

```powershell
python -m oncodex run A008
```

A008 replays six locked probability trees through beam widths 1, 2, and 3. It uses a
length-normalized geometric-mean path score, records every evaluated edge, and keeps synthetic
search-mechanics evidence separate from biological validation.

### A009 — top score versus exploration allocation

```powershell
python -m oncodex run A009
```

A009 compares four top-promise slots with an equal-budget allocation of two promise, one
uncertainty, and one novelty slot. Outcome labels are locked for evaluation and unavailable to
the allocator.

### A010 — rejected-candidate audit

```powershell
python -m oncodex run A010
```

A010 freezes historical decisions before joining later outcomes, then takes an outcome-blind,
stage-balanced rejection sample. Audit findings append a new evaluation view and never rewrite
the decision log.

### A011 — null and broken-association controls

```powershell
python -m oncodex run A011
python -m oncodex run A011 --live
```

A011 pairs masked histology tasks with a five-project GDC metadata slice, then compares the valid
pairing with three no-fixed-point derangements. Python generates controls and thresholds claims;
Jev supplies only independent Noul probabilities.

### A012 — Jev triage versus OncoX on every case

```powershell
python -m oncodex run A012
python -m oncodex run A012 --live
```

A012 locks ten cases built from real GDC project aggregates, five whose recorded structured state
already resolves the claim's material question and five that stay open, then compares OncoX on
every case with a Noul-triaged cascade. The frozen result was negative: bounded triage escalated
every live case, so it saved no OncoX calls; the cascade is not supported for this contract and the
rubric mechanics, adapter, and false-negative accounting are retained.

### A013 — Jev model-version regression

```powershell
python -m oncodex run A013
python -m oncodex run A013 --live
```

A013 rebuilds the A011 coherence capability, refuses to run if its projection fingerprint changed,
reads the recorded `jev-1.13.0` baseline back from the append-only store, re-runs that model as a
control, and scores `jev-preview` against frozen claim-rate, agreement, drift, and calibration
tolerances. The candidate was approved for that contract only.

### A014 — offline feature discovery and locked cases

```powershell
python -m oncodex run A014
python -m oncodex run A014 --live
```

A014 runs deterministic lexical feature discovery on a development split, gate it through one
batched Jev endorsement call, and score the survivors on a frozen locked test against a baseline
feature set. The frozen result was negative: discovery selected positional corpus artifacts, Jev
endorsed none of them, and nothing was promoted.

### A015 — gap routing and promotion guarding

```powershell
python -m oncodex run A015
```

A015 replays ten representative and four adversarial gap scenarios through a one-keyword baseline
and combined-signal routing with kind-owned guards, driving the real capability registry for each
promotion attempt. Combined-signal routing matched every scenario with zero unsafe activations.

### A016 — bounded progressive context

```powershell
python -m oncodex run A016
python -m oncodex run A016 --live
```

A016 compares replaying a raw investigation history with a deterministic bounded view that pins the
latest fact values, prunes superseded messages, and records every dropped id. Bounded context was
not adopted: success was unstable across repetitions and token savings were dominated by the fixed
instruction block.

### A017 — interrupted work and idempotent resume

```powershell
python -m oncodex run A017
```

A017 runs a six-step deterministic operation over the append-only store under injected
interruptions. Artifact identity is stable per operation step, so interrupts and resumes reach the
same final digest with six artifacts and zero duplicate writes.

### A018 — bounded reviewable change proposals

```powershell
python -m oncodex run A018
```

A018 compiles two change requests from the recorded A012 finding: a bounded, fully traced proposal
and an unbounded rewrite. It applies the bounded patch only in a scratch copy, runs compilation,
focused tests, and architecture checks there, and records the proposal for human review.

### A019 — masked real-data rediscovery

```powershell
python -m oncodex run A019
python -m oncodex run A019 --live
```

A019 masks eleven TCGA projects into identifier-free aggregate profiles, ranks candidate primary
sites deterministically, screens the ambiguous cases with one batched Noul call, and re-ranks
escalated cases with OncoX, with a deranged-label null control. The frozen target was missed
(recall@1 0.273 against a 0.50 target and 0.20 chance) with no leakage finding.

### A020 — science-efficiency frontier

```powershell
python -m oncodex run A020
```

A020 extracts frontier points from immutable recorded results (A012 cascade arms, A019 rediscovery
arms), computes per-task Pareto dominance, and reports whether the combined arm moves the frontier.
It did not: the central hypothesis is narrowed, with the Jev layer's recorded value kept in gating
and reranking rather than selective OncoX triage.

## Architecture experiment protocols

A001-A020 are complete declarative protocols, and every protocol currently has a runner.
Inspect any frozen protocol with:

```powershell
python -m oncodex plan A020
```

A019-A020 evaluate under frozen real-data protocols against versioned GDC-derived inputs and
recorded immutable results. A negative or missed target is a recorded finding, not a missing
capability.

## Provider configuration

OnCodex model choice is an edge concern, not a domain invariant. When `OPENROUTER_API_KEY`
and `LLM_MODEL` are configured, the Agents SDK uses an OpenAI-compatible chat-completions
model pointed at OpenRouter. The experimental Codex workspace tool remains separately isolated
behind `oncodex.codex_workspace` and uses Codex authentication/configuration.

The Codex workspace tool deliberately does not override Codex's own model/provider configuration unless explicitly configured later.

## Repository map

```text
AGENTS.md                     agent map
THESIS.md                     falsifiable thesis
ARCHITECTURE.md               boundaries and dependency rules
oncodex/                      autonomous harness integration
oncolab/                      legality, gaps, capabilities, experiment identity
research/                     scientific story objects
evidence/                     ScientificEvidence and semantic projections
discovery/                    search-frontier contracts
execution/                    deterministic measurement ports
jev/                          typed semantic instrument contracts/adapters
oncox/                        deep-reasoning boundary
evaluation/                   evaluation contracts and A/B/C design
store/                        generic append-only persistence
observatory/                  read-only projections
experiments/architecture/     A001–A020 implementations
experiments/scientific/       intentionally empty except guidance
docs/                         durable project knowledge
docs/tasks/                   reviewed task definitions for the current program
docs/exec-plans/              execution plans (active and completed)
tests/                        mechanical invariants
scripts/                      verification and architecture checks
```

## Non-goals of this scaffold

Not yet implemented: a scientific GDC/GDAN analysis pipeline, a full Observatory, a persistent
database schema, an automated capability-evolution service, or production UI/DB complexity before
it is needed.

Deliberately avoided by design: hardcoded modality lanes; fixed modality enumeration in core;
source-specific "GDCScience"-style architecture; permanent Jev question batteries; global Jev
thresholds; capability self-promotion; uncontrolled method invention; multi-agent swarms; RL; a
generic workflow engine.

Not a non-goal: real-data scientific evaluation. A020 was a recorded A/B/C frontier analysis over
recorded results, and the next milestone is the first capability-neutral scientific investigation.
The current GDC adapter remains intentionally limited to read-only public metadata. Real open
cancer data enters through source adapters; the core stays source and modality agnostic.
