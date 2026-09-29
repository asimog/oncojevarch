# T38 — Define the final repository mental model

Status: COMPLETE
Dependencies: T02, T05, T13
Verdict: KEEP — converge the docs on the two-layer model: scientific thesis vs harness strategy,
with capability evolution as the mechanism that pursues the thesis without predetermining tools.

## Scope

Add one final Mermaid (in `ARCHITECTURE.md`, referenced from README):

- SCIENTIFIC THESIS (does deterministic + Jev + OncoX improve science-efficiency?) and HARNESS
  STRATEGY (how to explore without predefining future science) as distinct layers;
- uncertainty → capability search → explicit gap → evaluated capability evolution → back to
  capability search; capability search feeds deterministic science → Jev → OncoX; the three tiers
  feed A/B/C evaluation → thesis → L0→L4 levels.
- Accompanying statement: capability evolution is the mechanism that allows the system to pursue
  the thesis without assuming in advance what scientific tools future investigations will require.

## Acceptance

- The diagram keeps thesis and harness distinct.
- It agrees with T05's operational flowchart (one is the strategic map, one the operational loop).
- No modality lane appears.

## Verification

Render check + `python scripts/verify.py`.
