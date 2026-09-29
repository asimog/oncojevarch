from __future__ import annotations

from dataclasses import dataclass

from discovery.beam import BeamSearchResult


@dataclass(frozen=True, slots=True)
class SearchPolicyMetrics:
    width: int
    trace_count: int
    terminal_recall: float
    mean_expanded_nodes: float
    mean_evaluated_edges: float
    mean_root_branch_diversity: float


def evaluate_search_policy(
    *, expected: dict[str, tuple[str, ...]], results: tuple[BeamSearchResult, ...]
) -> SearchPolicyMetrics:
    if not expected:
        raise ValueError("search evaluation requires at least one trace")
    by_trace = {result.trace_id: result for result in results}
    if len(by_trace) != len(results) or set(by_trace) != set(expected):
        raise ValueError("search results do not match the frozen trace set")
    widths = {result.width for result in results}
    if len(widths) != 1:
        raise ValueError("one policy evaluation must use one beam width")

    count = len(expected)
    hits = sum(
        by_trace[trace_id].selected_path == terminal for trace_id, terminal in expected.items()
    )
    return SearchPolicyMetrics(
        width=next(iter(widths)),
        trace_count=count,
        terminal_recall=hits / count,
        mean_expanded_nodes=sum(result.expanded_nodes for result in results) / count,
        mean_evaluated_edges=sum(result.evaluated_edges for result in results) / count,
        mean_root_branch_diversity=(
            sum(result.root_branch_diversity for result in results) / count
        ),
    )
