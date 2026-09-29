import pytest

from experiments.architecture.a015_gap_routing import (
    SCENARIOS,
    _promotion_probe,
)
from oncolab.capabilities import (
    CapabilityKind,
    CapabilityRecord,
    CapabilityRegistry,
    EngineeringReadiness,
    ScientificReadiness,
)
from oncolab.gaps import GapKind, GapRoute
from oncolab.routing import GapScenario, evaluate_routing, route_scenario


def test_combined_signal_routing_matches_every_frozen_scenario() -> None:
    evaluation = evaluate_routing(SCENARIOS, mode="combined_signal")

    assert evaluation.metrics["route_accuracy"] == 1.0
    assert evaluation.metrics["unsafe_activation_count"] == 0.0
    assert evaluation.metrics["review_requirement_coverage"] == 1.0


def test_routing_failure_branch_is_open() -> None:
    combined = evaluate_routing(SCENARIOS, mode="combined_signal")
    single = evaluate_routing(SCENARIOS, mode="single_factor")

    assert combined.metrics["route_accuracy"] > single.metrics["route_accuracy"]
    assert single.metrics["unsafe_activation_count"] > 0.0


def test_routes_follow_the_frozen_taxonomy() -> None:
    assert route_scenario(SCENARIOS[0], mode="combined_signal").gap.route is (
        GapRoute.SCIENTIFIC_RESEARCH
    )


def test_mixed_scenario_prefers_the_operational_gap() -> None:
    scenario = GapScenario(
        "mixed",
        "The runner crashes when a bounded judgment returns malformed output.",
        GapKind.HARNESS,
    )

    decision = route_scenario(scenario, mode="combined_signal")

    assert decision.gap.kind is GapKind.HARNESS


def test_unsignalled_scenario_defaults_to_a_method_gap() -> None:
    scenario = GapScenario("quiet", "Biology is hard to model here.", GapKind.METHOD)

    decision = route_scenario(scenario, mode="combined_signal")

    assert decision.gap.kind is GapKind.METHOD
    assert decision.requires_review is False


def test_promotion_requests_always_require_review_and_are_blocked() -> None:
    for scenario in SCENARIOS:
        if not scenario.expects_block:
            continue
        decision = route_scenario(scenario, mode="combined_signal")
        assert decision.blocked
        assert decision.requires_review


def test_promotion_probe_shows_why_review_is_mandatory() -> None:
    blocked = _promotion_probe(GapKind.CAPABILITY, requires_review=True)
    shortcut = _promotion_probe(GapKind.CAPABILITY, requires_review=False)

    assert blocked["advanced"] is False
    assert blocked["scientifically_advanced"] is False
    assert "review required" in str(blocked["blocked_reason"])
    # Without review the whole chain runs through, which is exactly the unsafe path to block.
    assert shortcut["advanced"] is True
    assert shortcut["scientifically_advanced"] is True


def test_registry_refuses_out_of_order_and_unverified_promotion() -> None:
    registry = CapabilityRegistry()
    registry.register(
        CapabilityRecord(
            capability_id="c",
            kind=CapabilityKind.JEV,
            version="0.1.0",
            source_identity="test",
        )
    )

    with pytest.raises(ValueError, match="one verified step"):
        registry.advance_engineering("c", "0.1.0", EngineeringReadiness.VERIFIED)
    with pytest.raises(ValueError, match="cannot advance before engineering verification"):
        registry.set_scientific_readiness("c", "0.1.0", ScientificReadiness.VALIDATED_FOR_REPLAY)


def test_unknown_routing_mode_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown routing mode"):
        route_scenario(SCENARIOS[0], mode="vibes")
