# A020 — does deterministic + Jev + OncoX shift the science-efficiency frontier?

Date: 2026-09-30
Class: architecture, recorded-results analysis
Status: completed; frozen failure branch taken — the central hypothesis is narrowed

## Question

Does the combined layer stack (A deterministic, B deterministic plus OncoX, C deterministic plus Jev
plus OncoX) improve scientific utility per unit resource on frozen real-data tasks?

## Frozen design

This checkpoint is a recorded-results analysis over immutable stored experiment results, not a new
prospective comparison. Two tasks had recorded points:

- `a012_oncox_cascade`: quality = useful-case retention (1 minus cascade false-negative rate),
  tokens from the recorded arm resources plus triage usage.
- `a019_masked_rediscovery`: quality = recall@1 divided by the frozen 0.50 target, tokens from the
  recorded arms; arm C's cost includes the Jev screen it contains as well as its OncoX calls.

Dominance: an arm dominates another when it uses no more tokens, loses no quality, and is strictly
better on at least one axis. Arm C moves the frontier only by strictly dominating a recorded arm.

## Results

| Task | Arm | Quality | Tokens | Calls | Non-dominated |
|---|---|---:|---:|---:|---|
| a012_oncox_cascade | B deterministic + OncoX | 1.000 | 13,656 | 4 | yes |
| a012_oncox_cascade | C deterministic + Jev + OncoX | 1.000 | 15,014 | 5 | no |
| a019_masked_rediscovery | A deterministic | 0.545 | 0 | 0 | yes |
| a019_masked_rediscovery | B deterministic + OncoX | 0.545 | 4,580 | 1 | no |
| a019_masked_rediscovery | C deterministic + Jev + OncoX | 0.545 | 4,580 | 2 | no |

Recorded resource facts: A012 cascade call reduction 0.00 with zero false negatives; A019 spent
4,580 Jev tokens and zero OncoX calls because nothing escalated.

The first extraction of this run attributed only OncoX tokens to arm C on the A019 task, which made
C look cheaper than B. That was a bookkeeping error: arm C contains the Jev screen, so the
attribution was corrected before the result was recorded. The corrected frontier is reported here.

## Decision

Arm C did **not** move the frontier on either recorded task, so the frozen failure branch applies:
the central hypothesis is **narrowed**, not confirmed.

- Retain the deterministic core and bounded Jev gating/reranking, whose recorded value appears in
  A006 (top-1 recall 0.40 to 1.00 at unchanged shortlist membership) and A007 (false acceptance 1.00
  to 0.00 at viable recall 1.00).
- Do not claim a frontier shift from Jev-screened OncoX: A012's cascade saved no calls, and where it
  did screen it saved calls at unchanged quality, which is a cost argument rather than a frontier
  movement.
- OncoX stays justified only where all-case deep reasoning is used, and A012's triage contract needs
  a new experiment identity before any redesign.

## Limits

- Two recorded tasks with one representation each cannot settle the central hypothesis.
- Quality axes are task-relative: retention for A012 and target-normalized recall@1 for A019.
- Only A012 recorded a deterministic-plus-OncoX arm and only A019 recorded all three arms, so the
  design is unbalanced.
- A006 and A007 are cited as recorded narrative evidence, not as frontier points in this analysis.
- Token counts are provider-reported; no monetary cost is claimed.
- This analysis cannot establish scientific discovery.
