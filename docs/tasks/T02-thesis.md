# T02 — Reconcile the scientific thesis

Status: COMPLETE
Dependencies: T00
Verdict: KEEP — `THESIS.md` is already falsifiable and correct in shape; it is missing the
recorded evidence status and an explicit statement that capability evolution is not part of the
scientific comparison.

## Scope

Edit `THESIS.md` (only):

- preserve central hypothesis, three-tier model, falsification list, A/B/C definition;
- add a short "Recorded evidence to date" section: A006/A007 are narrow positive recorded results
  for Jev gating/reranking; A012 (cascade), A019 (masked rediscovery target), A020 (frontier) are
  recorded negative/narrowing results; A014/A016 rejected their candidate capabilities;
- state that these narrow the hypothesis and are not proof;
- state that capability search/evolution is harness infrastructure around the three tiers, not a
  fourth arm and not part of A/B/C.

## Acceptance

- The thesis remains falsifiable; all listed falsification conditions remain possible.
- A/B/C remains intact and unchanged in meaning.
- Harness strategy is clearly subordinate, not an arm.

## Verification

`python scripts/verify.py` (docs-only; architecture checks include required-doc existence).
