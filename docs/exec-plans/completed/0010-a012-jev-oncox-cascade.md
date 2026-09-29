# A012 — Jev triage versus OncoX on every case

Status: complete (negative result recorded)

## Objective

Test whether a bounded Jev triage decision can select the cases where expensive open-ended
reasoning is worth paying for, without losing cases that all-case reasoning would have resolved
usefully.

## Frozen design

- Ten locked cases built from real public GDC project aggregates (Data Release 46.0), five closed
  and five open by construction; the live slice used the smallest balanced subset
  (c01, c05, c06, c09).
- One frozen rubric per case with recorded (already in the state) and novel considerations, with a
  mechanical invariant that no novel marker may appear in the frozen state.
- Arm ALL: OncoX on every case. Arm CASCADE: one batched Noul triage call, then OncoX only on
  escalated cases. Triage was computed before any OncoX output existed.
- Frozen triage threshold 0.5, maximum quality loss 0.05, minimum OncoX call reduction 0.30, two
  live repetitions.

## Implementation

- `oncox/ports.py`: `ReasoningRequest` carries the structured state; `ReasoningResult` carries the
  resource account.
- `oncox/agents_adapter.py`: the smallest real OncoX adapter over the Agents SDK, with a bounded
  structured output schema, bounded retries, recorded attempts, and provider/model choice injected
  at the edge.
- `evaluation/cascade.py`: frozen rubric matching, triage crossings, and cascade metrics with
  explicit false-negative reporting.
- `experiments/architecture/a012_jev_oncox_cascade.py`: locked cases, projection, capability, and
  the two-arm repetition runner.
- `scripts/check_architecture.py`: `oncox` may no longer import `oncodex`.

## Protocol adjustments before any result existed

Three live attempts failed with provider structured-output errors and produced no arm result: an
unparseable completion, then `finish_reason: length` with empty content when a completion cap was
consumed by reasoning tokens. A bounded retry (two attempts) was frozen, the completion cap was
removed (OpenRouter counts reasoning tokens inside `max_tokens`), reasoning effort was pinned to
`low`, and the live slice was reduced to four cases. No case, rubric, threshold, metric, arm, or
comparison changed.

## Evidence

- Focused cascade/oncox tests: 19 passed; full gate green.
- Frozen fingerprint `e22890bf…`, projection fingerprint `f10ada8b…`.
- Triage escalated 4/4 cases in both repetitions at probabilities 0.61–0.92.
- OncoX call reduction 0.00 in both repetitions; false negatives 0; quality loss 0.15 then -0.10.
- Useful cases were c06 and c09 (repetition 1) and c06 only (repetition 2); the label moved.
- OncoX: 4 calls per arm per repetition, ~2,000 input and ~10–11.6k output tokens per arm;
  triage: 2,144 input and 92 output tokens per repetition.
- GDC transfer: 9,883 project bytes plus 221 status bytes; no case or molecular data.

## Outcome

The cascade is not supported for this task and contract: triage over-escalated, so savings missed
the frozen target, and the revision must be a new experiment identity rather than a post-result
edit of A012. All-case reasoning remains justified for this task. The adapter, rubric mechanics,
and false-negative accounting are retained.
