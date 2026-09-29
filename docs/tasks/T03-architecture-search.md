# T03 — Reframe architecture as adaptive scientific search

Status: COMPLETE
Dependencies: T00
Verdict: KEEP — `ARCHITECTURE.md` describes roles and boundaries well but reads as a mostly
static flow. Add the search/control framing without adding a fixed pipeline.

## Scope

Edit `ARCHITECTURE.md`:

- describe OncoJev primarily as an **adaptive scientific search system** whose next action depends
  on scientific state, not a stage number;
- list the supported decisions: expand, narrow, replicate, branch, acquire information, change
  representation, investigate deeper, defer, backtrack, stop;
- state that no investigation must traverse the same sequence and no modality sequence is fixed;
- preserve the existing epistemic flow diagram (source → measurement → evidence → state → search →
  experiment → measurement → evidence).

## Acceptance

- Architecture reads as search/control oriented.
- No fixed modality sequence or pipeline stage list appears.
- Existing role sections (OnCodex, OncoLab, Discovery, Execution, Jev, OncoX, Store, Observatory)
  keep their boundaries.

## Verification

`python scripts/verify.py`; manual read-through against this acceptance.
