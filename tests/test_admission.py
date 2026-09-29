from evidence.models import Coverage, EntityLevel, Missingness, PopulationSpec, Provenance
from execution.ports import MeasuredResult
from oncolab.admission import AdmissionContext, AdmissionRefusalReason, admit_measured_result

POPULATION = PopulationSpec(
    population_id="pop-1",
    definition="frozen test population",
    entity_level=EntityLevel.OTHER,
)
CONTEXT = AdmissionContext(
    evidence_id="ev-1",
    measurement="mean_value",
    population=POPULATION,
    coverage=Coverage(requested=2, retrieved=2),
    missingness=Missingness(),
    provenance=Provenance(
        source="fixture",
        source_version="1",
        method_id="method-1",
        method_version="1",
        code_identity="module:abc",
    ),
)


def _result(**overrides: object) -> MeasuredResult:
    fields: dict[str, object] = {
        "operation_id": "op-1",
        "method_id": "method-1",
        "population_id": "pop-1",
        "measurements": {"mean_value": 4.0},
        "provenance": {"source": "fixture"},
    }
    fields.update(overrides)
    return MeasuredResult(**fields)  # type: ignore[arg-type]


def test_admission_builds_typed_evidence() -> None:
    admitted = admit_measured_result(_result(), context=CONTEXT)

    assert admitted.admitted is True
    evidence = admitted.evidence
    assert evidence is not None
    assert evidence.evidence_id == "ev-1"
    assert evidence.value == 4.0
    assert evidence.population is POPULATION
    assert admitted.refusal is None


def test_missing_value_is_refused_not_zero() -> None:
    refused = admit_measured_result(_result(measurements={"mean_value": None}), context=CONTEXT)

    assert refused.admitted is False
    assert refused.evidence is None
    assert refused.refusal is not None
    assert refused.refusal.reasons == (AdmissionRefusalReason.UNREPRESENTABLE_VALUE,)


def test_population_mismatch_and_missing_provenance_are_refused() -> None:
    refused = admit_measured_result(
        _result(population_id="other-population", provenance={}),
        context=CONTEXT,
    )

    assert refused.refusal is not None
    assert set(refused.refusal.reasons) == {
        AdmissionRefusalReason.POPULATION_MISMATCH,
        AdmissionRefusalReason.MISSING_PROVENANCE,
    }


def test_missing_measurement_and_method_are_refused() -> None:
    refused = admit_measured_result(
        _result(method_id="  ", measurements={"other": 1.0}),
        context=CONTEXT,
    )

    assert refused.refusal is not None
    assert set(refused.refusal.reasons) == {
        AdmissionRefusalReason.MISSING_METHOD,
        AdmissionRefusalReason.MISSING_MEASUREMENT,
    }
