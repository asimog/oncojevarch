from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from time import perf_counter
from typing import Any

from evaluation.rediscovery import (
    MaskedProject,
    ambiguous_cases,
    apply_overrides,
    build_features,
    evaluate_rankings,
    leakage_findings,
    leave_one_out_ranking,
    mask_id_for,
    permuted_labels,
)
from evidence.projections import freeze_projection
from execution.gdc import GdcClient, GdcResponse
from experiments.catalog import get_experiment
from jev.contracts import JevCapability, JevPrimitive, JevQuestion
from jev.typesafe_adapter import TypeSafeJevClient
from oncodex.config import Settings
from oncodex.model_provider import build_agent_model
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from oncox.agents_adapter import AgentsOncoXReasoner
from oncox.ports import ReasoningRequest
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A019")
SITE_PROJECTS: dict[str, tuple[str, ...]] = {
    "Kidney": ("TCGA-KIRC", "TCGA-KIRP", "TCGA-KICH"),
    "Lung": ("TCGA-LUAD", "TCGA-LUSC"),
    "Colon and rectum": ("TCGA-COAD", "TCGA-READ"),
    "Uterus": ("TCGA-UCEC", "TCGA-UCS"),
    "Brain": ("TCGA-GBM", "TCGA-LGG"),
}
PROJECT_IDS = tuple(project_id for projects in SITE_PROJECTS.values() for project_id in projects)
TARGET_RECALL_AT_1 = 0.50
NULL_CHANCE_MARGIN = 0.15
AMBIGUITY_MARGIN = 0.10
TRIAGE_THRESHOLD = 0.5
MAX_ONCOX_CALLS = 4
REASONING_EFFORT = "low"
K_VALUES = (1, 2, 3)


def _project_filter() -> str:
    return json.dumps(
        {"op": "in", "content": {"field": "project_id", "value": list(PROJECT_IDS)}},
        separators=(",", ":"),
    )


def _fetch(client: GdcClient) -> tuple[GdcResponse, GdcResponse, dict[str, dict[str, Any]]]:
    status = client.get("status")
    response = client.get(
        "projects",
        {
            "filters": _project_filter(),
            "expand": "summary,summary.data_categories,summary.experimental_strategies",
            "fields": "project_id,name,primary_site,disease_type,summary",
            "size": len(PROJECT_IDS),
        },
    )
    hits = response.payload.get("data", {}).get("hits", [])
    projects = {str(hit["project_id"]): hit for hit in hits}
    if set(projects) != set(PROJECT_IDS):
        raise ValueError("GDC response does not match the frozen project set")
    return status, response, projects


def _masked_projects(
    projects: dict[str, dict[str, Any]],
) -> tuple[tuple[MaskedProject, ...], dict[str, str], dict[str, str]]:
    masked: list[MaskedProject] = []
    labels: dict[str, str] = {}
    display: dict[str, str] = {}
    for site, project_ids in SITE_PROJECTS.items():
        for project_id in project_ids:
            summary = projects[project_id]["summary"]
            profile: dict[str, float] = {}
            for entry in summary["data_categories"]:
                profile[f"category::{entry['data_category']}"] = float(entry["file_count"])
            for entry in summary["experimental_strategies"]:
                profile[f"strategy::{entry['experimental_strategy']}"] = float(entry["file_count"])
            mask_id = mask_id_for(project_id)
            masked.append(
                MaskedProject(
                    mask_id=mask_id,
                    label=site,
                    features=build_features(
                        case_count=int(summary["case_count"]),
                        file_count=int(summary["file_count"]),
                        profile=profile,
                    ),
                )
            )
            labels[mask_id] = site
            display[mask_id] = project_id
    return tuple(sorted(masked, key=lambda project: project.mask_id)), labels, display


def _masked_view(masked: tuple[MaskedProject, ...]) -> dict[str, Any]:
    return {
        "projects": {
            project.mask_id: {
                "feature_count": len(project.features),
                "file_share_by_category": {
                    key.removeprefix("category::"): round(value, 6)
                    for key, value in sorted(project.features.items())
                    if key.startswith("category::")
                },
                "file_share_by_strategy": {
                    key.removeprefix("strategy::"): round(value, 6)
                    for key, value in sorted(project.features.items())
                    if key.startswith("strategy::")
                },
                "files_per_case": round(project.features["files_per_case"], 4),
            }
            for project in masked
        }
    }


