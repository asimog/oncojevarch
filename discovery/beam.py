from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BranchEdge:
    label: str
    probability: float


@dataclass(frozen=True, slots=True)
class ReplayTree:
    trace_id: str
    edges_by_path: dict[tuple[str, ...], tuple[BranchEdge, ...]]


@dataclass(frozen=True, slots=True)
class PathOutcome:
    path: tuple[str, ...]
    score: float


@dataclass(frozen=True, slots=True)
class BeamSearchResult:
    trace_id: str
    width: int
    selected_path: tuple[str, ...]
    selected_score: float
    final_beam: tuple[PathOutcome, ...]
    expanded_nodes: int
    evaluated_edges: int
    root_branch_diversity: int


@dataclass(frozen=True, slots=True)
class _PathState:
    path: tuple[str, ...]
    log_probability: float
    decisions: int

    @property
    def score(self) -> float:
        if self.decisions == 0:
            return 1.0
        return math.exp(self.log_probability / self.decisions)


def _validated_edges(tree: ReplayTree, path: tuple[str, ...]) -> tuple[BranchEdge, ...]:
    edges = tree.edges_by_path.get(path, ())
    if not edges:
        return ()
    labels = [edge.label for edge in edges]
    if len(labels) != len(set(labels)):
        raise ValueError(f"duplicate edge label at path {path}")
    if any(edge.probability <= 0.0 or edge.probability > 1.0 for edge in edges):
        raise ValueError(f"edge probabilities must be within (0, 1] at path {path}")
    if not math.isclose(sum(edge.probability for edge in edges), 1.0, abs_tol=1e-9):
        raise ValueError(f"edge probabilities must sum to 1 at path {path}")
    return edges


def beam_search(tree: ReplayTree, *, width: int) -> BeamSearchResult:
    """Replay a finite probability tree with a length-normalized bounded beam."""

    if width < 1:
        raise ValueError("beam width must be positive")
    if () not in tree.edges_by_path:
        raise ValueError("replay tree requires a root menu")

    beam: tuple[_PathState, ...] = (_PathState((), 0.0, 0),)
    expanded_nodes = 0
    evaluated_edges = 0
    max_steps = max((len(path) for path in tree.edges_by_path), default=0) + 1

    for _ in range(max_steps):
        candidates: list[_PathState] = []
        expanded_any = False
        for state in beam:
            edges = _validated_edges(tree, state.path)
            if not edges:
                candidates.append(state)
                continue
            expanded_any = True
            expanded_nodes += 1
            evaluated_edges += len(edges)
            candidates.extend(
                _PathState(
                    path=(*state.path, edge.label),
                    log_probability=state.log_probability + math.log(edge.probability),
                    decisions=state.decisions + 1,
                )
                for edge in edges
            )
        if not candidates:
            raise ValueError("replay tree produced no candidate paths")
        beam = tuple(sorted(candidates, key=lambda state: (-state.score, state.path))[:width])
        if not expanded_any:
            break

    final_beam = tuple(PathOutcome(state.path, state.score) for state in beam)
    selected = final_beam[0]
    return BeamSearchResult(
        trace_id=tree.trace_id,
        width=width,
        selected_path=selected.path,
        selected_score=selected.score,
        final_beam=final_beam,
        expanded_nodes=expanded_nodes,
        evaluated_edges=evaluated_edges,
        root_branch_diversity=len({outcome.path[0] for outcome in final_beam}),
    )
