from __future__ import annotations

import json
from dataclasses import asdict
from time import perf_counter
from typing import Any

from evaluation.regression import (
    ModelRegressionEvaluation,
    RegressionObservation,
    compare_model_versions,
)
from evidence.projections import SemanticProjection, freeze_projection
from execution.gdc import GdcClient, GdcResponse
from experiments.catalog import get_experiment
from jev.contracts import JevCapability, JevPrimitive, JevQuestion
from jev.typesafe_adapter import TypeSafeJevClient
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A013")
THRESHOLD = 0.5
BASELINE_MODEL = "jev-1.13.0"
CANDIDATE_MODEL = "jev-preview"
CURRENT_MODEL_ROLE = "control"
MIN_DECISION_AGREEMENT = 0.9
MAX_DRIFT_EXCESS = 0.05
MAX_BRIER_EXCESS = 0.05
MIN_POSITIVE_CLAIM_RATE = 0.8
MAX_NEGATIVE_MEAN_CLAIM_RATE = 0.2
MAX_NEGATIVE_GROUP_CLAIM_RATE = 0.4
BASELINE_EXPERIMENT_ID = "A011"
BASELINE_PROJECTION_ID = "a011-gdc-null-controls"
BASELINE_PROJECTION_FINGERPRINT = "b97d616b1b137326ca5a3d40ff8e18be750b4863387fe66d50af2261b9dcf86e"
PROJECT_IDS = ("TCGA-LUAD", "TCGA-LUSC", "TCGA-KICH", "TCGA-KIRC", "TCGA-KIRP")
CASE_IDS = ("case_01", "case_02", "case_03", "case_04", "case_05")
PROJECT_BY_CASE = dict(zip(CASE_IDS, PROJECT_IDS, strict=True))
VALID_ARM = "valid"
NULL_ARMS = ("deranged_1", "deranged_2", "deranged_4")
TASKS = {
    "case_01": "Lung adenocarcinoma",
    "case_02": "Lung squamous cell carcinoma",
    "case_03": "Kidney chromophobe",
    "case_04": "Kidney renal clear cell carcinoma",
    "case_05": "Kidney renal papillary cell carcinoma",
}


def cyclic_derangement(items: tuple[str, ...], *, offset: int) -> dict[str, str]:
    return {item: items[(index + offset) % len(items)] for index, item in enumerate(items)}


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
        projection_id=BASELINE_PROJECTION_ID,
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
        projection_id=BASELINE_PROJECTION_ID,
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


def _labels() -> dict[str, bool]:
    return {
        f"{arm_id}__{case_id}": arm_id == VALID_ARM
        for arm_id in (VALID_ARM, *NULL_ARMS)
        for case_id in CASE_IDS
    }


def _groups() -> dict[str, str]:
    return {
        f"{arm_id}__{case_id}": f"case::{case_id}"
        for arm_id in (VALID_ARM, *NULL_ARMS)
        for case_id in CASE_IDS
    }


def _run_model(
    client: TypeSafeJevClient, projection: SemanticProjection, capability: JevCapability
) -> RegressionObservation:
    started = perf_counter()
    decision = client.evaluate(projection, capability)
    latency_ms = (perf_counter() - started) * 1000
    return RegressionObservation(
        model_id=decision.model_id,
        probabilities={answer.question_id: float(answer.value) for answer in decision.answers},
        usage=decision.usage,
        latency_ms=latency_ms,
    )


def _recorded_baseline(
    settings: Settings,
) -> tuple[RegressionObservation, dict[str, Any], dict[str, Any]]:
    """Read the immutable recorded A011 repetition as the frozen baseline."""

    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    for event in reversed(store.read_all()):
        payload = event.payload
        if payload.get("experiment_id") != BASELINE_EXPERIMENT_ID:
            continue
        measurements = payload.get("measurements", {})
        if not measurements.get("live") or not measurements.get("repetitions"):
            continue
        if measurements.get("projection_fingerprint") != BASELINE_PROJECTION_FINGERPRINT:
            continue
        repetition = measurements["repetitions"][0]
        probabilities = {
            f"{arm_id}__{case_id}": float(value)
            for arm_id, cases in repetition["probabilities"].items()
            for case_id, value in cases.items()
        }
        return (
            RegressionObservation(
                model_id=str(measurements.get("model_id")),
                probabilities=probabilities,
                usage=dict(repetition.get("usage") or {}),
                latency_ms=float(repetition.get("latency_ms") or 0.0),
            ),
            {
                "event_id": event.event_id,
                "occurred_at": event.occurred_at,
                "model_id": measurements.get("model_id"),
                "projection_fingerprint": measurements.get("projection_fingerprint"),
                "repetition": repetition["repetition"],
                "repetitions_recorded": len(measurements["repetitions"]),
            },
            measurements,
        )
    raise RuntimeError(
        "no recorded A011 live baseline with the frozen projection fingerprint is available"
    )


def _repetition_drift(measurements: dict[str, Any]) -> float:
    """A011's own repetition spread gives the recorded provider-noise band."""

    repetitions = measurements.get("repetitions", [])
    if len(repetitions) < 2:
        return 0.0
    first = repetitions[0]["probabilities"]
    drifts: list[float] = []
    for repetition in repetitions[1:]:
        drifts.extend(
            abs(float(repetition["probabilities"][arm_id][case_id]) - float(first[arm_id][case_id]))
            for arm_id, cases in first.items()
            for case_id in cases
        )
    return sum(drifts) / len(drifts)


