# A004 — full state versus question-specific projection

## Classification

Architecture experiment, synthetic evaluation level. This result is not cancer ScientificEvidence
and does not establish a validated Jev capability.

## Frozen comparison

- Model: `jev-1.13.0` from local experiment configuration.
- Cases: replicated signal, replication conflict, underpowered signal, and replicated null.
- Full arm: protected scientific fields plus irrelevant workflow and ingestion distractors.
- Projected arm: population, measurement, coverage, missingness, uncertainty, replication,
  contradiction, and provenance only.
- Semantic output: one of `advance`, `inspect`, `acquire_more`, or `stop` for each case.
- Full-state fingerprint: `adcf49768e579a2407577069360bba10a8ad24c51821c508aa05ca51004b43a8`.
- Projected-state fingerprint: `af577629944091760b2889c18bdce75e08c93ed2748ad1f86a9e4afd70028828`.
- Experiment fingerprint: `d9fb209b828b4c34f2f9b69e793f9c5556bdf9b8605088fb529712527741885d`.

## First live run

| Metric | Full state | Projected state |
|---|---:|---:|
| Expected decisions | 4/4 | 4/4 |
| Serialized state | 2,299 bytes | 1,718 bytes |
| Input tokens | 1,715 | 1,500 |
| Output tokens | 195 | 195 |
| Latency | 760.3 ms | 408.2 ms |

The arms agreed on all four decisions. The projection reduced serialized input by 25.27% and
input tokens by 12.54% without an observed accuracy loss in this run. The projected arm therefore
met the frozen A004 success criteria.

## Interpretation and limitations

This is evidence that the integration and paired-evaluation mechanics work and that these
particular distractors were unnecessary for these four deliberately simple cases. It is not
evidence that the projection is sufficient for cancer discovery. The sample is synthetic and
small, the cases were authored around the decision contract, and a single run does not estimate
stability, calibration, or behavior under realistic biological ambiguity.

## Consequence

Keep the paired evaluator and question-specific projection boundary. Do not promote the A004
semantic capability. A003 still needs a larger frozen labeled set, perturbation tests, repeated
runs, and eventually real-data cases before any scientific-readiness claim.
