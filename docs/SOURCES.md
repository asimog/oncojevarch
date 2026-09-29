# Source map

Verified 2026-09-29. Re-check current documentation before changing external adapters.

## OpenAI harness / Agents / Codex

- Harness Engineering: https://openai.com/index/harness-engineering/
  - Transferable lessons used here: short `AGENTS.md` as a map; repository knowledge as system of record; progressive disclosure; mechanically enforced architecture; agent-legible logs/tools; plans in-repo; continual entropy cleanup.
  - This is an OpenAI engineering experience report, not a guarantee that every pattern generalizes to OncoJev.
- Codex App Server / harness: https://openai.com/index/unlocking-the-codex-harness/
  - Threads, turns, tool execution, auth/config, and event streaming belong to the Codex harness; OncoLab still owns scientific memory.
- Agents SDK: https://openai.github.io/openai-agents-python/
- Agents SDK tools / experimental `codex_tool`: https://openai.github.io/openai-agents-python/tools/
  - `codex_tool` is explicitly experimental; keep it behind an adapter.
- Agents SDK context: https://openai.github.io/openai-agents-python/context/
  - Local app context is distinct from model-visible context.
- Agents SDK sessions: https://openai.github.io/openai-agents-python/sessions/
  - Sessions preserve conversation history; they are not the scientific record.
- Agents SDK testing: https://openai.github.io/openai-agents-python/testing/
- Agents SDK model providers: https://openai.github.io/openai-agents-python/models/litellm/
- OpenAI Codex Python SDK: https://github.com/openai/codex/tree/main/sdk/python
  - Separate stable embedding option for Codex threads/turns; not required by the initial Agents-SDK `codex_tool` path.

Versions observed at scaffold creation:

- `openai-agents` 0.22.3 (PyPI release 2026-09-17)
- `openai-codex` 0.158.0 (PyPI release 2026-09-28)

## TypeSafe / Jev

- Documentation index requested by project baseline: https://docs.typesafe.ai/llms.txt
- TypeSafe: https://typesafe.ai/
- API/docs: https://docs.typesafe.ai/

The live documentation index and Python SDK usage page were revalidated on 2026-09-29.
The current SDK constructs `TypeSafeClient` with the pinned model and sends state plus a
mapping of typed questions through `system_one`. Live scientific use still requires a frozen,
domain-specific evaluation; successful transport is not semantic validation.

Concepts intentionally represented in the scaffold:

- state + bounded typed questions;
- Choice/Noul/Score;
- raw probabilistic decisions;
- question-specific projections;
- code-owned policy;
- no global confidence threshold;
- batching/fan-out/reranking/beam search as experiments rather than baked architecture;
- offline autoresearch for candidate Jev capabilities, never self-promotion.

Version observed at scaffold creation:

- `typesafe-sdk` 0.7.2 (PyPI release 2026-09-26)

## GDC/NCI reference sources

Reference only, not architecture dependencies:

- https://github.com/NCI-GDC/gdc-models
- https://github.com/NCI-GDC/gdc-workflow-overview
- https://github.com/NCI-GDC/gdcdatamodel2
- https://github.com/NCI-GDC/gdc-client
- https://docs.gdc.cancer.gov/API/Users_Guide/Getting_Started/
- https://docs.gdc.cancer.gov/Data_Dictionary/

Extract general lessons about source contracts, entity identity, harmonization, provenance, query strategy, cheap representations, and reproducibility.
