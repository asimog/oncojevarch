# A011 — null and broken-association controls

Date: 2026-09-29
Class: architecture, semi-synthetic
Status: completed; frozen success criteria met

## Question

Does the semantic candidate-claim stage become appropriately null when the association between a
requested histology and its project description is deliberately destroyed?

## Frozen comparison

Five public GDC project descriptions were assigned opaque case identities. The valid arm retained
the matching task/description pairs. Three null arms applied fixed cyclic derangements with no
case retaining its original description. One independent Noul judged each pair, and code applied
a 0.5 claim threshold.

Success required valid claim rate at least 0.80, mean null claim rate at most 0.20, no null arm
above 0.40, and valid-minus-null mean probability at least 0.40 in each of three repetitions.

## Source receipt

- GDC release: Data Release 46.0 - August 10, 2026
- API tag: 8.5.0
- API commit: `8f7c2a51ab0084b216ad1b62a3fae8b945439c53`
- Status response: 221 bytes
- Targeted five-project response: 1,105 bytes
- Case, sample, aliquot, file, and molecular records downloaded: 0
- Jev model: `jev-1.13.0`
- Frozen fingerprint: `58fe166cedad2ebf3c36c07b090b88031ee96c2ac52aa8e13f45679c93328f5e`
- Projection fingerprint: `b97d616b1b137326ca5a3d40ff8e18be750b4863387fe66d50af2261b9dcf86e`

## Results

| Metric | Repetition 1 | Repetition 2 | Repetition 3 |
|---|---:|---:|---:|
| Valid claim rate | 1.00 | 1.00 | 1.00 |
| Mean null claim rate | 0.00 | 0.00 | 0.00 |
| Maximum null-arm claim rate | 0.00 | 0.00 | 0.00 |
| Valid mean probability | 0.916 | 0.928 | 0.938 |
| Mean null probability | 0.055 | 0.055 | 0.053 |
| Valid-minus-null probability | 0.861 | 0.873 | 0.885 |

All five valid cases claimed and all fifteen deranged cases remained below threshold in every
repetition. Decisions were stable 3/3. Each run used 3,630 input and 469 output tokens; latencies
were 785.4 ms, 349.7 ms, and 401.4 ms (mean 512.2 ms).

## Decision

The bounded semantic claim gate passed this semi-synthetic null control. The generic derangement
generator and evaluator are retained. This does not validate biological null behavior, a complete
candidate pipeline, or narrative generation by OncoX.

## Limits

- The destroyed relationship is task-to-project-description coherence, not a molecular signal.
- Familiar TCGA project descriptions may occur in model training data.
- Five records and three derangements are too small to establish general false-narrative rates.
- Noul probabilities are raw judgments, not permission or measured scientific evidence.
