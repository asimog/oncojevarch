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

## 4. Five search problems

1. **Information search** — what evidence or information should be acquired next?
2. **Representation search** — what is the cheapest scientifically sufficient representation for the next decision?
3. **Capability search** — what validated capability can obtain, measure, transform, or judge the required information?
4. **Candidate search** — which scientific states deserve deeper investigation?
5. **Explanation search** — what explanation accounts for the evidence, and what observation would distinguish alternatives?

Capability search is distinct from candidate search: one finds the instrument, the other finds the objects worth investigating. When capability search fails, an explicit gap triggers capability evolution.

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

### Capability search

The question that precedes capability evolution: what validated scientific or operational capability can produce the information required by the next decision?

OnCodex discovers capabilities from scientific needs, not from a fixed catalogue of modalities. Biological modalities are examples of scientific information, not permanent orchestration lanes.

The architecture must be able to absorb scientific measurements that were not anticipated when the repository was created. Capability evolution is infrastructure around the three-tier model, not Tier 4.

The current mechanism is deterministic token-overlap search over typed summaries; it was evaluated
and repaired once by A022/A025 and is an initial mechanism, not established retrieval architecture.
`CapabilityRecord` metadata supports discovery; it is not the typed scientific capability
contract, which remains to be earned.

## 8. Evaluation ladder

```text
synthetic mechanics
 -> semi-synthetic signal recovery
 -> retrospective real-data rediscovery
 -> independent compatible validation
 -> temporal/prospective validation where feasible
```

Only real-data levels meaningfully test scientific discovery.

Executed coverage currently reaches retrospective real data (A019-A020); independent and temporal levels have no frozen protocols yet. `EVALUATION.md` owns coverage, level gates, and compatibility.

The full system comparison is A/B/C, but component ablations should precede it.

## 9. Earned lessons (A001-A020)

Durable architecture lessons from recorded results; none is a biological claim.

1. question-specific deterministic projections beat giant context (A003-A004);
2. irrelevant state can impose cost or degrade semantic performance (A004);
3. use the cheapest scientifically sufficient representation (A005);
4. deterministic high-recall retrieval precedes semantic reranking (A006);
5. Jev cannot rescue candidates eliminated upstream (A006);
6. relative selection does not imply absolute adequacy (A007);
7. uncertainty-preserving search can beat irreversible greedy pruning (A008);
8. exploration has legitimate scientific value (A009);
9. rejected-candidate audits reveal search false negatives (A010);
10. null controls are necessary for semantic components (A011);
11. model upgrades require contract-specific regression evaluation (A013);
12. semantic feature discovery can overfit (A014, negative);
13. gap routing and no-self-promotion are testable governance (A015);
14. bounded context must earn its value (A016, negative);
15. durable idempotent operations matter for autonomy (A017);
16. architecture changes should be bounded and evidence-traceable (A018);
17. cheap representations can be scientifically insufficient (A019, negative);
18. the tested Jev-to-OncoX cascade did not establish savings (A012, negative);
19. A020 did not demonstrate a combined-arm frontier shift on recorded tasks;
20. negative results narrow architecture rather than cause arbitrary redesign.

### Recorded additions (A021-A025, S001-S002)

21. an admission gate must refuse absent values rather than zero them (A021);
22. a mechanism that fails its own frozen rule is reopened; repairs need new identities (A022, A025);
23. pinned mechanisms keep recorded results reproducible when production code changes (A022);
24. gaps route correctly only when their kind is declared honestly (A023);
25. session-independent state is a precondition for agent-driven research (A024);
26. frozen thresholds must fit the real population; failures are recorded, not edited (S001, S002).
