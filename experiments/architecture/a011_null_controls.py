from __future__ import annotations

import json
from dataclasses import asdict
from time import perf_counter
from typing import Any

from evaluation.null_controls import cyclic_derangement, evaluate_null_controls
from evidence.projections import SemanticProjection, freeze_projection
from execution.gdc import GdcClient, GdcResponse
from experiments.catalog import get_experiment
from jev.contracts import JevCapability, JevPrimitive, JevQuestion
from jev.typesafe_adapter import TypeSafeJevClient
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A011")
THRESHOLD = 0.5
LIVE_REPETITIONS = 3
VALID_ARM = "valid"
NULL_ARMS = ("deranged_1", "deranged_2", "deranged_4")
PROJECT_IDS = ("TCGA-LUAD", "TCGA-LUSC", "TCGA-KICH", "TCGA-KIRC", "TCGA-KIRP")
CASE_IDS = ("case_01", "case_02", "case_03", "case_04", "case_05")
PROJECT_BY_CASE = dict(zip(CASE_IDS, PROJECT_IDS, strict=True))
TASKS = {
    "case_01": "Lung adenocarcinoma",
    "case_02": "Lung squamous cell carcinoma",
    "case_03": "Kidney chromophobe",
    "case_04": "Kidney renal clear cell carcinoma",
    "case_05": "Kidney renal papillary cell carcinoma",
}
ARM_MAPPINGS = {
    VALID_ARM: {case_id: case_id for case_id in CASE_IDS},
    "deranged_1": cyclic_derangement(CASE_IDS, offset=1),
    "deranged_2": cyclic_derangement(CASE_IDS, offset=2),
    "deranged_4": cyclic_derangement(CASE_IDS, offset=4),
}


def _project_filter() -> str:
    return json.dumps(
        {"op": "in", "content": {"field": "project_id", "value": list(PROJECT_IDS)}},
        separators=(",", ":"),
    )


def _fetch_projects(
    client: GdcClient,
) -> tuple[GdcResponse, GdcResponse, dict[str, dict[str, Any]]]:
    status = client.get("status")
    response = client.get(
        "projects",
        {
            "filters": _project_filter(),
            "fields": "project_id,name,primary_site,disease_type",
            "size": len(PROJECT_IDS),
        },
    )
    hits = response.payload.get("data", {}).get("hits", [])
    projects = {str(hit["project_id"]): hit for hit in hits}
    if set(projects) != set(PROJECT_IDS):
        raise ValueError("GDC response does not match the frozen project set")
    return status, response, projects


def _projection(projects: dict[str, dict[str, Any]]) -> SemanticProjection:
    return freeze_projection(
        projection_id="a011-gdc-null-controls",
        version="1",
        question_id="task-description-coherence",
        source_evidence_ids=tuple(f"gdc-project:{project_id}" for project_id in PROJECT_IDS),
        payload={
            "arms": {
                arm_id: {
                    case_id: {
                        "task": TASKS[case_id],
                        "description": {
                            "name": projects[PROJECT_BY_CASE[source_case]]["name"],
                            "primary_site": projects[PROJECT_BY_CASE[source_case]]["primary_site"],
                            "disease_type": projects[PROJECT_BY_CASE[source_case]]["disease_type"],
                        },
                    }
                    for case_id, source_case in mapping.items()
                }
                for arm_id, mapping in ARM_MAPPINGS.items()
            }
        },
    )


def _capability() -> JevCapability:
    return JevCapability(
        capability_id="a011-task-description-coherence",
        version="0.1.0",
        domain_owner="evaluation",
        semantic_purpose="Detect whether a masked GDC project description matches a task.",
        projection_id="a011-gdc-null-controls",
        projection_version="1",
        questions=tuple(
            JevQuestion(
                question_id=f"{arm_id}__{case_id}",
                primitive=JevPrimitive.NOUL,
                instructions=(
                    f"Using only `arms.{arm_id}.{case_id}`, does the project description "
                    "specifically match the requested histology? A shared organ or broad "
                    "disease family alone is not sufficient."
                ),
                criteria={
                    "true": "the description specifically matches the requested histology",
                    "false": "the description is a different organ or histologic subtype",
                },
            )
            for arm_id in (VALID_ARM, *NULL_ARMS)
            for case_id in CASE_IDS
        ),
    )


