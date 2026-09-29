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
- executable A001-A015 architecture experiments;
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
- `python -m oncodex run A007 --live` — an independent Noul gate reduced false acceptance
  from 1.00 to 0.00 while preserving viable recall at 1.00 across three stable repetitions.
- `python -m oncodex run A008` — beam width 2 improved frozen terminal recall from 0.333 to
  0.833 at 1.48 times the evaluated edges; width 3 reached 1.00 recall.
- `python -m oncodex run A009` — a frozen 2/1/1 promise/uncertainty/novelty allocation
  improved useful recall from 0.50 to 1.00 at the same four-candidate budget.
- `python -m oncodex run A010` — an outcome-blind balanced rejection sample found two useful
  misses among six audited rejections, both assigned actionable follow-up classes.
- `python -m oncodex run A011 --live` — all five valid project-description pairs claimed while
  all fifteen deranged pairs stayed null in each of three stable repetitions.
- `python -m oncodex run A012 --live` — the frozen cascade was **not** supported: bounded Noul
  triage escalated all four live cases (probabilities 0.61–0.92), so OncoX call reduction was 0.00
  against a 0.30 target, with zero false negatives. The OncoX adapter, rubric mechanics, and
  false-negative accounting are retained; a revised triage contract needs a new experiment
  identity.
- `python -m oncodex run A013 --live` — the frozen A011 projection fingerprint matched the
  recorded value; `jev-preview` scored 1.00 decision agreement, 0.0070 drift against a 0.0095
  same-model control, and 0.00391 Brier against a 0.00433 baseline, so the candidate was approved
  for that one contract only.

## First recommended next action

Record A012 as a negative architecture result, then continue with the frozen A013-A020 protocols
one checkpoint at a time, keeping every live slice as small as the question allows.
