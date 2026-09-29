from __future__ import annotations

from enum import StrEnum


class EvaluationLevel(StrEnum):
    SYNTHETIC = "synthetic"
    SEMI_SYNTHETIC = "semi_synthetic"
    RETROSPECTIVE_REAL = "retrospective_real"
    INDEPENDENT_REAL = "independent_real"
    TEMPORAL_PROSPECTIVE = "temporal_prospective"
