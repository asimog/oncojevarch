from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from typing import Any

from execution.gdc import GdcClient
from experiments.scientific.catalog import get_scientific_experiment
from experiments.scientific.s001_public_metadata_association import (
    ITERATIONS,
    SEED,
    AssayCoavailabilityCapability,
)
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_scientific_experiment("S004")
T1_EVENT = "s004_t1_frozen"
T2_MIN_AGE_HOURS = 24
MIN_PROJECTS = 30
PREDICTION = (
    "The GDC TCGA co-availability rate stays equal to the T1 value at T2, and any TCGA project "
    "newly listed between T1 and T2 is co-available (has both RNA-Seq and WXS files)."
)


def _fetch_rate() -> dict[str, Any]:
    capability = AssayCoavailabilityCapability(client=GdcClient(), min_projects=MIN_PROJECTS)
    measured = capability.execute(operation_id="op-s004-t2", inputs={})
    return {
        "rate": float(measured.measurements["max_site_share"]),
        "projects_total": int(measured.measurements["projects_total"]),
        "co_available_projects": int(measured.measurements["co_available_projects"]),
        "source_version": str(measured.provenance.get("source_version", "unknown")),
    }


def _latest_t1(store: AppendOnlyJsonlStore) -> dict[str, Any] | None:
    found: dict[str, Any] | None = None
    for event in store.read_all():
        if event.event_type == T1_EVENT:
            found = event.payload
    return found


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    now = datetime.now(UTC)

    t1 = _latest_t1(store)
    if t1 is None:
        if not live:
            result = ExperimentResult(
                experiment_id=SPEC.experiment_id,
                experiment_class=SPEC.experiment_class,
                status=ExperimentStatus.FROZEN,
                frozen_fingerprint=frozen.fingerprint,
                measurements={
                    "live": False,
                    "preflight": (
                        "T1 shadow protocol frozen; run with --live to freeze the T1 state"
                    ),
                    "prediction": PREDICTION,
                    "t2_min_age_hours": T2_MIN_AGE_HOURS,
                },
                observations=("The L4 shadow protocol awaits its T1 freeze.",),
                limitations=("Preflight records no scientific evidence by design.",),
            )
            store.append("scientific_experiment_result", asdict(result))
            return json.dumps(asdict(result), indent=2, default=str)
        snapshot = _fetch_rate()
        t1 = {
            "t1_frozen_at": now.isoformat(),
            "t1_cutoff": now.date().isoformat(),
            "t2_due_at": (now + timedelta(hours=T2_MIN_AGE_HOURS)).isoformat(),
            "prediction": PREDICTION,
            "t1_rate": snapshot["rate"],
            "t1_projects_total": snapshot["projects_total"],
            "t1_co_available_projects": snapshot["co_available_projects"],
            "t1_source_version": snapshot["source_version"],
            "seed": SEED,
            "iterations": ITERATIONS,
        }
        store.append(T1_EVENT, t1)

    due_at = datetime.fromisoformat(str(t1["t2_due_at"]))
    measurements: dict[str, Any] = {
        "live": True,
        "t1": t1,
        "t2_due_at": t1["t2_due_at"],
        "now": now.isoformat(),
    }
    if now < due_at:
        measurements["t2_status"] = "pending"
        measurements["reason"] = (
            "T2 requires genuinely later information; the frozen shadow becomes evaluable at "
            "the due time"
        )
        status = ExperimentStatus.FROZEN
        observations: tuple[str, ...] = (
            "T1 decision state is frozen with explicit cutoffs and criteria; T2 evaluation is "
            "scheduled, not simulated.",
        )
    else:
        snapshot = _fetch_rate()
        new_projects = snapshot["projects_total"] - int(t1["t1_projects_total"])
        rate_equal = snapshot["rate"] == float(t1["t1_rate"])
        new_co_available = (
            snapshot["co_available_projects"] - int(t1["t1_co_available_projects"])
            >= new_projects
        )
        outcome = (
            "prediction_supported" if rate_equal and new_co_available else "prediction_falsified"
        )
        measurements.update(
            {
                "t2_status": "evaluated",
                "t2": snapshot,
                "new_projects": new_projects,
                "rate_equal": rate_equal,
                "new_projects_co_available": new_co_available,
                "outcome": outcome,
            }
        )
        status = ExperimentStatus.COMPLETED
        observations = (f"T2 evaluation: {outcome}.",)
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=status,
        frozen_fingerprint=frozen.fingerprint,
        measurements=measurements,
        observations=observations,
        limitations=(
            "T1/T2 cutoffs derive from wall-clock time; the T2 snapshot must be taken after the "
            "due time for the evaluation to be temporal rather than contemporaneous.",
            "The prediction concerns public metadata structure only.",
        ),
    )
    store.append("scientific_experiment_result", asdict(result))
    return json.dumps(asdict(result), indent=2, default=str)
