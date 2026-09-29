from experiments.catalog import EXPERIMENTS
from oncolab.experiments import ExperimentClass


def test_only_two_experiment_classes_exist() -> None:
    assert set(ExperimentClass) == {ExperimentClass.ARCHITECTURE, ExperimentClass.SCIENTIFIC}


def test_initial_catalog_is_stable_and_unique() -> None:
    ids = [e.experiment_id for e in EXPERIMENTS]
    assert ids == [f"A{i:03d}" for i in range(1, 21)]
    assert len(ids) == len(set(ids))
    assert all(e.experiment_class is ExperimentClass.ARCHITECTURE for e in EXPERIMENTS)


def test_every_architecture_experiment_has_a_complete_frozen_protocol() -> None:
    assert {e.experiment_id: e.validation_errors() for e in EXPERIMENTS} == {
        e.experiment_id: () for e in EXPERIMENTS
    }
    assert [e.experiment_id for e in EXPERIMENTS if e.executable] == [
        "A001",
        "A002",
        "A003",
        "A004",
        "A005",
        "A006",
        "A007",
        "A008",
        "A009",
        "A010",
        "A011",
        "A012",
        "A013",
        "A014",
        "A015",
        "A016",
        "A017",
        "A018",
        "A019",
        "A020",
    ]
