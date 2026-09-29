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
- executable A001-A006 architecture experiments;
- real-data A/B/C evaluation design in docs;
- architecture checks and tests.

## Deliberately not implemented

- scientific GDC/GDAN acquisition and analysis pipelines;
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
- `python -m oncodex run A004 --live` — both frozen arms produced 4/4 expected decisions;
  the projection reduced serialized state by 25.27% and input tokens from 1,715 to 1,500.
- `python -m oncodex run A005 --live` — GDC metadata/count ladder resolved 517 TCGA-LUAD
  cases with both RNA-Seq and WXS file associations using three `size=0` count responses and
  no case records or molecular downloads.
- `python -m oncodex run A006 --live` — deterministic top-1 recall/precision improved from
  0.40 to 1.00 after bounded Jev reranking while recall@3 and shortlist membership remained
  1.00 across all three stable repetitions.

## First recommended next action

Proceed to A007 with a frozen mixed set containing adequate and best-of-bad-options cases. Keep
the Choice and absolute-viability Noul judgments distinct and let the measured false-acceptance
tradeoff determine whether an absolute gate is justified.
