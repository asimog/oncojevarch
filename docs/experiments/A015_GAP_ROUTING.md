# A015 — gap routing and promotion guarding

Date: 2026-09-30
Class: architecture, synthetic
Status: completed; frozen criteria met

## Question

Do Method, Capability, Decision, and Harness gaps route correctly, and does the promotion path
refuse every self-promotion attempt, including adversarial ones?

## Frozen design

Fourteen frozen scenarios: ten representative gaps and four adversarial attempts (a generated
capability promoting itself, engineering readiness claimed as scientific validation, a generated
Jev question entering a permanent battery, and a missing measurement recorded as a biological
negative). Two routing arms compare a one-keyword baseline against combined-signal routing with a
frozen precedence rule: harness, decision, capability, method, with an unsignalled gap falling back
to a method gap.

Guards are owned by the gap kind that can act on them, so a misroute really does drop the guard:
promotions require review in every routed kind, the "missing is not a biological negative" guard
lives with method gaps, and the "engineering readiness is not scientific readiness" guard lives with
harness gaps. Promotion probes drive the real capability registry, which enforces one-step
engineering advancement and engineering verification before any scientific readiness.

## Results

| Metric | Single-factor baseline | Combined signal |
|---|---:|---:|
| Route accuracy | 0.50 | 1.00 |
| Unsafe activations | 1 | 0 |
| Review-requirement coverage | 0.93 | 1.00 |
| Deterministic cost (scenarios) | 14 | 14 |
| Misrouted scenarios | g01, g05, g07, g11, g12, g13, g14 | none |

Every promotion probe was blocked before review, and every adversarial scenario required review.
The unsafe activation in the baseline arm is g14: without the method-routed guard, an absent
measurement would have been recorded as a biological negative.

## Decision

Combined-signal routing with kind-owned guards is adopted for the frozen scenario set, and the
conservative default (unsignalled gaps are method gaps) is kept. The registry rules already in
`oncolab/capabilities.py` are sufficient for the promotion probes; no new promotion machinery was
added.

## Limits

- Scenarios are frozen fixtures, not field observations of real gaps.
- Lexical signals are a baseline, not a validated semantic router; a paraphrase could evade them.
- Blocking a promotion here does not prove that no unsafe path exists elsewhere in the system.
- This architecture task cannot create ScientificEvidence.
