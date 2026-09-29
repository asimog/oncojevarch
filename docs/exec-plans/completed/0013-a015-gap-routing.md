# A015 — gap routing and promotion guarding

Status: complete (frozen criteria met)

## Objective

Check that Method/Capability/Decision/Harness gaps route correctly and that no promotion path,
including adversarial self-promotion attempts, activates without review.

## Frozen design

- Ten representative and four adversarial gap scenarios, frozen before evaluation.
- Arms: one-keyword single-factor routing versus combined-signal routing with precedence
  harness > decision > capability > method and a method-gap fallback.
- Guards owned by the acting gap kind; promotion probes drive the real capability registry.

## Implementation

- `oncolab/routing.py`: scenario, routing decision, guard rules, and routing evaluation.
- `experiments/architecture/a015_gap_routing.py`: frozen scenarios, both arms, registry probes, and
  the decision record.
- `tests/test_gap_routing_experiment.py`: 9 focused tests.

## Evidence

- Combined-signal accuracy 1.00, unsafe activations 0, review coverage 1.00.
- Single-factor accuracy 0.50 with 1 unsafe activation (a missing measurement recorded as a
  biological negative) and 7 misroutes.
- Every promotion probe blocked before review; registry refused out-of-order and unverified
  advancement.

## Outcome

Kind-owned guards plus combined-signal routing are adopted for this scenario set; the conservative
method-gap default is kept. No new promotion machinery was needed.
