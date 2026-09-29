# T31 — Multiplicity / adaptive-search policy

Status: COMPLETE
Dependencies: T23
Verdict: KEEP with constraint — docs only; no `ExperimentSpec` schema change (fingerprints of
A001-A020 must remain byte-identical; new fields would invalidate frozen records).

## Scope

`docs/EVALUATION.md`:

- label every future experiment as CONFIRMATORY, EXPLORATORY, or ADAPTIVE_DISCOVERY (declared at
  freeze time);
- confirmatory work requires prespecified multiplicity handling;
- exploratory work requires held-out/independent confirmation before confirmatory language;
- adaptive search must retain search history and the tested universe;
- Jev confidence is not a p-value; OncoX plausibility is not multiplicity correction.

Future experiments can declare the mode inside the existing `inputs` dict of `ExperimentSpec`;
no schema change is made now.

## Acceptance

- Three modes defined with obligations; the two "is not" statements present.
- No code schema change; catalog fingerprints unchanged.

## Verification

`python scripts/verify.py`; fingerprint stability script (see T19).
