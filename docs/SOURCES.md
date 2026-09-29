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

## OpenRouter provider route (OncoX / OnCodex model edge)

- Model card and confirmed APIs: https://openrouter.ai/deepseek/deepseek-v4.1-flash/llms.txt
- Reasoning token control: https://openrouter.ai/docs/guides/overview/models
- Models list: https://openrouter.ai/api/v1/models

Facts revalidated 2026-09-29 for the pinned live route `deepseek/deepseek-v4.1-flash`:

- the only confirmed OpenRouter API serving this model is Chat Completions
  (`POST /api/v1/chat/completions`), which is the surface the Agents SDK
  `OpenAIChatCompletionsModel` boundary already uses; the Responses API is not required and was
  not adopted;
- `supported_parameters` includes `response_format` and `structured_outputs`, so the SDK's
  `json_schema` response format is a supported request shape;
- `reasoning.supported_efforts` is `["max", "high", "low"]` with `default_effort: "high"` and
  `mandatory: false`;
- reasoning tokens are counted as output tokens and count against `max_tokens`, so a small
  `max_tokens` cap can be consumed entirely by reasoning and return `finish_reason: length` with
  empty content. OncoX therefore leaves the completion budget at the provider default and pins
  `reasoning.effort` explicitly per experiment.
- `usage.cost` is returned by OpenRouter, but the Agents SDK usage object used here exposes token
  counts only; OncoX records tokens and does not invent a monetary estimate.

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

Models offered by the account on 2026-09-30 (read through `TypeSafeClient.models.list()`):

- `jev-1.13.0` — the pinned model used by A002-A012;
- `jev-latest` (released 2026-09-10);
- `jev-preview` (released 2026-09-10).

A model upgrade is a governed change: A013 re-evaluates a candidate against recorded baseline
responses and frozen tolerances before any contract adopts it.

## GDC/NCI reference sources

Reference only, not architecture dependencies:

- https://github.com/NCI-GDC/gdc-models
- https://github.com/NCI-GDC/gdc-workflow-overview
- https://github.com/NCI-GDC/gdcdatamodel2
- https://github.com/NCI-GDC/gdc-client
- https://docs.gdc.cancer.gov/API/Users_Guide/Getting_Started/
- https://docs.gdc.cancer.gov/API/Users_Guide/Search_and_Retrieval/
- https://docs.gdc.cancer.gov/Data_Dictionary/

Live A005 metadata queries were run against GDC Data Release 46.0 (2026-08-10), API tag
8.5.0. The experiment used project metadata, file facets, and `size=0` case counts only.
Re-check `/status` and record the release for every future GDC experiment.

Extract general lessons about source contracts, entity identity, harmonization, provenance, query strategy, cheap representations, and reproducibility.
