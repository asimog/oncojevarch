from __future__ import annotations

from dataclasses import asdict

from evidence.models import (
    Coverage,
    EntityLevel,
    Missingness,
    PopulationSpec,
    Provenance,
    ScientificEvidence,
)
from evidence.projections import build_projection
from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.experiments import (
    ExperimentResult,
    ExperimentStatus,
    FrozenExperiment,
)
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A003")


def _demo_evidence() -> tuple[ScientificEvidence, ...]:
    population = PopulationSpec(
        "demo-pop", "synthetic architecture-only population", EntityLevel.CASE, 100
    )
    provenance = Provenance("synthetic", "1", "demo-method", "1", "scaffold")
    return (
        ScientificEvidence(
            "e1",
            population,
            "effect_direction",
            "positive",
            None,
            Coverage(100, 100, 100),
            Missingness(),
            provenance,
            {"magnitude_band": "moderate", "subgroup_size": 30, "uncertainty_band": "wide"},
        ),
        ScientificEvidence(
            "e2",
            population,
            "replication",
            "failed",
            None,
            Coverage(100, 95, 95),
            Missingness(unknown=5),
            provenance,
            {"source_relation": "independent replay"},
        ),
    )


def run(*, settings: Settings, live: bool = False) -> str:
    del live  # A003 scaffold currently tests projection mechanics only.
    frozen = FrozenExperiment.freeze(SPEC)
    evidence = _demo_evidence()

    projections = []
    projectors = (
        ("P0", lambda es: {"effect_direction": es[0].value}),
        (
            "P1",
            lambda es: {
                "effect_direction": es[0].value,
                "magnitude_band": es[0].metadata["magnitude_band"],
            },
        ),
        (
            "P2",
            lambda es: {
                "effect_direction": es[0].value,
                "magnitude_band": es[0].metadata["magnitude_band"],
                "subgroup_size": es[0].metadata["subgroup_size"],
            },
        ),
        (
            "P3",
            lambda es: {
                "effect_direction": es[0].value,
                "magnitude_band": es[0].metadata["magnitude_band"],
                "subgroup_size": es[0].metadata["subgroup_size"],
                "uncertainty_band": es[0].metadata["uncertainty_band"],
            },
        ),
        (
            "P4",
            lambda es: {
                "effect_direction": es[0].value,
                "magnitude_band": es[0].metadata["magnitude_band"],
                "subgroup_size": es[0].metadata["subgroup_size"],
                "uncertainty_band": es[0].metadata["uncertainty_band"],
                "missing_unknown": es[1].missingness.unknown,
            },
        ),
        (
            "P5",
            lambda es: {
                "effect_direction": es[0].value,
                "magnitude_band": es[0].metadata["magnitude_band"],
                "subgroup_size": es[0].metadata["subgroup_size"],
                "uncertainty_band": es[0].metadata["uncertainty_band"],
                "missing_unknown": es[1].missingness.unknown,
                "replication": es[1].value,
            },
        ),
    )
    for projection_id, projector in projectors:
        p = build_projection(
            projection_id=projection_id,
            version="1",
            question_id="demo-context-dependence",
            evidence=evidence,
            projector=projector,
        )
        projections.append(
            {"id": p.projection_id, "fingerprint": p.fingerprint, "payload": p.payload}
        )

    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={"projection_ladder": projections},
        limitations=(
            "No Jev model was evaluated in this scaffold-only A003 run.",
            "Real labeled biological cases are required to estimate semantic sufficiency.",
        ),
    )
    AppendOnlyJsonlStore(settings.store_dir / "events.jsonl").append(
        "architecture_experiment_result", asdict(result)
    )
    return str(asdict(result))