def _receipt(response: GdcResponse) -> dict[str, Any]:
    return {
        "url": response.url,
        "response_bytes": response.response_bytes,
        "latency_ms": response.latency_ms,
    }


def _run_live(settings: Settings, frozen: FrozenExperiment) -> ExperimentResult:
    status_response, project_response, projects = _fetch_projects(GdcClient())
    projection = _projection(projects)
    capability = _capability()
    client = TypeSafeJevClient(api_key=settings.typesafe_api_key, model=settings.jev_model)
    repetitions: list[dict[str, Any]] = []
    all_successful = True

    for repetition in range(1, LIVE_REPETITIONS + 1):
        started = perf_counter()
        decision = client.evaluate(projection, capability)
        latency_ms = (perf_counter() - started) * 1000
        answers = {answer.question_id: float(answer.value) for answer in decision.answers}
        probabilities = {
            arm_id: {case_id: answers[f"{arm_id}__{case_id}"] for case_id in CASE_IDS}
            for arm_id in (VALID_ARM, *NULL_ARMS)
        }
        evaluation = evaluate_null_controls(
            probabilities=probabilities,
            valid_arm_id=VALID_ARM,
            null_arm_ids=NULL_ARMS,
            threshold=THRESHOLD,
        )
        success = (
            evaluation.valid.claim_rate >= 0.8
            and evaluation.mean_null_claim_rate <= 0.2
            and evaluation.maximum_null_claim_rate <= 0.4
            and evaluation.valid_minus_null_mean_probability >= 0.4
        )
        all_successful = all_successful and success
        repetitions.append(
            {
                "repetition": repetition,
                "probabilities": probabilities,
                "evaluation": asdict(evaluation),
                "usage": decision.usage,
                "latency_ms": latency_ms,
                "success_criteria_met": success,
            }
        )

    stable = all(
        {
            arm_id: {
                case_id: probability >= THRESHOLD
                for case_id, probability in repetition["probabilities"][arm_id].items()
            }
            for arm_id in (VALID_ARM, *NULL_ARMS)
        }
        == {
            arm_id: {
                case_id: probability >= THRESHOLD
                for case_id, probability in repetitions[0]["probabilities"][arm_id].items()
            }
            for arm_id in (VALID_ARM, *NULL_ARMS)
        }
        for repetition in repetitions[1:]
    )
    status = status_response.payload
    return ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": True,
            "success_criteria_met": all_successful,
            "claim_decisions_stable": stable,
            "threshold": THRESHOLD,
            "arm_mappings": ARM_MAPPINGS,
            "projection_fingerprint": projection.fingerprint,
            "model_id": settings.jev_model,
            "repetitions": repetitions,
            "source": {
                "data_release": status.get("data_release"),
                "api_version": status.get("tag"),
                "commit": status.get("commit"),
                "status_receipt": _receipt(status_response),
                "project_receipt": _receipt(project_response),
            },
        },
        observations=(
            (
                "Candidate claims collapsed under every frozen derangement."
                if all_successful
                else "Persuasive candidate claims survived at least one frozen derangement."
            ),
        ),
        limitations=(
            "This tests project-description coherence, not biological signal destruction.",
            "Five familiar TCGA descriptions may be present in model pretraining.",
            "Semi-synthetic null success does not establish scientific false-narrative rates.",
        ),
    )


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    if not live:
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.FROZEN,
            frozen_fingerprint=frozen.fingerprint,
            measurements={
                "live": False,
                "project_ids": PROJECT_IDS,
                "opaque_case_ids": CASE_IDS,
                "tasks": TASKS,
                "arm_mappings": ARM_MAPPINGS,
                "threshold": THRESHOLD,
                "live_repetitions": LIVE_REPETITIONS,
            },
            limitations=(
                "Inputs are frozen, but no GDC or Jev call was made.",
                "This architecture task cannot create ScientificEvidence.",
            ),
        )
    else:
        try:
            result = _run_live(settings, frozen)
        except Exception as exc:
            result = ExperimentResult(
                experiment_id=SPEC.experiment_id,
                experiment_class=SPEC.experiment_class,
                status=ExperimentStatus.FAILED,
                frozen_fingerprint=frozen.fingerprint,
                measurements={"live": True, "error": f"{type(exc).__name__}: {exc}"},
                limitations=("External failure does not establish null-control behavior.",),
            )
    store.append("architecture_experiment_result", asdict(result))
    return str(asdict(result))
