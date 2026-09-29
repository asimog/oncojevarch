from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from evidence.models import Coverage, EntityLevel, Missingness, PopulationSpec, Provenance
from execution.gdc import GdcClient
from execution.ports import MeasuredResult
from experiments.scientific.catalog import get_scientific_experiment
from jev.fake import FakeJevClient
from oncodex.abc_runtimes import RuntimeArm, execute_arm_program
from oncodex.config import Settings
from oncodex.research_loop import ResearchRuntime
from oncodex.sandbox import SandboxJournal, create_sandbox, seed_sandbox
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

SPEC = get_scientific_experiment("S003")
CAPABILITY_ID = "gdc_gdan_analysis_layer"
MEASUREMENT = "gdan_analysis_co_availability_rate"
MIN_PROJECTS = 25
S002_GDC_RAW_RATE = 1.0
RATE_TOLERANCE = 0.20
POPULATION = PopulationSpec(
    population_id="gdc-tcga-projects-analysis-layer",
    definition=(
        "GDC TCGA projects as returned by the public projects endpoint, measured on the "
        "GDAN/GDAC-published analysis data categories instead of raw experimental strategies"
    ),
    entity_level=EntityLevel.OTHER,
)

COMPATIBILITY_CONTRACT = {
    "contract_id": "s003-gdc-raw-vs-gdan-analysis-layer",
    "reference_measurement": "S002 GDC TCGA raw-layer co-availability (RNA-Seq + WXS strategies)",
    "reference_value": S002_GDC_RAW_RATE,
    "independent_source": (
        "GDAN/GDAC analysis products published at GDC; measured through the projects endpoint's "
        "data-category file counts (Transcriptome Profiling, Simple Nucleotide Variation). NCI "
        "states GDAN GDAC results are made publicly available at the GDC"
    ),
    "population_mapping": "same GDC TCGA projects, measured on a different processing layer",
    "entity_mapping": "project aggregate on both sides",
    "measurement_mapping": (
        "raw layer: experimental_strategy RNA-Seq and WXS > 0; analysis layer: data_category "
        "Transcriptome Profiling and Simple Nucleotide Variation file counts > 0"
    ),
    "normalization": "boolean availability per project per layer; rates are project fractions",
    "estimand": "co-availability rate per layer; agreement is between the two layer rates",
    "declared_mismatches": (
        "both layers are published through the same GDC API host, so this is layer-level "
        "independence, not database-level independence",
        "data categories aggregate several upstream pipelines",
        "20% absolute rate tolerance is declared before execution",
    ),
    "tolerance": RATE_TOLERANCE,
}
RAW_STRATEGIES = ("RNA-Seq", "WXS")
ANALYSIS_CATEGORIES = ("Transcriptome Profiling", "Simple Nucleotide Variation")


@dataclass(frozen=True, slots=True)
class LayerProfile:
    project_id: str
    raw_rna: bool
    raw_wxs: bool
    analysis_transcriptome: bool
    analysis_snv: bool


def parse_layer_profiles(payload: dict[str, Any]) -> tuple[LayerProfile, ...]:
    hits = payload.get("data", {}).get("hits", [])
    profiles: list[LayerProfile] = []
    for hit in hits:
        summary = hit.get("summary") or {}
        strategies = {
            str(entry.get("experimental_strategy")): int(entry.get("file_count") or 0)
            for entry in summary.get("experimental_strategies") or []
        }
        categories = {
            str(entry.get("data_category")): int(entry.get("file_count") or 0)
            for entry in summary.get("data_categories") or []
        }
        profiles.append(
            LayerProfile(
                project_id=str(hit["project_id"]),
                raw_rna=strategies.get(RAW_STRATEGIES[0], 0) > 0,
                raw_wxs=strategies.get(RAW_STRATEGIES[1], 0) > 0,
                analysis_transcriptome=categories.get(ANALYSIS_CATEGORIES[0], 0) > 0,
                analysis_snv=categories.get(ANALYSIS_CATEGORIES[1], 0) > 0,
            )
        )
    return tuple(sorted(profiles, key=lambda profile: profile.project_id))


