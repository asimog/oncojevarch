from __future__ import annotations

import asyncio
import json
from dataclasses import asdict
from hashlib import sha256
from typing import Any

from evaluation.context import (
    ContextArmScore,
    ContextTask,
    compare_context_arms,
    evaluate_context_arm,
)
from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncodex.context import (
    HistoryMessage,
    build_bounded_view,
    render_full_history,
    render_view,
)
from oncodex.harness import run_harness_turn
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A016")
RECENCY_WINDOW = 6
BUDGET_CHARS = 1400
LIVE_REPETITIONS = 2
MAX_CONCURRENT_TURNS = 3
ARMS = ("full_history", "bounded_progressive")


def _output_model() -> type[Any]:
    from pydantic import BaseModel, Field

    class OnCodexAnswer(BaseModel):
        """Bounded OnCodex answer over a supplied investigation context."""

        answers: list[str] = Field(
            default_factory=list, description="Direct answers with the latest recorded values."
        )
        facts_used: list[str] = Field(
            default_factory=list, description="Fact keys used, without restating raw values."
        )

    return OnCodexAnswer


def histories() -> dict[str, tuple[HistoryMessage, ...]]:
    """Frozen synthetic investigation histories with recorded facts and later corrections."""

    return {
        "t01": (
            HistoryMessage("m01", "user", "Open an investigation on the KIRC cohort size claim."),
            HistoryMessage("m02", "tool", "FACT: kirc_cases = 537"),
            HistoryMessage("m03", "tool", "FACT: kirc_primary_site = Kidney"),
            HistoryMessage("m04", "assistant", "Recorded the KIRC cohort size from the inventory."),
            HistoryMessage("m05", "tool", "CORRECTION: kirc_cases = 531"),
            HistoryMessage("m06", "assistant", "Applied a duplicate-case correction to the count."),
            HistoryMessage("m07", "tool", "FACT: kirc_files = 35031"),
            HistoryMessage("m08", "user", "Also record the papillary project size."),
            HistoryMessage("m09", "tool", "FACT: kirp_cases = 291"),
            HistoryMessage("m10", "assistant", "Recorded the papillary project size."),
            HistoryMessage("m11", "user", "Do not use the superseded clear cell count again."),
            HistoryMessage("m12", "tool", "FACT: kirc_data_categories = 10"),
        ),
        "t02": (
            HistoryMessage("m01", "user", "Check whether the LUSC inventory has an array entry."),
            HistoryMessage("m02", "tool", "FACT: lusc_expression_array_files = 135"),
            HistoryMessage("m03", "tool", "FACT: lusc_rna_seq_files = 5058"),
            HistoryMessage("m04", "assistant", "Recorded the LUSC expression inventories."),
            HistoryMessage("m05", "user", "Confirm the platform label used for the count."),
            HistoryMessage("m06", "tool", "FACT: lusc_platform = Expression Array"),
            HistoryMessage("m07", "tool", "CORRECTION: lusc_platform = Genotyping Array"),
            HistoryMessage("m08", "assistant", "Corrected the platform label after review."),
            HistoryMessage("m09", "tool", "FACT: luad_rna_seq_files = 5409"),
            HistoryMessage("m10", "user", "Report the current label only."),
            HistoryMessage("m11", "tool", "FACT: lusc_case_count = 504"),
            HistoryMessage("m12", "assistant", "Ready to answer."),
        ),
        "t03": (
            HistoryMessage("m01", "user", "Review the KICH assay inventory claim."),
            HistoryMessage("m02", "tool", "FACT: fich_placeholder = 0"),
            HistoryMessage("m03", "tool", "FACT: kich_cases = 113"),
            HistoryMessage("m04", "tool", "CORRECTION: kich_atac_seq_files = 0"),
            HistoryMessage("m05", "assistant", "Recorded the reported ATAC-Seq absence."),
            HistoryMessage("m06", "user", "Check the other kidney projects for the same assay."),
            HistoryMessage("m07", "tool", "FACT: kirc_atac_seq_files = 16"),
            HistoryMessage("m08", "tool", "FACT: kirp_atac_seq_files = 34"),
            HistoryMessage("m09", "assistant", "Recorded both comparison inventories."),
            HistoryMessage("m10", "user", "Report whether the assay is established for KICH."),
            HistoryMessage("m11", "tool", "FACT: kich_strategy_count = 9"),
            HistoryMessage("m12", "assistant", "Ready to answer."),
        ),
    }


