# A018 — from architecture results to bounded reviewable changes

Status: complete (bounded proposal accepted for review)

## Objective

Turn a recorded architecture result into a bounded, fully traced change proposal that is verified
in a scratch copy and handed to human review, while an unbounded request is rejected.

## Frozen design

- Evidence: the recorded A012 triage over-escalation finding.
- Bounds: at most 40 changed lines, one file touched, full claim traceability.
- Verification: apply in a scratch copy, then `compileall`, focused cascade tests, and architecture
  checks.
- Nothing is applied to the repository.

## Implementation

- `oncolab/proposals.py`: change requests, unified diffs, bounds evaluation, claim traceability,
  scratch-copy verification, and proposal metrics.
- `experiments/architecture/a018_bounded_change_proposal.py`: the two frozen requests, the decision
  record, review findings, and gap classification.
- `tests/test_proposals.py`: 5 focused tests, including scratch verification and the untouched
  worktree.

## Evidence

- Bounded proposal: 13 changed lines, 1 file, traceability 1.00, verification passed in 1.05 s,
  accepted for review.
- Unbounded request: 97 changed lines, 2 files, traceability 0.00, rejected on all three bounds.
- Main worktree unchanged; no promotion.

## Outcome

Bounded proposals with evidence links and scratch verification are adopted as review inputs. The
missing write-capable, review-gated path is classified as a HarnessGap.
