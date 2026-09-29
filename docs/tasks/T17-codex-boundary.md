# T17 — Keep Codex on the engineering side

Status: COMPLETE
Dependencies: T14
Verdict: KEEP — already true in code (`oncodex/codex_workspace.py` is a lazy-import, read-only,
repo-root-confined adapter; the prompt says "keep it behind a narrow adapter"). Documentation
formalization only; no code change expected.

## Scope

Edit `ARCHITECTURE.md` (Codex boundary note) or keep in existing OnCodex text if it already fits:

- Codex is a bounded engineering capability, never in the scientific evidence path;
- the preferred relationship: scientific gap → OnCodex → bounded engineering specification →
  Codex → small implementation → verification → candidate capability → evaluated registration;
- Codex must not: alter scientific questions, alter frozen experiments, redefine populations,
  replace deterministic statistics with reasoning, reinterpret failed results until they pass,
  create ScientificEvidence, or self-promote capabilities.

## Acceptance

- The six prohibitions above appear and match existing code guards (read-only sandbox;
  `oncolab` promotion gates; proposals verified in scratch copy by `oncolab/proposals.py`).
- No new dependency from a domain package onto the Codex adapter.

## Verification

`python scripts/verify.py`; `scripts/check_architecture.py` forbidden-import rules unchanged.