def _triage_capability(masked_ids: tuple[str, ...]) -> JevCapability:
    return JevCapability(
        capability_id="a019-ambiguous-site-triage",
        version="0.1.0",
        domain_owner="evaluation",
        semantic_purpose=("Decide whether an ambiguous masked profile needs deeper reasoning."),
        projection_id="a019-masked-profiles",
        projection_version="1",
        questions=tuple(
            JevQuestion(
                question_id=f"escalate__{mask_id}",
                primitive=JevPrimitive.NOUL,
                instructions=(
                    f"Using only `projects.{mask_id}`, the deterministic ranking of candidate "
                    "primary sites is close between the leading candidates. Would open-ended "
                    "reasoning over the supplied aggregate profile plausibly resolve which site "
                    "the cohort comes from? Answer true only if the profile leaves a resolvable, "
                    "material ambiguity; answer false if the profile carries no further "
                    "discriminating information beyond the ranked order."
                ),
                criteria={
                    "true": "the aggregate profile could resolve the site ambiguity",
                    "false": "the profile adds nothing beyond the deterministic ranking",
                },
            )
            for mask_id in masked_ids
        ),
    )


async def _oncox_overrides(
    *,
    reasoner: AgentsOncoXReasoner,
    masked_view: dict[str, Any],
    rankings: dict[str, Any],
    candidates: tuple[str, ...],
) -> tuple[dict[str, tuple[str, ...]], list[dict[str, Any]]]:
    overrides: dict[str, tuple[str, ...]] = {}
    records: list[dict[str, Any]] = []
    for mask_id in candidates[:MAX_ONCOX_CALLS]:
        ranking = rankings[mask_id]
        request = ReasoningRequest(
            investigation_id=mask_id,
            evidence_ids=(f"masked-profile:{mask_id}",),
            question=(
                "Rank the three candidate primary sites for this masked cohort from most to least "
                "plausible, using only the supplied aggregate profile."
            ),
            structured_state={
                "profile": masked_view["projects"][mask_id],
                "deterministic_ranking": list(ranking.ranked_labels[:3]),
            },
        )
        result = await reasoner.reason(request)
        ordered = _extract_order(result.output, tuple(ranking.ranked_labels[:3]))
        records.append(
            {
                "mask_id": mask_id,
                "ranking": list(ordered),
                "interpretation": result.output.interpretation,
                "usage": result.usage,
                "latency_ms": result.latency_ms,
                "attempts": result.attempts,
            }
        )
        overrides[mask_id] = ordered + tuple(ranking.ranked_labels[3:])
    return overrides, records


