# A006 — deterministic ranking vs Jev reranking

Status: complete

## Objective

Test whether one bounded Jev capability can improve the ordering of a deterministic,
high-recall shortlist without changing shortlist membership. This is an architecture
experiment over public GDC project metadata, not a scientific discovery experiment.

## Frozen design

- Source: the public GDC API and its reported data release.
- Candidates: TCGA-LUAD, TCGA-LUSC, TCGA-KICH, TCGA-KIRC, and TCGA-KIRP.
- Queries: one frozen histology-selection task for each candidate.
- Labels: the matching GDC project identifier, fixed before Jev output is exposed.
- Baseline: filter by primary site, then order by descending case count and project ID.
- Treatment: preserve baseline shortlist membership and let Jev reorder it from bounded
  project name, primary-site, and disease-type metadata.
- Repetitions: three live Jev repetitions against the same frozen projection and pinned model.
- Data ceiling: one targeted project query plus one GDC status query; no case records or
  molecular files.

## Prespecified decision

Success required recall@3 of 1.0 in both arms, a Jev recall@1 improvement of at least 0.2 in
every repetition, no invalid choice, and unchanged shortlist membership.

## Evidence

- Focused ranking/catalog tests: 6 passed.
- Offline fingerprint: `752e572614a3c42d37a95108a37298c893ecd1e4b12fc2a8cde29b881b894130`.
- GDC Data Release 46.0 supplied five project records in a 1,265-byte response.
- Baseline recall@1/precision@1: 0.40; MRR: 0.667; recall@3: 1.00.
- Jev recall@1/precision@1/MRR/recall@3: 1.00 in all three repetitions.
- The five top choices were stable across all repetitions and membership was preserved.
- Jev usage per repetition: 1,758 input and 249 output tokens.
- Live latencies: 800.5 ms, 510.7 ms, and 409.3 ms.

## Outcome

The scoped success criteria were met. A deterministic high-recall retrieval stage followed by
bounded Jev top-choice refinement is supported for this exact metadata contract. No general
search-policy promotion or scientific claim follows from this result.
