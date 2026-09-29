# ABC agent runtimes and gap proof

Status: COMPLETE (through the evidence boundary)
Created: 2026-09-30
Completed: 2026-09-30
Base commit: `236a9e2`

## Delivered

- `oncodex/sandbox.py` — sandbox policy, path guard, seeded workspace, append-only action journal.
- `oncodex/abc_runtimes.py` — three independent runtimes: A deterministic, B +OncoX, C +Jev+OncoX;
  call budgets with hard `BudgetExceeded`; typed `JevClient` port; NOUL pursuit gate with a
  deterministic Python policy threshold; Agents SDK arm builders (capability tools + research
  tools + read-only Codex workspace tool rooted in the sandbox + arm-specific ports).
- `oncodex/research_loop.py` already provided the step; tools wired: `inspect_investigation`,
  `run_scientific_operation`, `request_oncox_reasoning`, `request_jev_judgment`.
- Experiment A026 (ABC runtimes) and A027 (gap proof + governed evolution), catalog + CLI wired.
- Tests: `tests/test_abc_runtimes.py` (8), plus A026/A027 tests (162 passed / 5 skipped overall).

## Findings and blockers solved

1. **Global Python lacked the Agents SDK.** Live runs moved to the project venv; the A026 live
   path now records `unavailable` with remediation instead of crashing.
2. **Arm agents were not bound to the configured model.** Fixed by passing the OpenRouter
   `build_agent_model(settings)` model into `build_arm_agent`; live sessions then completed.
3. **Live investigation identity mismatch.** The first live prompt named a non-existent
   investigation; the agents honestly recorded gaps. Fixed with per-arm live investigation and
   operation ids; agents then executed `run_scientific_operation` and admitted evidence.
4. **`Choice.criteria` shape.** The installed typesafe-sdk expects a dict, and the verified live
   pattern is NOUL; the pursuit gate moved to NOUL with threshold 0.5 → policy pursue/defer.
   Live Jev then succeeded from inside arm C (`jev-1.13.0`, value 0.38 → `defer`).
5. **Nested event loops in the OncoX tool.** `asyncio.run` inside the agent's tool execution
   raised "Event is bound to a different event loop"; the tool is now `async` and awaits the
   reasoner in-loop. Arm B and arm C then succeeded live OncoX
   (`deepseek/deepseek-v4.1-flash`).
6. **OncoX structured-output flakiness.** Model-behavior parse failures occurred at one attempt;
   A026 live now uses `max_attempts=2`, `max_tokens=800`. A failed reasoning call is turned into
   an explicit harness gap by arm C — the gap loop working live, recorded as a finding.
7. **Threshold "unfreezing".** Frozen recorded results stay frozen (constitution #12). Threshold
   errors are corrected by new identities; the earlier S001→S002 and A022→A025 corrections stand.
   Live blockers here were environmental and are now removed.
8. **Evidence accumulation across reruns.** A026 now measures evidence delta per run, so bounds
   hold on rerun (the earlier `boundary_held=False` was a rerun artifact).

## Evaluation levels with sandboxed agents

- L0/L1: A026 offline and live — three arms, sandboxes, journals, budgets, admitted evidence only
  from execution; live agents drove the tools.
- L2: S001/S002 remain the recorded retrospective-real runs; the arm runtimes are not yet driven
  through a real-data scientific experiment (next executable step; the runtime path is proven).
- L3: not executed — no independent compatible dataset or compatibility contract artifact exists
  yet; protocol fields are specified in `docs/EVALUATION.md`.
- L4: not executed — no T2 window exists; the frozen-T1 shadow protocol is specified but has no
  object to freeze.

## Reruns

- A001-A027 reran offline: 27/27 recorded. A021-A027 tests and the full suite pass.
- Final verification: architecture OK; compileall OK; 162 passed / 5 skipped; ruff OK; mypy OK
  (136 files).

## Workflow improvements applied from findings

- Arm tool ports are async and loop-safe; model binding is explicit; live sessions use
  run-scoped investigation ids; budgets are per-arm declared and enforced; runtime failures turn
  into recorded gaps instead of silent degradation.
