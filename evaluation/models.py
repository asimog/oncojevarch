from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class EvaluationLevel(StrEnum):
    SYNTHETIC = "synthetic"
    SEMI_SYNTHETIC = "semi_synthetic"
    RETROSPECTIVE_REAL = "retrospective_real"
    INDEPENDENT_REAL = "independent_real"
    TEMPORAL_PROSPECTIVE = "temporal_prospective"


class SystemArm(StrEnum):
    A_DETERMINISTIC = "A_deterministic"
    B_DETERMINISTIC_ONCOX = "B_deterministic_oncox"
    C_DETERMINISTIC_JEV_ONCOX = "C_deterministic_jev_oncox"


@dataclass(frozen=True, slots=True)
class MetricRecord:
    name: str
    value: float
    unit: str


@dataclass(frozen=True, slots=True)
class ABCTestPlan:
    evaluation_level: EvaluationLevel
    arms: tuple[SystemArm, ...]
    frozen_metrics: tuple[str, ...]
    equal_budget: bool
    equal_target: bool
    leakage_controls: tuple[str, ...] = ()
