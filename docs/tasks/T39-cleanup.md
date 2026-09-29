# T39 — Clean stale documentation and dead abstractions

Status: COMPLETE
Dependencies: T21, T22, T33
Verdict: KEEP — cleanup suppresses entropy after canonical updates. Prefer deletion to layering.

## Known stale items (recon)

- `AGENTS.md` "Initial executable architecture experiments: A001, A002, A003" — stale; A001-A020
  are all executable. Update the experiment line (keep AGENTS.md <= 130 lines; currently 91).
- `SCAFFOLD_MANIFEST.md` "pytest — 16 passed" — stale (now 110 passed / 3 skipped); the "First
  recommended next action" block is superseded by this program.
- `README.md` non-goals / "earned by" wording — handled in T21.
- `docs/EVALUATION.md` open gaps — updated by T33.
- Historical records (`docs/decisions/0001`, exec-plans/completed) are immutable history; do not
  rewrite them.
- Malformed Markdown: prior session fixed README fences; re-scan all docs for fence errors and fix
  any remaining (do not restyle otherwise).
- Dead abstractions proven unused: `evaluation/models.py` trio (T33). Remove; do not keep
  compatibility wrappers.

## Acceptance

- No stale status claim remains that contradicts recorded results or current code.
- Removed items are either code-dead (deleted) or historical (left with their date context).
- `python scripts/verify.py` green.

## Verification

Grep-based re-scan for known stale phrases + verify.
