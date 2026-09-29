# T05 — Canonical adaptive-search flowchart

Status: COMPLETE
Dependencies: T03, T04
Verdict: MODIFIED — publish the canonical Mermaid flow in `ARCHITECTURE.md`, adapted to the
repository's actual vocabulary, and labeled with what is implemented today. It must not imply
unimplemented components (evidence admission, Jev/OncoX agent wiring) already exist.

## Scope

- Add one Mermaid flowchart to `ARCHITECTURE.md` covering: mission → OnCodex/OncoLab → uncertainty
  → information/representation/capability search → applicable-capability check → explicit gap →
  capability evolution → execution → evidence admission → ScientificEvidence → candidate search →
  projection → Jev → Python policy → OncoX explanation search → hypotheses → frozen experiment →
  deterministic execution → store/observatory; with the constraints that Jev and OncoX cannot
  create measured evidence.
- Beneath it, the canonical role sentence set (OnCodex chooses and acts; OncoLab constrains,
  validates, remembers; Execution measures; Jev judges; Python decides; OncoX explains and
  hypothesizes; Store persists; Observatory reads).
- Mark implemented vs target edges explicitly: evidence admission and agent-side Jev/OncoX
  invocation are contracts today, not wired production paths.

## Acceptance

- Diagram renders as Mermaid (no syntax errors) and matches the canonical flow.
- Implemented/target distinction is honest and verifiable against code.
- No fixed modality sequence in the diagram.

## Verification

Render check (Mermaid syntax) + read-through; `python scripts/verify.py`.
