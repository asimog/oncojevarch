from pathlib import Path

import pytest

from experiments.architecture.a018_bounded_change_proposal import _outcome, _requests
from oncolab.proposals import (
    ChangeRequest,
    ProposalBounds,
    claim_traceability,
    evaluate_bounds,
    proposal_metrics,
)


def _request(*, patched: str, claims: tuple[tuple[str, str], ...] = (("c", "e"),)) -> ChangeRequest:
    return ChangeRequest(
        request_id="r1",
        summary="bounded change",
        target_path="a.py",
        original_text="line one\nline two\n",
        patched_text=patched,
        claims=claims,
    )


def test_changed_lines_counts_only_additions_and_removals() -> None:
    request = _request(patched="line one\nline two changed\n")

    assert request.changed_lines() == 2
    assert "-line two" in request.unified_diff()
    assert "+line two changed" in request.unified_diff()


def test_bounds_reject_oversized_multi_file_and_untraced_requests() -> None:
    oversized = ChangeRequest(
        request_id="r2",
        summary="too big",
        target_path="a.py",
        original_text="x\n",
        patched_text="x\n" + "".join(f"extra {index}\n" for index in range(60)),
        claims=(("claim", "evidence"),),
    )
    untraced = _request(patched="line one\n", claims=())
    multi = ChangeRequest(
        request_id="r3",
        summary="multi",
        target_path="a.py",
        original_text="x\n",
        patched_text="y\n",
        claims=(("claim", "evidence"),),
        extra_paths=("new_module.py",),
    )
    bounds = ProposalBounds(max_changed_lines=40, max_files_touched=1)

    assert any("changed lines" in reason for reason in evaluate_bounds(oversized, bounds))
    assert any("no claim" in reason for reason in evaluate_bounds(untraced, bounds))
    assert any("files touched" in reason for reason in evaluate_bounds(multi, bounds))
    assert evaluate_bounds(_request(patched="line one\n"), bounds) == ()


def test_claim_traceability_requires_evidence_for_every_claim() -> None:
    traced = _request(patched="line one\n", claims=(("a", "e1"), ("b", "e2")))
    half = _request(patched="line one\n", claims=(("a", "e1"), ("b", " ")))

    assert claim_traceability(traced) == 1.0
    assert claim_traceability(half) == 0.5
    assert claim_traceability(_request(patched="line one\n", claims=())) == 0.0


def test_proposal_metrics_require_at_least_one_proposal() -> None:
    with pytest.raises(ValueError, match="at least one proposal"):
        proposal_metrics(())


def test_verification_runs_in_a_scratch_copy_and_leaves_the_repository_untouched() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    scratch_root = repo_root / ".oncojev" / "a018-test-scratch"
    bounded, _unbounded = _requests(repo_root)
    before = (repo_root / bounded.target_path).read_text(encoding="utf-8")

    outcome = _outcome(
        request=bounded,
        repo_root=repo_root,
        scratch_root=scratch_root,
        verify=True,
    )

    assert outcome.verification is not None
    assert outcome.verification.compiled
    assert outcome.verification.focused_tests_passed
    assert outcome.verification.architecture_checks_passed
    assert (repo_root / bounded.target_path).read_text(encoding="utf-8") == before
    assert outcome.accepted_for_review
