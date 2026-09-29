# T32 — Strengthen experiment identity

Status: COMPLETE
Dependencies: T23
Verdict: KEEP with constraint — docs only; code already fingerprints `ExperimentSpec` fully
(`oncolab/experiments.py:42-44`) and binds results to the frozen fingerprint.

## Scope

`docs/EVALUATION.md` freezing section — enumerate what must be frozen/fingerprinted where
applicable: question; hypothesis; experiment class; evaluation level; population; source/version;
capabilities; methods; candidate universe; projections; Jev model/capability; OncoX configuration;
thresholds; budgets; controls; metrics; multiplicity; failure/stop rules. State: no history
rewriting; corrections are appended with provenance and a new identity if material (constitution
#12); post-result changes never edit the frozen record.

## Acceptance

- Freeze list complete; append-only correction rule stated.
- Consistent with `FrozenExperiment`/`ExperimentResult` code.

## Verification

`python scripts/verify.py`; read-through.
