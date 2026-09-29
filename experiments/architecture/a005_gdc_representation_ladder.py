from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from evaluation.representation import derive_paired_coverage, paired_feasibility_decision
from execution.gdc import GdcClient, GdcResponse
from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A005")
PROJECT_ID = "TCGA-LUAD"
LEFT_STRATEGY = "RNA-Seq"
RIGHT_STRATEGY = "WXS"
MINIMUM_PAIRED_CASES = 100
MINIMUM_PAIRED_FRACTION = 0.5


def _equals(field: str, value: str) -> dict[str, Any]:
    return {"op": "=", "content": {"field": field, "value": value}}


def _strategy_filter(strategies: tuple[str, ...]) -> dict[str, Any]:
    if len(strategies) == 1:
        return _equals("files.experimental_strategy", strategies[0])
    return {
        "op": "in",
        "content": {"field": "files.experimental_strategy", "value": list(strategies)},
    }


def _case_count_query(client: GdcClient, strategies: tuple[str, ...]) -> GdcResponse:
    filters = {
        "op": "and",
        "content": [
            _equals("project.project_id", PROJECT_ID),
            _strategy_filter(strategies),
        ],
    }
    return client.get(
        "cases",
        {"filters": json.dumps(filters, separators=(",", ":")), "size": 0},
    )


def _total(response: GdcResponse) -> int:
    return int(response.payload["data"]["pagination"]["total"])


def _receipt(response: GdcResponse) -> dict[str, Any]:
    return {
        "url": response.url,
        "response_bytes": response.response_bytes,
        "latency_ms": response.latency_ms,
    }


def _run_live() -> dict[str, Any]:
    client = GdcClient()
    status = client.get("status")
    project = client.get(
        f"projects/{PROJECT_ID}",
        {
            "fields": (
                "project_id,name,primary_site,disease_type,summary.case_count,summary.file_count"
            )
        },
    )
    file_filter = _equals("cases.project.project_id", PROJECT_ID)
    facets = client.get(
        "files",
        {
            "filters": json.dumps(file_filter, separators=(",", ":")),
            "facets": "experimental_strategy,data_category",
            "size": 0,
        },
    )
    left = _case_count_query(client, (LEFT_STRATEGY,))
    right = _case_count_query(client, (RIGHT_STRATEGY,))
    union = _case_count_query(client, (LEFT_STRATEGY, RIGHT_STRATEGY))

    project_data = project.payload["data"]
    total_cases = int(project_data["summary"]["case_count"])
    coverage = derive_paired_coverage(
        total_cases=total_cases,
        left_cases=_total(left),
        right_cases=_total(right),
        union_cases=_total(union),
    )
    decision = paired_feasibility_decision(
        coverage,
        minimum_cases=MINIMUM_PAIRED_CASES,
        minimum_fraction=MINIMUM_PAIRED_FRACTION,
    )

    strategy_buckets = facets.payload["data"]["aggregations"]["experimental_strategy"]["buckets"]
    strategies = {str(bucket["key"]): int(bucket["doc_count"]) for bucket in strategy_buckets}
    count_responses = (left, right, union)
    return {
        "source": {
            "api": "GDC",
            "status": status.payload["status"],
            "data_release": status.payload["data_release"],
            "api_tag": status.payload["tag"],
            "commit": status.payload["commit"],
        },
        "frozen_policy": {
            "project_id": PROJECT_ID,
            "left_strategy": LEFT_STRATEGY,
            "right_strategy": RIGHT_STRATEGY,
            "minimum_paired_cases": MINIMUM_PAIRED_CASES,
            "minimum_paired_fraction": MINIMUM_PAIRED_FRACTION,
        },
        "representations": (
            {
                "level": "project_metadata",
                "resolution": "scope_only",
                "payload": {
                    "project_id": project_data["project_id"],
                    "name": project_data["name"],
                    "primary_site": project_data["primary_site"],
                    "disease_type": project_data["disease_type"],
                    "case_count": total_cases,
                    "file_count": int(project_data["summary"]["file_count"]),
                },
                "receipt": _receipt(project),
            },
            {
                "level": "file_facets",
                "resolution": "modalities_present_but_overlap_unknown",
                "strategy_file_counts": {
                    LEFT_STRATEGY: strategies.get(LEFT_STRATEGY, 0),
                    RIGHT_STRATEGY: strategies.get(RIGHT_STRATEGY, 0),
                },
                "receipt": _receipt(facets),
            },
            {
                "level": "case_count_intersection",
                "resolution": "paired_case_coverage_resolved",
                "coverage": asdict(coverage),
                "decision": decision,
                "receipts": tuple(_receipt(response) for response in count_responses),
                "total_response_bytes": sum(
                    response.response_bytes for response in count_responses
                ),
                "total_latency_ms": sum(response.latency_ms for response in count_responses),
            },
        ),
        "decision": decision,
        "success_criteria_met": decision == "proceed_to_sample_compatibility_check",
        "raw_or_case_records_downloaded": False,
    }


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
                "project_id": PROJECT_ID,
                "strategies": (LEFT_STRATEGY, RIGHT_STRATEGY),
                "minimum_paired_cases": MINIMUM_PAIRED_CASES,
                "minimum_paired_fraction": MINIMUM_PAIRED_FRACTION,
                "representation_levels": (
                    "project_metadata",
                    "file_facets",
                    "case_count_intersection",
                ),
            },
            limitations=("No GDC API request was made in offline mode.",),
        )
    else:
        try:
            measurements = {"live": True, **_run_live()}
            result = ExperimentResult(
                experiment_id=SPEC.experiment_id,
                experiment_class=SPEC.experiment_class,
                status=ExperimentStatus.COMPLETED,
                frozen_fingerprint=frozen.fingerprint,
                measurements=measurements,
                observations=(
                    "Targeted aggregate counts resolved case overlap without case or file "
                    "payloads.",
                    "Deterministic code was sufficient; no Jev call was justified.",
                ),
                limitations=(
                    "GDC operational case associations are not a scientific analysis population.",
                    "Case-level file overlap does not prove compatible samples, aliquots, "
                    "or assays.",
                    "The feasibility thresholds are architecture-test policy, not scientific "
                    "criteria.",
                ),
            )
        except Exception as exc:
            result = ExperimentResult(
                experiment_id=SPEC.experiment_id,
                experiment_class=SPEC.experiment_class,
                status=ExperimentStatus.FAILED,
                frozen_fingerprint=frozen.fingerprint,
                measurements={"live": True, "error": f"{type(exc).__name__}: {exc}"},
                limitations=("GDC failure is not a biological negative.",),
            )
    store.append("architecture_experiment_result", asdict(result))
    return str(asdict(result))
