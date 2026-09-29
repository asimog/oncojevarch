# T21 — Reconcile README

Status: COMPLETE
Dependencies: T02, T03
Verdict: KEEP — stale scaffold framing must go; the README is otherwise structurally sound.

## Scope

Edit `README.md`:

- Mission section: "OncoJev is an experiment-driven autonomous computational cancer-discovery
  system."
- Scientific thesis: three-tier A/B/C hypothesis (reference `THESIS.md`).
- Harness strategy: scientific uncertainty → capability search → explicit gap → evaluated
  capability evolution.
- Current phase: A001-A020 tested architecture hypotheses and are recorded (link catalog);
  results include negative/narrowing outcomes; the next phase is using the autonomous harness on
  scientifically meaningful investigations with governed capability emergence (T36 wording).
- Fix stale claims:
  - "capabilities earned by A001-A020" overstates; replace with accurate recorded-results wording;
  - non-goals list must stop calling a scientific A/B/C evaluation a permanent non-goal (A020
    already ran a recorded frontier analysis) and use the T21 non-goal list: hardcoded modality
    lanes, fixed modality enumeration in core, source-specific scientific architecture, permanent
    Jev batteries, global Jev thresholds, capability self-promotion, uncontrolled method invention,
    multi-agent swarms, RL, generic workflow-engine architecture, production UI/DB before needed,
    giant raw downloads by default.
- Repository map: add `docs/tasks/` and note `docs/exec-plans/`.
- Keep quick start, provider configuration, per-experiment list (already corrected last session).

## Acceptance

- No stale runner/status/non-goal claim remains.
- README explains mission, thesis, harness strategy, current phase, non-goals coherently.

## Verification

`python scripts/verify.py`; grep for removed phrases (`earned by A001-A006`,
`scientific A/B/C benchmark` as non-goal) returns none.
