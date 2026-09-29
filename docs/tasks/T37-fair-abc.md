# T37 — Preserve fair A/B/C evaluation under capability evolution

Status: COMPLETE
Dependencies: T29
Verdict: KEEP — add the confound rule to `docs/EVALUATION.md`.

## Scope

- A/B/C comparisons must not give one arm better scientific tools because that arm triggered more
  capability evolution;
- for a mature frozen comparison keep constant: scientific task; population; data access; source
  versions; deterministic scientific capabilities; candidate universe; validated capability
  registry; resource-accounting rules; outcome labels;
- vary only: A (deterministic decision/search architecture), B (+OncoX), C (+Jev+OncoX);
- evaluating capability evolution itself requires a separate, explicitly designed experiment with
  its own identity; do not mix the two hypotheses.

## Acceptance

- Rule present and consistent with A020's recorded analysis and T29 accounting.
- No statement suggests capability evolution is part of the scientific treatment variable.

## Verification

`python scripts/verify.py`; read-through.
