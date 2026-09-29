# T36 — Define the next scientific milestone correctly

Status: COMPLETE
Dependencies: T21
Verdict: MODIFIED — define the milestone (README "Current phase" + `docs/EVALUATION.md` next
step); do not start it. Starting it is a separate decision requiring its own frozen experiment
identity, population, and source version.

## Scope

State the milestone in capability-neutral terms:

> Execute the first scientifically meaningful investigation in which OnCodex must determine what
> information is required, search for applicable capabilities, expose gaps where capabilities are
> absent, evolve only justified capabilities, and use the three-tier intelligence system where
> appropriate. The scientific question determines source, measurements, methods, capabilities,
> semantic questions, and follow-up reasoning; the architecture does not.

Explicitly reject "next implement mutation, then expression, then CNV".

## Acceptance

- Milestone text appears in README (and/or EVALUATION) with no modality pipeline.
- It references governed capability emergence (T6-T13), not a fixed pipeline.

## Verification

`python scripts/verify.py`; grep confirms no "then expression"/"then CNV" style statements.