def tasks() -> tuple[ContextTask, ...]:
    return (
        ContextTask(
            task_id="t01",
            question=(
                "State the current KIRC cohort size, the KIRP cohort size, and whether the KIRC "
                "count was superseded."
            ),
            required_facts={"kirc_cases": "531", "kirp_cases": "291"},
            contradicted_values=("537",),
        ),
        ContextTask(
            task_id="t02",
            question=(
                "State the current LUSC platform label and the LUSC expression array file count."
            ),
            required_facts={
                "lusc_platform": "Genotyping Array",
                "lusc_expression_array_files": "135",
            },
            contradicted_values=("Expression Array",),
        ),
        ContextTask(
            task_id="t03",
            question=("State the KIRC and KIRP ATAC-Seq file counts and the KICH case count."),
            required_facts={"kirc_atac_seq_files": "16", "kirp_atac_seq_files": "34"},
            contradicted_values=("fich_placeholder",),
        ),
    )


def _history_fingerprint() -> str:
    return sha256(
        json.dumps(
            {
                task_id: [asdict(message) for message in history]
                for task_id, history in histories().items()
            },
            sort_keys=True,
        ).encode("utf-8")
    ).hexdigest()


async def _run_arm_turn(
    *,
    settings: Settings,
    arm_id: str,
    task: ContextTask,
    context: str,
    output_model: type[Any],
    semaphore: asyncio.Semaphore,
) -> dict[str, Any]:
    prompt = "\n".join(
        (
            "INVESTIGATION CONTEXT:",
            context,
            "",
            f"QUESTION: {task.question}",
            (
                "Return the required structured answer using only the context. Use the latest "
                "recorded value of every fact."
            ),
        )
    )
    async with semaphore:
        result = await run_harness_turn(settings=settings, prompt=prompt, output_model=output_model)
    return {
        "arm_id": arm_id,
        "task_id": task.task_id,
        "output": result.output,
        "model_id": result.model_id,
        "usage": result.usage,
        "latency_ms": result.latency_ms,
        "context_chars": len(context),
    }


def _arm_resources(records: list[dict[str, Any]], contexts: dict[str, str]) -> dict[str, Any]:
    return {
        "input_tokens": sum(int(record["usage"].get("input_tokens") or 0) for record in records),
        "output_tokens": sum(int(record["usage"].get("output_tokens") or 0) for record in records),
        "mean_latency_ms": (
            sum(float(record["latency_ms"]) for record in records) / len(records)
            if records
            else 0.0
        ),
        "character_count": sum(len(text) for text in contexts.values()),
    }


async def _run_repetition(
    *,
    settings: Settings,
    repetition: int,
    tasks_frozen: tuple[ContextTask, ...],
    histories_frozen: dict[str, tuple[HistoryMessage, ...]],
    output_model: type[Any],
) -> dict[str, Any]:
    contexts: dict[str, dict[str, str]] = {
        "full_history": {
            task_id: render_full_history(histories_frozen[task_id]) for task_id in histories_frozen
        },
        "bounded_progressive": {
            task_id: render_view(
                build_bounded_view(
                    histories_frozen[task_id],
                    view_id=f"{task_id}-bounded",
                    recency_window=RECENCY_WINDOW,
                    budget_chars=BUDGET_CHARS,
                )
            )
            for task_id in histories_frozen
        },
    }
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_TURNS)
    records = await asyncio.gather(
        *(
            _run_arm_turn(
                settings=settings,
                arm_id=arm_id,
                task=task,
                context=contexts[arm_id][task.task_id],
                output_model=output_model,
                semaphore=semaphore,
            )
            for arm_id in ARMS
            for task in tasks_frozen
        )
    )
    arms: dict[str, Any] = {}
    for arm_id in ARMS:
        arm_records = [record for record in records if record["arm_id"] == arm_id]
        answers = {record["task_id"]: dict(record["output"]) for record in arm_records}
        score: ContextArmScore = evaluate_context_arm(
            arm_id=arm_id,
            tasks=tasks_frozen,
            answers=answers,
            resources=_arm_resources(arm_records, contexts[arm_id]),
        )
        arms[arm_id] = {**asdict(score), "records": arm_records}
    metrics = compare_context_arms(
        full_history=ContextArmScore(
            arm_id="full_history",
            metrics=arms["full_history"]["metrics"],
            per_task=tuple(arms["full_history"]["per_task"]),
        ),
        bounded=ContextArmScore(
            arm_id="bounded_progressive",
            metrics=arms["bounded_progressive"]["metrics"],
            per_task=tuple(arms["bounded_progressive"]["per_task"]),
        ),
    )
    return {
        "repetition": repetition,
        "arms": arms,
        "comparison": metrics,
        "bounded_views": {
            task_id: {
                "pinned_facts": build_bounded_view(
                    histories_frozen[task_id],
                    view_id=f"{task_id}-bounded",
                    recency_window=RECENCY_WINDOW,
                    budget_chars=BUDGET_CHARS,
                ).pinned_facts,
                "superseded_fact_keys": build_bounded_view(
                    histories_frozen[task_id],
                    view_id=f"{task_id}-bounded",
                    recency_window=RECENCY_WINDOW,
                    budget_chars=BUDGET_CHARS,
                ).superseded_fact_keys,
                "dropped_message_ids": build_bounded_view(
                    histories_frozen[task_id],
                    view_id=f"{task_id}-bounded",
                    recency_window=RECENCY_WINDOW,
                    budget_chars=BUDGET_CHARS,
                ).dropped_message_ids,
                "character_count": len(contexts["bounded_progressive"][task_id]),
                "full_history_character_count": len(contexts["full_history"][task_id]),
            }
            for task_id in histories_frozen
        },
    }


