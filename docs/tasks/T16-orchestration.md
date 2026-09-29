# T16 — Begin minimal Agents SDK orchestration

Status: COMPLETE
Dependencies: T06, T07, T08
Verdict: MODIFIED — build the smallest research tool surface over the (now searchable) capability
layer; keep the A001 smoke agent semantics unchanged so its recorded result stays valid.

## Scope

- New module `oncodex/capability_tools.py`:
  - pure, deterministic functions: `search_capabilities(need, kind?, limit?)`,
    `load_capability(capability_id, version)`, `record_gap(need, kind, evidence, unmet?)`;
  - thin `agents`-SDK `function_tool` wrappers built lazily, importable without the SDK;
  - registry/ledger injection (no global state).
- `oncodex/agent.py`: add `build_oncodex_research_agent(settings, registry, gap_store)` that
  composes the read-only Codex workspace tool + capability tools with research-oriented
  instructions; leave `build_oncodex_agent` and its smoke instructions untouched.
- Do not wire Jev/OncoX invocation yet: no evaluated per-decision Jev capability exists, and
  OncoX must not be improvised into the evidence path. Record as remaining gap in T40.
- Review current official Agents SDK docs before touching integration code (context7/webfetch).

## Acceptance

- Capability discovery does not require loading every full capability into context.
- Absence of an applicable capability is an explicit tool outcome leading to `record_gap`.
- Underlying tool functions are testable without the `agents` extra; wrapper smoke-tests skip
  gracefully when it is absent (same pattern as `tests/test_oncox_adapter.py`).
- If every Agents SDK thread/session disappears, recorded gaps and registry state remain
  reproducible from OncoLab/store.

## Verification

New tests (`tests/test_capability_tools.py`) + `python scripts/verify.py`.

## Findings (2026-09-30)

- `oncodex/capability_tools.py` provides pure `*_impl` functions plus `build_capability_tools`;
  `oncodex/agent.py` adds `build_oncodex_research_agent` and leaves the A001 smoke builder
  untouched.
- Wrapper path exercised in the venv with the agents SDK installed: the three tools build
  (`search_capabilities`, `load_capability`, `record_gap`).
- Jev/OncoX invocation tools are deliberately not wired: no evaluated per-decision Jev capability
  exists yet. Recorded as a remaining gap.
