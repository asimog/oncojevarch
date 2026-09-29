from __future__ import annotations

import json
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path

from experiments.catalog import get_experiment
from oncodex.config import Settings
from oncolab.experiments import ExperimentResult, ExperimentStatus, FrozenExperiment
from oncolab.proposals import (
    ChangeRequest,
    ProposalBounds,
    ProposalOutcome,
    claim_traceability,
    describe_outcome,
    evaluate_bounds,
    proposal_metrics,
    verify_in_scratch_copy,
)
from store.jsonl import AppendOnlyJsonlStore

SPEC = get_experiment("A018")
TARGET_PATH = "experiments/architecture/a012_jev_oncox_cascade.py"
EVIDENCE_RESULT = "A012"
EVIDENCE_FINDING = "bounded triage escalated every live case, so no OncoX calls were saved"
BOUNDS = ProposalBounds(max_changed_lines=40, max_files_touched=1)
FOCUSED_TESTS = ("tests/test_cascade.py",)
ORIGINAL_QUESTION_LINES = (
    '        f"Using only `cases.{case_id}`, judge whether open-ended deep scientific '
    'reasoning about "\n'
    '        "the candidate claim would add materially new scientific information beyond '
    'the recorded "\n'
    '        "structured evidence. Answer true only if the recorded checks leave a '
    'materially open "\n'
    '        "question for this claim, such as an unrecorded confounder, an undiscriminated '
    'alternative "\n'
    '        "explanation, or a decisive unmeasured quantity that could change how the '
    'claim is "\n'
    '        "evaluated. Answer false if the recorded checks already resolve the material '
    'question of "\n'
    '        "the claim, even when the state lists missing items. A listed missing item that '
    'cannot "\n'
    '        "change the evaluation of this claim is not material."\n'
)
REVISED_QUESTION_LINES = (
    '        f"Using only `cases.{case_id}`, judge whether the recorded structured evidence '
    'leaves a "\n'
    '        "material scientific question that open-ended reasoning could resolve beyond '
    'what is "\n'
    '        "already recorded. An unsupported claim is not by itself a material question, '
    'and a "\n'
    '        "missing item that cannot change how the claim is evaluated is not material. '
    'Answer "\n'
    '        "true only when such a materially open question remains."\n'
)


def _original_text(repo_root: Path) -> str:
    return (repo_root / TARGET_PATH).read_text(encoding="utf-8")


def _patched_text(original: str) -> str:
    if ORIGINAL_QUESTION_LINES not in original:
        raise ValueError("frozen A012 triage question text is not present in the target file")
    return original.replace(ORIGINAL_QUESTION_LINES, REVISED_QUESTION_LINES)


def _requests(repo_root: Path) -> tuple[ChangeRequest, ChangeRequest]:
    original = _original_text(repo_root)
    patched = _patched_text(original)
    bounded = ChangeRequest(
        request_id="bounded_triage_wording",
        summary=(
            "Record a revised A012 triage question as a new experiment input, with every claim "
            "traced to the recorded A012 result."
        ),
        target_path=TARGET_PATH,
        original_text=original,
        patched_text=patched,
        claims=(
            (
                "the A012 cascade saved no OncoX calls",
                EVIDENCE_FINDING,
            ),
            (
                "the triage question, not the adapter, caused the escalation behavior",
                "A012 structured output validated on every escalated call",
            ),
        ),
        extra_paths=(),
    )
    unbounded = ChangeRequest(
        request_id="unbounded_rewrite",
        summary=(
            "Rewrite the cascade, the rubric, and the thresholds together and add a new module."
        ),
        target_path=TARGET_PATH,
        original_text=original,
        patched_text=patched
        + "\n\nA012_TRIAGE_THRESHOLD = 0.35\nA012_QUALITY_MARGIN = 0.25\n"
        + "".join(f"\n# reviewer note {index}: relax the frozen margin\n" for index in range(40)),
        claims=(),
        extra_paths=("experiments/architecture/a012b_triage_v2.py",),
    )
    return bounded, unbounded


def _outcome(
    *,
    request: ChangeRequest,
    repo_root: Path,
    scratch_root: Path,
    verify: bool,
) -> ProposalOutcome:
    reasons = evaluate_bounds(request, BOUNDS)
    verification = None
    if not reasons and verify:
        verification = verify_in_scratch_copy(
            repo_root=repo_root,
            scratch_root=scratch_root / request.request_id,
            request=request,
            focused_test_paths=FOCUSED_TESTS,
        )
        if verification.findings:
            reasons = tuple(reasons) + tuple(verification.findings)
    return ProposalOutcome(
        request_id=request.request_id,
        accepted_for_review=not reasons,
        rejection_reasons=reasons,
        bounds=BOUNDS,
        changed_lines=request.changed_lines(),
        files_touched=1 + len(request.extra_paths),
        claim_traceability=claim_traceability(request),
        verification=verification,
        diff=request.unified_diff(),
    )


