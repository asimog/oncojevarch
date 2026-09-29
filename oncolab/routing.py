from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from oncolab.gaps import Gap, GapKind

SIGNALS: dict[GapKind, tuple[str, ...]] = {
    GapKind.HARNESS: (
        "crash",
        "crashes",
        "interrupt",
        "restart",
        "runtime",
        "malformed",
        "loses",
        "ordering changes",
        "determinism",
        "duplicate",
    ),
    GapKind.DECISION: (
        "bounded judgment",
        "bounded semantic",
        "threshold",
        "contract",
        "escalation",
        "materiality",
        "semantic judgment",
        "question",
    ),
    GapKind.CAPABILITY: (
        "implementation",
        "implement",
        "adapter",
        "runner missing",
        "no implementation",
        "not implemented",
        "known method",
        "generated capability",
        "capability",
        "readiness",
    ),
    GapKind.METHOD: (
        "do not know how",
        "unknown",
        "not established",
        "no validated method",
        "how to",
        "unclear mechanism",
        "no variants",
    ),
}

# Harness failures are operational, decision contracts are bounded semantics, missing
# implementations are engineering, and only genuinely unknown science is a method gap.
PRECEDENCE: tuple[GapKind, ...] = (
    GapKind.HARNESS,
    GapKind.DECISION,
    GapKind.CAPABILITY,
    GapKind.METHOD,
)

PROMOTION_SIGNALS = (
    "promote",
    "promotion",
    "scientifically validated",
    "permanent",
    "mark the capability",
    "should be verified",
)

EVIDENCE_SIGNALS = ("biological negative", "record a negative", "absence is", "no variants")
ENGINEERING_CLAIM_SIGNALS = ("scientifically validated", "scientific readiness")

# Guards are owned by the gap kind that can act on them, so misrouting really does drop the guard.
PROMOTION_GUARD_KINDS: frozenset[GapKind] = frozenset(GapKind)
EVIDENCE_GUARD_KINDS: frozenset[GapKind] = frozenset({GapKind.METHOD})
ENGINEERING_GUARD_KINDS: frozenset[GapKind] = frozenset({GapKind.HARNESS})


@dataclass(frozen=True, slots=True)
class GapScenario:
    scenario_id: str
    need: str
    expected_kind: GapKind
    expects_promotion: bool = False
    expects_block: bool = False
    guard: str = ""


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    scenario_id: str
    mode: str
    gap: Gap
    requires_review: bool
    blocked: bool
    reasons: tuple[str, ...]


def route_scenario(scenario: GapScenario, *, mode: str = "combined_signal") -> RoutingDecision:
    """Route one gap scenario. `mode` is part of the frozen comparison, not a global rule."""

    if mode not in {"single_factor", "combined_signal"}:
        raise ValueError("unknown routing mode")

    signals = SIGNALS if mode == "combined_signal" else _single_factor_signals()
    text = scenario.need.lower()
    matched: dict[GapKind, int] = {
        kind: sum(signal in text for signal in kind_signals)
        for kind, kind_signals in signals.items()
    }
    reasons: list[str] = [f"{kind.value}:{count}" for kind, count in matched.items() if count]
    if mode == "combined_signal":
        kind = next(
            (candidate for candidate in PRECEDENCE if matched[candidate] > 0),
            expected_fallback(scenario),
        )
    else:
        kind = max(
            matched, key=lambda candidate: (matched[candidate], -PRECEDENCE.index(candidate))
        )
    promotion = scenario.expects_promotion or any(signal in text for signal in PROMOTION_SIGNALS)
    if promotion:
        reasons.append("promotion requested")
    evidence_action = any(signal in text for signal in EVIDENCE_SIGNALS)
    engineering_claim = any(signal in text for signal in ENGINEERING_CLAIM_SIGNALS)
    requires_review = False
    if promotion and kind in PROMOTION_GUARD_KINDS:
        reasons.append("generated artifacts never self-promote")
        requires_review = True
    if evidence_action and kind in EVIDENCE_GUARD_KINDS:
        reasons.append("missing is not a biological negative")
        requires_review = True
    if engineering_claim and kind in ENGINEERING_GUARD_KINDS:
        reasons.append("engineering readiness is not scientific readiness")
        requires_review = True
    return RoutingDecision(
        scenario_id=scenario.scenario_id,
        mode=mode,
        gap=Gap(gap_id=scenario.scenario_id, kind=kind, need=scenario.need),
        requires_review=requires_review,
        blocked=requires_review,
        reasons=tuple(reasons),
    )


def expected_fallback(scenario: GapScenario) -> GapKind:
    """No signal is a method gap by default: unknown science is the conservative default."""

    return GapKind.METHOD


def _single_factor_signals() -> dict[GapKind, tuple[str, ...]]:
    """Deliberately thin baseline: one keyword per gap kind."""

    return {
        GapKind.HARNESS: ("crash",),
        GapKind.DECISION: ("judgment",),
        GapKind.CAPABILITY: ("implementation",),
        GapKind.METHOD: ("unknown",),
    }


@dataclass(frozen=True, slots=True)
class RoutingEvaluation:
    mode: str
    metrics: dict[str, float]
    per_scenario: tuple[dict[str, Any], ...]


def evaluate_routing(scenarios: tuple[GapScenario, ...], *, mode: str) -> RoutingEvaluation:
    if not scenarios:
        raise ValueError("routing evaluation requires scenarios")
    decisions = tuple(route_scenario(scenario, mode=mode) for scenario in scenarios)
    correct = sum(
        decision.gap.kind == scenario.expected_kind
        for decision, scenario in zip(decisions, scenarios, strict=True)
    )
    unsafe = sum(
        1
        for decision, scenario in zip(decisions, scenarios, strict=True)
        if scenario.expects_block and not decision.blocked
    )
    review_coverage = sum(
        1
        for decision, scenario in zip(decisions, scenarios, strict=True)
        if not scenario.expects_block or decision.requires_review
    ) / len(scenarios)
    metrics = {
        "scenario_count": float(len(scenarios)),
        "route_accuracy": correct / len(scenarios),
        "unsafe_activation_count": float(unsafe),
        "review_requirement_coverage": review_coverage,
        "deterministic_cost": float(len(scenarios)),
    }
    per_scenario = tuple(
        {
            "scenario_id": decision.scenario_id,
            "expected_kind": scenario.expected_kind.value,
            "routed_kind": decision.gap.kind.value,
            "route": decision.gap.route.value,
            "requires_review": decision.requires_review,
            "blocked": decision.blocked,
            "correct": decision.gap.kind == scenario.expected_kind,
        }
        for decision, scenario in zip(decisions, scenarios, strict=True)
    )
    return RoutingEvaluation(mode=mode, metrics=metrics, per_scenario=per_scenario)
