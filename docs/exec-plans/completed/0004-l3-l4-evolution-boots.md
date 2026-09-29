# L3, L4, boots, and automated evolution

Status: COMPLETE through the evidence boundary
Created: 2026-09-30
Completed: 2026-09-30
Base commit: `4ebb1f3`

## Executed

- **L3 independent/compatibility validation (S003)**: compatibility contract artifact
  `s003-gdc-raw-vs-gdan-analysis-layer` frozen before execution. cBioPortal was skipped per
  instruction; the independent side is the GDAN/GDAC analysis layer published through the GDC API
  (Transcriptome Profiling and Simple Nucleotide Variation data categories) against the S002 raw
  layer (RNA-Seq/WXS strategies). Live result: **analysis-layer rate 1.0000 vs raw-layer
  reference 1.0000 — compatible reproduction** within the declared 0.20 tolerance, over 33
  projects. Arm A and arm C (live OncoX + Jev judgment) drove the run in sandboxes; evidence
  admitted. Limitation recorded: layer-level independence only, not cross-database independence.
- **L4 temporal shadow (S004)**: T1 frozen live on 2026-09-29 with an explicit falsifiable
  prediction, T1 cutoff, source version (Data Release 46.0), and a due time of
  `2026-09-30T22:36:41Z`; T2 recorded `pending` rather than simulated. An automated T2 check is
  scheduled (session cron at the due time) and `python -m oncodex run S004 --live` evaluates the
  prediction as `prediction_supported` or `prediction_falsified` after the due time.
- **Real-data experiment through arm A/C**: S003 executed through `execute_arm_program` (A
  deterministic; C with live OncoX and one bounded Jev judgment `0.4 → defer`) with sandbox
  journals and recorded budgets.
- **Whole-response capture**: `ReasoningResult.raw_output` (full structured model payload) and
  `JevDecision.raw` (full provider response) are now recorded; ABC records/tools carry them, and
  the live boot run returned the complete OncoX interpretation verbatim.
- **Budget policy**: enforcement is opt-in (`CallBudget(enforce=False)` records calls without
  blocking); enforced mode is retained and covered by tests.
- **Independent agent boots**: `oncodex/agent_boots.py` builds OnCodeX, OncoX, and OnCoLab agents
  with distinct, boundary-tested tool surfaces; the OnCodeX controller composes the others via
  Agents SDK `as_tool`. `python -m oncodex boot <target> [--prompt]` boots any of them. Live test:
  the controller invoked the independent OncoX agent and returned its full bounded
  interpretation.
- **Automated capability evolution**: `oncolab/evolution.py` (plan from gap; verification-gated
  promotion; MethodGap refused) plus experiment A028: failed verification stays draft, passed
  verification advances one step at a time, a declared evaluation promotes, zero unsafe
  promotions.

## Verification

architecture OK; compileall OK; 170 passed / 5 skipped; ruff OK; mypy OK (144 files); venv boot
contract tests pass with the Agents SDK installed. Live runs: S003 (completed, compatible
reproduction), S004 (T1 frozen, T2 pending by definition), A026 (live arms), boot controller
(live).

## Remaining by construction

- T2 evaluation requires wall-clock time; the scheduler and checker are in place.
- L3 independence is layer-level until a second database-level source is accessible.
