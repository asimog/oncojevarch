from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class ContextTask:
    task_id: str
    question: str
    required_facts: dict[str, str]
    contradicted_values: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TaskAnswerScore:
    task_id: str
    success: bool
    matched_required: tuple[str, ...]
    missing_required: tuple[str, ...]
    contradicted_present: tuple[str, ...]

    @property
    def contradicted(self) -> bool:
        return bool(self.contradicted_present)


def serialize_answer(output: dict[str, Any]) -> str:
    return " ".join(str(value) for value in output.values() if value is not None).lower()


def score_answer(task: ContextTask, output: dict[str, Any]) -> TaskAnswerScore:
    text = serialize_answer(output)
    matched = tuple(key for key, value in task.required_facts.items() if value.lower() in text)
    missing = tuple(key for key in task.required_facts if key not in matched)
    contradicted = tuple(value for value in task.contradicted_values if value.lower() in text)
    return TaskAnswerScore(
        task_id=task.task_id,
        success=not missing and not contradicted,
        matched_required=matched,
        missing_required=missing,
        contradicted_present=contradicted,
    )


@dataclass(frozen=True, slots=True)
class ContextArmScore:
    arm_id: str
    metrics: dict[str, float]
    per_task: tuple[dict[str, Any], ...]


def evaluate_context_arm(
    *,
    arm_id: str,
    tasks: tuple[ContextTask, ...],
    answers: dict[str, dict[str, Any]],
    resources: dict[str, Any],
) -> ContextArmScore:
    if set(answers) != {task.task_id for task in tasks}:
        raise ValueError("arm answers do not match the frozen task set")
    scores = [score_answer(task, answers[task.task_id]) for task in tasks]
    successes = sum(score.success for score in scores)
    contradictions = sum(score.contradicted for score in scores)
    metrics = {
        "task_count": float(len(tasks)),
        "success_rate": successes / len(tasks),
        "contradiction_rate": contradictions / len(tasks),
        "input_tokens": float(resources.get("input_tokens") or 0),
        "output_tokens": float(resources.get("output_tokens") or 0),
        "mean_latency_ms": float(resources.get("mean_latency_ms") or 0.0),
        "character_count": float(resources.get("character_count") or 0),
    }
    per_task = tuple(
        {
            "task_id": score.task_id,
            "success": score.success,
            "missing_required": score.missing_required,
            "contradicted_present": score.contradicted_present,
            "answer": json.dumps(answers[score.task_id], sort_keys=True, default=str),
        }
        for score in scores
    )
    return ContextArmScore(arm_id=arm_id, metrics=metrics, per_task=per_task)


def compare_context_arms(
    *, full_history: ContextArmScore, bounded: ContextArmScore
) -> dict[str, float]:
    """Paired comparison; bounded context is only adopted when it does not lose task success."""

    if full_history.metrics["task_count"] != bounded.metrics["task_count"]:
        raise ValueError("context arms must cover the same frozen task set")
    return {
        "full_history_success_rate": full_history.metrics["success_rate"],
        "bounded_success_rate": bounded.metrics["success_rate"],
        "success_delta": bounded.metrics["success_rate"] - full_history.metrics["success_rate"],
        "full_history_contradiction_rate": full_history.metrics["contradiction_rate"],
        "bounded_contradiction_rate": bounded.metrics["contradiction_rate"],
        "contradiction_delta": bounded.metrics["contradiction_rate"]
        - full_history.metrics["contradiction_rate"],
        "input_token_reduction": 1.0
        - (
            bounded.metrics["input_tokens"] / full_history.metrics["input_tokens"]
            if full_history.metrics["input_tokens"]
            else 1.0
        ),
        "latency_delta_ms": bounded.metrics["mean_latency_ms"]
        - full_history.metrics["mean_latency_ms"],
    }
