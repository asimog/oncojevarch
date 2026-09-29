# A005 GDC representation ladder

Status: completed

## Objective

Execute A005 against the smallest useful public GDC API responses to determine when richer
representations materially improve a deterministic acquisition decision.

## Frozen question

For TCGA-LUAD, what is the cheapest representation that can establish whether enough cases have
both RNA-Seq and WXS file associations to justify a later paired-modality feasibility study?

The architecture-only feasibility gate is at least 100 paired cases and at least 50% of project
cases. This gate does not establish assay compatibility, sample pairing, or scientific validity.

## Representation ladder

1. Project metadata: establishes project scope, not modality availability.
2. File facets: establishes that both strategies exist, not within-case overlap.
3. Three `size=0` case counts: RNA-Seq, WXS, and their union. Code derives the intersection by
   inclusion-exclusion without retrieving case records or molecular files.

## Invariants

- GDC source/version is recorded before evaluation.
- Case counts are operational metadata, not a scientific population or ScientificEvidence.
- Exact counting and set arithmetic remain deterministic code; Jev is not used where unnecessary.
- No controlled files or molecular payloads are downloaded.
- Source failure is recorded as operational failure, never a biological negative.

## Test-authoring gate

- Observable contract: overlap arithmetic must reject impossible counts and compute the exact
  intersection and coverage used by the acquisition decision.
- Credible regression: malformed or drifted counts could silently produce negative/impossible
  overlap or an unjustified proceed decision.
- Existing tests do not cover cross-query count consistency or representation sufficiency.
- No test-only seam is added; the arithmetic is the production decision boundary.

## Work

- [x] Add a narrow read-only GDC HTTP adapter under `execution`.
- [x] Add deterministic paired-coverage and feasibility evaluation.
- [x] Add the executable A005 offline/live experiment and CLI registration.
- [x] Run focused tests, full verification, and the live GDC experiment.
- [x] Record results, complete the plan, commit, and push.

## Acceptance criteria

- A005 reaches a decision using metadata/aggregate responses only.
- The result records API release, query URLs, response bytes, latency, counts, and limitations.
- Invalid inclusion-exclusion inputs fail closed.
- Full repository verification passes.

## Verification evidence

- Focused representation/catalog tests: 6 passed.
- Offline A005 froze the project, modalities, gate, ladder, and experiment fingerprint.
- Live source: GDC Data Release 46.0, API tag 8.5.0.
- Project metadata: 585 cases and 36,740 files in TCGA-LUAD.
- File facets: 5,409 RNA-Seq files and 10,096 WXS files; overlap remained unresolved.
- Three `size=0` count responses totaled 417 bytes and resolved 517 paired cases (88.38%).
- Decision: `proceed_to_sample_compatibility_check`.
- No case records, controlled data, or molecular payloads were downloaded; no Jev call was made.
- Durable result: `docs/experiments/A005_GDC_REPRESENTATION_LADDER.md`.
