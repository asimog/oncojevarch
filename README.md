# OncoJev scaffold

An experiment-first scaffold for an autonomous computational cancer-discovery laboratory.

**Status:** architecture-experiment harness. This is deliberately not a complete autonomous lab and makes no scientific discovery claims.

The project begins with a falsifiable question: can deterministic scientific computation + high-throughput typed semantic judgment + selective deep scientific reasoning improve scientifically useful discovery per unit compute? See `THESIS.md`.

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

The scaffold intentionally implements only the boundaries, durable experiment records,
capability/gap lifecycle, semantic projection contract, minimal search frontier, append-only
store, and the architecture capabilities earned by A001-A006.

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

## Architecture experiment protocols

A001-A020 are complete declarative protocols. Inspect any frozen protocol with:

```powershell
python -m oncodex plan A020
```

Only A001-A006 currently have runners. A007-A020 are deliberately plan-ready rather than
pretending that required data, capabilities, or scientific results already exist.

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
experiments/architecture/     A001–A006 implementations
experiments/scientific/       intentionally empty except guidance
docs/                         durable project knowledge
tests/                        mechanical invariants
scripts/                      verification and architecture checks
```

## Non-goals of this scaffold

It does not yet implement a scientific GDC/GDAN pipeline, cancer-specific modalities in core,
mutation/expression/CNV analysis, a full Observatory, a persistent database schema, RL,
multi-agent swarms, permanent Jev question batteries, automatic code promotion, or a scientific
A/B/C benchmark. The current GDC adapter is intentionally limited to read-only public metadata.

Real open cancer data should enter early, but through source adapters after projection/Jev mechanics are understood; the core must remain source and modality agnostic.
