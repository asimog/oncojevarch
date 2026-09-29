import pytest

from oncolab.capabilities import CapabilityRegistry, EngineeringReadiness, ScientificReadiness
from oncolab.evolution import apply_verification, plan_capability_evolution
from oncolab.gaps import Gap, GapKind


def _gap(kind: GapKind, need: str = "summarize availability across sources") -> Gap:
    return Gap(
        gap_id="gap-" + kind.value,
        kind=kind,
        need=need,
        evidence=("recorded gap evidence",),
        unmet_requirements=("no applicable capability",),
        origin="test",
    )


def test_method_gap_is_refused_by_engineering() -> None:
    with pytest.raises(ValueError, match="MethodGap"):
        plan_capability_evolution(_gap(GapKind.METHOD, "estimate tumor purity"))


def test_failed_verification_leaves_the_capability_unverified() -> None:
    registry = CapabilityRegistry()
    plan = plan_capability_evolution(_gap(GapKind.CAPABILITY))

    record, notes = apply_verification(
        registry,
        plan,
        verification_passed=False,
        verification_evidence=("verify.py failed",),
    )

    assert record.engineering_readiness is EngineeringReadiness.DRAFT
    assert any("not passed" in note for note in notes)
    assert registry.get(plan.capability_id, "1").engineering_readiness is EngineeringReadiness.DRAFT


def test_passed_verification_advances_one_step_at_a_time_and_evaluation_promotes() -> None:
    registry = CapabilityRegistry()
    plan = plan_capability_evolution(_gap(GapKind.CAPABILITY))

    verified, _ = apply_verification(registry, plan, verification_passed=True)
    assert verified.engineering_readiness is EngineeringReadiness.VERIFIED
    assert verified.scientific_readiness is ScientificReadiness.EXPERIMENTAL

    promoted, notes = apply_verification(
        registry,
        plan,
        verification_passed=True,
        scientifically_evaluated=True,
        evaluated_domain="frozen fixture domain",
    )
    assert promoted.engineering_readiness is EngineeringReadiness.PROMOTED
    assert promoted.scientific_readiness is ScientificReadiness.VALIDATED_FOR_DEFINED_DOMAIN
    assert any("scientific readiness" in note for note in notes)
