from __future__ import annotations

from oncox.ports import ReasoningOutput, ReasoningRequest, ReasoningResult


class StaticReasoner:
    """Deterministic twin used where a bounded reasoning port is required but no model runs.

    Its output is an explicitly labeled test double and must never be treated as model evidence.
    """

    async def reason(self, request: ReasoningRequest) -> ReasoningResult:
        return ReasoningResult(
            output=ReasoningOutput(
                interpretation="static test double: bounded interpretation placeholder",
                hypotheses=(),
                alternative_explanations=(),
                proposed_tests=(),
                unresolved_uncertainty=(),
            ),
            model_id="static-test-double",
            usage={"input_tokens": 0, "output_tokens": 0},
            latency_ms=0.0,
            raw_output="static test double: no model was called",
        )
