from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import StrEnum
from hashlib import sha256
from typing import Any


class ExperimentClass(StrEnum):
    ARCHITECTURE = "architecture"
    SCIENTIFIC = "scientific"


class ExperimentStatus(StrEnum):
    PLANNED = "planned"
    FROZEN = "frozen"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class ExperimentSpec:
    experiment_id: str
    experiment_class: ExperimentClass
    question: str
    hypothesis: str = ""
    required_data: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    comparison: tuple[str, ...] = ()
    metrics: tuple[str, ...] = ()
    inputs: dict[str, Any] = field(default_factory=dict)
    success_criteria: tuple[str, ...] = ()
    failure_criteria: tuple[str, ...] = ()
    decision_consequences: tuple[str, ...] = ()
    budget: dict[str, Any] = field(default_factory=dict)
    capability_versions: dict[str, str] = field(default_factory=dict)
    evaluation_level: str = "synthetic"
    executable: bool = False

    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"), default=str)
        return sha256(payload.encode("utf-8")).hexdigest()

    def validation_errors(self) -> tuple[str, ...]:
        required = {
            "question": self.question,
            "hypothesis": self.hypothesis,
            "required_data": self.required_data,
            "required_capabilities": self.required_capabilities,
            "comparison": self.comparison,
            "metrics": self.metrics,
            "success_criteria": self.success_criteria,
            "failure_criteria": self.failure_criteria,
            "decision_consequences": self.decision_consequences,
            "budget": self.budget,
            "evaluation_level": self.evaluation_level,
        }
        return tuple(name for name, value in required.items() if not value)


@dataclass(frozen=True, slots=True)
class FrozenExperiment:
    spec: ExperimentSpec
    fingerprint: str

    @classmethod
    def freeze(cls, spec: ExperimentSpec) -> FrozenExperiment:
        return cls(spec=spec, fingerprint=spec.fingerprint())


@dataclass(frozen=True, slots=True)
class ExperimentResult:
    experiment_id: str
    experiment_class: ExperimentClass
    status: ExperimentStatus
    frozen_fingerprint: str
    measurements: dict[str, Any] = field(default_factory=dict)
    observations: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    artifact_refs: tuple[str, ...] = ()
