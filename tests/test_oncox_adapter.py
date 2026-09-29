import asyncio
import importlib
import json
from typing import Any

import pytest

from oncox.agents_adapter import (
    AgentsOncoXReasoner,
    reasoning_output_model,
    reasoning_prompt,
    to_reasoning_output,
)
from oncox.ports import ReasoningRequest


def _import_or_skip(module: str) -> Any:
    try:
        return importlib.import_module(module)
    except ImportError:
        pytest.skip(f"{module} is not installed")


class _Structured:
    interpretation = "the comparison is confounded"
    hypotheses = ["tumor purity could explain the difference"]
    alternative_explanations = ["assay mix differs"]
    proposed_tests = ["measure purity per case"]
    unresolved_uncertainty = ["purity is unmeasured"]


class _BlankInterpretation:
    interpretation = "   "
    hypotheses: list[str] = []
    alternative_explanations: list[str] = []
    proposed_tests: list[str] = []
    unresolved_uncertainty: list[str] = []


class _NonTextItem:
    interpretation = "ok"
    hypotheses: list[Any] = ["ok", 3]
    alternative_explanations: list[str] = []
    proposed_tests: list[str] = []
    unresolved_uncertainty: list[str] = []


def test_structured_output_converts_into_the_port_type() -> None:
    output = to_reasoning_output(_Structured())

    assert output.interpretation == "the comparison is confounded"
    assert output.hypotheses == ("tumor purity could explain the difference",)
    assert output.alternative_explanations == ("assay mix differs",)
    assert output.proposed_tests == ("measure purity per case",)
    assert output.unresolved_uncertainty == ("purity is unmeasured",)


def test_unstructured_prose_is_rejected() -> None:
    with pytest.raises(ValueError, match="unstructured"):
        to_reasoning_output("a paragraph of free text")


def test_blank_interpretation_is_rejected() -> None:
    with pytest.raises(ValueError, match="non-empty interpretation"):
        to_reasoning_output(_BlankInterpretation())


def test_non_text_considerations_are_rejected() -> None:
    with pytest.raises(ValueError, match="only text"):
        to_reasoning_output(_NonTextItem())


def test_bounded_reasoning_schema_matches_the_port_contract() -> None:
    _import_or_skip("pydantic")

    schema = reasoning_output_model().model_json_schema()

    assert set(schema["properties"]) == {
        "interpretation",
        "hypotheses",
        "alternative_explanations",
        "proposed_tests",
        "unresolved_uncertainty",
    }


def test_reasoning_prompt_carries_identity_question_and_state() -> None:
    request = ReasoningRequest(
        investigation_id="c01",
        evidence_ids=("gdc-project:TCGA-KIRC",),
        question="what remains open?",
        structured_state={"b": 1, "a": [2]},
    )

    prompt = reasoning_prompt(request)

    assert "INVESTIGATION: c01" in prompt
    assert "gdc-project:TCGA-KIRC" in prompt
    assert "QUESTION: what remains open?" in prompt
    assert json.dumps({"a": [2], "b": 1}, indent=2, sort_keys=True) in prompt


def test_reason_records_usage_and_latency(monkeypatch: Any) -> None:
    _import_or_skip("agents")
    _import_or_skip("pydantic")

    class _Usage:
        requests = 1
        input_tokens = 233
        output_tokens = 1229
        total_tokens = 1462

    class _ContextWrapper:
        usage = _Usage()

    class _RunResult:
        final_output = _Structured()
        context_wrapper = _ContextWrapper()

    async def _fake_run(agent: Any, input: Any, **kwargs: Any) -> Any:
        return _RunResult()

    monkeypatch.setattr("agents.Runner.run", _fake_run)
    reasoner = AgentsOncoXReasoner(model="test-model")

    result = asyncio.run(
        reasoner.reason(
            ReasoningRequest(
                investigation_id="c01",
                evidence_ids=(),
                question="q",
                structured_state={"x": 1},
            )
        )
    )

    assert result.model_id == "test-model"
    assert result.output.interpretation == "the comparison is confounded"
    assert result.usage["input_tokens"] == 233
    assert result.usage["total_tokens"] == 1462
    assert result.latency_ms >= 0.0
    assert result.attempts == 1
    assert result.errors == ()


def test_structured_output_failures_are_retried_once_and_recorded(monkeypatch: Any) -> None:
    _import_or_skip("agents")
    _import_or_skip("pydantic")

    class _ContextWrapper:
        usage = None

    class _RunResult:
        final_output = _Structured()
        context_wrapper = _ContextWrapper()

    calls = {"count": 0}

    async def _flaky_run(agent: Any, input: Any, **kwargs: Any) -> Any:
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("Invalid JSON when parsing model output")
        return _RunResult()

    monkeypatch.setattr("agents.Runner.run", _flaky_run)
    reasoner = AgentsOncoXReasoner(model="test-model", retry_delay_seconds=0.0)

    result = asyncio.run(
        reasoner.reason(
            ReasoningRequest(
                investigation_id="c01",
                evidence_ids=(),
                question="q",
                structured_state={"x": 1},
            )
        )
    )

    assert calls["count"] == 2
    assert result.attempts == 2
    assert result.errors == ("RuntimeError: Invalid JSON when parsing model output",)
    assert result.usage == {}


def test_repeated_structured_output_failure_is_surfaced(monkeypatch: Any) -> None:
    _import_or_skip("agents")
    _import_or_skip("pydantic")

    calls = {"count": 0}

    async def _failing_run(agent: Any, input: Any, **kwargs: Any) -> Any:
        calls["count"] += 1
        raise RuntimeError("Invalid JSON when parsing model output")

    monkeypatch.setattr("agents.Runner.run", _failing_run)
    reasoner = AgentsOncoXReasoner(model="test-model", max_attempts=2, retry_delay_seconds=0.0)

    with pytest.raises(RuntimeError, match="failed after 2 attempts"):
        asyncio.run(
            reasoner.reason(
                ReasoningRequest(
                    investigation_id="c01",
                    evidence_ids=(),
                    question="q",
                    structured_state={"x": 1},
                )
            )
        )

    assert calls["count"] == 2
