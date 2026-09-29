# A006 — deterministic ranking vs Jev reranking

Date: 2026-09-29  
Class: architecture  
Status: completed; frozen success criteria met

## Question

Does bounded Jev reranking improve the top of a deterministic high-recall shortlist without
changing which candidates survive retrieval?

## Frozen comparison

Five public TCGA project records formed two primary-site ambiguity groups: LUAD/LUSC for
bronchus and lung, and KIRC/KIRP/KICH for kidney. The deterministic arm filtered by primary
site and ordered by descending GDC case count. The treatment kept exactly that membership and
moved one Jev Choice to rank one using only project name, primary site, and disease type.

Labels, `k=3`, the 0.20 minimum recall@1 improvement, and three live repetitions were fixed
before any live Jev output was exposed.

## Source receipt

- GDC release: Data Release 46.0 - August 10, 2026
- API tag: 8.5.0
- API commit: `8f7c2a51ab0084b216ad1b62a3fae8b945439c53`
- Status response: 221 bytes
- Targeted five-project response: 1,265 bytes
- Case, sample, aliquot, file, and molecular records downloaded: 0
- Jev model: `jev-1.13.0`
- Frozen experiment fingerprint: `752e572614a3c42d37a95108a37298c893ecd1e4b12fc2a8cde29b881b894130`
- Projection fingerprint: `9e72485b3056d8eac1dd9f0a14901a353fc3522c50f87f6fed509d583af23888`

## Results

| Metric | Deterministic | Jev reranked (each of 3 runs) |
|---|---:|---:|
| Recall@1 | 0.40 | 1.00 |
| Precision@1 | 0.40 | 1.00 |
| Recall@3 | 1.00 | 1.00 |
| Mean reciprocal rank | 0.667 | 1.00 |

Jev selected the expected project for all five tasks in all three repetitions. Top choices were
stable 3/3, shortlist membership was preserved, and no out-of-shortlist choice occurred. Each
repetition used 1,758 input tokens and 249 output tokens. Latencies were 800.5 ms, 510.7 ms, and
409.3 ms (mean 573.5 ms).

## Decision

The experiment supports a narrowly scoped, deterministic-retrieval-then-Jev-top-choice pattern
for this projection and pinned model. It does not justify a general reranker or automatic
promotion. Deterministic retrieval remains responsible for recall; Jev cannot recover an omitted
candidate.

## Limits

- This is metadata-description matching, not a measure of biological or scientific utility.
- Five queries and two ambiguity groups are too small for generalization.
- TCGA project names may be present in model pretraining, so this does not test novelty.
- Probabilities were degenerate at 0/1 and must not be treated as calibrated confidence.
