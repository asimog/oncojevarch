# A012 — Jev triage versus reasoning on every case

Date: 2026-09-30
Class: architecture, semi-synthetic
Status: completed; frozen criteria **not** met — the cascade is not supported for this contract

## Question

Can a bounded Jev triage decision reduce OncoX use without harming scientific quality, by
selecting only the cases where expensive open-ended reasoning is worth paying for?

## Frozen comparison

Ten locked cases were built from real public GDC project aggregates (Data Release 46.0):
five whose recorded structured state already resolves the claim's material question, and five
that leave a material question open. Each case carries a frozen rubric of recorded (already in the
state) and novel (not in the state) considerations.

- Arm ALL: OncoX reasons on every case.
- Arm CASCADE: one batched Noul triage call decides escalation at a frozen threshold of 0.5, then
  OncoX reasons only on escalated cases.
- Ordering: triage was computed from the frozen structured state before any OncoX output existed
  in each repetition.
- Frozen criteria: zero cascade false negatives, quality loss at most 0.05, OncoX calls down by at
  least 0.30, at least one OncoX-useful case.

The live slice used the smallest balanced subset (two closed, two open) inside a short budget.
Rubric, cases, projection, thresholds, metrics, and arms were frozen before the live run; the
first live attempts produced no result and only provider-robustness parameters changed (bounded
retry, no completion cap, pinned reasoning effort).

## Source receipt

- GDC release: Data Release 46.0 - August 10, 2026; API tag 8.5.0; commit
  `8f7c2a51ab0084b216ad1b62a3fae8b945439c53`
- Project response: 9,883 bytes; status response: 221 bytes; 0 case, sample, aliquot, file, or
  molecular records downloaded
- Jev model: `jev-1.13.0`; OncoX model: `deepseek/deepseek-v4.1-flash` via OpenRouter Chat
  Completions, reasoning effort `low`, no completion cap
- Frozen experiment fingerprint: `e22890bf26932ed111808c7b7737c156828ccab37475baa59bd3b0d2a9f5b6b6`
- Projection fingerprint: `f10ada8be4811958f0bd22103db66c403cf204fc61c84472d061619db1bb67f5`

## Results

| Metric | Repetition 1 | Repetition 2 |
|---|---:|---:|
| Escalated cases | 4 / 4 | 4 / 4 |
| Triage probabilities (c01/c05/c06/c09) | 0.92 / 0.61 / 0.81 / 0.92 | 0.92 / 0.62 / 0.79 / 0.91 |
| OncoX call reduction | 0.00 | 0.00 |
| False negatives | 0 | 0 |
| Quality loss | 0.150 | -0.100 |
| Useful cases (OncoX-all) | c06, c09 | c06 |
| Triage false-positive rate | 1.00 | 1.00 |
| OncoX calls / tokens (ALL) | 4 / 2,045 in, 11,611 out | 4 / 2,045 in, 10,286 out |
| OncoX calls / tokens (CASCADE) | 4 / 2,337 in, 10,441 out | 4 / 2,045 in, 10,854 out |
| Mean OncoX latency | 21.5 s / 24.8 s | 18.6 s / 17.9 s |
| Triage usage / latency | 2,144 in, 92 out / 0.44 s | 2,144 in, 92 out / 0.41 s |

Triage decisions were stable across repetitions; the useful-case label was not (c09 was useful in
repetition 1 and not in repetition 2), so rubric matching is noisy at this output length. No case
that OncoX-all judged useful was screened out, because nothing was screened out at all.

## Decision

**A012 does not support the cascade for this frozen task and triage contract.** Bounded triage
escalated every case, including the two whose recorded state already contained the material
considerations, so it saved no OncoX calls and missed the 0.30 savings target. All-case reasoning
remains the justified architecture for this task.

The failure mode is specific and informative: the frozen triage question asked whether deeper
reasoning "would add materially new information", and the model treated an unsupported claim as a
sufficient reason to escalate even when the recorded state already resolved the claim's material
question. That is a decision-contract defect, not an OncoX-adapter defect; the adapter itself
produced validated structured output on every escalated call.

## Limits

- Usefulness is a frozen lexical rubric outcome, not a scientific measure of quality.
- False-negative burden is a bounded measurement: only prespecified considerations can be matched,
  so unanticipated material additions to a screened-out case would not be detected.
- The live slice covers four of ten locked cases; the held-back cases remain frozen and untested.
- Two repetitions cannot establish general triage behavior, and the useful-case label moved.
- OncoX output is interpretation only and cannot create ScientificEvidence.

## Follow-up

A revised triage contract is a new experiment identity: it would need its own frozen projection,
question, threshold, and evaluation. Two candidate causes remain untested here: the wording of the
materiality criterion, and the calibration of the Noul threshold for this decision.