def layer_rates(profiles: tuple[LayerProfile, ...]) -> dict[str, float | int]:
    total = len(profiles)
    if total == 0:
        return {"projects": 0, "raw_rate": 0.0, "analysis_rate": 0.0}
    raw = sum(1 for profile in profiles if profile.raw_rna and profile.raw_wxs)
    analysis = sum(
        1 for profile in profiles if profile.analysis_transcriptome and profile.analysis_snv
    )
    return {
        "projects": total,
        "raw_rate": raw / total,
        "analysis_rate": analysis / total,
        "raw_co_available": raw,
        "analysis_co_available": analysis,
    }


def fetch_layer_profiles(
    client: GdcClient, *, min_projects: int
) -> tuple[tuple[LayerProfile, ...], str]:
    response = client.get(
        "projects",
        {
            "filters": json.dumps(
                {"op": "in", "content": {"field": "program.name", "value": ["TCGA"]}},
                separators=(",", ":"),
            ),
            "expand": "summary,summary.experimental_strategies,summary.data_categories",
            "fields": "project_id,summary",
            "size": 500,
        },
    )
    status = client.get("status")
    release = str(status.payload.get("data_release") or status.payload.get("tag") or "unknown")
    profiles = parse_layer_profiles(response.payload)
    if len(profiles) < min_projects:
        raise ValueError(
            f"retrieved {len(profiles)} TCGA projects; the frozen minimum is {min_projects}"
        )
    return profiles, release


class GdcGdanLayerCapability:
    capability_id = CAPABILITY_ID
    version = "1"

    def execute(self, *, operation_id: str, inputs: dict[str, Any]) -> MeasuredResult:
        profiles, release = fetch_layer_profiles(GdcClient(), min_projects=MIN_PROJECTS)
        rates = layer_rates(profiles)
        return MeasuredResult(
            operation_id=operation_id,
            method_id=self.capability_id,
            population_id=POPULATION.population_id,
            measurements={
                MEASUREMENT: float(rates["analysis_rate"]),
                "raw_rate": float(rates["raw_rate"]),
                "projects": int(rates["projects"]),
                "analysis_co_available": int(rates.get("analysis_co_available", 0)),
                "raw_co_available": int(rates.get("raw_co_available", 0)),
            },
            provenance={"source": "GDC API (GDAN analysis layer)", "source_version": release},
        )

    def admission_context(
        self, *, result: MeasuredResult, base: AdmissionContext
    ) -> AdmissionContext:
        total = int(result.measurements["projects"])
        return AdmissionContext(
            evidence_id=base.evidence_id,
            measurement=base.measurement,
            population=base.population,
            coverage=Coverage(requested=total, retrieved=total, assayed=total),
            missingness=Missingness(unknown=0),
            provenance=Provenance(
                source="GDC API (GDAN analysis layer)",
                source_version=str(result.provenance.get("source_version", "unknown")),
                method_id=self.capability_id,
                method_version=self.version,
                code_identity=base.provenance.code_identity,
            ),
            metadata={
                **dict(base.metadata or {}),
                "raw_rate": result.measurements["raw_rate"],
                "projects": total,
                "analysis_co_available": result.measurements["analysis_co_available"],
                "raw_co_available": result.measurements["raw_co_available"],
                "contract_id": COMPATIBILITY_CONTRACT["contract_id"],
            },
        )