def run(*, settings: Settings, live: bool = False) -> str:
    frozen = FrozenExperiment.freeze(SPEC)
    store = AppendOnlyJsonlStore(settings.store_dir / "events.jsonl")
    repo_root = settings.repo_root
    scratch_root = settings.store_dir / "a018-scratch"
    bounded, unbounded = _requests(repo_root)
    outcomes = (
        _outcome(request=bounded, repo_root=repo_root, scratch_root=scratch_root, verify=True),
        _outcome(request=unbounded, repo_root=repo_root, scratch_root=scratch_root, verify=False),
    )
    metrics = proposal_metrics(outcomes)
    bounded_outcome = outcomes[0]
    accepted = bounded_outcome.accepted_for_review and not outcomes[1].accepted_for_review
    review_findings = (
        (
            "the wording change alters a frozen A012 input, so it is only a proposal for a new "
            "experiment identity and must never be applied to A012 itself",
            "the Codex workspace tool is read-only, so no agent path can apply this patch",
            "acceptance means ready for human review, not promotion",
        )
        if accepted
        else (
            "the bounded proposal failed verification or the unbounded proposal was not rejected",
        )
    )
    gaps = (
        {
            "gap_kind": "harness",
            "need": (
                "a write-capable, review-gated proposal path is missing: the Codex workspace tool "
                "is read-only, so proposals are compiled deterministically and verified in a "
                "scratch copy"
            ),
            "route": "harness_engineering",
        },
    )
    result = ExperimentResult(
        experiment_id=SPEC.experiment_id,
        experiment_class=SPEC.experiment_class,
        status=ExperimentStatus.COMPLETED,
        frozen_fingerprint=frozen.fingerprint,
        measurements={
            "live": live,
            "bounded_proposal_accepted_for_review": accepted,
            "evidence_result": EVIDENCE_RESULT,
            "evidence_finding": EVIDENCE_FINDING,
            "metrics": metrics,
            "outcomes": [describe_outcome(outcome) for outcome in outcomes],
            "diffs": {outcome.request_id: outcome.diff for outcome in outcomes},
            "review_findings": list(review_findings),
            "gap_classification": list(gaps),
            "self_promotion": False,
            "applied_to_repository": False,
            "protocol": {
                "bounds": asdict(BOUNDS),
                "focused_tests": list(FOCUSED_TESTS),
                "target_path": TARGET_PATH,
                "scratch_root": str(scratch_root),
                "change_request_fingerprint": sha256(
                    "".join(sorted(outcome.diff for outcome in outcomes)).encode("utf-8")
                ).hexdigest(),
            },
            "cost": {
                "measured": False,
                "basis": "deterministic proposal compilation plus a local scratch verification",
            },
        },
        observations=(
            (
                "A bounded, fully traced proposal passed compilation, focused tests, and "
                "architecture checks in a scratch copy and is recorded for human review only; "
                "the unbounded request was rejected."
                if accepted
                else "No bounded proposal passed verification, so nothing is proposed."
            ),
        ),
        limitations=(
            "The proposal is compiled deterministically, not by an autonomous agent turn.",
            "Verification runs in a scratch copy; the main worktree is never modified.",
            "The change itself is gated on a new experiment identity, because A012 is frozen.",
            "An accepted proposal is a review input, not a promotion.",
        ),
    )
    store.append("architecture_experiment_result", asdict(result))
    if not live:
        return json.dumps(_bounded_view(result), indent=2, default=str)
    return json.dumps(_bounded_view(result), indent=2, default=str)


def _bounded_view(result: ExperimentResult) -> dict[str, object]:
    measurements = dict(result.measurements)
    return {
        "experiment_id": result.experiment_id,
        "status": result.status,
        "bounded_proposal_accepted_for_review": measurements[
            "bounded_proposal_accepted_for_review"
        ],
        "evidence": {
            "result": measurements["evidence_result"],
            "finding": measurements["evidence_finding"],
        },
        "metrics": measurements["metrics"],
        "outcomes": measurements["outcomes"],
        "review_findings": measurements["review_findings"],
        "gap_classification": measurements["gap_classification"],
        "applied_to_repository": measurements["applied_to_repository"],
        "observations": result.observations,
        "limitations": result.limitations,
    }
