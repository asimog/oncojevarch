from __future__ import annotations

import json
from dataclasses import asdict, dataclass, replace
from hashlib import sha256
from pathlib import Path
from typing import Any

from evidence.models import Coverage, EntityLevel, Missingness, PopulationSpec, Provenance
from execution.gdc import GdcClient
from execution.ports import MeasuredResult
from experiments.scientific.catalog import get_scientific_experiment
from oncodex.config import Settings
from oncodex.research_loop import ResearchRuntime, run_research_step
from oncolab.admission import AdmissionContext
from oncolab.capabilities import (
    CapabilityKind,
    CapabilityRecord,
    CapabilityRegistry,
    EngineeringReadiness,
    ScientificReadiness,
)
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from oncolab.gaps import GapLedger
from oncolab.operations import OperationRegistry, ScientificOperation
from research.ledger import EvidenceLedger, InvestigationLedger
from research.models import Investigation
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_scientific_experiment("S001")

SOURCE_ID = "gdc_public_metadata"
METHOD_ID = "assay_coavailability_permutation"
CAPABILITY_VERSION = "1"
MEASUREMENT = "max_site_share"
SEED = "s001:2026-09-30"
ITERATIONS = 1000
MIN_PROJECTS = 40
POPULATION = PopulationSpec(
    population_id="gdc-tcga-projects",
    definition="GDC projects with program TCGA as returned by the public projects endpoint",
    entity_level=EntityLevel.OTHER,
)


@dataclass(frozen=True, slots=True)
class ProjectAssayProfile:
    project_id: str
    primary_site: str
    rna_seq: bool
    wxs: bool


def parse_profiles(payload: dict[str, Any]) -> tuple[ProjectAssayProfile, ...]:
    hits = payload.get("data", {}).get("hits", [])
    profiles: list[ProjectAssayProfile] = []
    for hit in hits:
        summary = hit.get("summary") or {}
        strategy_counts: dict[str, int] = {}
        for entry in summary.get("experimental_strategies") or []:
            strategy_counts[str(entry.get("experimental_strategy"))] = int(
                entry.get("file_count") or 0
            )
        profiles.append(
            ProjectAssayProfile(
                project_id=str(hit["project_id"]),
                primary_site=str(hit.get("primary_site") or "unknown"),
                rna_seq=strategy_counts.get("RNA-Seq", 0) > 0,
                wxs=strategy_counts.get("WXS", 0) > 0,
            )
        )
    return tuple(sorted(profiles, key=lambda profile: profile.project_id))


def max_site_share(sites: list[str], rna: list[bool], wxs: list[bool]) -> float:
    counts: dict[str, int] = {}
    total = 0
    for site, has_rna, has_wxs in zip(sites, rna, wxs, strict=True):
        if has_rna and has_wxs:
            counts[site] = counts.get(site, 0) + 1
            total += 1
    if total == 0:
        return 0.0
    return max(counts.values()) / total


def _permuted(values: list[Any], *, salt: str, iteration: int) -> list[Any]:
    order = sorted(
        range(len(values)),
        key=lambda index: sha256(f"{SEED}:{salt}:{iteration}:{index}".encode()).hexdigest(),
    )
    return [values[index] for index in order]


def permutation_statistic(
    profiles: tuple[ProjectAssayProfile, ...],
    *,
    iterations: int = ITERATIONS,
) -> dict[str, float]:
    """Deterministic independence null: RNA-Seq and WXS flags are permuted independently."""

    sites = [profile.primary_site for profile in profiles]
    rna = [profile.rna_seq for profile in profiles]
    wxs = [profile.wxs for profile in profiles]
    observed = max_site_share(sites, rna, wxs)
    exceed = 0
    null_sum = 0.0
    for iteration in range(iterations):
        value = max_site_share(
            sites,
            _permuted(rna, salt="rna", iteration=iteration),
            _permuted(wxs, salt="wxs", iteration=iteration),
        )
        null_sum += value
        if value >= observed:
            exceed += 1
    return {
        "max_site_share": observed,
        "null_mean": null_sum / iterations,
        "permutation_p": (exceed + 1) / (iterations + 1),
    }


def code_identity() -> str:
    return "module:" + sha256(Path(__file__).read_bytes()).hexdigest()[:16]


