# T19 — Audit type erosion

Status: COMPLETE
Dependencies: T00
Verdict: MODIFIED — full inventory exists (recon); fix only the smallest boundaries required by
the next phase. No broad typing rewrite; no narrowing that breaks existing consumers.

## Scope

Fix:

1. `oncolab/experiments.py:39` — `evaluation_level: str` → `EvaluationLevel` from
   `evaluation.models`. Catalog passes enum members; values unchanged, and catalog fingerprints
   MUST be verified byte-identical before/after (frozen A019/A020 records depend on it).
   `validation_errors()` keeps requiring a non-empty level.
2. `tests/` — add a catalog test that every experiment's level is a valid `EvaluationLevel`.

Record (do not rewrite):

- `execution/ports.py` `measurements/inputs: dict[str, Any]` — no consumer yet; typed when the
  first execution capability lands (remaining gap in T40).
- `evidence/models.py` `value/uncertainty: Any` — scientific values vary; narrowing waits for a
  typed measurement contract.
- `store/jsonl.py` payload — intentionally generic serialization.
- `jev/contracts.py` `criteria/value: Any` and `oncox/ports.py` `structured_state` — raw model/
  state boundaries; documented as such.
- JSON blob boundaries (`gdc.py:38`, `agents_adapter.py:113`, `projections.py:54`) are transport
  boundaries; validation happens at their typed consumers.

## Acceptance

- No `Any` is removed unless a typed consumer exists.
- `ExperimentSpec` fingerprints for A001-A020 are unchanged (verified by script).
- The inventory above is recorded in `docs/tasks/T19` findings and referenced from T40.

## Verification

Fingerprint comparison script (before/after) + focused test + `python scripts/verify.py`.

## Findings (2026-09-30)

- `evaluation_level` is now `EvaluationLevel` for all A001-A020 specs; catalog fingerprints were
  compared before/after and are byte-identical (20 entries), so recorded results stay bound.
- No other `Any` was removed because no typed consumer exists yet. The unimplemented
  `MeasuredResult -> ScientificEvidence` admission path is listed in `docs/EVALUATION.md`
  open gaps.
