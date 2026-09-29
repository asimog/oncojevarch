from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RankingMetrics:
    query_count: int
    recall_at_1: float
    recall_at_k: float
    precision_at_1: float
    mean_reciprocal_rank: float


def evaluate_rankings(
    *, expected: dict[str, str], rankings: dict[str, tuple[str, ...]], k: int
) -> RankingMetrics:
    if not expected:
        raise ValueError("ranking evaluation requires at least one query")
    if k < 1:
        raise ValueError("k must be positive")
    if set(rankings) != set(expected):
        raise ValueError("rankings do not match the frozen query set")

    reciprocal_rank = 0.0
    hits_at_1 = 0
    hits_at_k = 0
    for query_id, relevant in expected.items():
        ranking = rankings[query_id]
        if not ranking:
            raise ValueError(f"ranking is empty for {query_id}")
        if len(ranking) != len(set(ranking)):
            raise ValueError(f"ranking contains duplicate candidates for {query_id}")
        if relevant in ranking:
            rank = ranking.index(relevant) + 1
            reciprocal_rank += 1.0 / rank
            hits_at_1 += int(rank == 1)
            hits_at_k += int(rank <= k)

    count = len(expected)
    return RankingMetrics(
        query_count=count,
        recall_at_1=hits_at_1 / count,
        recall_at_k=hits_at_k / count,
        precision_at_1=hits_at_1 / count,
        mean_reciprocal_rank=reciprocal_rank / count,
    )


def promote_choice(shortlist: tuple[str, ...], choice: str) -> tuple[str, ...]:
    """Move one valid semantic choice to rank one without changing membership."""

    if choice not in shortlist:
        raise ValueError(f"reranker selected candidate outside shortlist: {choice}")
    return (choice, *(candidate for candidate in shortlist if candidate != choice))
