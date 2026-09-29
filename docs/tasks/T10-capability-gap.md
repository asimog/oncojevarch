# T10 — Formalize CapabilityGap routing

Status: COMPLETE
Dependencies: T09
Verdict: KEEP — route exists (`GapKind.CAPABILITY → ENGINEERING`) and the promotion pipeline is
partly documented (`docs/CAPABILITY_EVOLUTION.md` "Promotion"). Formalize the full route.

## Scope

Edit `docs/CAPABILITY_EVOLUTION.md`:

- CapabilityGap definition: method/operation understood sufficiently, but no executable validated
  capability implements it;
- route: bounded engineering specification → Codex/engineering capability → implementation →
  focused tests → architecture checks → verification → scientific evaluation if scientifically
  consequential → versioned capability;
- restate: Codex receives bounded specifications; generated code cannot self-promote
  (matches `oncolab/capabilities.py` one-step advancement and A015/A018 recorded results).

## Acceptance

- The documented route matches the code-enforced promotion gates.
- "Bounded specification before implementation" is explicit.

## Verification

`python scripts/verify.py`; `tests/test_capability_promotion.py`, `tests/test_gap_routing.py`.
