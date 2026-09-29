from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any

from evaluation.viability import evaluate_viability
from evidence.projections import SemanticProjection, freeze_projection
from execution.gdc import GdcClient, GdcResponse
from experiments.catalog import get_experiment
from jev.contracts import JevCapability, JevPrimitive, JevQuestion
from jev.typesafe_adapter import TypeSafeJevClient
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A007")
THRESHOLD = 0.5
LIVE_REPETITIONS = 3
PROJECT_IDS = ("TCGA-LUAD", "TCGA-LUSC", "TCGA-KICH", "TCGA-KIRC", "TCGA-KIRP")
LUNG = ("TCGA-LUAD", "TCGA-LUSC")
KIDNEY = ("TCGA-KIRC", "TCGA-KIRP", "TCGA-KICH")


@dataclass(frozen=True, slots=True)
class ViabilityCase:
    case_id: str
    task: str
    candidates: tuple[str, ...]
    viable: bool


CASES = (
    ViabilityCase("lung_adeno", "Lung adenocarcinoma", LUNG, True),
    ViabilityCase("lung_squamous", "Lung squamous cell carcinoma", LUNG, True),
    ViabilityCase("lung_glioblastoma", "Glioblastoma", LUNG, False),
    ViabilityCase("lung_breast", "Breast invasive carcinoma", LUNG, False),
    ViabilityCase("kidney_clear", "Kidney renal clear cell carcinoma", KIDNEY, True),
    ViabilityCase("kidney_papillary", "Kidney renal papillary cell carcinoma", KIDNEY, True),
    ViabilityCase("kidney_ovarian", "Ovarian serous cystadenocarcinoma", KIDNEY, False),
    ViabilityCase("kidney_prostate", "Prostate adenocarcinoma", KIDNEY, False),
)
EXPECTED = {case.case_id: case.viable for case in CASES}


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
        projection_id="a007-gdc-project-viability",
        version="1",
        question_id="relative-choice-and-absolute-viability",
        source_evidence_ids=tuple(f"gdc-project:{project_id}" for project_id in PROJECT_IDS),
        payload={
            "cases": {
                case.case_id: {
                    "task": case.task,
                    "candidates": {
                        project_id: {
                            "name": projects[project_id]["name"],
                            "primary_site": projects[project_id]["primary_site"],
                            "disease_type": projects[project_id]["disease_type"],
                        }
                        for project_id in case.candidates
                    },
                }
                for case in CASES
            }
        },
    )


def _capability() -> JevCapability:
    questions: list[JevQuestion] = []
    for case in CASES:
        questions.extend(
            (
                JevQuestion(
                    question_id=f"{case.case_id}__choice",
                    primitive=JevPrimitive.CHOICE,
                    instructions=(
                        f"Using only `cases.{case.case_id}`, select the relatively closest "
                        "candidate even if no candidate is adequate."
                    ),
                    criteria={project_id: project_id for project_id in case.candidates},
                ),
                JevQuestion(
                    question_id=f"{case.case_id}__viable",
                    primitive=JevPrimitive.NOUL,
                    instructions=(
                        f"Using only `cases.{case.case_id}`, is at least one candidate an "
                        "adequate specific match for the task?"
                    ),
                    criteria={
                        "true": "at least one candidate specifically matches the task",
                        "false": "all candidates are materially mismatched to the task",
                    },
                ),
            )
        )
    return JevCapability(
        capability_id="a007-project-choice-with-viability",
        version="0.1.0",
        domain_owner="evaluation",
        semantic_purpose="Separate relative project choice from absolute match adequacy.",
        projection_id="a007-gdc-project-viability",
        projection_version="1",
        questions=tuple(questions),
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
    client = TypeSafeJevClient(api_key=settings.typesafe_api_key, model=settings.jev_model)
    choice_only_acceptance = {case.case_id: True for case in CASES}
    choice_only = evaluate_viability(
        expected=EXPECTED,
        accepted=choice_only_acceptance,
        probabilities={case.case_id: 1.0 for case in CASES},
    )

    repetitions: list[dict[str, Any]] = []
    all_successful = True
    for repetition in range(1, LIVE_REPETITIONS + 1):
        started = perf_counter()
        decision = client.evaluate(projection, _capability())
        latency_ms = (perf_counter() - started) * 1000
        answers = {answer.question_id: answer for answer in decision.answers}
        choices = {case.case_id: str(answers[f"{case.case_id}__choice"].value) for case in CASES}
        invalid_choices = tuple(
            case.case_id for case in CASES if choices[case.case_id] not in case.candidates
        )
        probabilities = {
            case.case_id: float(answers[f"{case.case_id}__viable"].value) for case in CASES
        }
        accepted = {
            case_id: probability >= THRESHOLD for case_id, probability in probabilities.items()
        }
        combined = evaluate_viability(
            expected=EXPECTED,
            accepted=accepted,
            probabilities=probabilities,
        )
        false_acceptance_improvement = (
            choice_only.false_acceptance_rate - combined.false_acceptance_rate
        )
        success = (
            false_acceptance_improvement >= 0.5
            and combined.viable_recall >= 0.75
            and not invalid_choices
        )
        all_successful = all_successful and success
        repetitions.append(
            {
                "repetition": repetition,
                "choices": choices,
                "viability_probabilities": probabilities,
                "accepted": accepted,
                "combined_metrics": asdict(combined),
                "false_acceptance_improvement": false_acceptance_improvement,
                "invalid_choices": invalid_choices,
                "usage": decision.usage,
                "latency_ms": latency_ms,
                "success_criteria_met": success,
            }
        )

    stable = all(
        repetition["choices"] == repetitions[0]["choices"]
        and repetition["accepted"] == repetitions[0]["accepted"]
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
            "decision_stable": stable,
            "threshold": THRESHOLD,
            "expected": EXPECTED,
            "choice_only_metrics": asdict(choice_only),
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
                "The absolute gate met the scoped A007 criteria in every repetition."
                if all_successful
                else "The absolute gate did not meet the scoped criteria in every repetition."
            ),
        ),
        limitations=(
            "Labels measure project-description adequacy, not scientific candidate viability.",
            "The no-match tasks are controlled fixtures over real public metadata.",
            "A small, balanced task set does not establish probability calibration.",
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
                "cases": [asdict(case) for case in CASES],
                "expected": EXPECTED,
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
                limitations=("External failure does not establish gate quality.",),
            )
    store.append("architecture_experiment_result", asdict(result))
    return str(asdict(result))
