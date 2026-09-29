# T30 — Controls and leakage policy

Status: COMPLETE
Dependencies: T23
Verdict: KEEP — extend the existing controls/leakage sections to the full required lists.

## Scope

`docs/EVALUATION.md`:

- controls (applicable, declared): null; shuffled/permuted labels; broken associations; randomized
  candidate identities; negative-control populations/features; deterministic-only baseline;
  semantic-layer ablation.
- leakage review: identifiers; outcomes; future data; literature; model training familiarity;
  prompt/context; derived target-encoding features; adaptive modifications after result exposure.
- null outputs that remain persuasive count against the system.

## Acceptance

- Both lists present; controls required from L1 upward remains stated.
- No biological modality requirement.

## Verification

`python scripts/verify.py`; read-through.
