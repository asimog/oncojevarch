# ADR-0001 — Initial experiment-first scaffold

Status: accepted for scaffold

## Decision

Start with a flat repository containing only epistemic contracts, lab governance primitives, external adapters, persistence, mechanical architecture checks, and executable shells for architecture experiments A001–A003.

Use the OpenAI Agents SDK as the OnCodex orchestration surface. Keep experimental `codex_tool` behind `oncodex.codex_workspace`. Keep TypeSafe behind `jev.typesafe_adapter`. Core tests do not require either SDK.

## Why

Prior attempts accumulated mature architecture before the central Jev/search hypotheses were experimentally established. The new repository must let experiments earn abstractions.

## Consequences

- no GDC/GDAN implementation yet;
- no permanent Jev batteries;
- no production Observatory/UI;
- no automatic capability self-promotion;
- no RL;
- real data should enter early through adapters once A001–A003 mechanics are understood.
