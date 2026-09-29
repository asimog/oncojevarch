# A016 — bounded progressive context versus full history

Date: 2026-09-30
Class: architecture, synthetic
Status: completed; frozen failure branch taken — bounded context not adopted

## Question

Does a deterministic bounded progressive context view preserve OnCodex task success at lower input
cost than replaying the raw full history?

## Frozen design

Three frozen synthetic investigation histories with recorded facts and later corrections, each
asked one locked question whose answer requires the latest value and forbids the superseded one.

- Arm `full_history`: the entire history is supplied.
- Arm `bounded_progressive`: a deterministic view that pins the latest value of every fact key,
  drops fact-only messages from the window, then drops the oldest messages until the character
  budget is met; every dropped message id is recorded.
- Frozen parameters: recency window 6, character budget 1,400, two repetitions, at most three
  concurrent turns.
- Adoption requires that bounded context never loses task success, always reduces input tokens, and
  is stable across repetitions.

## Results

| Metric | Repetition 1 | Repetition 2 |
|---|---:|---:|
| Full-history success | 0.667 | 0.667 |
| Bounded success | 0.667 | 1.000 |
| Full-history contradictions | 0 (0.00) | 1 (0.33) |
| Bounded contradictions | 1 (0.33) | 0 (0.00) |
| Input-token reduction | 0.012 | 0.302 |
| Character reduction | ~40% | ~40% |
| Full-history input tokens | 1,018 | 1,192 |
| Bounded input tokens | 1,006 | 832 |
| Mean latency delta | +1.10 s | +1.42 s |

Every task that failed failed on a superseded value: in repetition 2 the full-history arm reported
`537` for the corrected KIRC count, and in repetition 1 the bounded arm was flagged for containing
the phrase "Expression Array" while answering the platform question.

## Decision

Bounded context is **not** adopted. Repetition stability failed (the bounded arm scored 0.667 then
1.000 with contradictory outcomes), token savings were marginal in one repetition because the fixed
instruction block dominates at this history size, and the contradiction signal itself is lexical.

The bounded view builder is retained as a deterministic, auditable context projection: it pinned
the corrected values, dropped the superseded messages, and recorded every dropped id.

## Limits

- Histories and tasks are frozen synthetic fixtures, not real agent sessions.
- The contradiction check is lexical and cannot separate "reported the superseded value as current"
  from "mentioned that a value was superseded"; the repetition-1 bounded flag is that artifact.
- Three tasks and two repetitions cannot establish general context behavior.
- Character budget is a proxy for tokens, and the provider tokenizer ultimately decides cost.
