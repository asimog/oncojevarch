# A019 — masked real-data rediscovery

Status: complete (negative; target missed, no leakage)

## Objective

Test whether a frozen pipeline recovers a held-out relationship in real, versioned data under
identifier masking, with a leakage audit and a null control.

## Frozen design

- Eleven real TCGA projects across five primary sites, masked to `sha256(identifier)[:8]`.
- Aggregate profile features only: file shares per data category, file shares per strategy, files
  per case. No identifiers, names, sites, or disease types in any arm input.
- Arm A: leave-one-out nearest centroid. Arm B: plus one batched Noul screen over cases inside a
  frozen 0.10 ambiguity margin. Arm C: plus OncoX re-ranking of escalated cases only.
- Null control: deranged label assignment. Frozen target: best-arm recall@1 at least 0.50.

## Implementation

- `evaluation/rediscovery.py`: masking, features, leave-one-out ranking, ambiguity selection,
  bounded overrides, metrics, deranged null, leakage findings.
- `experiments/architecture/a019_masked_rediscovery.py`: GDC aggregate fetch, masked profiles, three
  arms, null control, and the decision record.
- `tests/test_rediscovery.py`: 8 focused tests.

## Evidence

- Arm A recall@1 0.273 (chance 0.20), recall@3 0.545, MRR 0.498.
- Jev screen probabilities 0.34 and 0.35 on the two ambiguous cases: nothing escalated, so arm C
  equals arm B and no OncoX call was spent.
- Null control recall@1 0.00; leakage findings none; 21.6 kB of aggregates, no case or molecular
  records.
- Frozen target missed, so the failure branch applies and the architecture is revised or rejected
  for this task and representation.

## Outcome

Aggregate file-share profiles do not carry enough primary-site signal for the frozen target. The
screen behaved as designed by declining to pay for reasoning with no discriminating information.
A richer cheap representation, or a different held-out relationship, is a new experiment identity
(candidate CapabilityGap).