def _run_live(settings: Settings, frozen: FrozenExperiment) -> ExperimentResult:
    tasks_frozen = tasks()
    histories_frozen = histories()
    output_model = _output_model()
    repetitions = [
        asyncio.run(
            _run_repetition(
                settings=settings,
                repetition=repetition,
                tasks_frozen=tasks_frozen,
                histories_frozen=histories_frozen,
                output_model=output_model,
            )
        )
        for repetition in range(1, LIVE_REPETITIONS + 1)
    ]
    success_patterns = {
        (
            record["repetition"],
            tuple(entry["success"] for entry in record["arms"]["bounded_progressive"]["per_task"]),
            tuple(entry["success"] for entry in record["arms"]["full_history"]["per_task"]),
        )
        for record in repetitions
    }
    bounded_success = [record["comparison"]["bounded_success_rate"] for record in repetitions]
    full_success = [record["comparison"]["full_history_success_rate"] for record in repetitions]
    token_reduction = [record["comparison"]["input_token_reduction"] for record in repetitions]
    stable = len({(pattern[1], pattern[2]) for pattern in success_patterns}) == 1
    adopted = min(bounded_success) >= min(full_success) and min(token_reduction) > 0.0 and stable
    return ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": True,
            "bounded_context_adopted": adopted,
            "history_fingerprint": _history_fingerprint(),
            "repetitions": repetitions,
            "protocol": {
                "recency_window": RECENCY_WINDOW,
                "budget_chars": BUDGET_CHARS,
                "live_repetitions": LIVE_REPETITIONS,
                "max_concurrent_turns": MAX_CONCURRENT_TURNS,
                "arms": list(ARMS),
                "task_count": len(tasks_frozen),
            },
            "cost": {
                "measured": False,
                "basis": "the Agents SDK usage path exposes tokens only",
            },
        },
        observations=(
            (
                "Bounded progressive context matched full-history success with fewer input "
                "tokens across repetitions, so it is adopted for this task set."
                if adopted
                else "Bounded progressive context is not adopted: success, token reduction, or "
                "repetition stability failed a frozen condition."
            ),
        ),
        limitations=(
            "Histories and tasks are frozen synthetic fixtures, not real agent sessions.",
            "Three tasks and two repetitions cannot establish general context behavior.",
            "The context builder is deterministic pruning, not learned summarization.",
            "Character budgets are a proxy; real token accounting depends on the "
            "provider tokenizer.",
        ),
    )


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    if not live:
        views = {
            task_id: build_bounded_view(
                history,
                view_id=f"{task_id}-bounded",
                recency_window=RECENCY_WINDOW,
                budget_chars=BUDGET_CHARS,
            )
            for task_id, history in histories().items()
        }
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.FROZEN,
            frozen_fingerprint=frozen.fingerprint,
            measurements={
                "live": False,
                "history_fingerprint": _history_fingerprint(),
                "protocol": {
                    "recency_window": RECENCY_WINDOW,
                    "budget_chars": BUDGET_CHARS,
                    "live_repetitions": LIVE_REPETITIONS,
                    "arms": list(ARMS),
                    "task_ids": [task.task_id for task in tasks()],
                },
                "bounded_views": {
                    task_id: {
                        "pinned_facts": view.pinned_facts,
                        "superseded_fact_keys": view.superseded_fact_keys,
                        "dropped_message_ids": view.dropped_message_ids,
                        "character_count": view.character_count,
                        "full_history_character_count": len(
                            render_full_history(histories()[task_id])
                        ),
                    }
                    for task_id, view in views.items()
                },
            },
            limitations=(
                "No model call was made; this is the frozen protocol only.",
                "This architecture task cannot create ScientificEvidence.",
            ),
        )
        store.append("architecture_experiment_result", asdict(result))
        return json.dumps(asdict(result), indent=2, default=str)
    try:
        result = _run_live(settings, frozen)
    except Exception as exc:
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.FAILED,
            frozen_fingerprint=frozen.fingerprint,
            measurements={"live": True, "error": f"{type(exc).__name__}: {exc}"},
            limitations=("External failure does not establish context behavior.",),
        )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
