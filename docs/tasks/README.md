# Evidence-gated program (9 tasks)

Status: Tasks 1-5 complete; Tasks 6-7 wired and live-verified at the runtime level; Tasks 8-9
remain gated. See `docs/exec-plans/completed/0003-abc-agent-runtimes.md` for the latest evidence.
Created: 2026-09-30
Base commit: `711824f`
Execution record: `docs/exec-plans/completed/0002-evidence-gated-nine-task-program.md`

These nine tasks replace the former 41-file task program. Each task proves a capability or
resolves a question; none specifies files to edit. Every task states its evidence gate: a task may
only proceed when the previous task's outcome justifies it. Gated tasks that were not triggered
are recorded as such with the exact trigger that would open them.

---

## Task 1 — Establish the executable scientific nucleus

**Status: COMPLETE.**
Goal: one investigation progresses question → required operation → measured result → admitted
ScientificEvidence → revised investigation, without Jev or OncoX.
Depends on: nothing.
Evidence gate: none; this is the base of the chain.
Implemented: `oncolab/admission.py` (deterministic admission gate: method identity, matching
population, provenance, present measurement; `None` is refused, never zeroed),
`research/state.py` (monotonic investigation revision), `research/ledger.py` (append-only
investigation and evidence ledgers), `oncolab/operations.py` (operation registry and admission
context disclosure protocol).
Acceptance met: A021 recorded positive admission, a refused value-less measurement, two persisted
revisions, and a persisted evidence record; `tests/test_admission.py` covers refusal reasons.
Not yet earned: typed capability output contracts; admission context is assembled by deterministic
caller code.

## Task 2 — Prove capability search is actually needed

**Status: COMPLETE (negative result recorded, minimal repair re-evaluated under a new identity).**
Goal: decide whether the lexical search mechanism is justified against simpler retrieval, without
assuming expansion is needed.
Depends on: Task 1 (admission identity for recording).
Evidence gate: a frozen need set and a decision rule recorded before result exposure.
Outcome: A022 froze six capabilities, eight needs (six matchable, two absent), a substring
baseline, and the rule "retain only if top-1 accuracy ≥ baseline and every absent need is detected
without a false hit". Raw token overlap scored 6/6 top-1 but returned one false hit
("call structural variants in a tumor normal pair" matched on stopwords), so A022 recorded
**reopen capability retrieval**. The minimal repair (stopword filtering in `_tokens`) was then
evaluated by A025 on the same frozen needs: 6/6 top-1, 2/2 misses detected, 0 false hits,
decision **keep the repaired deterministic search as the initial mechanism**.
Not earned: semantic retrieval; registry-scale evidence; the mechanism remains an initial
mechanism, not established retrieval architecture.

## Task 3 — Prove the gap loop

**Status: COMPLETE.**
Goal: when no capability exists, the system produces the correct typed gap and route without
improvising science.
Depends on: Tasks 1-2.
Evidence gate: none beyond the frozen scenarios.
Outcome: A023 recorded all four gap kinds with provenance (Method→scientific research,
Capability→engineering, Decision→Jev design/eval, Harness→harness engineering); blocked two unsafe
promotions (skip-step promotion, scientific readiness before engineering verification); activated
the fixture capability only after bounded promotion and admitted its measurement; refused a
reasoning-only result lacking provenance at admission (`missing_provenance`).
Not earned: gap classification is caller-declared; routing under ambiguous real needs is untested.

## Task 4 — Build the minimum OnCodex scientific control loop

**Status: COMPLETE for the step; need-identification remains agent reasoning (target).**
Goal: OnCodex can inspect an investigation, search capabilities, execute one allowed operation or
expose a gap, and persist the result independently of its session.
Depends on: Tasks 1-3.
Evidence gate: the step must use only admitted evidence and durable ledgers.
Implemented: `oncodex/research_loop.py` (`run_research_step`, `ResearchRuntime`,
`unmet_activation_requirements`), tools `inspect_investigation` and `run_scientific_operation`
added to `build_oncodex_research_agent` (A001 smoke agent untouched).
Outcome: A024 executed an evidence step and a gap step; rebuilding every ledger from the same
store reproduced evidence, gap, and the revised investigation (`session_independent: true`).
Not demonstrated: identifying the next information need from scientific state — the step takes the
need as input; that remains agent reasoning and is the first thing to demonstrate live.

