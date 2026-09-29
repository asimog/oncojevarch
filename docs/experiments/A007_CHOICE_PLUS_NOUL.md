# A007 — Choice plus absolute-viability Noul

Date: 2026-09-29
Class: architecture
Status: completed; frozen success criteria met

## Question

Does a separate absolute adequacy judgment prevent a relative Choice from accepting the best of
an entirely unsuitable candidate set?

## Frozen comparison

Eight tasks used the same small public GDC project-description surface as A006. Four tasks had an
exact viable match; four asked lung or kidney shortlists to satisfy unrelated brain, breast,
ovarian, or prostate tasks. Choice always selected the relative best. The combined arm accepted
that choice only when an independent Noul viability probability was at least 0.5.

The labels, threshold, 0.50 minimum false-acceptance improvement, 0.75 minimum viable recall, and
three repetitions were fixed before live output.

## Source receipt

- GDC release: Data Release 46.0 - August 10, 2026
- API tag: 8.5.0
- API commit: `8f7c2a51ab0084b216ad1b62a3fae8b945439c53`
- Status response: 221 bytes
- Targeted five-project response: 1,105 bytes
- Case, sample, aliquot, file, and molecular records downloaded: 0
- Jev model: `jev-1.13.0`
- Frozen experiment fingerprint: `c5bba4fbdf0c88b3feb5c5c93040bea0be911864315b11936bcc32337d68c3b6`
- Projection fingerprint: `3021d471f1217d86e13fe9cfd1639af60b143afac9cb78ac6deac962628528cb`

## Results

| Metric | Choice only | Choice + Noul (each of 3 runs) |
|---|---:|---:|
| False-acceptance rate | 1.00 | 0.00 |
| False-rejection rate | 0.00 | 0.00 |
| Viable recall | 1.00 | 1.00 |
| Accuracy | 0.50 | 1.00 |
| Coverage | 1.00 | 0.50 |
| Brier score | 0.50 | 0.0010–0.0013 |

All acceptance decisions and relative Choices were stable in all three repetitions. There were no
out-of-shortlist Choices. Each repetition used 3,133 input and 579 output tokens. Latencies were
801.4 ms, 418.4 ms, and 422.3 ms (mean 547.4 ms).

## Decision

The result supports a separate absolute-viability gate for this exact metadata-matching contract.
Relative Choice must not imply adequacy. The Noul threshold and capability remain scoped and do
not self-promote into scientific workflows.

## Limits

- The task labels project-description adequacy, not biological candidate viability.
- No-match tasks are controlled fixtures on real metadata, not naturally sampled failures.
- Eight balanced cases cannot establish calibration despite the low observed Brier score.
- Known TCGA terminology may be present in model pretraining.