class AssayCoavailabilityCapability:
    """Deterministic capability: project profiles from GDC public metadata plus the null test."""

    capability_id = METHOD_ID
    version = CAPABILITY_VERSION

    def __init__(self, *, client: GdcClient, min_projects: int = MIN_PROJECTS) -> None:
        self.client = client
        self.min_projects = min_projects

    def execute(self, *, operation_id: str, inputs: dict[str, Any]) -> MeasuredResult:
        status = self.client.get("status")
        data_release = str(
            status.payload.get("data_release") or status.payload.get("tag") or "unknown"
        )
        response = self.client.get(
            "projects",
            {
                "filters": json.dumps(
                    {
                        "op": "in",
                        "content": {"field": "program.name", "value": ["TCGA"]},
                    },
                    separators=(",", ":"),
                ),
                "expand": "summary,summary.experimental_strategies",
                "fields": "project_id,name,primary_site,summary",
                "size": 500,
            },
        )
        profiles = parse_profiles(response.payload)
        if len(profiles) < self.min_projects:
            raise ValueError(
                f"retrieved {len(profiles)} TCGA projects; the frozen minimum is "
                f"{self.min_projects}"
            )
        statistics = permutation_statistic(profiles)
        co_available = sum(
            1 for profile in profiles if profile.rna_seq and profile.wxs
        )
        no_file_data = sum(
            1 for profile in profiles if not profile.rna_seq and not profile.wxs
        )
        return MeasuredResult(
            operation_id=operation_id,
            method_id=self.capability_id,
            population_id=POPULATION.population_id,
            measurements={
                MEASUREMENT: statistics["max_site_share"],
                "null_mean": statistics["null_mean"],
                "permutation_p": statistics["permutation_p"],
                "projects_total": len(profiles),
                "co_available_projects": co_available,
                "no_file_data_projects": no_file_data,
            },
            provenance={
                "source": "GDC API",
                "source_version": data_release,
                "api_url": response.url,
            },
        )

    def admission_context(
        self, *, result: MeasuredResult, base: AdmissionContext
    ) -> AdmissionContext:
        total = int(result.measurements["projects_total"])
        no_file_data = int(result.measurements["no_file_data_projects"])
        co_available = int(result.measurements["co_available_projects"])
        return replace(
            base,
            coverage=Coverage(requested=total, retrieved=total, assayed=co_available),
            missingness=Missingness(unknown=no_file_data),
            provenance=replace(
                base.provenance,
                source_version=str(result.provenance.get("source_version", "unknown")),
            ),
            metadata={
                **dict(base.metadata or {}),
                "null_mean": float(result.measurements["null_mean"]),
                "permutation_p": float(result.measurements["permutation_p"]),
                "projects_total": total,
                "co_available_projects": co_available,
                "no_file_data_projects": no_file_data,
            },
        )


def _promote(registry: CapabilityRegistry, capability_id: str) -> CapabilityRecord:
    for target in (
        EngineeringReadiness.TESTED,
        EngineeringReadiness.VERIFIED,
        EngineeringReadiness.PROMOTED,
    ):
        registry.advance_engineering(capability_id, CAPABILITY_VERSION, target)
    return registry.get(capability_id, CAPABILITY_VERSION)


def _register(registry: CapabilityRegistry) -> None:
    identity = code_identity()
    registry.register(
        CapabilityRecord(
            capability_id=SOURCE_ID,
            kind=CapabilityKind.SOURCE,
            version=CAPABILITY_VERSION,
            source_identity=identity,
            applicability=("public metadata", "project aggregates"),
            purpose="read public GDC project metadata with experimental-strategy file counts",
            domain_owner="gdc-source",
            inputs=("program filter",),
            outputs=("project assay profiles",),
            evaluated_domain="GDC public projects endpoint, TCGA program",
        )
    )
    registry.register(
        CapabilityRecord(
            capability_id=METHOD_ID,
            kind=CapabilityKind.METHOD,
            version=CAPABILITY_VERSION,
            source_identity=identity,
            applicability=("association tests", "null models", "project aggregates"),
            purpose="seeded permutation statistic for assay co-availability concentration",
            domain_owner="s001",
            inputs=("project assay profiles",),
            outputs=(MEASUREMENT,),
            evaluated_domain="GDC project metadata, TCGA program",
        )
    )
    _promote(registry, SOURCE_ID)
    _promote(registry, METHOD_ID)
    registry.set_scientific_readiness(
        SOURCE_ID, CAPABILITY_VERSION, ScientificReadiness.VALIDATED_FOR_REPLAY
    )
    registry.set_scientific_readiness(
        METHOD_ID, CAPABILITY_VERSION, ScientificReadiness.VALIDATED_FOR_DEFINED_DOMAIN
    )


