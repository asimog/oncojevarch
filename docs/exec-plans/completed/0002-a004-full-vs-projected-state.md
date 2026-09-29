# A004 full-state versus projected-state evaluation

Status: completed

## Objective

Implement and execute A004: compare a rich state containing relevant evidence plus distractors
against a deterministic question-specific projection over the same frozen synthetic cases.

## Invariants

- This is an architecture experiment and creates no cancer ScientificEvidence.
- The expected labels, cases, model, questions, comparison, metrics, and stop rules are frozen
  before the live responses are observed.
- Both arms use the same Jev model and semantic questions.
- The projection is deterministic and retains case identity, population, measurement meaning,
  coverage, missingness, uncertainty, replication, contradiction, and provenance when relevant.
- Raw typed decisions and probabilities remain available; aggregate metrics do not replace them.
- Transport failure is recorded as an operational failure, not a semantic negative.

## Test-authoring gate

- Observable contract: paired arm evaluation must align cases by ID and report independently
  calculated accuracy, agreement, serialized bytes, token use, and latency.
- Credible regression: arm results can be silently compared in the wrong order or cost reduction
  can be reported without preserving outcome quality.
- Existing coverage only protects projection fingerprints and catalog completeness; it does not
  protect paired evaluation semantics.
- No test-only production seam is introduced; the evaluator is used directly by A004.

## Work

- [x] Add reusable paired projection evaluation records and metrics.
- [x] Add frozen A004 cases, full states, deterministic projections, and one Choice question per case.
- [x] Add offline freeze and live TypeSafe execution paths.
- [x] Register A004 with the CLI and update repository guidance.
- [x] Run focused tests, full verification, offline A004, and live A004.
- [x] Record results, complete this plan, commit, and push to `origin/main`.

## Acceptance criteria

- `python -m oncodex run A004` freezes and records the comparison without making an API call.
- `python -m oncodex run A004 --live` executes both arms and records raw decisions plus metrics.
- A mismatched case set fails closed instead of producing misleading paired metrics.
- `python scripts/verify.py` passes.

## Verification evidence

- Focused projection/catalog tests: 7 passed before the full suite.
- `python scripts/verify.py`: architecture checks, compileall, 18 tests, Ruff, and mypy passed.
- Offline A004 froze four cases plus full/projected state and experiment fingerprints.
- Two live A004 runs produced the same four expected decisions in both arms.
- Final live run: full and projected accuracy 1.0; arm agreement 1.0; zero regressions.
- Projection reduced serialized state from 2,299 to 1,718 bytes (25.27%).
- Projection reduced input tokens from 1,715 to 1,500 (12.54%); output tokens remained 195.
- Final observed latency was 858.2 ms full versus 425.7 ms projected. Timing is descriptive,
  not a stable benchmark.
- Durable checked-in result: `docs/experiments/A004_FULL_VS_PROJECTED_STATE.md`.
