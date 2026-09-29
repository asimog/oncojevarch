# Architecture

## Principle

Keep epistemic rules stable; let capabilities evolve.

## Runtime roles

### OnCodex

Top autonomous research agent and evolving harness built around the OpenAI Agents SDK. It decides what to work on, invokes tools/capabilities, adapts, branches, backtracks, and runs architecture or scientific experiments.

The experimental Agents SDK `codex_tool` is an optional workspace/coding capability behind a narrow adapter. It is not a domain dependency.

### OncoLab

Durable laboratory substrate. Owns experiment identity, capability lifecycle/readiness, gaps, budgets, legality, evidence admission policy, operation identity, recovery rules, and durable history.

OnCodex chooses and acts. OncoLab constrains, validates, and remembers.

### Discovery

Search subsystem. Owns frontiers, branches, candidate states, exploration reasons, reranking/search policies, and search history. It does not manufacture ScientificEvidence or mechanisms.

### Execution

Deterministic acquisition and measurement boundary. It may return measured results; OncoLab decides whether those results satisfy admission requirements to become ScientificEvidence.

### Jev

Shared typed semantic infrastructure. The shared layer owns invocation and primitive/result mechanics; domains own question semantics, projections, applicability, thresholds, and policy.

### OncoX

Selective deep scientific reasoner. It may create interpretations, hypotheses, alternatives, predictions, and proposed discriminating experiments. It may not create measured evidence.

### Store

Generic persistence only. It must not contain scientific decision policy.

### Observatory

Read-only projection over durable state.

## Epistemic direction

```text
source data
  -> deterministic measurement
  -> ScientificEvidence
  -> deterministic semantic projection
  -> JevDecision
  -> policy / frontier
  -> selective OncoX reasoning
  -> hypothesis / proposed experiment
  -> frozen experiment
  -> deterministic execution
  -> new ScientificEvidence
```

## Experiment classes

Only two:

- `ARCHITECTURE`: tests OncoJev itself and may justify architecture changes.
- `SCIENTIFIC`: tests biological/scientific hypotheses and may update research evidence.

No third "harness experiment" class.

## Dependency intent

Core scientific data types should sit low in the graph. External SDKs are leaf adapters.

Allowed conceptual direction:

```text
evidence <- execution
   ^          ^
   |          |
   +------ oncolab
             ^
             |
          oncodex

jev contracts <- domain-owned projections
oncox ports   <- oncodex orchestration
store         <- generic serialized events only
```

Mechanical checks intentionally forbid obvious inverse dependencies such as `evidence -> oncodex`, `execution -> oncox`, or `store -> discovery`.

## Capability evolution

```text
Need
 -> classify gap
 -> MethodGap | CapabilityGap | DecisionGap | HarnessGap
 -> appropriate research/development path
 -> evaluation
 -> versioned promotion
 -> bounded activation
```

Dynamic composition of existing capabilities is routine. Creating a new capability is a governed lifecycle.

## What is intentionally absent

- source-specific core types;
- full data pipelines;
- permanent Wide/Deep Jev batteries;
- autonomous code self-promotion;
- RL;
- a generic `harness/` package;
- a nested `oncojev/oncojev/` package topology;
- a production UI.
