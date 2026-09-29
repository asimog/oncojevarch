# T11 — Formalize DecisionGap routing

Status: COMPLETE
Dependencies: T10
Verdict: KEEP — route exists (`GapKind.DECISION → JEV_DESIGN_EVAL`). Formalize the route and
preserve the no-permanent-battery rule.

## Scope

Edit `docs/CAPABILITY_EVOLUTION.md`:

- DecisionGap definition: exact evidence exists, but a validated bounded semantic judgment needed
  by policy is missing;
- route: bounded semantic question → deterministic projection → candidate Jev capability →
  development evaluation → validation → locked evaluation → bounded activation;
- restate: no permanent global Jev batteries; questions emerge only from an actual decision gap;
  model confidence is not permission (epistemic constitution #8).

## Acceptance

- DecisionGap route ends in bounded activation scoped to an evaluated domain.
- No sentence implies a global/permanent Jev question battery.

## Verification

`python scripts/verify.py`; consistency with `docs/CONCEPT_BOOK.md` section 7 and
`docs/CAPABILITY_EVOLUTION.md` promotion rules.
