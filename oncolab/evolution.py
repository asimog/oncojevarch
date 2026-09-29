from __future__ import annotations

from dataclasses import dataclass

from oncolab.capabilities import (
    CapabilityKind,
    CapabilityRecord,
    CapabilityRegistry,
    EngineeringReadiness,
    ScientificReadiness,
)
from oncolab.gaps import Gap, GapKind


@dataclass(frozen=True, slots=True)
class EvolutionPlan:
    """Bounded engineering specification derived from one recorded gap."""

    gap_id: str
    capability_id: str
    capability_kind: CapabilityKind
    purpose: str
    applicability: tuple[str, ...]
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    acceptance: tuple[str, ...]
    verification_command: str


def plan_capability_evolution(gap: Gap) -> EvolutionPlan:
    """Translate a recorded gap into the smallest bounded engineering specification.

    A MethodGap must not reach this path: method invention is scientific research, not engineering.
    """

    if gap.kind is GapKind.METHOD:
        raise ValueError("MethodGap routes to scientific research, not engineering")
    return EvolutionPlan(
        gap_id=gap.gap_id,
        capability_id="evolved_" + gap.gap_id,
        capability_kind=CapabilityKind.METHOD,
        purpose=f"close gap {gap.gap_id}: {gap.need}",
        applicability=(gap.need,),
        inputs=("operation inputs",),
        outputs=("measured output",),
        acceptance=(
            f"the capability satisfies: {gap.need}",
            "measurements pass the admission gate with explicit provenance",
        ),
        verification_command="python scripts/verify.py",
    )


def apply_verification(
    registry: CapabilityRegistry,
    plan: EvolutionPlan,
    *,
    verification_passed: bool,
    verification_evidence: tuple[str, ...] = (),
    scientifically_evaluated: bool = False,
    evaluated_domain: str = "",
) -> tuple[CapabilityRecord, tuple[str, ...]]:
    """Advance a planned capability only through recorded evidence.

    Registration starts at DRAFT; passing verification advances one step at a time to VERIFIED;
    PROMOTED additionally requires a scientific/contract evaluation flag plus an evaluated
    domain. Generated capabilities never self-promote.
    """

    notes: list[str] = []
    try:
        record = registry.get(plan.capability_id, "1")
    except KeyError:
        registry.register(
            CapabilityRecord(
                capability_id=plan.capability_id,
                kind=plan.capability_kind,
                version="1",
                source_identity=f"gap:{plan.gap_id}",
                applicability=plan.applicability,
                purpose=plan.purpose,
                inputs=plan.inputs,
                outputs=plan.outputs,
            )
        )
        record = registry.get(plan.capability_id, "1")
        notes.append("registered as draft")
    _ = verification_evidence
    if not verification_passed:
        notes.append(
            f"verification not passed; readiness stays {record.engineering_readiness.value}"
        )
        return record, tuple(notes)

    next_step = {
        EngineeringReadiness.DRAFT: EngineeringReadiness.TESTED,
        EngineeringReadiness.TESTED: EngineeringReadiness.VERIFIED,
    }
    while record.engineering_readiness in next_step:
        record = registry.advance_engineering(
            plan.capability_id, "1", next_step[record.engineering_readiness]
        )
    notes.append(f"engineering readiness is {record.engineering_readiness.value}")

    if scientifically_evaluated and evaluated_domain:
        if record.scientific_readiness is ScientificReadiness.EXPERIMENTAL:
            record = registry.set_scientific_readiness(
                plan.capability_id,
                "1",
                ScientificReadiness.VALIDATED_FOR_DEFINED_DOMAIN,
            )
        if record.engineering_readiness is EngineeringReadiness.VERIFIED:
            record = registry.advance_engineering(
                plan.capability_id, "1", EngineeringReadiness.PROMOTED
            )
        notes.append(f"scientific readiness is {record.scientific_readiness.value}")
    return record, tuple(notes)