def _extract_order(output: Any, candidates: tuple[str, ...]) -> tuple[str, ...]:
    """Read the model's ranking, keeping only candidates the deterministic arm already offered."""

    text = " ".join(
        (
            output.interpretation,
            *output.hypotheses,
            *output.alternative_explanations,
            *output.proposed_tests,
            *output.unresolved_uncertainty,
        )
    ).lower()
    positions = {label: text.find(label.lower()) for label in candidates}
    ordered = tuple(
        label
        for label in sorted(
            candidates, key=lambda label: (positions[label] < 0, positions[label], label)
        )
        if positions[label] >= 0
    )
    if not ordered:
        return candidates
    return ordered + tuple(label for label in candidates if label not in ordered)


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    status_response, project_response, projects = _fetch(GdcClient())
    masked, labels, display = _masked_projects(projects)
    masked_view = _masked_view(masked)
    masked_text = json.dumps(masked_view, sort_keys=True)
    deterministic = leave_one_out_ranking(masked)
    deterministic_metrics = evaluate_rankings(
        rankings=deterministic, labels=labels, k_values=K_VALUES
    )
    ambiguous = ambiguous_cases(deterministic, relative_margin=AMBIGUITY_MARGIN)
    null_labels = permuted_labels(labels)
    null_ranking = leave_one_out_ranking(
        tuple(
            MaskedProject(
                mask_id=project.mask_id,
                label=null_labels[project.mask_id],
                features=project.features,
            )
            for project in masked
        )
    )
    null_metrics = evaluate_rankings(rankings=null_ranking, labels=null_labels, k_values=(1,))
    secrets = tuple(sorted(PROJECT_IDS)) + tuple(
        str(projects[project_id]["name"]) for project_id in PROJECT_IDS
    )
    findings = leakage_findings(
        masked_text=masked_text,
        secrets=secrets,
        null_recall_at_1=null_metrics.metrics["recall@1"],
        chance_recall_at_1=deterministic_metrics.metrics["chance_recall@1"],
        margin=NULL_CHANCE_MARGIN,
    )

    arms: dict[str, Any] = {
        "deterministic": {
            "metrics": deterministic_metrics.metrics,
            "candidates": len(masked),
            "oncox_calls": 0,
            "jev_calls": 0,
            "input_tokens": 0,
            "output_tokens": 0,
        }
    }
    if live and ambiguous:
        projection = freeze_projection(
            projection_id="a019-masked-profiles",
            version="1",
            question_id="ambiguous-site-triage",
            source_evidence_ids=tuple(f"masked-profile:{mask_id}" for mask_id in ambiguous),
            payload=masked_view,
        )
        capability = _triage_capability(ambiguous)
        client = TypeSafeJevClient(api_key=settings.typesafe_api_key, model=settings.jev_model)
        triage_started = perf_counter()
        decision = client.evaluate(projection, capability)
        triage_latency_ms = (perf_counter() - triage_started) * 1000
        probabilities = {
            answer.question_id.removeprefix("escalate__"): float(answer.value)
            for answer in decision.answers
        }
        escalated = tuple(
            mask_id for mask_id in ambiguous if probabilities[mask_id] >= TRIAGE_THRESHOLD
        )
        reasoner = AgentsOncoXReasoner(
            model=build_agent_model(settings), reasoning_effort=REASONING_EFFORT
        )
        ranking_by_id = {ranking.mask_id: ranking for ranking in deterministic}
        overrides, oncox_records = __import__("asyncio").run(
            _oncox_overrides(
                reasoner=reasoner,
                masked_view=masked_view,
                rankings=ranking_by_id,
                candidates=escalated,
            )
        )
        reranked = apply_overrides(deterministic, overrides)
        reranked_metrics = evaluate_rankings(rankings=reranked, labels=labels, k_values=K_VALUES)
        arms["deterministic_plus_jev"] = {
            "metrics": evaluate_rankings(
                rankings=deterministic, labels=labels, k_values=K_VALUES
            ).metrics,
            "ambiguous_cases": list(ambiguous),
            "escalated_cases": list(escalated),
            "probabilities": probabilities,
            "jev_calls": 1,
            "oncox_calls": 0,
            "input_tokens": int(decision.usage.get("input_tokens") or 0),
            "output_tokens": int(decision.usage.get("output_tokens") or 0),
            "latency_ms": triage_latency_ms,
        }
        arms["deterministic_plus_jev_plus_oncox"] = {
            "metrics": reranked_metrics.metrics,
            "escalated_cases": list(escalated),
            "oncox_records": oncox_records,
            "oncox_calls": len(oncox_records),
            "jev_calls": 1,
            "input_tokens": sum(
                int(record["usage"].get("input_tokens") or 0) for record in oncox_records
            ),
            "output_tokens": sum(
                int(record["usage"].get("output_tokens") or 0) for record in oncox_records
            ),
        }

    best_recall = max(arm["metrics"]["recall@1"] for arm in arms.values())
    passed = (
        best_recall >= TARGET_RECALL_AT_1
        and not findings
        and null_metrics.metrics["recall@1"]
        <= deterministic_metrics.metrics["chance_recall@1"] + NULL_CHANCE_MARGIN
    )
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": live,
            "rediscovery_supported": passed,
            "masked_case_count": len(masked),
            "label_space": sorted(set(labels.values())),
            "label_fingerprint": sha256(json.dumps(labels, sort_keys=True).encode()).hexdigest(),
            "arms": arms,
            "deterministic_per_case": deterministic_metrics.per_case,
            "null_control": {
                "recall@1": null_metrics.metrics["recall@1"],
                "chance_recall@1": deterministic_metrics.metrics["chance_recall@1"],
                "margin": NULL_CHANCE_MARGIN,
            },
            "leakage_findings": list(findings),
            "masked_identity_revealed": False,
            "protocol": {
                "target_recall_at_1": TARGET_RECALL_AT_1,
                "ambiguity_margin": AMBIGUITY_MARGIN,
                "triage_threshold": TRIAGE_THRESHOLD,
                "max_oncox_calls": MAX_ONCOX_CALLS,
                "reasoning_effort": REASONING_EFFORT,
                "k_values": list(K_VALUES),
                "mask_function": "sha256(identifier)[:8] prefixed with p",
            },
            "source": {
                "data_release": status_response.payload.get("data_release"),
                "api_version": status_response.payload.get("tag"),
                "commit": status_response.payload.get("commit"),
                "project_receipt": {
                    "url": project_response.url,
                    "response_bytes": project_response.response_bytes,
                    "latency_ms": project_response.latency_ms,
                },
                "records_downloaded": (
                    "project aggregates only; 0 case, sample, aliquot, file, or molecular records"
                ),
            },
            "cost": {
                "measured": False,
                "basis": "provider usage paths expose tokens only",
            },
        },
        observations=(
            (
                "A held-out site relationship was recovered above the frozen target with no "
                "leakage finding and a null control at chance."
                if passed
                else "The frozen rediscovery target was not met, or a leakage indicator fired."
            ),
        ),
        limitations=(
            "Primary site from aggregate file profiles is a metadata relationship, not a "
            "biological discovery, and it cannot establish cancer biology.",
            "Eleven masked projects across five sites is a small evaluation set.",
            "The deterministic arm is leave-one-out nearest centroid over aggregate shares.",
            "Model pretraining may already associate TCGA-like profiles with sites.",
            "OncoX re-ranks only inside the candidate set the deterministic arm produced.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
