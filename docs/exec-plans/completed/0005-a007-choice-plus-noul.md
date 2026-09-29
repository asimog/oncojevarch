# A007 — Choice plus absolute-viability Noul

Status: complete

## Objective

Test whether an independent absolute-viability Noul gate reduces Choice's forced
best-of-bad-options acceptances while preserving viable selections.

## Frozen design

- Five public GDC project descriptions; eight balanced viable/no-match tasks.
- Choice selects the relative best candidate for every task.
- Noul independently evaluates whether any candidate adequately matches the task.
- Acceptance threshold: 0.5; three repetitions with the pinned Jev model.
- Success: false-acceptance improvement at least 0.50, viable recall at least 0.75, and no
  out-of-shortlist Choice.

## Evidence

- Offline fingerprint: `c5bba4fbdf0c88b3feb5c5c93040bea0be911864315b11936bcc32337d68c3b6`.
- GDC Data Release 46.0 supplied the five descriptions in 1,105 bytes.
- Choice-only false acceptance: 1.00; accuracy: 0.50.
- Choice + Noul false acceptance: 0.00; viable recall and accuracy: 1.00 in every repetition.
- Decisions and Choices were stable 3/3, with no invalid Choice.
- Jev usage per repetition: 3,133 input and 579 output tokens.
- Live latencies: 801.4 ms, 418.4 ms, and 422.3 ms.

## Outcome

The scoped criteria were met. Keep relative preference and absolute adequacy as distinct typed
judgments for this contract. This does not validate scientific viability or authorize automatic
capability promotion.
