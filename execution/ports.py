from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True, slots=True)
class MeasuredResult:
    operation_id: str
    method_id: str
    population_id: str
    measurements: dict[str, Any]
    provenance: dict[str, str] = field(default_factory=dict)


class ExecutionCapability(Protocol):
    capability_id: str
    version: str

    def execute(self, *, operation_id: str, inputs: dict[str, Any]) -> MeasuredResult: ...
