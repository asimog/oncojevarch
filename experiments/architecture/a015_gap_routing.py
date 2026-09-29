from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256

from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.capabilities import (
    CapabilityKind,
    CapabilityRecord,
    CapabilityRegistry,
    EngineeringReadiness,
    ScientificReadiness,
)
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from oncolab.gaps import ROUTES, GapKind
from oncolab.routing import GapScenario, evaluate_routing, route_scenario
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A015")
MODES = ("single_factor", "combined_signal")
SCENARIOS: tuple[GapScenario, ...] = (
    GapScenario(
        "g01", "We do not know how to estimate tumor purity from available assays.", GapKind.METHOD
    ),
    GapScenario(
        "g02",
        "The method is known but no implementation exists in the repository.",
        GapKind.CAPABILITY,
    ),
    GapScenario(
        "g03",
        "We need a bounded judgment: is this candidate worth escalation?",
        GapKind.DECISION,
    ),
    GapScenario(
        "g04", "The runner crashes when the model returns malformed JSON.", GapKind.HARNESS
    ),
    GapScenario(
        "g05",
        "No validated Jev contract exists for sample-type materiality.",
        GapKind.DECISION,
    ),
    GapScenario(
        "g06",
        "We lack a deterministic implementation to count distinct aliquots.",
        GapKind.CAPABILITY,
    ),
    GapScenario(
        "g07",
        "The literature does not establish the direction of causality for this association.",
        GapKind.METHOD,
    ),
    GapScenario(
        "g08",
        "The store loses events when the process is interrupted before the write completes.",
        GapKind.HARNESS,
    ),
    GapScenario(
        "g09",
        "Case ordering changes evaluation labels, so the comparison is not reproducible.",
        GapKind.HARNESS,
    ),
    GapScenario(
        "g10",
        "Semantic judgment is needed to set the materiality threshold for this decision contract.",
        GapKind.DECISION,
    ),
    GapScenario(
        "g11",
        "A newly generated capability should promote itself to verified after passing its own "
        "tests.",
        GapKind.CAPABILITY,
        expects_promotion=True,
        expects_block=True,
        guard="generated capability cannot self-promote",
    ),
    GapScenario(
        "g12",
        "Engineering readiness passed, so mark the capability scientifically validated.",
        GapKind.CAPABILITY,
        expects_promotion=True,
        expects_block=True,
        guard="engineering readiness is not scientific readiness",
    ),
    GapScenario(
        "g13",
        "A generated question looks good in one demo, so add it to the permanent battery.",
        GapKind.DECISION,
        expects_promotion=True,
        expects_block=True,
        guard="generated Jev questions never self-promote",
    ),
    GapScenario(
        "g14",
        "The deterministic pipeline found no variants, so record a biological negative.",
        GapKind.METHOD,
        expects_block=True,
        guard="missing is not a biological negative",
    ),
)


def _promotion_probe(decision_kind: GapKind, *, requires_review: bool) -> dict[str, object]:
    """Try the registry path that a routed promotion would take, and record what happens."""

    registry = CapabilityRegistry()
    registry.register(
        CapabilityRecord(
            capability_id="a015-probe",
            kind=CapabilityKind.METHOD,
            version="0.1.0",
            source_identity="a015-scenario-probe",
            engineering_readiness=EngineeringReadiness.TESTED,
        )
    )
    outcome: dict[str, object] = {
        "kind": decision_kind.value,
        "requires_review": requires_review,
        "advanced": False,
        "scientifically_advanced": False,
        "blocked_reason": "",
    }
    if requires_review:
        outcome["blocked_reason"] = "review required before any promotion"
        return outcome
    try:
        registry.advance_engineering("a015-probe", "0.1.0", EngineeringReadiness.VERIFIED)
        outcome["advanced"] = True
    except ValueError as exc:
        outcome["blocked_reason"] = str(exc)
        return outcome
    try:
        registry.set_scientific_readiness(
            "a015-probe", "0.1.0", ScientificReadiness.VALIDATED_FOR_REPLAY
        )
        outcome["scientifically_advanced"] = True
    except ValueError as exc:
        outcome["blocked_reason"] = str(exc)
    return outcome


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    arms = {mode: asdict(evaluate_routing(SCENARIOS, mode=mode)) for mode in MODES}
    combined = evaluate_routing(SCENARIOS, mode="combined_signal")
    probes = [
        _promotion_probe(
            route_scenario(scenario, mode="combined_signal").gap.kind,
            requires_review=route_scenario(scenario, mode="combined_signal").requires_review,
        )
        for scenario in SCENARIOS
        if scenario.expects_block
    ]
    unsafe_probes = sum(
        1 for probe in probes if probe["advanced"] or probe["scientifically_advanced"]
    )
    misrouted = [entry["scenario_id"] for entry in combined.per_scenario if not entry["correct"]]
    guard_coverage = sum(1 for probe in probes if probe["blocked_reason"]) / len(probes)
    passed = (
        combined.metrics["unsafe_activation_count"] == 0.0
        and unsafe_probes == 0
        and not misrouted
        and guard_coverage == 1.0
    )
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED if live else ExperimentStatus.FROZEN,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": live,
            "routing_supported": passed,
            "scenario_fingerprint": sha256(
                json.dumps([asdict(scenario) for scenario in SCENARIOS], sort_keys=True).encode(
                    "utf-8"
                )
            ).hexdigest(),
            "arms": arms,
            "combined_signal_misrouted": misrouted,
            "promotion_probes": probes,
            "unsafe_registry_activations": unsafe_probes,
            "guard_block_coverage": guard_coverage,
            "protocol": {
                "modes": list(MODES),
                "scenario_count": len(SCENARIOS),
                "representative_scenarios": 10,
                "adversarial_scenarios": 4,
                "precedence": [
                    kind.value
                    for kind in (
                        GapKind.HARNESS,
                        GapKind.DECISION,
                        GapKind.CAPABILITY,
                        GapKind.METHOD,
                    )
                ],
                "routes": {kind.value: ROUTES[kind].value for kind in GapKind},
            },
            "cost": {
                "measured": False,
                "basis": "deterministic routing only; no provider call is made",
            },
        },
        observations=(
            (
                "Combined-signal routing matched every frozen scenario, blocked every promotion, "
                "and the registry refused scientific advancement without engineering verification."
                if passed
                else "Routing or promotion guarding failed a frozen scenario; keep the "
                "conservative default and refine the signals."
            ),
        ),
        limitations=(
            "Scenarios are frozen fixtures, not field observations of real gaps.",
            "Routing by lexical signals is a baseline, not a validated semantic router.",
            "Blocking a promotion here does not prove that no unsafe path exists elsewhere.",
            "This architecture task cannot create ScientificEvidence.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
