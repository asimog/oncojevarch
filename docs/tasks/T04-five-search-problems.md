# T04 — Five search problems

Status: COMPLETE
Dependencies: T03
Verdict: KEEP — `docs/CONCEPT_BOOK.md` currently lists "Four search problems"; capability search
is missing everywhere. Add it as first-class, distinct from candidate search.

## Scope

Edit `ARCHITECTURE.md` and `docs/CONCEPT_BOOK.md`:

1. information search — what evidence/information should be acquired next?
2. representation search — cheapest scientifically sufficient representation for the next decision?
3. capability search — what validated capability can obtain, measure, transform, or judge it?
4. candidate search — which scientific states deserve deeper investigation?
5. explanation search — what accounts for the evidence and what would distinguish alternatives?

State that capability evolution is triggered when capability search finds no applicable capability,
and that capability evolution is not a sixth intelligence tier.

## Acceptance

- Capability search is a first-class search problem in both docs.
- It is not confused with candidate search (which states deserve investigation).
- Capability evolution remains harness infrastructure around the three tiers.

## Verification

`python scripts/verify.py`; grep confirms no "Four search problems" heading remains.
