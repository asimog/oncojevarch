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

S003 = replace(
    S001,
    experiment_id="S003",
    question=(
        "Does the S002 co-availability measurement reproduce on an independent compatible source?"
    ),
    hypothesis=(
        "The co-availability rate on cBioPortal Firehose Legacy TCGA studies agrees with the GDC "
        "TCGA rate inside the declared tolerance."
    ),
    required_data=(
        "cBioPortal public studies endpoint (DETAIL projection)",
        "S002 recorded GDC reference value",
    ),
    required_capabilities=(
        "cBioPortal study profile source",
        "compatibility contract",
        "ABC arm runtimes",
        "admission gate",
    ),
    comparison=("independent cBioPortal rate vs S002 GDC rate under a frozen tolerance",),
    metrics=("co-availability rate", "compatible study count", "tolerance agreement"),
    success_criteria=(
        "the compatibility contract is frozen before fetching",
        "the independent rate is admitted as evidence",
        "agreement is recorded against the declared tolerance",
    ),
    failure_criteria=(
        "the independent fetch fails",
        "the measurement is refused at admission",
        "agreement cannot be evaluated",
    ),
    decision_consequences=(
        "support, narrow, or reject transportability of the S002 measurement on an independent "
        "source",
    ),
    inputs={
        "compatibility_contract": "s003-gdc-raw-vs-gdan-analysis-layer",
        "primary_source": "GDC projects endpoint (raw experimental strategies)",
        "independent_source": "GDAN/GDAC analysis layer published through GDC data categories",
    },
    evaluation_level=EvaluationLevel.INDEPENDENT_REAL,
)

S004 = replace(
    S001,
    experiment_id="S004",
    question=(
        "Does a T1 prediction about TCGA co-availability hold on genuinely later GDC information?"
    ),
    hypothesis=(
        "The co-availability rate and the co-availability of newly listed projects remain as "
        "predicted at the T1 freeze."
    ),
    required_data=("T1 frozen GDC snapshot", "T2 GDC snapshot at or after the due time"),
    required_capabilities=("GDC metadata source", "T1 shadow freeze", "T2 checker"),
    comparison=("T1 prediction vs T2 snapshot evaluation",),
    metrics=("rate equality", "new projects", "new-project co-availability", "outcome"),
    success_criteria=(
        "T1 state is frozen with prediction, cutoffs, and criteria before T2 exists",
        "T2 is evaluated only after the due time",
        "the outcome is recorded as supported or falsified",
    ),
    failure_criteria=(
        "T1 is refrozen after T2 sightings",
        "T2 is evaluated before the due time and reported as temporal",
        "the prediction is edited after results",
    ),
    decision_consequences=("retain or revise the temporal stability claim for assay structure",),
    inputs={
        "t1_cutoff": "wall-clock date at the T1 freeze",
        "t2_cutoff": "due time = T1 plus the frozen minimum age",
        "t2_min_age_hours": 24,
    },
    evaluation_level=EvaluationLevel.TEMPORAL_PROSPECTIVE,
)

SCIENTIFIC_EXPERIMENTS: tuple[ExperimentSpec, ...] = (S001, S002, S003, S004)

EXPERIMENTS_BY_ID = {experiment.experiment_id: experiment for experiment in SCIENTIFIC_EXPERIMENTS}


def get_scientific_experiment(experiment_id: str) -> ExperimentSpec:
    return EXPERIMENTS_BY_ID[experiment_id]
