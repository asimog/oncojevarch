# T20 — Update Concept Book

Status: COMPLETE
Dependencies: T04, T06
Verdict: KEEP — keep `docs/CONCEPT_BOOK.md` canonical; add the capability-search synthesis.

## Scope

Edit `docs/CONCEPT_BOOK.md`:

- update "Four search problems" → five, with capability search first-class (T04);
- add "Capability search and evolution" content:
  - capability search question: what validated scientific or operational capability can produce
    the information required by the next decision?
  - capability evolution triggers only when capability search fails;
  - biological modalities are examples of scientific information, not permanent orchestration
    lanes;
  - OnCodex discovers capabilities from scientific needs;
  - the architecture must absorb measurements not anticipated at repository creation;
  - capability evolution is infrastructure around the three-tier model, not Tier 4.

Preserve all existing sections (epistemic distinctions, projections, representations reranking,
exploration, progressive disclosure, hypothesis science, gaps, evaluation, A/B/C).

## Acceptance

- New synthesis present; nothing existing removed or contradicted.
- No modality lane list appears.

## Verification

`python scripts/verify.py`; read-through.
