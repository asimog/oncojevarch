# Learning curriculum

This is the concept sequence to work through before expanding OncoJev. For each module, the exit criterion is intentionally practical.

| # | Topic | Why it matters | Exit criterion |
|---:|---|---|---|
| 1 | Epistemic object types | prevents evidence/judgment/hypothesis collapse | classify examples correctly |
| 2 | Minimal molecular biology | enough semantics to avoid invalid assumptions | explain gene/variant/CNV/expression/pathway/outcome |
| 3 | Biological entity identity | cross-modal joins depend on identity level | explain case vs sample vs aliquot vs file |
| 4 | Cohorts/populations | discovery claims belong to populations | construct an explicit PopulationSpec |
| 5 | Missingness | missing is scientific information | distinguish unknown/absent/zero/failure |
| 6 | Scientific inference basics | agents must not invent inferential meaning | explain estimand/effect/uncertainty/confounding |
| 7 | Validation/leakage | adaptive discovery can fool itself | identify dev/test/temporal leakage |
| 8 | Search/retrieval | OncoJev is a search system | explain recall@K and reranking |
| 9 | Greedy vs beam | early pruning can be irreversible | trace a beam search by hand |
| 10 | Exploration/exploitation | novelty may score poorly early | design one exploration control |
| 11 | Decision theory | more information has a cost | explain value-of-information intuition |
| 12 | System One/Jev model | bounded semantic computation | map tasks to code/Jev/OncoX |
| 13 | Choice | relative bounded selection | spot best-of-bad-options failure |
| 14 | Noul | probability a condition holds | distinguish probability from intensity |
| 15 | Score | ordered semantic rubric | write standalone ordered criteria |
| 16 | Confidence/calibration | confidence is not permission | explain high-confidence wrong cases |
| 17 | Jev state design | state controls semantic quality | remove irrelevant/indirect fields |
| 18 | Semantic projection | core OncoJev research problem | define a question-specific projection |
| 19 | Projection evaluation | sufficiency must be measured | run ablation/invariance/counterfactual tests |
| 20 | Cheapest representation | control data/context cost | choose metadata vs aggregate vs raw correctly |
| 21 | Value of information | governs acquisition | justify one richer-data request |
| 22 | Parallel questions | independent dimensions can share state | identify dependent vs independent questions |
| 23 | Speculative fan-out | branch questions can be prefetched | state branch premises explicitly |
| 24 | Semantic reranking | high-recall cheap search + semantic refinement | design shortlist recall test |
| 25 | Relative + absolute judgment | ranking != adequacy | combine Choice and Noul appropriately |
| 26 | Hierarchical search | search large semantic taxonomies | compare K=1 and K>1 |
| 27 | Progressive disclosure | large registries should not flood context | design summary->detail lookup |
| 28 | Entity alignment | some identities are semantic | know when exact IDs must dominate |
| 29 | Semantic evidence routing | "good evidence" is multidimensional | decompose relevance/support/conflict |
| 30 | Citation verification | OncoX claims need source support | separate citation support from new evidence |
| 31 | Verification cascades | save expensive reasoning | design producer->Jev->OncoX cascade |
| 32 | Select-not-generate | bounded outputs are inspectable | enumerate candidate set before judgment |
| 33 | Function/capability routing | semantic routing is sometimes useful | avoid it when exact state determines route |
| 34 | Composite scoring | utility models embed assumptions | preserve raw dimensions before weighting |
| 35 | Self-consistency | stability diagnostic | explain why stable != correct |
| 36 | Semantic feature discovery | evolve useful Jev distinctions offline | define dev/validation/locked test split |
| 37 | MethodGap | not all missing ability is coding | route a method uncertainty correctly |
| 38 | CapabilityGap | known method lacks implementation | write an engineering task boundary |
| 39 | DecisionGap | bounded semantic distinction missing | specify projection + JevEval route |
| 40 | HarnessGap | runtime ability missing | distinguish runtime from science gap |
| 41 | Engineering promotion | self-generated code needs governance | trace task->verification->Git identity->promotion |
| 42 | Scientific readiness | tested code may be invalid science | state validated domain/assumptions |
| 43 | Capability registry | capabilities need applicability/version | inspect capability without loading everything |
| 44 | Hypothesis science | plausible prose is not a testable hypothesis | write prediction + discriminating test |
| 45 | Investigation model | science spans many operations | reconstruct one evidence/hypothesis story |
| 46 | Dossier/reproducibility | final artifact must be auditable | reproduce inputs/method/version lineage |
| 47 | Agent harnesses | do not reinvent generic loops | explain Agents SDK vs OncoLab responsibilities |
| 48 | Agent vs lab substrate | cognition != scientific memory | delete session and retain research state |
| 49 | Long-running reliability | autonomy needs resume/idempotency | recover without duplicate evidence |
| 50 | Evaluation design | architecture needs falsification | pre-register baseline/control/metrics |
| 51 | Real-data A/B/C | tests central thesis | specify leakage-resistant real-data protocol |
| 52 | Harness engineering | repository must be agent-legible | navigate via AGENTS + docs + mechanical checks |

## Suggested study method

For each module: read primary material, write one plain-language explanation, complete one tiny exercise, record one OncoJev failure it prevents, and do not turn the concept into architecture until an experiment needs it.