def _register(registry: CapabilityRegistry) -> None:
    registry.register(
        CapabilityRecord(
            capability_id=CAPABILITY_ID,
            kind=CapabilityKind.METHOD,
            version="1",
            source_identity="module:s003",
            applicability=("public metadata", "project aggregates", "analysis layers"),
            purpose="measure the GDAN/GDAC analysis-layer co-availability of TCGA projects",
            domain_owner="s003",
            inputs=("GDC projects endpoint",),
            outputs=(MEASUREMENT, "raw_rate"),
            evaluated_domain="GDC project metadata, TCGA program, analysis data categories",
        )
    )
    for target in (
        EngineeringReadiness.TESTED,
        EngineeringReadiness.VERIFIED,
        EngineeringReadiness.PROMOTED,
    ):
        registry.advance_engineering(CAPABILITY_ID, "1", target)
    registry.set_scientific_readiness(
        CAPABILITY_ID, "1", ScientificReadiness.VALIDATED_FOR_DEFINED_DOMAIN
    )


def _base_context() -> AdmissionContext:
    return AdmissionContext(
        evidence_id="ev-s003",
        measurement=MEASUREMENT,
        population=POPULATION,
        coverage=Coverage(requested=None, retrieved=None),
        missingness=Missingness(),
        provenance=Provenance(
            source="GDC API (GDAN analysis layer)",
            source_version="pending-dispatch",
            method_id=CAPABILITY_ID,
            method_version="1",
            code_identity="module:s003",
        ),
        metadata={"contract_id": COMPATIBILITY_CONTRACT["contract_id"]},
    )


def _build_reasoner(settings: Settings) -> Any:
    try:
        from oncodex.model_provider import build_agent_model
        from oncox.agents_adapter import AgentsOncoXReasoner

        model = build_agent_model(settings)
        if model is None:
            return _StaticReasoner()
        return AgentsOncoXReasoner(
            model=model, max_tokens=800, reasoning_effort="low", max_attempts=2
        )
    except Exception:  # noqa: BLE001 - deterministic fallback
        return _StaticReasoner()


