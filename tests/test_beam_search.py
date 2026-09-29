import pytest

from discovery.beam import BranchEdge, ReplayTree, beam_search


def test_beam_recovers_branch_lost_by_greedy_search() -> None:
    tree = ReplayTree(
        trace_id="early-error",
        edges_by_path={
            (): (BranchEdge("local", 0.55), BranchEdge("recoverable", 0.45)),
            ("local",): (BranchEdge("wrong", 0.55), BranchEdge("also-wrong", 0.45)),
            ("recoverable",): (BranchEdge("target", 0.99), BranchEdge("other", 0.01)),
        },
    )

    assert beam_search(tree, width=1).selected_path == ("local", "wrong")
    recovered = beam_search(tree, width=2)
    assert recovered.selected_path == ("recoverable", "target")
    assert recovered.evaluated_edges == 6


def test_beam_rejects_non_distribution_edge_probabilities() -> None:
    tree = ReplayTree(
        trace_id="invalid",
        edges_by_path={(): (BranchEdge("a", 0.8), BranchEdge("b", 0.8))},
    )

    with pytest.raises(ValueError, match="sum to 1"):
        beam_search(tree, width=2)
