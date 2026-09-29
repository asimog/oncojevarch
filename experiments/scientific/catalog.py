from __future__ import annotations

from dataclasses import replace

from evaluation.models import EvaluationLevel
from oncolab.experiments import ExperimentClass, ExperimentSpec

S001 = ExperimentSpec(
    experiment_id="S001",
    experiment_class=ExperimentClass.SCIENTIFIC,
    question=(
        "Among GDC TCGA projects, is co-availability of RNA-Seq and WXS file classes "
        "associated with primary site beyond an independence null?"
    ),
    hypothesis=(
        "Site concentration of projects with both RNA-Seq and WXS files differs from a "
        "hash-seeded independence null that preserves availability marginals."
    ),
    required_data=(
        "GDC public project metadata for program TCGA",
        "experimental-strategy file counts per project",
    ),
    required_capabilities=(
        "gdc public metadata source",
        "seeded permutation association method",
        "admission gate",
        "investigation ledger",
    ),
    comparison=(
        "observed site concentration of co-available projects vs independent-flags "
        "permutation null",
    ),
    metrics=(
        "max site share of co-available projects",
        "permutation p-value",
        "project coverage",
        "missingness",
    ),
    success_criteria=(
        "at least 40 TCGA projects with file-class data are retrieved",
        "the permutation null is computed with the frozen seed and iteration count",
        "the measurement passes evidence admission and is recorded",
    ),
    failure_criteria=(
        "fewer than 40 projects are retrieved",
        "the null cannot be computed",
        "the measurement is refused at admission",
    ),
    decision_consequences=(
        "record assay co-availability structure as exploratory metadata evidence; any "
        "follow-up policy judgment opens a DecisionGap instead of assuming semantics",
    ),
    budget={"max_wall_minutes": 10, "max_requests": 4, "max_permutations": 1000},
    evaluation_level=EvaluationLevel.RETROSPECTIVE_REAL,
    executable=True,
)

S002 = replace(
    S001,
    experiment_id="S002",
    success_criteria=(
        "at least 30 TCGA projects with file-class data are retrieved",
        "the permutation null is computed with the frozen seed and iteration count",
        "the measurement passes evidence admission and is recorded",
    ),
    failure_criteria=(
        "fewer than 30 projects are retrieved",
        "the null cannot be computed",
        "the measurement is refused at admission",
    ),
)

SCIENTIFIC_EXPERIMENTS: tuple[ExperimentSpec, ...] = (S001, S002)

EXPERIMENTS_BY_ID = {experiment.experiment_id: experiment for experiment in SCIENTIFIC_EXPERIMENTS}


def get_scientific_experiment(experiment_id: str) -> ExperimentSpec:
    return EXPERIMENTS_BY_ID[experiment_id]