class _StaticReasoner:
    async def reason(self, request: Any) -> Any:
        from oncox.ports import ReasoningOutput, ReasoningResult

        return ReasoningResult(
            output=ReasoningOutput(
                interpretation="the layer comparison is a bounded reproduction",
                hypotheses=("analysis-layer availability mirrors raw availability",),
                alternative_explanations=("processing pipelines could diverge per project",),
                proposed_tests=("repeat on a later release",),
                unresolved_uncertainty=(),
            ),
            model_id="static-test-double",
            usage={"input_tokens": 0, "output_tokens": 0},
            latency_ms=0.0,
            raw_output="static test double: no model was called",
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
                "preflight": "compatibility contract frozen; no network contacted",
                "compatibility_contract": COMPATIBILITY_CONTRACT,
            },
            observations=(
                f"Compatibility contract {COMPATIBILITY_CONTRACT['contract_id']} frozen "
                "before execution.",
            ),
            limitations=("Preflight records no scientific evidence by design.",),
        )
        store.append("scientific_experiment_result", asdict(result))
        return json.dumps(asdict(result), indent=2, default=str)

    registry = CapabilityRegistry()
    _register(registry)
    runtime = ResearchRuntime(
        registry=registry,
        operations=OperationRegistry(),
        executors={CAPABILITY_ID: GdcGdanLayerCapability()},
        gaps=GapLedger(store),
        investigations=InvestigationLedger(store),
        evidence=EvidenceLedger(store),
    )
    runtime.operations.register(
        ScientificOperation(
            operation_id="op-s003",
            capability_id=CAPABILITY_ID,
            version="1",
            inputs={},
            context=_base_context(),
        )
    )
    investigation = Investigation(
        investigation_id="inv-s003",
        question_id="q-s003",
        candidate_id="c-s003",
        population_id=POPULATION.population_id,
        unresolved_uncertainty=(
            "the S002 raw-layer measurement has not been reproduced on the GDAN analysis layer",
        ),
    )
    runtime.investigations.record(investigation)
    sandbox = create_sandbox(settings.store_dir / "s003" / "sandbox", sandbox_id="s003")
    journal = SandboxJournal(
        store=AppendOnlyJsonlStore(settings.store_dir / "s003" / "sandbox.jsonl"),
        sandbox_id=sandbox.sandbox_id,
    )
    seed_sandbox(sandbox, {"workspace/README.md": "# L3 compatibility sandbox\n"})

    arm_records: list[dict[str, Any]] = []
    status = ExperimentStatus.FAILED
    measurements: dict[str, Any] = {"live": True, "compatibility_contract": COMPATIBILITY_CONTRACT}
    observations: tuple[str, ...] = ()
    try:
        arm_a = execute_arm_program(
            runtime=runtime,
            arm=RuntimeArm.A_DETERMINISTIC,
            sandbox=sandbox,
            journal=journal,
            investigation=investigation,
            need="reproduce the co-availability measurement on the GDAN analysis layer",
            operation_id="op-s003",
            question="",
        )
        arm_records.append({**asdict(arm_a), "arm": arm_a.arm.value})
        if arm_a.outcome != "evidence":
            raise RuntimeError(f"arm A outcome was {arm_a.outcome}")
        evidence = runtime.evidence.get(arm_a.evidence_id)
        if evidence is None:
            raise RuntimeError("S003 evidence was not persisted")
        analysis_rate = float(evidence.value)
        raw_rate = float(evidence.metadata.get("raw_rate", 0.0))
        evaluated = runtime.investigations.latest("inv-s003")
        arm_c = execute_arm_program(
            runtime=runtime,
            arm=RuntimeArm.C_PLUS_JEV_PLUS_ONCOX,
            sandbox=sandbox,
            journal=journal,
            investigation=evaluated if evaluated is not None else investigation,
            need="decide whether the layer-compatibility result warrants further pursuit",
            operation_id="op-s003",
            question="does the compatibility result warrant deeper pursuit?",
            reasoner=_build_reasoner(settings),
            jev_client=FakeJevClient(answers={"pursue__inv-s003": 0.4}),
        )
        arm_records.append({**asdict(arm_c), "arm": arm_c.arm.value})
        agreement = abs(analysis_rate - S002_GDC_RAW_RATE) <= RATE_TOLERANCE
        status = ExperimentStatus.COMPLETED
        measurements.update(
            {
                "arm_outcomes": [record["outcome"] for record in arm_records],
                "evidence_id": evidence.evidence_id,
                "value": analysis_rate,
                "raw_layer_rate": raw_rate,
                "s002_reference": S002_GDC_RAW_RATE,
                "agreement_within_tolerance": agreement,
                "tolerance": RATE_TOLERANCE,
                "projects": int(evidence.metadata.get("projects", 0)),
                "analysis_co_available": int(evidence.metadata.get("analysis_co_available", 0)),
                "jev_policy": (arm_c.jev_record or {}).get("policy", ""),
            }
        )
        observations = (
            (
                f"GDAN analysis-layer rate {analysis_rate:.4f} vs S002 raw-layer reference "
                f"{S002_GDC_RAW_RATE:.4f}; raw layer measured now {raw_rate:.4f}; tolerance "
                f"{RATE_TOLERANCE}: "
                f"{'compatible reproduction' if agreement else 'reproduction outside tolerance'}."
            ),
        )
    except Exception as exc:  # noqa: BLE001 - failures are recorded, not fatal
        measurements["failure_reason"] = f"{type(exc).__name__}: {exc}"
        observations = (
            "S003 did not complete; the compatibility contract and failure are recorded.",
        )
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=status,
        frozen_fingerprint=frozen.fingerprint,
        measurements={**measurements, "arms": arm_records},
        observations=observations,
        limitations=(
            "Layer-level independence only: both layers are published through the GDC API, so "
            "this is not cross-database independence.",
            "Data categories aggregate several upstream pipelines; the mapping is declared, not "
            "derived.",
            "Estimand is aggregate metadata structure, not disease biology.",
        ),
    )
    store.append("scientific_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
