from evidence.projections import SemanticProjection
from jev.contracts import JevAnswer, JevDecision, JevPrimitive
from research.models import Hypothesis


def test_jev_decision_is_not_scientific_evidence() -> None:
    decision = JevDecision(
        capability_id="c",
        capability_version="1",
        projection_fingerprint="fp",
        model_id="jev",
        answers=(JevAnswer("q", JevPrimitive.NOUL, 0.9),),
    )
    assert not hasattr(decision, "measurement")
    assert not hasattr(decision, "population")


def test_hypothesis_references_evidence_without_becoming_evidence() -> None:
    hypothesis = Hypothesis("h", "i", "possible mechanism", supporting_evidence_ids=("e1",))
    assert hypothesis.supporting_evidence_ids == ("e1",)
    assert not hasattr(hypothesis, "measurement")


def test_projection_carries_source_evidence_identity() -> None:
    projection = SemanticProjection("p", "1", "q", ("e1",), {"x": 1}, "fp")
    assert projection.source_evidence_ids == ("e1",)
