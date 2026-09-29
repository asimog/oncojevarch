# A019 — masked real-data rediscovery

Date: 2026-09-30
Class: architecture, retrospective real metadata
Status: completed; frozen failure branch taken — target missed, no leakage

## Question

Can the pipeline recover a held-out relationship in real, versioned data when identifiers are masked,
without leakage?

## Frozen design

Eleven real TCGA projects across five primary sites (kidney 3, lung 2, colon and rectum 2, uterus 2,
brain 2) were reduced to aggregate, identifier-free profiles: file shares per data category, file
shares per experimental strategy, and files per case. Identifiers, names, primary sites, and disease
types never enter an arm input; the masks are `sha256(identifier)[:8]`.

- Arm A: deterministic leave-one-out nearest centroid over z-scored shares.
- Arm B (deterministic plus Jev): a single batched Noul screen over the cases whose top two
  candidates fall inside a frozen 0.10 relative margin, at threshold 0.5.
- Arm C (deterministic plus Jev plus OncoX): OncoX re-ranks the escalated cases only, inside the
  candidate set the deterministic arm already produced.
- Null control: the deterministic arm re-run over a deranged label assignment.
- Frozen target: best-arm recall@1 at least 0.50; chance is 0.20; null margin 0.15.

## Results

| Metric | Arm A | Arm B | Arm C |
|---|---:|---:|---:|
| recall@1 | 0.273 | 0.273 | 0.273 |
| recall@2 | 0.455 | 0.455 | 0.455 |
| recall@3 | 0.545 | 0.545 | 0.545 |
| mean reciprocal rank | 0.498 | 0.498 | 0.498 |
| Jev calls | 0 | 1 | 1 |
| OncoX calls | 0 | 0 | 0 |
| Jev tokens (in/out) | 0 | 4,521 / 59 | 4,521 / 59 |

Ambiguous cases: 2. Jev triage probabilities: 0.34 and 0.35, both below the frozen threshold, so
nothing escalated and arm C equals arm B. Null control recall@1: 0.00 against a 0.20 chance rate and
a 0.15 margin. Leakage findings: none. Source: GDC Data Release 46.0, 21.6 kB of project aggregates,
zero case, sample, aliquot, file, or molecular records.

## Decision

The frozen target was missed, so per the frozen failure criteria the architecture is revised or
rejected **for this task and representation**: aggregate file-share profiles over eleven projects do
not carry enough primary-site signal to reach a 0.50 recall@1, and the near-chance null control
confirms that the ranking is not driven by leakage.

The screen behaved as designed: it judged that the ambiguous profiles carried no further
discriminating information and declined to spend OncoX calls on them. That is the intended cost
behavior, but it also means the cascade could not improve a ranking that had no signal to exploit.

## Limits

- Primary site from aggregate file profiles is a metadata relationship, not a biological discovery,
  and this experiment cannot establish cancer biology.
- Eleven masked projects across five sites is a small evaluation set with five candidate labels.
- The deterministic arm is a single nearest-centroid method with one feature representation.
- Model pretraining may already associate TCGA-like profiles with sites, which the null control
  cannot detect for the deterministic arm alone.
- The ambiguity rule selected only two cases, so the model arms had little room to act.

## Follow-up

A representation with more discriminative structure (per-case or per-assay aggregates rather than
file shares) or a different held-out relationship is a new experiment identity. A candidate
CapabilityGap: a richer, still-cheap representation builder for masked rediscovery tasks.
