# A011 — null and broken-association controls

Status: complete

## Objective

Test whether a bounded semantic candidate-claim stage becomes null when task-to-metadata
associations are destroyed.

## Frozen design

- Five masked public GDC project descriptions.
- One valid arm and three fixed no-fixed-point derangements.
- Noul claim threshold 0.5; three live repetitions.
- Success: valid rate at least 0.80, mean null rate at most 0.20, maximum null arm at most 0.40,
  and valid-minus-null mean probability at least 0.40.

## Evidence

- Focused null-control/catalog tests: 5 passed.
- Frozen fingerprint: `58fe166cedad2ebf3c36c07b090b88031ee96c2ac52aa8e13f45679c93328f5e`.
- Valid claims: 5/5; null claims: 0/15 in every repetition.
- Valid mean probability: 0.916–0.938; null mean: 0.053–0.055.
- Decisions were stable across all repetitions.
- Jev usage per repetition: 3,630 input and 469 output tokens.
- GDC transfer: 1,105 project bytes plus 221 status bytes; no case or molecular data.

## Outcome

The scoped criteria were met. This supports the control-generation and bounded semantic-gate
mechanics only; biological null behavior and complete-pipeline narrative suppression remain
unvalidated.
