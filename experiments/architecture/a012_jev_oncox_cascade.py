from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from time import perf_counter
from typing import Any

from evaluation.cascade import (
    CascadeCase,
    ReasoningAssessment,
    ReasoningConsideration,
    assess_reasoning,
    assess_without_reasoning,
    evaluate_cascade,
    triage_escalations,
    validate_case_set,
)
from evidence.projections import SemanticProjection, freeze_projection
from execution.gdc import GdcClient, GdcResponse
from experiments.catalog import get_experiment
from jev.contracts import JevCapability, JevPrimitive, JevQuestion
from jev.ports import JevClient
from jev.typesafe_adapter import TypeSafeJevClient
from oncodex.config import Settings
from oncodex.model_provider import build_agent_model
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from oncox.agents_adapter import ONCOX_INSTRUCTIONS, AgentsOncoXReasoner
from oncox.ports import ReasoningRequest, ScientificReasoner
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A012")
TRIAGE_THRESHOLD = 0.5
MAX_QUALITY_LOSS = 0.05
MIN_ONCOX_CALL_REDUCTION = 0.30
LIVE_REPETITIONS = 2
ONCOX_MAX_ATTEMPTS = 2
# None keeps the provider default: this OpenRouter route spends reasoning tokens inside the
# completion budget, so a small explicit cap can consume the allowance before any content exists.
ONCOX_MAX_TOKENS: int | None = None
# The pinned OpenRouter route defaults to high reasoning effort; the frozen protocol pins low
# effort for both arms to bound tokens and wall time.
ONCOX_REASONING_EFFORT = "low"
# Ten cases are locked in the rubric; the live slice keeps the smallest balanced subset that can
# still measure triage behaviour (two closed, two open) inside a short live budget.
LIVE_CASE_IDS = ("c01", "c05", "c06", "c09")
PROJECT_IDS = ("TCGA-LUAD", "TCGA-LUSC", "TCGA-KIRC", "TCGA-KIRP", "TCGA-KICH")
CAPABILITY_ID = "a012-oncox-escalation-triage"
PROJECTION_ID = "a012-oncox-triage"
REASONING_QUESTION = (
    "Identify the material alternative explanations, unrecorded confounders, and discriminating "
    "tests that the recorded structured evidence leaves open for this claim."
)

# Captured read-only GDC aggregate metadata (Data Release 46.0, API tag 8.5.0, commit
# 8f7c2a51ab0084b216ad1b62a3fae8b945439c53, 9,883 byte response, 2026-09-29). Only project-level
# counts are stored: no case, sample, aliquot, file, or molecular records.
FROZEN_PROJECT_METADATA: dict[str, dict[str, Any]] = {
    "TCGA-LUAD": {
        "primary_site": ["Bronchus and lung"],
        "disease_type": [
            "Acinar Cell Neoplasms",
            "Adenomas and Adenocarcinomas",
            "Cystic, Mucinous and Serous Neoplasms",
            "Ductal and Lobular Neoplasms",
        ],
        "case_count": 585,
        "file_count": 36740,
        "data_categories": {
            "Biospecimen": 2731,
            "Clinical": 1146,
            "Copy Number Variation": 6926,
            "DNA Methylation": 2130,
            "Proteome Profiling": 365,
            "Sequencing Reads": 5053,
            "Simple Nucleotide Variation": 12207,
            "Somatic Structural Variation": 1150,
            "Structural Variation": 2696,
            "Transcriptome Profiling": 2336,
        },
        "experimental_strategies": {
            "ATAC-Seq": 22,
            "Diagnostic Slide": 541,
            "Genotyping Array": 7237,
            "Methylation Array": 2130,
            "RNA-Seq": 5409,
            "Reverse Phase Protein Array": 365,
            "Tissue Slide": 1067,
            "WGS": 5903,
            "WXS": 10096,
            "miRNA-Seq": 1701,
        },
    },
    "TCGA-LUSC": {
        "primary_site": ["Bronchus and lung"],
        "disease_type": ["Adenomas and Adenocarcinomas", "Squamous Cell Neoplasms"],
        "case_count": 504,
        "file_count": 32404,
        "data_categories": {
            "Biospecimen": 2630,
            "Clinical": 1081,
            "Copy Number Variation": 6459,
            "DNA Methylation": 1719,
            "Proteome Profiling": 328,
            "Sequencing Reads": 4107,
            "Simple Nucleotide Variation": 10339,
            "Somatic Structural Variation": 958,
            "Structural Variation": 2458,
            "Transcriptome Profiling": 2325,
        },
        "experimental_strategies": {
            "ATAC-Seq": 16,
            "Diagnostic Slide": 512,
            "Expression Array": 135,
            "Genotyping Array": 6798,
            "Methylation Array": 1719,
            "RNA-Seq": 5058,
            "Reverse Phase Protein Array": 328,
            "Tissue Slide": 1100,
            "WGS": 4091,
            "WXS": 8949,
            "miRNA-Seq": 1599,
        },
    },
    "TCGA-KIRC": {
        "primary_site": ["Kidney"],
        "disease_type": ["Adenomas and Adenocarcinomas"],
        "case_count": 537,
        "file_count": 35031,
        "data_categories": {
            "Biospecimen": 3257,
            "Clinical": 1165,
            "Copy Number Variation": 7048,
            "DNA Methylation": 2709,
            "Proteome Profiling": 478,
            "Sequencing Reads": 4440,
            "Simple Nucleotide Variation": 9316,
            "Somatic Structural Variation": 1326,
            "Structural Variation": 2832,
            "Transcriptome Profiling": 2460,
        },
        "experimental_strategies": {
            "ATAC-Seq": 16,
            "Diagnostic Slide": 519,
            "Genotyping Array": 7243,
            "Methylation Array": 2709,
            "RNA-Seq": 5526,
            "Reverse Phase Protein Array": 478,
            "Tissue Slide": 1654,
            "WGS": 6005,
            "WXS": 6784,
            "miRNA-Seq": 1848,
        },
    },
    "TCGA-KIRP": {
        "primary_site": ["Kidney"],
        "disease_type": ["Adenomas and Adenocarcinomas"],
        "case_count": 291,
        "file_count": 18749,
        "data_categories": {
            "Biospecimen": 1365,
            "Clinical": 647,
            "Copy Number Variation": 3812,
            "DNA Methylation": 1026,
            "Proteome Profiling": 216,
            "Sequencing Reads": 2439,
            "Simple Nucleotide Variation": 5790,
            "Somatic Structural Variation": 698,
            "Structural Variation": 1458,
            "Transcriptome Profiling": 1298,
        },
        "experimental_strategies": {
            "ATAC-Seq": 34,
            "Diagnostic Slide": 299,
            "Genotyping Array": 3904,
            "Methylation Array": 1026,
            "RNA-Seq": 2907,
            "Reverse Phase Protein Array": 216,
            "Tissue Slide": 474,
            "WGS": 2963,
            "WXS": 4709,
            "miRNA-Seq": 978,
        },
    },
    "TCGA-KICH": {
        "primary_site": ["Kidney"],
        "disease_type": ["Adenomas and Adenocarcinomas"],
        "case_count": 113,
        "file_count": 6076,
        "data_categories": {
            "Biospecimen": 562,
            "Clinical": 248,
            "Copy Number Variation": 1130,
            "DNA Methylation": 198,
            "Proteome Profiling": 63,
            "Sequencing Reads": 766,
            "Simple Nucleotide Variation": 1789,
            "Somatic Structural Variation": 499,
            "Structural Variation": 457,
            "Transcriptome Profiling": 364,
        },
        "experimental_strategies": {
            "Diagnostic Slide": 121,
            "Genotyping Array": 856,
            "Methylation Array": 198,
            "RNA-Seq": 819,
            "Reverse Phase Protein Array": 63,
            "Tissue Slide": 205,
            "WGS": 2001,
            "WXS": 1056,
            "miRNA-Seq": 273,
        },
    },
}


