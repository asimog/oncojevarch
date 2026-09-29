# A016 — bounded progressive context versus full history

Status: complete (negative; bounded context not adopted)

## Objective

Compare replaying a raw full investigation history with a deterministic bounded progressive view,
scoring task success, contradiction rate, input tokens, and latency.

## Frozen design

- Three synthetic histories with recorded facts and later corrections; one locked question each.
- Arm `full_history` versus arm `bounded_progressive` (pinned latest facts, fact-only messages
  pruned, oldest messages dropped to meet a character budget).
- Adoption requires no success loss, an input-token reduction, and repetition stability.

## Implementation

- `oncodex/context.py`: history messages, bounded view construction, renderers.
- `oncodex/harness.py`: one bounded OnCodex harness turn with structured output.
- `evaluation/context.py`: answer scoring, arm evaluation, and the paired comparison.
- `experiments/architecture/a016_progressive_context.py`: frozen histories/tasks, both arms,
  repetitions, and the decision record.
- `tests/test_progressive_context.py`: 8 focused tests.

## Evidence

- Bounded success 0.667 then 1.000 against a stable 0.667 for full history: stability failed.
- Input-token reduction 0.012 then 0.302; character reduction about 40%.
- One contradiction per arm, in different repetitions, both lexical matches of superseded values.
- Bounded views pinned corrected values and dropped fact-only messages in every task.

## Outcome

Failure branch taken: bounded context is not adopted for this task set. The view builder is
retained as an auditable deterministic projection, and the lexical contradiction check is recorded
as a measurement limitation.
