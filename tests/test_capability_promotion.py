import pytest

from oncolab.capabilities import (
    CapabilityKind,
    CapabilityRecord,
    CapabilityRegistry,
    EngineeringReadiness,
    ScientificReadiness,
)


def test_capability_cannot_self_promote() -> None:
    registry = CapabilityRegistry()
    record = CapabilityRecord("demo", CapabilityKind.JEV, "1", "git:abc")
    registry.register(record)

    with pytest.raises(ValueError):
        registry.advance_engineering("demo", "1", EngineeringReadiness.PROMOTED)

    tested = registry.advance_engineering("demo", "1", EngineeringReadiness.TESTED)
    assert tested.engineering_readiness is EngineeringReadiness.TESTED
    verified = registry.advance_engineering("demo", "1", EngineeringReadiness.VERIFIED)
    assert verified.engineering_readiness is EngineeringReadiness.VERIFIED
    promoted = registry.advance_engineering("demo", "1", EngineeringReadiness.PROMOTED)
    assert promoted.engineering_readiness is EngineeringReadiness.PROMOTED


def test_scientific_readiness_is_separate_axis() -> None:
    registry = CapabilityRegistry()
    registry.register(CapabilityRecord("m", CapabilityKind.METHOD, "1", "git:def"))
    with pytest.raises(ValueError):
        registry.set_scientific_readiness("m", "1", ScientificReadiness.VALIDATED_FOR_REPLAY)
    registry.advance_engineering("m", "1", EngineeringReadiness.TESTED)
    registry.advance_engineering("m", "1", EngineeringReadiness.VERIFIED)
    updated = registry.set_scientific_readiness("m", "1", ScientificReadiness.VALIDATED_FOR_REPLAY)
    assert updated.engineering_readiness is EngineeringReadiness.VERIFIED
    assert updated.scientific_readiness is ScientificReadiness.VALIDATED_FOR_REPLAY
