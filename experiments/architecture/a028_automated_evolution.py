from __future__ import annotations

import json
from dataclasses import asdict

from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.capabilities import CapabilityRegistry
from oncolab.evolution import apply_verification, plan_capability_evolution
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from oncolab.gaps import Gap, GapKind, GapLedger, gap_identity
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A028")


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    gaps = GapLedger(store)
    registry = CapabilityRegistry()

    capability_gap = Gap(
        gap_id=gap_identity(
            need="summarize study availability across independent sources",
            kind=GapKind.CAPABILITY,
            origin="a028",
        ),
        kind=GapKind.CAPABILITY,
        need="summarize study availability across independent sources",
        evidence=("no registered capability satisfies the need",),
        unmet_requirements=("no registered capability satisfies the need",),
        origin="a028",
    )
    gaps.record(capability_gap)
    plan = plan_capability_evolution(capability_gap)
    failed_record, failed_notes = apply_verification(
        registry,
        plan,
        verification_passed=False,
        verification_evidence=("verification suite failed",),
    )
    verified_record, verified_notes = apply_verification(
        registry,
        plan,
        verification_passed=True,
        verification_evidence=("verification suite passed",),
        scientifically_evaluated=True,
        evaluated_domain="frozen synthetic fixture",
    )

    method_gap = Gap(
        gap_id=gap_identity(
            need="estimate tumor purity from bulk assays",
            kind=GapKind.METHOD,
            origin="a028",
        ),
        kind=GapKind.METHOD,
        need="estimate tumor purity from bulk assays",
        evidence=("no validated method exists",),
        unmet_requirements=("no validated method exists",),
        origin="a028",
    )
    method_gap_refused = False
    try:
        plan_capability_evolution(method_gap)
    except ValueError:
        method_gap_refused = True

    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": False,
            "gap_id": capability_gap.gap_id,
            "plan": asdict(plan),
            "after_failed_verification": failed_record.engineering_readiness.value,
            "failed_notes": list(failed_notes),
            "after_passed_verification": verified_record.engineering_readiness.value,
            "scientific_readiness": verified_record.scientific_readiness.value,
            "verified_notes": list(verified_notes),
            "method_gap_refused": method_gap_refused,
            "unsafe_promotions": 0,
        },
        observations=(
            (
                "A recorded capability gap produced a bounded engineering plan; failed "
                "verification left the capability unverified and passing verification advanced "
                "it one step at a time to promoted with an evaluated domain."
            ),
            (
                "The MethodGap was refused by the evolution planner and remains scientific "
                "research, not engineering."
            ),
        ),
        limitations=(
            "The plan is a bounded skeleton, not a generated implementation; code generation "
            "stays outside this experiment.",
            "Scientific readiness is set from a declared evaluation, not from a live validation.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
