from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from time import perf_counter
from typing import Any

from evaluation.ranking import evaluate_rankings, promote_choice
from evidence.projections import SemanticProjection, freeze_projection
from execution.gdc import GdcClient, GdcResponse
from experiments.catalog import get_experiment
from jev.contracts import JevCapability, JevPrimitive, JevQuestion
from jev.typesafe_adapter import TypeSafeJevClient
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A006")
K = 3
LIVE_REPETITIONS = 3
PROJECT_IDS = ("TCGA-LUAD", "TCGA-LUSC", "TCGA-KICH", "TCGA-KIRC", "TCGA-KIRP")


@dataclass(frozen=True, slots=True)
class Query:
    query_id: str
    task: str
    primary_site: str
    expected_project_id: str


QUERIES = (
    Query("lung_adenocarcinoma", "Lung adenocarcinoma", "Bronchus and lung", "TCGA-LUAD"),
    Query(
        "lung_squamous",
        "Lung squamous cell carcinoma",
        "Bronchus and lung",
        "TCGA-LUSC",
    ),
    Query("kidney_clear_cell", "Kidney renal clear cell carcinoma", "Kidney", "TCGA-KIRC"),
    Query("kidney_papillary", "Kidney renal papillary cell carcinoma", "Kidney", "TCGA-KIRP"),
    Query("kidney_chromophobe", "Kidney chromophobe", "Kidney", "TCGA-KICH"),
)
EXPECTED = {query.query_id: query.expected_project_id for query in QUERIES}


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
            "fields": "project_id,name,primary_site,disease_type,summary.case_count",
            "size": len(PROJECT_IDS),
        },
    )
    hits = response.payload.get("data", {}).get("hits", [])
    projects = {str(hit["project_id"]): hit for hit in hits}
    if set(projects) != set(PROJECT_IDS):
        raise ValueError("GDC response does not match the frozen project set")
    return status, response, projects


def _case_count(project: dict[str, Any]) -> int:
    return int(project["summary"]["case_count"])


def _baseline_rankings(projects: dict[str, dict[str, Any]]) -> dict[str, tuple[str, ...]]:
    rankings: dict[str, tuple[str, ...]] = {}
    for query in QUERIES:
        matching = (
            project_id
            for project_id, project in projects.items()
            if query.primary_site in project["primary_site"]
        )
        rankings[query.query_id] = tuple(
            sorted(matching, key=lambda item: (-_case_count(projects[item]), item))
        )
    return rankings


def _projection(
    projects: dict[str, dict[str, Any]], rankings: dict[str, tuple[str, ...]]
) -> SemanticProjection:
    payload = {
        "queries": {
            query.query_id: {
                "task": query.task,
                "candidates": {
                    project_id: {
                        "name": projects[project_id]["name"],
                        "primary_site": projects[project_id]["primary_site"],
                        "disease_type": projects[project_id]["disease_type"],
                    }
                    for project_id in rankings[query.query_id]
                },
            }
            for query in QUERIES
        }
    }
    return freeze_projection(
        projection_id="a006-gdc-project-reranking",
        version="1",
        question_id="best-matching-gdc-project",
        source_evidence_ids=tuple(f"gdc-project:{project_id}" for project_id in PROJECT_IDS),
        payload=payload,
    )


def _capability(rankings: dict[str, tuple[str, ...]]) -> JevCapability:
    return JevCapability(
        capability_id="a006-project-histology-reranker",
        version="0.1.0",
        domain_owner="evaluation",
        semantic_purpose="Choose the GDC project whose description best matches a task.",
        projection_id="a006-gdc-project-reranking",
        projection_version="1",
        questions=tuple(
            JevQuestion(
                question_id=query.query_id,
                primitive=JevPrimitive.CHOICE,
                instructions=(
                    f"Using only `queries.{query.query_id}`, select the candidate whose "
                    "GDC metadata most specifically matches the task."
                ),
                criteria={project_id: project_id for project_id in rankings[query.query_id]},
            )
            for query in QUERIES
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
    baseline = _baseline_rankings(projects)
    baseline_metrics = evaluate_rankings(expected=EXPECTED, rankings=baseline, k=K)
    projection = _projection(projects, baseline)
    capability = _capability(baseline)
    client = TypeSafeJevClient(api_key=settings.typesafe_api_key, model=settings.jev_model)

    repetitions: list[dict[str, Any]] = []
    all_successful = True
    for repetition in range(1, LIVE_REPETITIONS + 1):
        started = perf_counter()
        decision = client.evaluate(projection, capability)
        latency_ms = (perf_counter() - started) * 1000
        choices = {answer.question_id: str(answer.value) for answer in decision.answers}
        probabilities = {answer.question_id: answer.probabilities for answer in decision.answers}
        reranked = {
            query_id: promote_choice(baseline[query_id], choices[query_id]) for query_id in EXPECTED
        }
        metrics = evaluate_rankings(expected=EXPECTED, rankings=reranked, k=K)
        membership_preserved = all(
            set(reranked[query_id]) == set(baseline[query_id]) for query_id in EXPECTED
        )
        success = (
            baseline_metrics.recall_at_k == 1.0
            and metrics.recall_at_k == 1.0
            and metrics.recall_at_1 - baseline_metrics.recall_at_1 >= 0.2
            and membership_preserved
        )
        all_successful = all_successful and success
        repetitions.append(
            {
                "repetition": repetition,
                "choices": choices,
                "probabilities": probabilities,
                "reranked": reranked,
                "metrics": asdict(metrics),
                "membership_preserved": membership_preserved,
                "usage": decision.usage,
                "latency_ms": latency_ms,
                "success_criteria_met": success,
            }
        )

    stable = all(
        repetition["choices"] == repetitions[0]["choices"] for repetition in repetitions[1:]
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
            "top_choice_stable": stable,
            "k": K,
            "expected": EXPECTED,
            "baseline_rankings": baseline,
            "baseline_metrics": asdict(baseline_metrics),
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
                "Jev met the scoped reranking criteria in every repetition."
                if all_successful
                else "Jev did not meet the scoped reranking criteria in every repetition."
            ),
            (
                "Treatment membership was fixed by deterministic retrieval; "
                "Jev only selected rank one."
            ),
        ),
        limitations=(
            "Labels test project-description matching, not biological discovery utility.",
            "Five queries across two primary-site ambiguity groups are not a general benchmark.",
            (
                "A model may know TCGA project names from pretraining; "
                "this task does not test novelty."
            ),
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
                "queries": [asdict(query) for query in QUERIES],
                "expected": EXPECTED,
                "k": K,
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
                limitations=("External failure does not establish reranking quality.",),
            )
    store.append("architecture_experiment_result", asdict(result))
    return str(asdict(result))
