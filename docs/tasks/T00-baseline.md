# T00 — Baseline

Status: COMPLETE
Dependencies: none
Verdict: KEEP — executed before any change.

## Recorded

- Starting HEAD: `2ec39eb222c1fe9dc31314f689c9543be8e0c22c` ("Record A019 and A020 execution plans").
- Working tree at start: modified `README.md`, `docs/CONCEPT_BOOK.md`, `docs/EVALUATION.md`,
  `docs/EXPERIMENT_CATALOG.md` (prior evaluation-docs session, uncommitted).
- Baseline verification (run before any edit):
  - `python scripts/check_architecture.py` — OK;
  - compileall over all 12 packages — OK;
  - pytest — 110 passed, 3 skipped (optional `agents`/`pydantic` adapter tests);
  - ruff — OK; mypy — OK (108 source files).

## Inventory facts established

- `oncolab/capabilities.py` registry has no search/summary/eligibility API; a miss raises a bare
  `KeyError` (`capabilities.py:53-54`).
- `oncolab/gaps.py` `Gap` records need + evidence only; no "why existing capabilities could not
  satisfy" field and no persistence.
- OnCodex agent has exactly one tool (read-only Codex workspace); no capability/gap/Jev/OncoX tool
  surface (`oncodex/agent.py:15-30`).
- `evaluation/models.py` (`EvaluationLevel`, `SystemArm`, `MetricRecord`, `ABCTestPlan`) is
  referenced nowhere outside itself and docs — dead/declarative.
- AGENTS.md is 91 lines; contains a stale "A001-A003" executable-experiment list.
- CI (`.github/workflows/ci.yml`) installs `.[dev]` only; adapter tests skip there.

## Failures attributable to new work

None known. All baseline checks green; subsequent failures must be attributed to this program.
