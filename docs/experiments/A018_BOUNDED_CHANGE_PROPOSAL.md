# A018 — from architecture results to bounded reviewable changes

Date: 2026-09-30
Class: architecture, synthetic
Status: completed; frozen criteria met for the bounded proposal

## Question

Can a completed architecture result justify a small, reviewable repository change without an
unbounded edit and without a claim that has no evidence?

## Frozen design

Evidence: the recorded A012 result that bounded triage escalated every live case, so the cascade
saved no OncoX calls at a frozen 0.30 target.

Two change requests were compiled deterministically against the repository baseline:

- `bounded_triage_wording`: reword the A012 triage question in one file, with every claim traced to
  a recorded A012 finding.
- `unbounded_rewrite`: rewrite the cascade, rubric, and thresholds together, add a new module, and
  carry no evidence links.

Frozen bounds: at most 40 changed lines, one file touched, and full claim traceability. Verification
applies the patch in a scratch copy of the repository and runs `compileall`, the focused cascade
tests, and `scripts/check_architecture.py`.

## Results

| Metric | Bounded proposal | Unbounded request |
|---|---:|---:|
| Changed lines | 13 | 97 |
| Files touched | 1 | 2 |
| Claim traceability | 1.00 | 0.00 |
| Compiled in scratch copy | yes | not attempted |
| Focused tests | passed | not attempted |
| Architecture checks | passed | not attempted |
| Verification duration | 1.05 s | — |
| Accepted for review | yes | rejected |

`max_changed_lines` across proposals was 97 and the verification pass rate over verified proposals
was 1.00. The unbounded request was rejected on all three bounds before any verification ran. The
main worktree was never modified: the bounded proposal exists only as a recorded diff.

Review findings recorded with the proposal: the wording change alters a frozen A012 input, so it can
only justify a **new experiment identity**, never a post-result edit of A012; the Codex workspace
tool is read-only, so no agent path could apply a patch anyway; and acceptance means ready for human
review, not promotion.

## Decision

The bounded proposal is accepted for human review and stored with its diff, evidence links, and
verification transcript. Nothing is applied, promoted, or self-promoted.

Gap classification: the missing write-capable, review-gated proposal path is a **HarnessGap**
(`harness_engineering`), not a capability or method gap.

## Limits

- The proposal was compiled deterministically by code, not by an autonomous agent turn.
- Verification covers one focused test file, not the whole suite.
- A scratch copy is not an isolated environment: it shares the interpreter and site packages.
- The change is scoped to a future experiment identity and has no scientific standing.
