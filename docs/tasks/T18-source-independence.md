# T18 — Preserve source independence

Status: COMPLETE
Dependencies: T00
Verdict: KEEP — no source-specific science exists in core today; the GDC adapter is confined to
`execution/gdc.py` and experiment modules. Documentation formalization plus one check (see T34).

## Scope

- Document the source path explicitly (in `ARCHITECTURE.md` or the T05 flowchart section):
  external response → source-specific parser → typed acquisition record → scientific capability →
  typed scientific result → ScientificEvidence.
- State the prohibition: no `GDCScience`/`TCGAScience`/`GDANScience` style generic scientific
  architecture; source-specific details terminate at adapters.
- Keep `execution/gdc.py` as the single read-only public-metadata adapter.

## Acceptance

- The documented path matches code: `execution/ports.py` types, `execution/gdc.py` adapter,
  experiment-level parsing (A005/A006/A012/A019).
- No core package imports a source adapter except the adapter's own package and experiments.

## Verification

`python scripts/verify.py`; T34 adds a containment check.
