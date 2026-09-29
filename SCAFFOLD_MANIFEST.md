# Scaffold manifest

Created: 2026-09-29

## Purpose

This is an experiment-first repository scaffold derived from the canonical OncoJev baseline and current source review. It is not a scientific result and not a complete autonomous lab.

## Implemented now

- flat package topology;
- short navigation-oriented `AGENTS.md`;
- falsifiable thesis and epistemic constitution;
- OnCodex / OncoLab / Discovery / Execution / Jev / OncoX / Store / Observatory boundaries;
- gap taxonomy: MethodGap, CapabilityGap, DecisionGap, HarnessGap;
- separate engineering and scientific readiness;
- deterministic experiment freezing/fingerprinting;
- append-only local event store;
- ScientificEvidence and SemanticProjection types;
- deterministic projection fingerprinting;
- Jev Choice/Noul/Score contracts;
- optional thin TypeSafe adapter;
- optional thin Agents SDK experimental Codex-tool adapter;
- uncertainty-aware frontier contract;
- complete frozen A001-A020 architecture experiment protocols;
- executable A001-A003 scaffold experiments;
- real-data A/B/C evaluation design in docs;
- architecture checks and tests.

## Deliberately not implemented

- GDC/GDAN adapters;
- cancer-specific modalities in core;
- scientific experiment pipelines;
- permanent Wide/Deep Jev batteries;
- full autonomous research loop;
- full OncoX implementation;
- production database;
- production Observatory UI;
- automatic capability engineering/promotion;
- reinforcement learning.

## Verification performed in build environment

- `python scripts/check_architecture.py` — passed.
- `python -m compileall ...` — passed.
- `python -m pytest` — 16 passed.
- `python -m ruff check .` — passed.
- `python -m mypy .` — passed.
- `python -m oncodex status` — passed.
- `python -m oncodex run A001` — offline preflight passed.
- `python -m oncodex run A002` — deterministic test-double path passed.
- `python -m oncodex run A003` — projection-ladder mechanics passed.
- `python -m oncodex run A001 --live` — OpenRouter-backed Agents SDK plus read-only
  `codex_tool` passed.
- `python -m oncodex run A002 --live` — direct TypeSafe/Jev call passed with typed answers
  and usage accounting.

## First recommended next action

Do not add another large architecture layer. Install dependencies locally, run A001 live, then A002 against a small frozen labeled Jev evaluation set, then replace A003's synthetic cases with a small frozen real open cancer-data slice. Let those experiments determine the next abstraction.
