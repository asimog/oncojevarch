# T15 — Clarify OncoLab responsibilities

Status: COMPLETE
Dependencies: T03
Verdict: KEEP — mostly present; make the ownership list explicit and state the immutability rule.

## Scope

Edit `ARCHITECTURE.md` OncoLab section:

- owns/governs: experiment identity; operation identity; capability registry; engineering
  readiness; scientific readiness; budgets; legality; evidence admission; gap state; activation
  constraints; recovery; durable history;
- keep the sentence pair "OnCodex chooses and acts. OncoLab constrains, validates, and remembers."
- add: OnCodex cannot make historical scientific state mutable by itself (constitution #12/#13).

## Acceptance

- Ownership list matches code reality: registry/readiness in `oncolab/capabilities.py`, gaps in
  `oncolab/gaps.py`, identity/freeze in `oncolab/experiments.py`, recovery in `oncolab/recovery.py`.
- Immutability rule stated.

## Verification

`python scripts/verify.py`; cross-check with `docs/EPISTEMIC_CONSTITUTION.md` items 12-13.