## Task 5 — Run the first capability-neutral scientific investigation

**Status: COMPLETE (one failed identity, one completed identity with honest null result).**
Goal: freeze a scientific question and let the investigation determine required information,
capabilities, and outcomes — including a recorded gap as a successful harness outcome.
Depends on: Tasks 1-4.
Evidence gate: real data through the nucleus; no modality is prescribed.
Question (frozen): are RNA-Seq and WXS co-availability patterns across GDC TCGA projects
associated with primary site beyond an independence null?
Outcome: S001 (frozen minimum 40 projects) **failed live** after retrieving 33 TCGA projects —
the frozen threshold was wrong, recorded as a failure rather than edited. S002 (new identity,
minimum 30, `predecessor: S001`) **completed live**: 33/33 projects co-available, max site share
0.0909 equal to the null mean, p=1.0; the first admitted scientific evidence is `ev-s002`.
The degenerate null (no variance in co-availability) is the substantive finding: this question on
this source cannot discriminate yet.
Not earned: a disease-biology claim; this is public-metadata structure.

## Task 6 — Introduce Jev only through a real DecisionGap

**Status: EVALUATED — NOT TRIGGERED; Jev stays unwired.**
Goal: add Jev only if an investigation exposes a bounded semantic distinction that deterministic
science cannot answer conveniently and that matters to policy.
Depends on: Task 5.
Evidence gate (trigger): a recorded DecisionGap from a live investigation, with projection and
evaluation plan.
Outcome: S002's measurement and its interpretation are fully deterministic; no DecisionGap was
exposed. Adding Jev now would specify the answer instead of discovering the need. Trigger
condition recorded: any future investigation where a recorded policy decision cannot be expressed
as a deterministic rule must open a DecisionGap before a Jev capability is built.

## Task 7 — Introduce OncoX only when explanation search is justified

**Status: EVALUATED — NOT TRIGGERED; OncoX stays unwired.**
Goal: wire open-ended explanation/hypothesis reasoning into the research loop only when evidence
warrants it.
Depends on: Task 5 (and Task 6 if triggered).
Evidence gate (trigger): recorded evidence whose interpretation needs alternatives, hypotheses, or
discriminating experiments that deterministic analysis cannot supply.
Outcome: the S002 null is explained by assay-design invariance (all projects have both assays); no
open-ended explanation need was exposed. Trigger condition recorded: any investigation whose
recorded evidence leaves competing explanations that deterministic checks cannot separate.

## Task 8 — Run scientific A/B/C

**Status: DEFERRED BY DESIGN DEPENDENCY (not a hidden blocker).**
Goal: with one real scientific task and capability set frozen, compare A deterministic vs
B +OncoX vs C +Jev+OncoX on the same population, data access, capabilities, and accounting.
Depends on: Tasks 5-7.
Evidence gate: arms B and C must contain evidence-backed components; a mature comparison holds
the validated capability set constant (see EVALUATION.md).
Dependency: Tasks 6 and 7 were not triggered, so B and C have no components to differ by; running
A/B/C now would compare identical arms. The recorded-results A/B/C machinery from A020 remains
available for tasks where B and C differ. Trigger condition: any frozen investigation with an
evidence-backed DecisionGap (C) or explanation need (B); the comparison then runs under the
existing equal-budget/equal-target and resource-accounting rules.

## Task 9 — Graduate evaluation (L3, then L4) only when earned

**Status: NOT EARNED — no protocol created.**
Goal: independent compatibility validation (L3) followed by temporal/prospective evaluation (L4)
for candidates that survive L2.
Depends on: Task 8.
Evidence gate: an L2 result with a candidate/prediction worth validating independently; a declared
compatibility contract; then versioned T1/T2 cutoffs.
Outcome: S002 is an exploratory measurement with no candidate or prediction, so there is nothing
to validate independently; creating an L3/L4 protocol now would be protocol creation without an
object. Trigger condition: the first L2 investigation that records a reproducible
candidate/prediction — that experiment's follow-up must become the L3 protocol with an explicit
compatibility contract, and its temporal version the L4 protocol with versioned cutoffs.
