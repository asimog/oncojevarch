from evidence.models import (
    Coverage,
    EntityLevel,
    Missingness,
    PopulationSpec,
    Provenance,
    ScientificEvidence,
)
from evidence.projections import build_projection


def _evidence() -> ScientificEvidence:
    return ScientificEvidence(
        evidence_id="e1",
        population=PopulationSpec("p1", "demo", EntityLevel.CASE, 10),
        measurement="effect",
        value=0.2,
        uncertainty={"ci": [0.1, 0.3]},
        coverage=Coverage(10, 10, 10),
        missingness=Missingness(),
        provenance=Provenance("source", "1", "method", "1", "git:abc"),
        metadata={"irrelevant": "x"},
    )


def test_projection_fingerprint_is_reproducible() -> None:
    def projector(es: tuple[ScientificEvidence, ...]) -> dict[str, object]:
        return {"value": es[0].value, "uncertainty": es[0].uncertainty}

    first = build_projection(
        projection_id="p", version="1", question_id="q", evidence=[_evidence()], projector=projector
    )
    second = build_projection(
        projection_id="p", version="1", question_id="q", evidence=[_evidence()], projector=projector
    )
    assert first.fingerprint == second.fingerprint


def test_projection_does_not_implicitly_include_unselected_metadata() -> None:
    projection = build_projection(
        projection_id="p",
        version="1",
        question_id="q",
        evidence=[_evidence()],
        projector=lambda es: {"value": es[0].value},
    )
    assert "irrelevant" not in projection.payload
