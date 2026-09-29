# OnCodex architecture-experiment readiness

Status: completed

## Objective

Initialize the repository and make OnCodex ready to begin the A001-A020 architecture
experiment sequence with real OpenAI Agents SDK, experimental `codex_tool`, TypeSafe/Jev,
and OpenRouter integration boundaries.

## Invariants

- ScientificEvidence, JevDecision, Hypothesis, LiteratureContext, and AgentReasoning remain distinct.
- Only A001-A003 are executable in this change; A004-A020 become complete frozen protocols, not
  simulated results.
- External SDK imports remain behind `oncodex` or `jev` adapters.
- Process environment overrides `.env.local`; secrets are never printed or committed.
- Live failures are operational observations, not negative scientific evidence.
- No capability self-promotes and no synthetic result is described as scientific validation.

## Work

- [x] Read the thesis, architecture, epistemic constitution, concept book, evaluation design,
  learning curriculum, experiment catalog, and source map.
- [x] Revalidate the current Agents SDK `codex_tool` and TypeSafe Python SDK contracts.
- [x] Initialize Git and a Python 3.12 virtual environment.
- [x] Load local configuration safely and add an explicit OpenRouter model adapter.
- [x] Correct the TypeSafe adapter to the installed SDK contract.
- [x] Define complete protocols for A001-A020 and expose plan inspection through the CLI.
- [x] Add owner-boundary tests for configuration and protocol completeness.
- [x] Run offline verification and live A001/A002 integration smokes where credentials permit.
- [x] Record verification evidence and move this plan to `completed/`.

## Acceptance criteria

- `python scripts/verify.py` passes in `.venv` including ruff.
- `python -m oncodex status` reports provider readiness without exposing credentials.
- `python -m oncodex plan A020` prints the frozen A/B/C protocol.
- A001 can construct the Agents SDK `codex_tool` only through `oncodex.codex_workspace`.
- A002 can call TypeSafe/Jev using a pinned model through `jev.typesafe_adapter`.
- Every A001-A020 protocol declares data, capabilities, comparison, metrics, falsification,
  decision consequence, budget, and evaluation level.

## Verification evidence

- Python 3.12 virtual environment created; `.[dev,agents,jev]` installed.
- `python scripts/verify.py`: architecture check, compileall, 16 tests, Ruff, and mypy passed.
- `python -m oncodex plan A020`: emitted the complete frozen real-data A/B/C protocol.
- Offline A001, A002, and A003: completed and recorded to the ignored local event store.
- Live A001: OpenRouter-backed Agents SDK agent invoked the read-only Codex workspace tool
  and returned the requested repository facts; no workspace files were modified by the tool.
- Live A002: TypeSafe/Jev 1.13 returned Choice, Noul, and Score answers with probabilities
  and token usage. This demonstrates transport/schema mechanics only.