def _build_view(project_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
    case_count = int(metadata["case_count"])
    file_count = int(metadata["file_count"])
    if case_count <= 0:
        raise ValueError(f"{project_id} has no recorded cases")
    return {
        "project_id": project_id,
        "primary_site": list(metadata["primary_site"]),
        "disease_type": list(metadata["disease_type"]),
        "case_count": case_count,
        "file_count": file_count,
        "files_per_case": round(file_count / case_count, 2),
        "data_categories": dict(metadata["data_categories"]),
        "experimental_strategies": dict(metadata["experimental_strategies"]),
    }


def _frozen_views() -> dict[str, dict[str, Any]]:
    return {pid: _build_view(pid, FROZEN_PROJECT_METADATA[pid]) for pid in PROJECT_IDS}


def _es(view: dict[str, Any], name: str) -> int:
    return int(view["experimental_strategies"].get(name, 0))


def _dc(view: dict[str, Any], name: str) -> int:
    return int(view["data_categories"].get(name, 0))


def _state(
    case_id: str,
    claim: str,
    project_ids: tuple[str, ...],
    observed: dict[str, Any],
    recorded_checks: tuple[str, ...],
    missing: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "investigation_id": case_id,
        "claim": claim,
        "question": REASONING_QUESTION,
        "evidence_ids": [f"gdc-project:{project_id}" for project_id in project_ids],
        "observed": observed,
        "recorded_checks": list(recorded_checks),
        "missing": list(missing),
    }


def _build_cases(views: dict[str, dict[str, Any]]) -> tuple[CascadeCase, ...]:
    luad = views["TCGA-LUAD"]
    lusc = views["TCGA-LUSC"]
    kirc = views["TCGA-KIRC"]
    kirp = views["TCGA-KIRP"]
    kich = views["TCGA-KICH"]

    c01_claim = (
        f"TCGA-KIRC recorded {kirc['case_count']} cases and TCGA-KIRP {kirp['case_count']} "
        "cases, so kidney clear cell carcinoma is about "
        f"{round(kirc['case_count'] / kirp['case_count'], 2)} times as common as papillary "
        "renal carcinoma."
    )
    c01 = CascadeCase(
        case_id="c01",
        claim=c01_claim,
        question=REASONING_QUESTION,
        state=_state(
            "c01",
            c01_claim,
            ("TCGA-KIRC", "TCGA-KIRP"),
            {
                "TCGA-KIRC": {
                    "case_count": kirc["case_count"],
                    "primary_site": kirc["primary_site"],
                },
                "TCGA-KIRP": {
                    "case_count": kirp["case_count"],
                    "primary_site": kirp["primary_site"],
                },
            },
            (
                "TCGA project case counts are operational cohort sizes.",
                "Both projects carry the Adenomas and Adenocarcinomas label for kidney tumors.",
                "No incidence or population denominator is present in this state.",
            ),
            ("population registry incidence rates", "treatment response outcomes"),
        ),
        considerations=(
            ReasoningConsideration(
                "c01a",
                "project case counts are operational rather than population incidence",
                (
                    "not population incidence",
                    "operational cohort",
                    "not a population",
                    "non-population",
                    "not population-based",
                ),
                True,
            ),
            ReasoningConsideration(
                "c01b",
                "the shared disease type label means the counts are not subtype-specific incidence",
                (
                    "disease_type",
                    "disease type label",
                    "shared disease type",
                    "not histology-specific",
                    "not subtype-specific",
                ),
                True,
            ),
            ReasoningConsideration(
                "c01c",
                "no population denominator is available in the state",
                (
                    "no population registry",
                    "population registry denominator",
                    "denominator",
                    "registry incidence",
                    "incidence rate",
                ),
                True,
            ),
        ),
    )

    c02_claim = (
        f"TCGA-LUSC recorded {lusc['files_per_case']} files per case against "
        f"{luad['files_per_case']} in TCGA-LUAD, so lung squamous cell carcinoma cases receive "
        "deeper molecular characterization."
    )
    c02 = CascadeCase(
        case_id="c02",
        claim=c02_claim,
        question=REASONING_QUESTION,
        state=_state(
            "c02",
            c02_claim,
            ("TCGA-LUSC", "TCGA-LUAD"),
            {
                "TCGA-LUSC": {
                    "case_count": lusc["case_count"],
                    "file_count": lusc["file_count"],
                    "files_per_case": lusc["files_per_case"],
                },
                "TCGA-LUAD": {
                    "case_count": luad["case_count"],
                    "file_count": luad["file_count"],
                    "files_per_case": luad["files_per_case"],
                },
                "TCGA-LUSC.rna_seq_files": _es(lusc, "RNA-Seq"),
                "TCGA-LUAD.rna_seq_files": _es(luad, "RNA-Seq"),
            },
            (
                "File inventories mix Biospecimen and Clinical records with assay records.",
                "RNA-Seq inventories are recorded for both projects.",
                "Several files can belong to one case.",
            ),
            ("treatment response outcomes", "specimen quality metadata"),
        ),
        considerations=(
            ReasoningConsideration(
                "c02a",
                "file counts include biospecimen and clinical records, so they are not molecular "
                "depth",
                (
                    "biospecimen",
                    "clinical records",
                    "not a measure of molecular depth",
                    "not molecular depth",
                ),
                True,
            ),
            ReasoningConsideration(
                "c02b",
                "RNA-Seq file inventories are comparable in both projects",
                (
                    "comparable rna-seq",
                    "rna-seq file counts are comparable",
                    "similar rna-seq",
                    "rna-seq inventories are comparable",
                    "comparable transcriptome",
                ),
                True,
            ),
            ReasoningConsideration(
                "c02c",
                "file identity is not assay identity because a case contributes several files",
                (
                    "multiple files",
                    "not assay identity",
                    "file is not an assay",
                    "more than one file",
                ),
                True,
            ),
        ),
    )

    c03_claim = (
        f"TCGA-KICH contains {kich['file_count']} files against {kirc['file_count']} in "
        f"TCGA-KIRC, so chromophobe cases have far less molecular data per case."
    )
    c03 = CascadeCase(
        case_id="c03",
        claim=c03_claim,
        question=REASONING_QUESTION,
        state=_state(
            "c03",
            c03_claim,
            ("TCGA-KICH", "TCGA-KIRC"),
            {
                "TCGA-KICH": {
                    "case_count": kich["case_count"],
                    "file_count": kich["file_count"],
                    "files_per_case": kich["files_per_case"],
                    "data_category_count": len(kich["data_categories"]),
                },
                "TCGA-KIRC": {
                    "case_count": kirc["case_count"],
                    "file_count": kirc["file_count"],
                    "files_per_case": kirc["files_per_case"],
                    "data_category_count": len(kirc["data_categories"]),
                },
            },
            (
                "The two projects differ in cohort size.",
                "Files per case are recorded for both projects.",
                "The same data categories are present in both projects.",
            ),
            ("treatment response outcomes", "population registry incidence rates"),
        ),
        considerations=(
            ReasoningConsideration(
                "c03a",
                "totals are not per-case measures because cohort sizes differ",
                (
                    "cohort size",
                    "different number of cases",
                    "totals are not",
                    "113 cases",
                    "537 cases",
                ),
                True,
            ),
            ReasoningConsideration(
                "c03b",
                "per-case file counts are recorded for both projects",
                (
                    "files per case",
                    "per-case file count",
                    "53.77",
                    "65.23",
                ),
                True,
            ),
            ReasoningConsideration(
                "c03c",
                "both projects contain the same data categories",
                (
                    "same data categories",
                    "ten data categories",
                    "10 data categories",
                    "comparable data categories",
                ),
                True,
            ),
        ),
    )

    c04_claim = (
        f"TCGA-LUSC contains {_es(lusc, 'Expression Array')} Expression Array files that "
        "TCGA-LUAD lacks, so lung squamous tumors were characterized on a different expression "
        "platform."
    )
    c04 = CascadeCase(
        case_id="c04",
        claim=c04_claim,
        question=REASONING_QUESTION,
        state=_state(
            "c04",
            c04_claim,
            ("TCGA-LUSC", "TCGA-LUAD"),
            {
                "TCGA-LUSC.expression_array_files": _es(lusc, "Expression Array"),
                "TCGA-LUSC.rna_seq_files": _es(lusc, "RNA-Seq"),
                "TCGA-LUAD.rna_seq_files": _es(luad, "RNA-Seq"),
                "TCGA-LUSC.genotyping_array_files": _es(lusc, "Genotyping Array"),
                "TCGA-LUAD.genotyping_array_files": _es(luad, "Genotyping Array"),
            },
            (
                "Transcriptome profiling in both projects is recorded under RNA-Seq.",
                "The Expression Array entry covers a small number of files in one project.",
                "Strategy entries are file inventory records.",
            ),
            ("treatment response outcomes", "specimen quality metadata"),
        ),
        considerations=(
            ReasoningConsideration(
                "c04a",
                "transcriptome profiling is dominated by RNA-Seq in both projects",
                (
                    "dominated by rna-seq",
                    "rna-seq",
                    "transcriptome profiling",
                ),
                True,
            ),
            ReasoningConsideration(
                "c04b",
                "the Expression Array entry is a small legacy inventory subset",
                ("135", "legacy", "expression array"),
                True,
            ),
            ReasoningConsideration(
                "c04c",
                "strategy labels are file-level inventory entries, not per-case assay assignments",
                ("file-level", "inventory records", "not per-case", "file inventory"),
                True,
            ),
        ),
    )

    c05_claim = (
        f"TCGA-KICH recorded {kich['file_count']} files for {kich['case_count']} cases, so each "
        f"chromophobe case carries about {kich['files_per_case']} molecular assays."
    )
    c05 = CascadeCase(
        case_id="c05",
        claim=c05_claim,
        question=REASONING_QUESTION,
        state=_state(
            "c05",
            c05_claim,
            ("TCGA-KICH",),
            {
                "TCGA-KICH.case_count": kich["case_count"],
                "TCGA-KICH.file_count": kich["file_count"],
                "TCGA-KICH.files_per_case": kich["files_per_case"],
                "TCGA-KICH.biospecimen_records": _dc(kich, "Biospecimen"),
                "TCGA-KICH.clinical_records": _dc(kich, "Clinical"),
            },
            (
                "File totals and per-case totals are recorded for this project.",
                "The inventory includes Biospecimen and Clinical records.",
                "A case can be represented by more than one record.",
            ),
            ("specimen counts grouped by collection source", "treatment response outcomes"),
        ),
        considerations=(
            ReasoningConsideration(
                "c05a",
                "biospecimen and clinical records are not molecular assays",
                ("biospecimen", "clinical", "not assays", "non-assay"),
                True,
            ),
            ReasoningConsideration(
                "c05b",
                "a case contributes several files, so files are not assays",
                ("multiple files", "more than one file", "several files", "per case"),
                True,
            ),
            ReasoningConsideration(
                "c05c",
                "the state records file totals rather than distinct assay counts",
                ("file totals", "assays per case", "assay-per-case", "distinct assay"),
                True,
            ),
        ),
    )

    c06_claim = (
        f"TCGA-KIRC records {kirc['files_per_case']} files per case and TCGA-KIRP "
        f"{kirp['files_per_case']}, so both cohorts have a comparable molecular data volume per "
        "case."
    )
    c06 = CascadeCase(
        case_id="c06",
        claim=c06_claim,
        question=REASONING_QUESTION,
        state=_state(
            "c06",
            c06_claim,
            ("TCGA-KIRC", "TCGA-KIRP"),
            {
                "TCGA-KIRC": {
                    "case_count": kirc["case_count"],
                    "file_count": kirc["file_count"],
                    "files_per_case": kirc["files_per_case"],
                },
                "TCGA-KIRP": {
                    "case_count": kirp["case_count"],
                    "file_count": kirp["file_count"],
                    "files_per_case": kirp["files_per_case"],
                },
                "TCGA-KIRC.rna_seq_files": _es(kirc, "RNA-Seq"),
                "TCGA-KIRP.rna_seq_files": _es(kirp, "RNA-Seq"),
            },
            (
                "File inventories aggregate several data categories for both projects.",
                "Per-case totals are recorded for both projects.",
                "Both projects record RNA-Seq, WXS, and methylation inventories.",
            ),
            (
                "specimen counts grouped by collection source",
                "per-case aliquot counts",
                "treatment response outcomes",
            ),
        ),
        considerations=(
            ReasoningConsideration(
                "c06a",
                "file totals aggregate biospecimen, clinical, and molecular records",
                (
                    "aggregate",
                    "data categories",
                    "biospecimen and clinical",
                    "mixes",
                ),
                True,
            ),
            ReasoningConsideration(
                "c06b",
                "the recorded per-case totals are close in both projects",
                ("comparable", "similar per-case", "65.23", "64.43"),
                True,
            ),
            ReasoningConsideration(
                "c06c",
                "the totals can hide different assay mixes between the cohorts",
                (
                    "assay mix",
                    "different mix",
                    "composition of assays",
                    "mixture of assays",
                    "different assay composition",
                ),
                False,
            ),
            ReasoningConsideration(
                "c06d",
                "sample-type composition such as normal or metastatic tissue can differ",
                ("normal tissue", "metastatic", "sample type", "tumor-adjacent", "adjacent normal"),
                False,
            ),
            ReasoningConsideration(
                "c06e",
                "per-case sequencing depth is unmeasured",
                ("sequencing depth", "read depth", "coverage depth", "depth per case"),
                False,
            ),
        ),
    )

    c07_claim = (
        "TCGA-LUAD and TCGA-LUSC record the same assay inventory categories, so their expression "
        "data can be compared directly across projects."
    )
    c07 = CascadeCase(
        case_id="c07",
        claim=c07_claim,
        question=REASONING_QUESTION,
        state=_state(
            "c07",
            c07_claim,
            ("TCGA-LUAD", "TCGA-LUSC"),
            {
                "TCGA-LUAD": {
                    "rna_seq_files": _es(luad, "RNA-Seq"),
                    "wxs_files": _es(luad, "WXS"),
                    "wgs_files": _es(luad, "WGS"),
                    "methylation_array_files": _es(luad, "Methylation Array"),
                },
                "TCGA-LUSC": {
                    "rna_seq_files": _es(lusc, "RNA-Seq"),
                    "wxs_files": _es(lusc, "WXS"),
                    "wgs_files": _es(lusc, "WGS"),
                    "methylation_array_files": _es(lusc, "Methylation Array"),
                    "expression_array_files": _es(lusc, "Expression Array"),
                },
            },
            (
                "Both projects record RNA-Seq, WXS, WGS, and methylation inventories.",
                "The recorded strategy inventories are otherwise similar.",
            ),
            (
                "per-case cellularity estimates",
                "sequencing depth per case",
                "treatment response outcomes",
            ),
        ),
        considerations=(
            ReasoningConsideration(
                "c07a",
                "both projects record the same broad assay categories",
                ("rna-seq", "wxs", "wgs", "methylation"),
                True,
            ),
            ReasoningConsideration(
                "c07b",
                "LUSC includes an additional small expression array inventory",
                ("expression array", "135", "legacy"),
                True,
            ),
            ReasoningConsideration(
                "c07c",
                "unrecorded batch, center, or processing differences can affect comparability",
                (
                    "batch",
                    "processing pipeline",
                    "sequencing center",
                    "different centers",
                    "protocol differences",
                    "pipeline differences",
                ),
                False,
            ),
            ReasoningConsideration(
                "c07d",
                "differences in tumor content or purity can bias expression comparisons",
                ("tumor content", "purity", "admixture"),
                False,
            ),
            ReasoningConsideration(
                "c07e",
                "specimen fixation or preservation differences are plausible",
                ("ffpe", "fresh frozen", "formalin", "preservation method", "fixation"),
                False,
            ),
        ),
    )

    c08_claim = (
        "TCGA-KICH records the smallest file inventory of the kidney projects, so chromophobe "
        "renal cell carcinoma is under-studied and should be the priority target for new "
        "molecular profiling."
    )
    c08 = CascadeCase(
        case_id="c08",
        claim=c08_claim,
        question=REASONING_QUESTION,
        state=_state(
            "c08",
            c08_claim,
            ("TCGA-KICH", "TCGA-KIRC", "TCGA-KIRP"),
            {
                "TCGA-KICH": {
                    "case_count": kich["case_count"],
                    "file_count": kich["file_count"],
                },
                "TCGA-KIRC": {
                    "case_count": kirc["case_count"],
                    "file_count": kirc["file_count"],
                },
                "TCGA-KIRP": {
                    "case_count": kirp["case_count"],
                    "file_count": kirp["file_count"],
                },
                "TCGA-KICH.strategy_count": len(kich["experimental_strategies"]),
            },
            (
                "Inventory totals and cohort sizes are recorded for the three kidney projects.",
                "The KICH inventory covers nine experimental strategies.",
                "The recorded state contains no study-attention metadata.",
            ),
            ("per-case sample inventories", "treatment response outcomes"),
        ),
        considerations=(
            ReasoningConsideration(
                "c08a",
                "the state records inventory totals and cohort sizes for the three projects",
                ("file totals", "inventory", "113", "cohort sizes"),
                True,
            ),
            ReasoningConsideration(
                "c08b",
                "the smaller totals track the smaller KICH cohort",
                ("smaller cohort", "113 cases", "fewer cases"),
                True,
            ),
            ReasoningConsideration(
                "c08c",
                "an operational inventory total does not measure research attention",
                (
                    "does not measure research",
                    "not a measure of research",
                    "inventory is not",
                    "not evidence of research",
                    "not a measure of effort",
                ),
                False,
            ),
            ReasoningConsideration(
                "c08d",
                "external cohort inventories or publication records would be required",
                (
                    "publication count",
                    "literature",
                    "cptac",
                    "icgc",
                    "external cohort",
                    "other cohorts",
                ),
                False,
            ),
            ReasoningConsideration(
                "c08e",
                "the claim treats data availability as scientific priority",
                ("conflat", "confuses", "treats availability", "equates"),
                False,
            ),
        ),
    )

    c09_claim = (
        f"TCGA-LUAD records {_es(luad, 'WXS')} WXS and {_es(luad, 'WGS')} WGS files and "
        f"TCGA-LUSC {_es(lusc, 'WXS')} WXS and {_es(lusc, 'WGS')} WGS files, so their somatic "
        "mutation burdens can be compared directly."
    )
    c09 = CascadeCase(
        case_id="c09",
        claim=c09_claim,
        question=REASONING_QUESTION,
        state=_state(
            "c09",
            c09_claim,
            ("TCGA-LUAD", "TCGA-LUSC"),
            {
                "TCGA-LUAD.wxs_files": _es(luad, "WXS"),
                "TCGA-LUAD.wgs_files": _es(luad, "WGS"),
                "TCGA-LUSC.wxs_files": _es(lusc, "WXS"),
                "TCGA-LUSC.wgs_files": _es(lusc, "WGS"),
            },
            (
                "Both projects record WXS and WGS file inventories.",
                "File totals describe data available in the inventory.",
                "The recorded state contains no derived mutation-call results.",
            ),
            ("per-case coverage summaries", "treatment response outcomes"),
        ),
        considerations=(
            ReasoningConsideration(
                "c09a",
                "both projects record WXS and WGS inventories",
                ("wxs", "wgs"),
                True,
            ),
            ReasoningConsideration(
                "c09b",
                "file counts are inventory records rather than analyzed mutation calls",
                ("inventory", "not analyzed", "not calls", "file counts are not"),
                True,
            ),
            ReasoningConsideration(
                "c09c",
                "comparable mutation burdens require the same capture kits and calling pipelines",
                ("capture kit", "calling pipeline", "variant caller", "pipeline", "callset"),
                False,
            ),
            ReasoningConsideration(
                "c09d",
                "sequencing depth and coverage thresholds are not recorded",
                ("sequencing depth", "coverage threshold", "read depth", "depth"),
                False,
            ),
            ReasoningConsideration(
                "c09e",
                "somatic callability depends on tumor purity and ploidy",
                ("ploidy", "purity", "tumor content"),
                False,
            ),
        ),
    )

    c10_claim = (
        f"TCGA-KICH records no ATAC-Seq files while TCGA-KIRC records {_es(kirc, 'ATAC-Seq')} and "
        f"TCGA-KIRP {_es(kirp, 'ATAC-Seq')}, so chromatin accessibility data are unavailable for "
        "chromophobe tumors."
    )
    c10 = CascadeCase(
        case_id="c10",
        claim=c10_claim,
        question=REASONING_QUESTION,
        state=_state(
            "c10",
            c10_claim,
            ("TCGA-KICH", "TCGA-KIRC", "TCGA-KIRP"),
            {
                "TCGA-KICH.atac_seq_files": _es(kich, "ATAC-Seq"),
                "TCGA-KIRC.atac_seq_files": _es(kirc, "ATAC-Seq"),
                "TCGA-KIRP.atac_seq_files": _es(kirp, "ATAC-Seq"),
                "TCGA-KICH.strategy_count": len(kich["experimental_strategies"]),
            },
            (
                "The KICH strategy inventory contains no ATAC-Seq entry in this release.",
                "The KIRC and KIRP inventories contain a few ATAC-Seq entries.",
                "The recorded state aggregates all three projects into one GDC release.",
            ),
            ("per-case sample inventories", "treatment response outcomes"),
        ),
        considerations=(
            ReasoningConsideration(
                "c10a",
                "the KICH inventory records no ATAC-Seq entries in this release",
                ("no atac", "contains no atac", "absence of atac", "zero atac"),
                True,
            ),
            ReasoningConsideration(
                "c10b",
                "KIRC and KIRP record only a few ATAC-Seq files",
                ("16", "34", "few atac", "small number of atac"),
                True,
            ),
            ReasoningConsideration(
                "c10c",
                "absence from an operational inventory is not biological unavailability",
                (
                    "not evidence of unavailability",
                    "does not establish unavailability",
                    "inventory absence",
                    "not biological",
                    "absence of records is not",
                ),
                False,
            ),
            ReasoningConsideration(
                "c10d",
                "the small totals suggest a supplementary study rather than a subtype property",
                ("supplementary", "pilot", "small subset", "ancillary"),
                False,
            ),
            ReasoningConsideration(
                "c10e",
                "assessing availability requires per-case records and submission dates",
                (
                    "submission date",
                    "release date",
                    "per-case record",
                    "point in time",
                    "inventory timestamp",
                ),
                False,
            ),
        ),
    )

    return (c01, c02, c03, c04, c05, c06, c07, c08, c09, c10)


def _select_cases(cases: tuple[CascadeCase, ...]) -> tuple[CascadeCase, ...]:
    selected = tuple(case for case in cases if case.case_id in LIVE_CASE_IDS)
    if tuple(case.case_id for case in selected) != LIVE_CASE_IDS:
        raise ValueError("live slice does not match the locked case set")
    return selected


def _case_set_fingerprint(cases: tuple[CascadeCase, ...]) -> str:
    canonical = json.dumps(
        [
            {
                "case_id": case.case_id,
                "claim": case.claim,
                "question": case.question,
                "state": case.state,
                "considerations": [asdict(item) for item in case.considerations],
            }
            for case in cases
        ],
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return sha256(canonical.encode("utf-8")).hexdigest()


def _triage_instructions(case_id: str) -> str:
    return (
        f"Using only `cases.{case_id}`, judge whether open-ended deep scientific reasoning about "
        "the candidate claim would add materially new scientific information beyond the recorded "
        "structured evidence. Answer true only if the recorded checks leave a materially open "
        "question for this claim, such as an unrecorded confounder, an undiscriminated alternative "
        "explanation, or a decisive unmeasured quantity that could change how the claim is "
        "evaluated. Answer false if the recorded checks already resolve the material question of "
        "the claim, even when the state lists missing items. A listed missing item that cannot "
        "change the evaluation of this claim is not material."
    )


def _projection(cases: tuple[CascadeCase, ...]) -> SemanticProjection:
    return freeze_projection(
        projection_id=PROJECTION_ID,
        version="1",
        question_id="oncox-escalation-triage",
        source_evidence_ids=tuple(
            sorted(
                {
                    evidence_id
                    for case in cases
                    for evidence_id in case.state.get("evidence_ids", [])
                }
            )
        ),
        payload={"cases": {case.case_id: case.state for case in cases}},
    )


def _capability(cases: tuple[CascadeCase, ...]) -> JevCapability:
    return JevCapability(
        capability_id=CAPABILITY_ID,
        version="0.1.0",
        domain_owner="evaluation",
        semantic_purpose=(
            "Decide whether open-ended deep reasoning would add material information beyond a "
            "frozen structured state."
        ),
        projection_id=PROJECTION_ID,
        projection_version="1",
        questions=tuple(
            JevQuestion(
                question_id=f"escalate__{case.case_id}",
                primitive=JevPrimitive.NOUL,
                instructions=_triage_instructions(case.case_id),
                criteria={
                    "true": "deep reasoning would likely add material information not recorded",
                    "false": "the recorded checks already resolve the material question",
                },
            )
            for case in cases
        ),
    )


@dataclass(frozen=True, slots=True)
class ArmRecord:
    arm_id: str
    calls: int
    input_tokens: int
    output_tokens: int
    wall_ms: float
    mean_latency_ms: float


async def _reason_case(
    reasoner: ScientificReasoner, case: CascadeCase
) -> tuple[ReasoningAssessment, dict[str, Any]]:
    request = ReasoningRequest(
        investigation_id=case.case_id,
        evidence_ids=tuple(case.state.get("evidence_ids", [])),
        question=case.question,
        structured_state=case.state,
    )
    result = await reasoner.reason(request)
    assessment = assess_reasoning(case, result.output)
    return assessment, {
        "case_id": case.case_id,
        "output": asdict(result.output),
        "model_id": result.model_id,
        "usage": result.usage,
        "latency_ms": result.latency_ms,
        "attempts": result.attempts,
        "attempt_errors": list(result.errors),
        "matched_considerations": assessment.matched_consideration_ids,
        "novel_matched": assessment.novel_matched_ids,
        "knowledge": assessment.knowledge,
    }


async def _run_repetition(
    *,
    repetition: int,
    cases: tuple[CascadeCase, ...],
    projection: SemanticProjection,
    capability: JevCapability,
    jev: JevClient,
    reasoner: ScientificReasoner,
) -> dict[str, Any]:
    case_ids = tuple(case.case_id for case in cases)

    triage_started = perf_counter()
    decision = jev.evaluate(projection, capability)
    triage_latency_ms = (perf_counter() - triage_started) * 1000
    probabilities = {
        answer.question_id.removeprefix("escalate__"): float(answer.value)
        for answer in decision.answers
    }
    escalations = triage_escalations(
        probabilities=probabilities, case_ids=case_ids, threshold=TRIAGE_THRESHOLD
    )
    escalated = tuple(case_id for case_id in case_ids if escalations[case_id])

    all_arm: dict[str, ReasoningAssessment] = {}
    all_records: list[dict[str, Any]] = []
    for case in cases:
        assessment, record = await _reason_case(reasoner, case)
        all_arm[case.case_id] = assessment
        all_records.append(record)

    cascade_arm: dict[str, ReasoningAssessment] = {}
    cascade_records: list[dict[str, Any]] = []
    for case in cases:
        if escalations[case.case_id]:
            assessment, record = await _reason_case(reasoner, case)
            cascade_arm[case.case_id] = assessment
            cascade_records.append(record)
        else:
            cascade_arm[case.case_id] = assess_without_reasoning(case)

    evaluation = evaluate_cascade(
        cases=cases,
        all_arm=all_arm,
        cascade_arm=cascade_arm,
        escalations=escalations,
    )
    return {
        "repetition": repetition,
        "triage": {
            "probabilities": probabilities,
            "escalations": escalations,
            "escalated_case_ids": list(escalated),
            "usage": decision.usage,
            "latency_ms": triage_latency_ms,
            "model_id": decision.model_id,
            "capability_id": decision.capability_id,
            "capability_version": decision.capability_version,
            "projection_fingerprint": decision.projection_fingerprint,
        },
        "all_arm": {
            "calls": len(all_records),
            "cases": all_records,
            "inputs": "every eligible case",
        },
        "cascade_arm": {
            "calls": len(cascade_records),
            "cases": cascade_records,
            "screened_out_case_ids": [cid for cid in case_ids if not escalations[cid]],
        },
        "all_arm_resources": _arm_record("all", all_records),
        "cascade_arm_resources": _arm_record("cascade", cascade_records),
        "evaluation": asdict(evaluation),
    }


def _arm_record(arm_id: str, cases: list[dict[str, Any]]) -> dict[str, Any]:
    input_tokens = sum(int(case["usage"].get("input_tokens") or 0) for case in cases)
    output_tokens = sum(int(case["usage"].get("output_tokens") or 0) for case in cases)
    latency = sum(float(case["latency_ms"]) for case in cases)
    return {
        "arm_id": arm_id,
        "calls": len(cases),
        "attempts": sum(int(case["attempts"]) for case in cases),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "wall_ms": latency,
        "mean_latency_ms": (latency / len(cases)) if cases else 0.0,
    }


def _repetition_metrics(repetition: dict[str, Any]) -> dict[str, float]:
    return dict(repetition["evaluation"]["metrics"])


def _repetition_success(metrics: dict[str, float]) -> bool:
    return (
        metrics["useful_case_count"] > 0
        and metrics["false_negative_count"] == 0
        and metrics["quality_loss"] <= MAX_QUALITY_LOSS
        and metrics["oncox_call_reduction"] >= MIN_ONCOX_CALL_REDUCTION
    )


def _fetch_projects(
    client: GdcClient,
) -> tuple[GdcResponse, GdcResponse, dict[str, dict[str, Any]]]:
    status = client.get("status")
    filters = json.dumps(
        {"op": "in", "content": {"field": "project_id", "value": list(PROJECT_IDS)}},
        separators=(",", ":"),
    )
    response = client.get(
        "projects",
        {
            "filters": filters,
            "expand": "summary,summary.data_categories,summary.experimental_strategies",
            "fields": "project_id,name,primary_site,disease_type,summary",
            "size": len(PROJECT_IDS),
        },
    )
    hits = response.payload.get("data", {}).get("hits", [])
    views: dict[str, dict[str, Any]] = {}
    for hit in hits:
        summary = hit["summary"]
        views[str(hit["project_id"])] = _build_view(
            str(hit["project_id"]),
            {
                "primary_site": sorted(hit["primary_site"]),
                "disease_type": sorted(hit["disease_type"]),
                "case_count": summary["case_count"],
                "file_count": summary["file_count"],
                "data_categories": {
                    entry["data_category"]: entry["file_count"]
                    for entry in summary["data_categories"]
                },
                "experimental_strategies": {
                    entry["experimental_strategy"]: entry["file_count"]
                    for entry in summary["experimental_strategies"]
                },
            },
        )
    if set(views) != set(PROJECT_IDS):
        raise ValueError("GDC response does not match the frozen project set")
    return status, response, views


def _receipt(response: GdcResponse) -> dict[str, Any]:
    return {
        "url": response.url,
        "response_bytes": response.response_bytes,
        "latency_ms": response.latency_ms,
    }


def _frozen_protocol(cases: tuple[CascadeCase, ...]) -> dict[str, Any]:
    return {
        "case_ids": [case.case_id for case in cases],
        "live_case_ids": list(LIVE_CASE_IDS),
        "case_set_fingerprint": _case_set_fingerprint(cases),
        "novel_consideration_counts": {
            case.case_id: len(case.novel()) for case in cases
        },
        "consideration_counts": {case.case_id: len(case.considerations) for case in cases},
        "triage_threshold": TRIAGE_THRESHOLD,
        "max_quality_loss": MAX_QUALITY_LOSS,
        "min_oncox_call_reduction": MIN_ONCOX_CALL_REDUCTION,
        "live_repetitions": LIVE_REPETITIONS,
        "oncox_max_attempts": ONCOX_MAX_ATTEMPTS,
        "oncox_max_tokens": ONCOX_MAX_TOKENS,
        "oncox_reasoning_effort": ONCOX_REASONING_EFFORT,
        "oncox_instructions_sha256": sha256(ONCOX_INSTRUCTIONS.encode("utf-8")).hexdigest(),
        "reasoning_question": REASONING_QUESTION,
        "capability_id": CAPABILITY_ID,
        "projection_id": PROJECTION_ID,
    }


def _run_live(settings: Settings, frozen: FrozenExperiment) -> ExperimentResult:
    try:
        from agents import set_tracing_disabled
    except ImportError as exc:
        raise RuntimeError("install the agents extra: pip install -e '.[agents]'") from exc

    set_tracing_disabled(settings.disable_tracing)
    status_response, project_response, views = _fetch_projects(GdcClient())
    locked_cases = _build_cases(views)
    validate_case_set(locked_cases)
    cases = _select_cases(locked_cases)
    projection = _projection(cases)
    capability = _capability(cases)
    jev = TypeSafeJevClient(api_key=settings.typesafe_api_key, model=settings.jev_model)
    reasoner = AgentsOncoXReasoner(
        model=build_agent_model(settings),
        max_attempts=ONCOX_MAX_ATTEMPTS,
        max_tokens=ONCOX_MAX_TOKENS,
        reasoning_effort=ONCOX_REASONING_EFFORT,
    )

    repetitions: list[dict[str, Any]] = []
    for repetition in range(1, LIVE_REPETITIONS + 1):
        record = asyncio.run(
            _run_repetition(
                repetition=repetition,
                cases=cases,
                projection=projection,
                capability=capability,
                jev=jev,
                reasoner=reasoner,
            )
        )
        metrics = _repetition_metrics(record)
        record["success_criteria_met"] = _repetition_success(metrics)
        repetitions.append(record)

    escalations_stable = all(
        record["triage"]["escalations"] == repetitions[0]["triage"]["escalations"]
        for record in repetitions[1:]
    )
    useful_stable = all(
        record["evaluation"]["useful_case_ids"] == repetitions[0]["evaluation"]["useful_case_ids"]
        for record in repetitions[1:]
    )
    false_negatives = [
        {
            "repetition": record["repetition"],
            "case_id": case_id,
            "triage_probability": record["triage"]["probabilities"][case_id],
            "all_arm_novel_matched": next(
                entry["novel_matched_all"]
                for entry in record["evaluation"]["per_case"]
                if entry["case_id"] == case_id
            ),
        }
        for record in repetitions
        for case_id in record["evaluation"]["false_negative_case_ids"]
    ]
    all_successful = all(record["success_criteria_met"] for record in repetitions)
    status = status_response.payload
    return ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": True,
            "success_criteria_met": all_successful,
            "protocol": _frozen_protocol(cases),
            "projection_fingerprint": projection.fingerprint,
            "case_states": {case.case_id: case.state for case in cases},
            "rubric": {
                case.case_id: [
                    {
                        "consideration_id": item.consideration_id,
                        "description": item.description,
                        "recorded_in_state": item.recorded_in_state,
                    }
                    for item in case.considerations
                ]
                for case in cases
            },
            "oncox": {
                "model_id": reasoner.model_id,
                "max_turns": reasoner.max_turns,
                "max_attempts": reasoner.max_attempts,
                "max_tokens": reasoner.max_tokens,
                "reasoning_effort": reasoner.reasoning_effort or "provider default",
                "instructions_sha256": sha256(
                    ONCOX_INSTRUCTIONS.encode("utf-8")
                ).hexdigest(),
                "temperature": "provider default",
                "schema_retry_note": (
                    "two live attempts failed with provider structured-output errors before any "
                    "result was observed: first an unparseable completion, then an output cap "
                    "consumed entirely by reasoning tokens. A bounded retry was frozen and the "
                    "token cap removed before any arm result existed."
                ),
            },
            "jev": {
                "model_id": settings.jev_model,
                "capability_id": CAPABILITY_ID,
                "capability_version": "0.1.0",
            },
            "cost": {
                "measured": False,
                "basis": (
                    "the Agents SDK usage path exposes tokens only; no provider cost is recorded "
                    "or estimated"
                ),
            },
            "repetitions": repetitions,
            "escalations_stable": escalations_stable,
            "useful_case_ids_stable": useful_stable,
            "false_negatives": false_negatives,
            "source": {
                "data_release": status.get("data_release"),
                "api_version": status.get("tag"),
                "commit": status.get("commit"),
                "status_receipt": _receipt(status_response),
                "project_receipt": _receipt(project_response),
                "records_downloaded": (
                    "project aggregates only; 0 case, sample, aliquot, file, or molecular records"
                ),
            },
        },
        observations=(
            (
                "Jev triage reduced OncoX calls without losing an OncoX-useful case in this run."
                if all_successful
                else "The frozen cascade criteria were not met in every repetition."
            ),
        ),
        limitations=(
            "Usefulness is a frozen lexical rubric outcome, not a scientific measure of quality.",
            "The four live cases were built with unambiguous triage signals; boundary cases and "
            "the six held-back locked cases remain untested.",
            "Arm ALL ground truth and the cascade arm come from the same model and adapter.",
            "Two repetitions of a four-case live slice cannot establish general triage behavior.",
            "Rubric matching moved between repetitions, so useful-case counts are noisy at this "
            "output length.",
            "OncoX output is interpretation and cannot create ScientificEvidence.",
        ),
    )


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    if not live:
        locked_cases = _build_cases(_frozen_views())
        validate_case_set(locked_cases)
        cases = _select_cases(locked_cases)
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.FROZEN,
            frozen_fingerprint=frozen.fingerprint,
            measurements={
                "live": False,
                "protocol": _frozen_protocol(locked_cases),
                "projection_fingerprint": _projection(cases).fingerprint,
                "case_states": {case.case_id: case.state for case in cases},
                "rubric": {
                    case.case_id: [
                        {
                            "consideration_id": item.consideration_id,
                            "description": item.description,
                            "recorded_in_state": item.recorded_in_state,
                        }
                        for item in case.considerations
                    ]
                    for case in locked_cases
                },
                "source_snapshot": "frozen GDC project aggregates captured 2026-09-29",
            },
            limitations=(
                "No OncoX or Jev call was made; this is the frozen protocol only.",
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
                limitations=("External failure does not establish cascade behavior.",),
            )
    store.append("architecture_experiment_result", asdict(result))
    if not live:
        return str(asdict(result))
    return json.dumps(_console_summary(result), indent=2, default=str)


