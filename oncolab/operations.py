from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from execution.ports import MeasuredResult
from oncolab.admission import AdmissionContext


@dataclass(frozen=True, slots=True)
class ScientificOperation:
    """A frozen execution request: which capability, with which inputs and admission context."""

    operation_id: str
    capability_id: str
    version: str
    inputs: dict[str, Any]
    context: AdmissionContext


@runtime_checkable
class AdmissionContextDisclosure(Protocol):
    """A capability that can finish its own admission context from a measured result.

    The base context carries frozen identity (evidence id, measurement, population, method).
    Coverage, missingness, and source version are properties of the measurement itself, so a
    capability that can disclose them deterministically may complete the context before admission.
    """

    def admission_context(
        self, *, result: MeasuredResult, base: AdmissionContext
    ) -> AdmissionContext: ...


class OperationRegistry:
    """Registry of scientific operations available to the research loop."""

    def __init__(self) -> None:
        self._operations: dict[str, ScientificOperation] = {}

    def register(self, operation: ScientificOperation) -> None:
        if operation.operation_id in self._operations:
            raise ValueError(f"operation already registered: {operation.operation_id}")
        self._operations[operation.operation_id] = operation

    def get(self, operation_id: str) -> ScientificOperation:
        return self._operations[operation_id]

    def list_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._operations))
