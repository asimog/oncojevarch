from __future__ import annotations

from dataclasses import dataclass

from execution.ports import ExecutionCapability
from oncolab.admission import admit_measured_result
from oncolab.capabilities import (
    CapabilityRecord,
    CapabilityRegistry,
    EngineeringReadiness,
    ScientificReadiness,
)
from oncolab.gaps import Gap, GapKind, GapLedger, gap_identity
from oncolab.operations import AdmissionContextDisclosure, OperationRegistry
from research.ledger import EvidenceLedger, InvestigationLedger
from research.models import Investigation
from research.state import revise_investigation

_ACTIVATED_ENGINEERING = {EngineeringReadiness.VERIFIED, EngineeringReadiness.PROMOTED}


@dataclass
class ResearchRuntime:
    """Collaborators for session-independent research steps."""

    registry: CapabilityRegistry
    operations: OperationRegistry
    executors: dict[str, ExecutionCapability]
    gaps: GapLedger
    investigations: InvestigationLedger
    evidence: EvidenceLedger


@dataclass(frozen=True, slots=True)
class ResearchStepResult:
    investigation_id: str
    need: str
    outcome: str
    revision: Investigation
    search_candidates: tuple[str, ...] = ()
    evidence_id: str = ""
    gap_id: str = ""
    refusal_reasons: tuple[str, ...] = ()


def unmet_activation_requirements(record: CapabilityRecord) -> tuple[str, ...]:
    unmet: list[str] = []
    if record.engineering_readiness not in _ACTIVATED_ENGINEERING:
        unmet.append(f"engineering readiness is {record.engineering_readiness.value}")
    if record.scientific_readiness is ScientificReadiness.EXPERIMENTAL:
        unmet.append("scientific readiness is experimental; bounded activation has not happened")
    return tuple(unmet)


def run_research_step(
    *,
    runtime: ResearchRuntime,
    investigation: Investigation,
    need: str,
    operation_id: str,
) -> ResearchStepResult:
    """One session-independent research step: search, then execute-or-gap, then persist.

    The step never improvises science: if no activated capability can satisfy the need, it records
    a typed gap and revises the investigation. If a measurement is admitted, the evidence and the
    revised investigation are persisted before the step returns.

    Raises KeyError if the operation id is not registered; callers should treat that as a caller
    error rather than a capability gap.
    """

    operation = runtime.operations.get(operation_id)
    candidates = runtime.registry.search(need, limit=5)
    candidate_ids = tuple(f"{summary.capability_id}:{summary.version}" for summary in candidates)

    try:
        record = runtime.registry.get(operation.capability_id, operation.version)
    except KeyError:
        record = None

    unmet: list[str] = []
    if record is None:
        unmet.append("no registered capability for the required operation")
    else:
        unmet.extend(unmet_activation_requirements(record))
        if operation.capability_id not in runtime.executors:
            unmet.append("no executable implementation is registered")

    if unmet:
        gap = Gap(
            gap_id=gap_identity(
                need=need,
                kind=GapKind.CAPABILITY,
                origin=investigation.investigation_id,
            ),
            kind=GapKind.CAPABILITY,
            need=need,
            evidence=tuple(unmet),
            unmet_requirements=tuple(unmet),
            attempted=(*candidate_ids, f"{operation.capability_id}:{operation.version}"),
            origin=investigation.investigation_id,
        )
        runtime.gaps.record(gap)
        revision = revise_investigation(
            investigation,
            next_action=f"resolve gap {gap.gap_id} via {gap.route.value}",
        )
        runtime.investigations.record(revision)
        return ResearchStepResult(
            investigation_id=investigation.investigation_id,
            need=need,
            outcome="gap",
            revision=revision,
            search_candidates=candidate_ids,
            gap_id=gap.gap_id,
        )

    executor = runtime.executors[operation.capability_id]
    measured = executor.execute(operation_id=operation.operation_id, inputs=operation.inputs)
    context = operation.context
    if isinstance(executor, AdmissionContextDisclosure):
        context = executor.admission_context(result=measured, base=context)
    admission = admit_measured_result(measured, context=context)
    evidence = admission.evidence
    if evidence is None:
        refusal = admission.refusal
        refusal_reasons: tuple[str, ...] = ()
        if refusal is not None:
            refusal_reasons = tuple(reason.value for reason in refusal.reasons)
        return ResearchStepResult(
            investigation_id=investigation.investigation_id,
            need=need,
            outcome="refused",
            revision=investigation,
            search_candidates=candidate_ids,
            refusal_reasons=refusal_reasons,
        )

    runtime.evidence.record(evidence)
    revision = revise_investigation(investigation, evidence_ids=(evidence.evidence_id,))
    runtime.investigations.record(revision)
    return ResearchStepResult(
        investigation_id=investigation.investigation_id,
        need=need,
        outcome="evidence",
        revision=revision,
        search_candidates=candidate_ids,
        evidence_id=evidence.evidence_id,
    )