def _base_context() -> AdmissionContext:
    return AdmissionContext(
        evidence_id="ev-s001",
        measurement=MEASUREMENT,
        population=POPULATION,
        coverage=Coverage(requested=None, retrieved=None),
        missingness=Missingness(),
        provenance=Provenance(
            source="GDC API",
            source_version="pending-dispatch",
            method_id=METHOD_ID,
            method_version=CAPABILITY_VERSION,
            code_identity=code_identity(),
        ),
        metadata={
            "seed": SEED,
            "iterations": ITERATIONS,
            "null": "independent RNA-Seq and WXS flag permutations preserving marginals",
        },
    )


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    if not live:
        preflight_refusal = None
        if SPEC.validation_errors():
            preflight_refusal = "specification is incomplete"
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.FROZEN,
            frozen_fingerprint=frozen.fingerprint,
            measurements={
                "live": False,
                "preflight": "protocol frozen; no measurement taken and no network contacted",
                "spec_errors": list(SPEC.validation_errors()),
                "preflight_refusal": preflight_refusal,
                "population": POPULATION.population_id,
                "seed": SEED,
                "iterations": ITERATIONS,
                "min_projects": MIN_PROJECTS,
            },
            observations=("The S001 protocol and admission identity are frozen; execution "
                          "requires --live.",),
            limitations=("Preflight records no scientific evidence by design.",),
        )
        store.append("scientific_experiment_result", asdict(result))
        return json.dumps(asdict(result), indent=2, default=str)

    registry = CapabilityRegistry()
    _register(registry)
    runtime = ResearchRuntime(
        registry=registry,
        operations=OperationRegistry(),
        executors={METHOD_ID: AssayCoavailabilityCapability(client=GdcClient())},
        gaps=GapLedger(store),
        investigations=InvestigationLedger(store),
        evidence=EvidenceLedger(store),
    )
    runtime.operations.register(
        ScientificOperation(
            operation_id="op-s001",
            capability_id=METHOD_ID,
            version=CAPABILITY_VERSION,
            inputs={},
            context=_base_context(),
        )
    )
    investigation = Investigation(
        investigation_id="inv-s001",
        question_id="q-s001",
        candidate_id="c-s001",
        population_id=POPULATION.population_id,
        unresolved_uncertainty=(
            "assay co-availability structure across TCGA projects is unmeasured",
        ),
    )
    runtime.investigations.record(investigation)

    status = ExperimentStatus.FAILED
    measurements: dict[str, Any] = {"live": True}
    observations: tuple[str, ...] = ()
    failure_reason = ""
    try:
        step = run_research_step(
            runtime=runtime,
            investigation=investigation,
            need="measure assay co-availability concentration across TCGA projects",
            operation_id="op-s001",
        )
        measurements["step_outcome"] = step.outcome
        if step.outcome == "evidence":
            evidence = runtime.evidence.get(step.evidence_id)
            if evidence is None:
                raise RuntimeError("admitted evidence was not persisted")
            value = float(evidence.value)
            null_mean = float(evidence.metadata["null_mean"])
            p_value = float(evidence.metadata["permutation_p"])
            status = ExperimentStatus.COMPLETED
            measurements["evidence_id"] = evidence.evidence_id
            measurements["value"] = value
            measurements["null_mean"] = null_mean
            measurements["permutation_p"] = p_value
            measurements["projects_total"] = int(evidence.metadata["projects_total"])
            measurements["co_available_projects"] = int(
                evidence.metadata["co_available_projects"]
            )
            measurements["coverage"] = {
                "requested": evidence.coverage.requested,
                "retrieved": evidence.coverage.retrieved,
                "assayed": evidence.coverage.assayed,
            }
            measurements["missingness"] = {
                "unknown": evidence.missingness.unknown,
            }
            if p_value <= 0.05:
                statement = (
                    f"The site concentration of co-available projects exceeded the frozen "
                    f"independence null (max share {value:.4f}, null mean {null_mean:.4f}, "
                    f"p={p_value:.4f}); this is a public-metadata structure observation, not "
                    "a biological claim."
                )
            else:
                statement = (
                    f"The site concentration of co-available projects did not exceed the frozen "
                    f"independence null (max share {value:.4f}, null mean {null_mean:.4f}, "
                    f"p={p_value:.4f})."
                )
            observations = (statement,)
        else:
            failure_reason = f"step outcome was {step.outcome}"
    except Exception as exc:  # noqa: BLE001 - failure branch must record, not crash
        failure_reason = f"{type(exc).__name__}: {exc}"
    if status is ExperimentStatus.FAILED:
        measurements["failure_reason"] = failure_reason or "unknown failure"
        observations = (f"S001 did not complete: {measurements['failure_reason']}.",)
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=status,
        frozen_fingerprint=frozen.fingerprint,
        measurements=measurements,
        observations=observations,
        limitations=(
            "The question is about public metadata structure, not disease biology.",
            "One prespecified statistic and one null family; no multiplicity family is claimed.",
            "Coverage and missingness are disclosed by the capable execution and admitted "
            "together with the value.",
            "No Jev and no OncoX participate in this investigation.",
        ),
    )
    store.append("scientific_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
