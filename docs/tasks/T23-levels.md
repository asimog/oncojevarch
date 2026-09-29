# T23 — Reconcile evaluation levels L0-L4

Status: COMPLETE
Dependencies: T00
Verdict: KEEP — `docs/EVALUATION.md` already has the coverage table from the prior session;
make the level/readiness distinction explicit and align wording with recorded results.

## Scope

Edit `docs/EVALUATION.md`:

- explicit statement: `executed evaluation level != scientific readiness`;
- explicit statement: evaluation machinery has exercised L0-L2, but OncoJev has not yet
  demonstrated successful scientific cancer-discovery validation through L2;
- A019 is a retrospective-real architecture evaluation that missed its frozen target; A020 is a
  frontier analysis over recorded experiment results;
- L3/L4 unexecuted (no protocol, runner, compatibility contract, or result);
- mapping verified against code: L0 = A001-A010, A013-A018; L1 = A011-A012;
  L2 = A019-A020; L3/L4 none (`experiments/catalog.py`, `evaluation/models.py`).

## Acceptance

- A reader cannot mistake "Level 2 executed" for "scientific readiness demonstrated".
- Mapping matches catalog code exactly.

## Verification

`python scripts/verify.py`; cross-check catalog levels via a script.