def _console_summary(result: ExperimentResult) -> dict[str, Any]:
    """Bounded console view; the append-only store keeps the full reasoning records."""

    measurements = result.measurements
    repetitions = measurements.get("repetitions", [])
    return {
        "experiment_id": result.experiment_id,
        "status": result.status,
        "live": measurements.get("live"),
        "success_criteria_met": measurements.get("success_criteria_met"),
        "protocol": measurements.get("protocol"),
        "projection_fingerprint": measurements.get("projection_fingerprint"),
        "source": measurements.get("source"),
        "escalations_stable": measurements.get("escalations_stable"),
        "useful_case_ids_stable": measurements.get("useful_case_ids_stable"),
        "false_negatives": measurements.get("false_negatives"),
        "repetitions": [
            {
                "repetition": record["repetition"],
                "escalated_case_ids": record["triage"]["escalated_case_ids"],
                "triage_probabilities": record["triage"]["probabilities"],
                "metrics": record["evaluation"]["metrics"],
                "all_arm_resources": record["all_arm_resources"],
                "cascade_arm_resources": record["cascade_arm_resources"],
                "triage_usage": record["triage"]["usage"],
                "triage_latency_ms": record["triage"]["latency_ms"],
                "success_criteria_met": record["success_criteria_met"],
                "per_case": record["evaluation"]["per_case"],
            }
            for record in repetitions
        ],
        "observations": result.observations,
        "limitations": result.limitations,
        "store": "full reasoning records appended to the durable event store",
    }
