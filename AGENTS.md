# AGENTS.md

This file is a map, not the project encyclopedia.

## Mission

OncoJev is an experiment-driven autonomous computational cancer-discovery system. Its central hypothesis is that deterministic scientific computation, bounded typed semantic judgment, and selective deep reasoning may improve useful discovery per unit compute.

## Read first

1. `THESIS.md` — falsifiable research thesis.
2. `ARCHITECTURE.md` — current boundaries and dependency rules.
3. `docs/EPISTEMIC_CONSTITUTION.md` — invariants that protect scientific meaning.
4. `docs/CONCEPT_BOOK.md` — Jev, projection, search, and representation concepts.
5. `docs/CAPABILITY_EVOLUTION.md` — gap taxonomy and promotion rules.
6. `docs/EVALUATION.md` — real-data A/B/C and falsification design.
7. `docs/LEARNING_CURRICULUM.md` — concepts to learn before expanding the system.
8. `docs/EXPERIMENT_CATALOG.md` — architecture/scientific experiments.
9. `docs/SOURCES.md` — current primary sources and version notes.
10. `docs/tasks/README.md` — reviewed task program for the current phase (working state).

## Stable rules

- OncoJev is the whole system.
- OnCodex chooses and acts.
- OncoLab constrains, validates, and remembers.
- Discovery searches.
- Execution measures.
- Jev judges bounded semantics.
- OncoX reasons deeply.
- Store persists; it makes no scientific decisions.
- Observatory is read-only.
- ScientificEvidence, JevDecision, Hypothesis, LiteratureContext, and AgentReasoning are distinct.
- Missing is not zero or negative unless a validated contract explicitly says so.
- Operational shard is not scientific population.
- Case, sample, aliquot, and file identities are distinct.
- Freeze scientifically material experiment choices before result exposure.
- A newly generated capability never self-promotes.
- Engineering readiness is not scientific readiness.
- Agent/session memory is not scientific memory.
- Synthetic success is not scientific validation.

## Change discipline

- Prefer the smallest change justified by an experiment or a clear invariant.
- Do not add a framework because it may be useful later.
- Do not add source-specific abstractions to core packages without evidence they generalize.
- Do not hard-code permanent Wide/Deep Jev batteries.
- Keep external SDKs behind adapters.
- Keep provider/model choice at configuration boundaries.
- Record consequential architecture changes in `docs/decisions/`.
- Complex implementation work gets a checked-in plan under `docs/exec-plans/active/`.
- Move completed plans to `docs/exec-plans/completed/`.
- Remove stale docs and dead abstractions rather than layering replacements beside them.

## Experiments

There are only two experiment classes:

- architecture experiments: test OncoJev itself;
- scientific experiments: answer biological/scientific questions.

Architecture experiments do not create cancer ScientificEvidence.
Scientific experiments do not silently redesign OnCodex.

Executable architecture experiments:

- A001-A028 and scientific S001-S004 — all executable; architecture outcomes live in
  `docs/EXPERIMENT_CATALOG.md`, scientific outcomes in `experiments/scientific/catalog.py`.

## Verification

Run from repository root:

```powershell
python scripts/verify.py
```

Before committing a structural change, also inspect:

```powershell
python scripts/check_architecture.py
```

## External integrations

- `openai-agents` is the OnCodex orchestration surface.
- experimental Agents SDK `codex_tool` is isolated behind `oncodex.codex_workspace`.
- `typesafe-sdk` is isolated behind `jev.typesafe_adapter`.

Never place credentials in repository files.
