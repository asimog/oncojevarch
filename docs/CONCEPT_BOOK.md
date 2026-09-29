# Concept book — nucleus

This document is deliberately shorter than the learning report that preceded the scaffold. It records the mental model agents need to navigate the code. Detailed learning belongs in `LEARNING_CURRICULUM.md`; experiments belong in `EXPERIMENT_CATALOG.md`.

## 1. Three-tier intelligence

```text
Tier 1  deterministic science  -> what was measured?
Tier 2  Jev                    -> what bounded semantic property does this state have?
Tier 3  OncoX                  -> what might explain it and what should be tested next?
```

Jev is not a measurement engine, hypothesis generator, prose engine, or replacement for OncoX.

## 2. Scientifically sufficient semantic projection

A scientific semantic projection is a deterministic, reproducible, question-specific representation derived from durable ScientificEvidence for bounded semantic judgment.

A **scientifically sufficient semantic projection** is the smallest such view that preserves the information needed for a particular judgment while excluding irrelevant context.

It is not a generic summary or a universal `CandidateSummary`.

Projection design starts from the semantic question, not the source database schema.

Protected information classes, when relevant, include population identity, entity level, source/version, measurement meaning, sample count, coverage, missingness, uncertainty, comparison/baseline, directionality, replication status, contradictions, and provenance.

### Projection tests

- **Ablation/sufficiency:** remove fields and measure loss.
- **Invariance:** change irrelevant details; judgment should remain stable.
- **Counterfactual sensitivity:** change scientifically material evidence; judgment should respond.
- **Distractor robustness:** add irrelevant fields and measure degradation.
- **Full vs projected state:** test whether projection improves or preserves quality while reducing cost/context.

## 3. Cheapest scientifically sufficient representation

At each step acquire or construct the least expensive information representation that can resolve the current uncertainty.

Conceptual ladder:

```text
schema/inventory
 -> metadata
 -> server-side filters/counts
 -> aggregates/summaries
 -> targeted small tables
 -> derived scientific representation
 -> bounded local computation
 -> large raw data only when justified
```

This is an information-acquisition policy, not merely a bandwidth optimization.

Value-of-information intuition:

```text
expected improvement in the next scientific decision - cost of acquiring information
```

The initial system does not need a formal VOI optimizer; it does need to record why richer information was requested.

## 4. Four search problems

1. **Information search** — what evidence or representation should be acquired next?
2. **Candidate search** — which biological states deserve deeper investigation?
3. **Explanation search** — what hypothesis best accounts for evidence and what would distinguish alternatives?
4. **Representation search** — what is the cheapest scientifically sufficient representation for the next decision?

## 5. Discovery must preserve uncertainty

The search frontier is not simply top-N by Jev score. A candidate may survive because of high promise, high uncertainty, novelty, contradiction, replication importance, or explicit exploration allocation.

Greedy pruning is a risk because later evidence cannot rescue discarded branches. Beam/frontier mechanisms are architecture hypotheses to test, not permanent defaults.

## 6. TypeSafe/Jev lessons to test

| Pattern/cookbook | Transferable OncoJev idea | Main risk |
|---|---|---|
| Self-consistency Noul/Choice | stability and threshold diagnostics | stability is not correctness |
| Parallel questions | independent semantic dimensions share one state/request | batching dependent questions |
| Re-ranking | cheap high-recall retrieval then semantic refinement | Jev cannot recover omitted candidates |
| Semantic find | relative Choice + absolute Noul | best-of-bad-options |
| Structure recovery | bounded semantic operations can recover structure | unnecessary AI where parser suffices |
| Function calling | semantic selection of typed handler/args | replacing deterministic routing |
| Skill suggestion | progressive disclosure over large registries | capability recall failure |
| Entity alignment | semantic identity when exact IDs do not exist | guessing over authoritative IDs |
| RAG passage classification | decompose vague evidence quality into dimensions | conflating literature with measured evidence |
| Citation check | deterministic identity + semantic support check | support check is not new experimental evidence |
| LLM guardrails | bounded semantic controls around agent behavior | treating control metadata as evidence |
| SDE cascade | cheap producer -> Jev verify -> selective deep reasoning | verifier false negatives |
| Date extraction | semantic extraction + deterministic normalization | core bloat for supporting task |
| Pre-parsed extraction | enumerate/select/normalize rather than generate | candidate-set incompleteness |
| Hierarchical classification | beam search over semantic probabilities | cost without recall gain |
| Autoresearch feature discovery | offline discovery of useful semantic questions | semantic overfitting/self-promotion |
| Classification with confidence | reduce specificity/escalate under uncertainty | global threshold misuse |
| Speculative fan-out | ask useful independent branch questions early | wasted tokens/premise violations |
| Confidence-gated routing | answer and confidence are separate policy inputs | confidence mistaken for permission |
| Composite scoring | expose multiple dimensions, optionally combine later | arbitrary scientific utility score |
| Intent routing | map ambiguous need to bounded handler | unnecessary semantic routing |

## 7. Capability evolution

Dynamic composition means selecting existing validated capabilities. Capability evolution begins only when a real gap exists.

```text
MethodGap     -> methodological/scientific research
CapabilityGap -> engineering implementation of a known method
DecisionGap   -> projection + Jev contract + evaluation
HarnessGap    -> runtime/harness engineering
```

Generated code or prompts never self-promote.

## 8. Evaluation ladder

```text
synthetic mechanics
 -> semi-synthetic signal recovery
 -> retrospective real-data rediscovery
 -> independent compatible validation
 -> temporal/prospective validation where feasible
```

Only real-data levels meaningfully test scientific discovery.

The full system comparison is A/B/C, but component ablations should precede it.
