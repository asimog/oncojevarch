# T40 — Final verification and architectural questions

Status: COMPLETE
Dependencies: all
Verdict: KEEP — closing audit. Answers must be evidence-based; any "no" becomes an explicit
remaining gap, never a speculative abstraction.

## Method

Answer all 20 governing questions with evidence (file:line, test, or recorded result):

1. Can OnCodex identify what scientific information is missing?
2. Can it search capabilities without loading the entire registry?
3. Can it determine that no suitable capability exists?
4. Can missing capability become an explicit typed gap?
5. Can MethodGap avoid being sent directly to a coding agent?
6. Can CapabilityGap produce bounded engineering work?
7. Can DecisionGap produce an evaluated semantic instrument?
8. Can HarnessGap improve runtime capabilities without changing science?
9. Can a generated capability remain inactive until evaluated?
10. Can a new scientific measurement type be added without editing the generic OncoJev core?
11. Is the system still useful if the next investigation needs an unanticipated measurement?
12. Can deleting every agent/session thread leave the experiment reproducible?
13. Does Jev remain judgment rather than measurement or policy?
14. Does OncoX remain reasoning rather than measured evidence?
15. Does Python/deterministic code retain exact science?
16. Can A/B/C be run with the same scientific capability set?
17. Are L0-L4 level and scientific readiness represented as different concepts?
18. Can failed experiments narrow architecture without broad refactors?
19. Can repository-local docs teach a new agent without a giant AGENTS.md?
20. Is any fixed cancer modality pipeline embedded in core architecture?

## Acceptance

- All 20 answered in the final report with evidence; each "no"/partial listed under remaining
  gaps with an owner (Method/Capability/Decision/Harness route context).
- Final verification counts recorded exactly: architecture checks, compile, tests
  passed/skipped, ruff, mypy.

## Verification

`python scripts/verify.py` + the report itself.

## Findings (2026-09-30)

Evidence-backed answers:

1. yes — scientific state and uncertainty surfaces exist (`research/models.py`), and
   `build_oncodex_research_agent` carries the research instructions.
2. yes — `CapabilityRegistry.search` returns bounded summaries without loading full records.
3. yes — a search miss is explicit (`NO_APPLICABLE_CAPABILITY`).
4. yes — `Gap` + `GapLedger`: typed kinds, provenance, durable append-only store.
5. yes — `ROUTES[GapKind.METHOD] = SCIENTIFIC_RESEARCH`; docs forbid direct Codex routing.
6. yes — CapabilityGap -> ENGINEERING; bounded proposals in `oncolab/proposals.py`; promotion gates.
7. partial — DecisionGap route and Jev contracts exist, but no live evaluated Jev instrument has
   been built since A013; this remains an explicit gap.
8. yes — HarnessGap -> HARNESS_ENGINEERING; no path mutates scientific methods.
9. yes — DRAFT->TESTED->VERIFIED->PROMOTED one step at a time; scientific readiness is gated on
   engineering verification (tests).
10. yes — an unanticipated capability registers and is searchable without core type changes (test).
11. yes — capability search + gap ledger make unanticipated needs first-class.
12. yes — durable state lives in store/oncolab; agent threads are not scientific memory.
13. yes — Jev cannot create evidence; `JevDecision` stays distinct (epistemic boundary tests).
14. yes — OncoX output is interpretation only, never ScientificEvidence.
15. yes — deterministic execution retains exact science; Python policy decides.
16. yes — the validated capability set is injectable and held constant across arms (EVALUATION.md).
17. yes — executed level != scientific readiness is stated in `docs/EVALUATION.md`.
18. yes — negative results narrow architecture; retests are new experiment identities.
19. yes — AGENTS.md is 90 lines; canonical docs carry the knowledge.
20. yes — no modality-lane identifiers or fixed modality pipeline in any core package (grep + the
    new source-adapter containment check).

Remaining gaps are listed in `docs/EVALUATION.md` and the program report.
