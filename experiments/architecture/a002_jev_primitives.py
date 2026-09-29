from __future__ import annotations

from dataclasses import asdict

from evidence.projections import SemanticProjection
from experiments.catalog import get_experiment
from jev.contracts import JevCapability, JevPrimitive, JevQuestion
from jev.fake import FakeJevClient
from jev.typesafe_adapter import TypeSafeJevClient
from oncodex.config import Settings
from oncolab.experiments import (
    ExperimentResult,
    ExperimentStatus,
    FrozenExperiment,
)
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A002")

CAPABILITY = JevCapability(
    capability_id="a002-demo-semantics",
    version="0.1.0",
    domain_owner="evaluation",
    semantic_purpose=(
        "Exercise Choice, Noul, and Score mechanics; not a validated cancer capability."
    ),
    projection_id="a002-demo",
    projection_version="1",
    questions=(
        JevQuestion(
            question_id="route",
            primitive=JevPrimitive.CHOICE,
            instructions="Which bounded follow-up class best matches this demo state?",
            criteria={
                "replicate": "replication is the clearest next bounded class",
                "inspect": "more inspection is needed",
                "stop": "no follow-up is justified",
            },
        ),
        JevQuestion(
            question_id="contradiction",
            primitive=JevPrimitive.NOUL,
            instructions=(
                "Does this demo state contain a material contradiction between the two "
                "stated observations?"
            ),
            criteria={
                "true": "the observations materially conflict",
                "false": "they do not materially conflict",
            },
        ),
        JevQuestion(
            question_id="concern",
            primitive=JevPrimitive.SCORE,
            instructions="How strong is the semantic concern in this demo state?",
            criteria=["none", "weak", "moderate", "strong", "dominant"],
        ),
    ),
)

PROJECTION = SemanticProjection(
    projection_id="a002-demo",
    version="1",
    question_id="primitive-semantics",
    source_evidence_ids=("demo-e1", "demo-e2"),
    payload={
        "notice": "synthetic architecture-only state",
        "observation_a": "signal is present in subgroup A",
        "observation_b": "independent replay did not reproduce the signal",
        "coverage": {"discovery": 100, "replay": 95},
    },
    fingerprint="a002-static-demo",
)


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    client = (
        TypeSafeJevClient(
            api_key=settings.typesafe_api_key,
            model=settings.jev_model,
        )
        if live
        else FakeJevClient({"route": "replicate", "contradiction": 0.82, "concern": 3})
    )
    try:
        decision = client.evaluate(PROJECTION, CAPABILITY)
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.COMPLETED,
            frozen_fingerprint=frozen.fingerprint,
            measurements={"decision": asdict(decision), "live": live},
            limitations=(
                "The bundled state is synthetic and cannot validate cancer-domain Jev behavior.",
                "Live TypeSafe results require a separately designed labeled evaluation "
                "set before promotion.",
            ),
        )
    except Exception as exc:
        result = ExperimentResult(
            experiment_id=SPEC.experiment_id,
            experiment_class=SPEC.experiment_class,
            status=ExperimentStatus.FAILED,
            frozen_fingerprint=frozen.fingerprint,
            measurements={"error": f"{type(exc).__name__}: {exc}", "live": live},
            limitations=("External failure does not establish semantic capability performance.",),
        )
    AppendOnlyJsonlStore(settings.store_dir / "events.jsonl").append(
        "architecture_experiment_result", asdict(result)
    )
    return str(asdict(result))