def _run_live(settings: Settings, frozen: FrozenExperiment) -> ExperimentResult:
    status_response, project_response, projects = _fetch_projects(GdcClient())
    projection = _projection(projects)
    if projection.fingerprint != BASELINE_PROJECTION_FINGERPRINT:
        raise ValueError(
            "rebuilt A011 projection does not match the recorded fingerprint; "
            "the frozen evaluation set changed"
        )
    capability = _capability()
    baseline, baseline_record, baseline_measurements = _recorded_baseline(settings)

    control = _run_model(
        TypeSafeJevClient(api_key=settings.typesafe_api_key, model=BASELINE_MODEL),
        projection,
        capability,
    )
    candidate = _run_model(
        TypeSafeJevClient(api_key=settings.typesafe_api_key, model=CANDIDATE_MODEL),
        projection,
        capability,
    )
    evaluation: ModelRegressionEvaluation = compare_model_versions(
        labels=_labels(),
        baseline=baseline,
        candidate=candidate,
        control=control,
        threshold=THRESHOLD,
        min_decision_agreement=MIN_DECISION_AGREEMENT,
        max_drift_excess=MAX_DRIFT_EXCESS,
        max_brier_excess=MAX_BRIER_EXCESS,
        groups=_groups(),
        min_positive_claim_rate=MIN_POSITIVE_CLAIM_RATE,
        max_negative_mean_claim_rate=MAX_NEGATIVE_MEAN_CLAIM_RATE,
        max_negative_group_claim_rate=MAX_NEGATIVE_GROUP_CLAIM_RATE,
    )
    status = status_response.payload
    approved = not evaluation.failures
    return ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": True,
            "upgrade_approved": approved,
            "baseline": {
                "role": "recorded",
                "record": baseline_record,
                "model_id": baseline.model_id,
                "probabilities": baseline.probabilities,
                "usage": baseline.usage,
                "latency_ms": baseline.latency_ms,
            },
            "control": {
                "role": CURRENT_MODEL_ROLE,
                "model_id": control.model_id,
                "probabilities": control.probabilities,
                "usage": control.usage,
                "latency_ms": control.latency_ms,
            },
            "candidate": {
                "role": "candidate",
                "model_id": candidate.model_id,
                "probabilities": candidate.probabilities,
                "usage": candidate.usage,
                "latency_ms": candidate.latency_ms,
            },
            "evaluation": asdict(evaluation),
            "protocol": {
                "threshold": THRESHOLD,
                "baseline_model": BASELINE_MODEL,
                "candidate_model": CANDIDATE_MODEL,
                "min_decision_agreement": MIN_DECISION_AGREEMENT,
                "max_drift_excess": MAX_DRIFT_EXCESS,
                "max_brier_excess": MAX_BRIER_EXCESS,
                "min_positive_claim_rate": MIN_POSITIVE_CLAIM_RATE,
                "max_negative_mean_claim_rate": MAX_NEGATIVE_MEAN_CLAIM_RATE,
                "max_negative_group_claim_rate": MAX_NEGATIVE_GROUP_CLAIM_RATE,
                "projection_fingerprint": projection.fingerprint,
                "recorded_repetition_drift": _repetition_drift(baseline_measurements),
            },
            "cost": {
                "measured": False,
                "basis": "the TypeSafe SDK usage path exposes tokens only",
            },
            "source": {
                "data_release": status.get("data_release"),
                "api_version": status.get("tag"),
                "commit": status.get("commit"),
                "project_receipt": {
                    "url": project_response.url,
                    "response_bytes": project_response.response_bytes,
                    "latency_ms": project_response.latency_ms,
                },
            },
        },
        observations=(
            (
                f"The candidate model {CANDIDATE_MODEL} stays within the frozen tolerances."
                if approved
                else "The candidate model exceeded a frozen tolerance: "
                + "; ".join(evaluation.failures)
            ),
        ),
        limitations=(
            "One capability evaluation set cannot represent every Jev behavior.",
            "The recorded baseline and the candidate ran in different sessions.",
            "Approval scope is this contract, model pair, and evaluation set only.",
            "A capability regression result is not scientific validation.",
        ),
    )


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    if not live:
        baseline_available = False
        try:
            _, _, measurements = _recorded_baseline(settings)
            baseline_available = True
        except RuntimeError:
            measurements = {}
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.FROZEN,
            frozen_fingerprint=frozen.fingerprint,
            measurements={
                "live": False,
                "protocol": {
                    "threshold": THRESHOLD,
                    "baseline_model": BASELINE_MODEL,
                    "candidate_model": CANDIDATE_MODEL,
                    "min_decision_agreement": MIN_DECISION_AGREEMENT,
                    "max_drift_excess": MAX_DRIFT_EXCESS,
                    "max_brier_excess": MAX_BRIER_EXCESS,
                    "question_count": len(_labels()),
                    "positive_questions": VALID_ARM,
                    "negative_arms": list(NULL_ARMS),
                },
                "baseline_record_available": baseline_available,
                "recorded_repetition_drift": _repetition_drift(measurements)
                if baseline_available
                else None,
            },
            limitations=(
                "No model call was made; this is the frozen protocol only.",
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
                limitations=("External failure does not establish regression behavior.",),
            )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
