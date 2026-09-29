# T09 — Formalize MethodGap routing

Status: COMPLETE
Dependencies: T01
Verdict: KEEP — code already routes MethodGap to `SCIENTIFIC_RESEARCH` (`oncolab/gaps.py:21-26`)
and A015 recorded combined-signal routing at 14/14. This is a documentation formalization.

## Scope

Edit `docs/CAPABILITY_EVOLUTION.md`:

- MethodGap definition: a scientifically justified method needed for progress is not established;
- route: methodological/scientific research → candidate method → method evaluation →
  scientifically defensible method → if code is absent, CapabilityGap;
- explicit prohibition: MethodGap is never routed directly to Codex implementation; a reasoning
  model may not invent a method and treat it as validated.

## Acceptance

- Method invention and software implementation remain separate epistemic events in the documented
  route.
- The documented route matches `ROUTES[GapKind.METHOD] == SCIENTIFIC_RESEARCH`.

## Verification

`python scripts/verify.py`; `tests/test_gap_routing.py` continues to pass.
