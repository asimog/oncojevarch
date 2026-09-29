# A005 — GDC representation ladder

## Classification

Architecture experiment over public operational metadata. The counts below are not a scientific
population and are not cancer ScientificEvidence.

## Frozen question and policy

For TCGA-LUAD, what is the cheapest representation that can establish whether enough cases have
both RNA-Seq and WXS file associations to justify a later sample-compatibility check?

The architecture-only gate was frozen at 100 paired cases and 50% of project cases.

## Source

- GDC Data Release 46.0 — August 10, 2026
- API tag: 8.5.0
- API commit: `8f7c2a51ab0084b216ad1b62a3fae8b945439c53`
- Experiment fingerprint: `bad829e1b915c4250b885e09ba10e8030b1d567e2504a1d6a6bdea8a567459d2`

## Representation ladder

| Level | Response | Bytes | What it resolves |
|---|---|---:|---|
| Project metadata | Project identity, sites, disease types, 585 cases, 36,740 files | 324 | Scope only |
| File facets | 5,409 RNA-Seq files and 10,096 WXS files | 1,215 | Both modalities exist; case overlap remains unknown |
| Targeted case counts | RNA-Seq count, WXS count, and union count | 417 total | Exact case-level association overlap |

The three `size=0` case responses contained 139 bytes each:

- RNA-Seq cases: 518
- WXS cases: 582
- union: 583
- intersection by inclusion-exclusion: `518 + 582 - 583 = 517`
- paired fraction: `517 / 585 = 88.38%`

The frozen decision was `proceed_to_sample_compatibility_check`.

## Interpretation

Project metadata could not answer the question. File facets established modality availability but
could not establish within-case overlap. Targeted aggregate counts resolved the decision without
returning a single case record or molecular file. In this experiment, the semantically richer
representation was also smaller than the broader facet response because the query was more precise.

Jev was not used: availability counts and inclusion-exclusion are exact deterministic work.

## Limitations and next information need

Case association does not establish that RNA-Seq and WXS belong to scientifically compatible
samples, aliquots, tumor/normal roles, workflows, or access classes. Operational shard is not
scientific population. The next justified representation is a bounded metadata slice that resolves
sample and aliquot compatibility for a small deterministic cohort; raw molecular data is not yet
justified.
