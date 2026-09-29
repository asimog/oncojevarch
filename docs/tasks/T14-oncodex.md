# T14 — Clarify OnCodex responsibilities

Status: COMPLETE
Dependencies: T03
Verdict: KEEP — `ARCHITECTURE.md` has a short OnCodex paragraph; the responsibility set and the
anti-pattern statement are missing.

## Scope

Edit `ARCHITECTURE.md` OnCodex section:

- responsibilities (target): inspect scientific state; identify unresolved uncertainty; choose
  what to investigate next; search capabilities; progressively load contracts; verify
  applicability; invoke allowed capabilities; expose explicit gaps; request richer
  representations; manage frontier/search decisions; request bounded Jev judgments where useful;
  invoke OncoX selectively; propose experiments; branch, backtrack, defer, stop;
- explicit anti-pattern: OnCodex must not become a giant hardcoded pipeline coordinator;
- state the acceptance test: the next action can depend on scientific state rather than a stage
  number.

## Acceptance

- Responsibilities are state-driven, not stage-driven.
- Anti-pattern is explicit.
- Consistent with T16 (tools make the loop mechanically possible) and with the constitution.

## Verification

`python scripts/verify.py`; read-through.
