from evidence.projections import SemanticProjection
from jev.contracts import JevAnswer, JevDecision, JevPrimitive
from oncox.ports import ReasoningOutput, ReasoningResult
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


def test_reasoning_output_is_not_scientific_evidence() -> None:
    output = ReasoningOutput(
        interpretation="the comparison is confounded",
        hypotheses=("purity could explain the difference",),
        alternative_explanations=("assay mix differs",),
        proposed_tests=("measure purity per case",),
        unresolved_uncertainty=("purity is unmeasured",),
    )
    result = ReasoningResult(output=output, model_id="oncox")

    for candidate in (output, result):
        assert not hasattr(candidate, "measurement")
        assert not hasattr(candidate, "population")
        assert not hasattr(candidate, "provenance")


def test_hypothesis_references_evidence_without_becoming_evidence() -> None:
    hypothesis = Hypothesis("h", "i", "possible mechanism", supporting_evidence_ids=("e1",))
    assert hypothesis.supporting_evidence_ids == ("e1",)
    assert not hasattr(hypothesis, "measurement")


def test_projection_carries_source_evidence_identity() -> None:
    projection = SemanticProjection("p", "1", "q", ("e1",), {"x": 1}, "fp")
    assert projection.source_evidence_ids == ("e1",)
