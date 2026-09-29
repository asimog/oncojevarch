from __future__ import annotations

import difflib
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from time import perf_counter
from typing import Any

IGNORED_DIRECTORIES = (
    ".git",
    ".venv",
    ".oncojev",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "node_modules",
)


@dataclass(frozen=True, slots=True)
class ChangeRequest:
    request_id: str
    summary: str
    target_path: str
    patched_text: str
    original_text: str
    claims: tuple[tuple[str, str], ...] = ()
    extra_paths: tuple[str, ...] = ()

    def unified_diff(self) -> str:
        return "".join(
            difflib.unified_diff(
                self.original_text.splitlines(keepends=True),
                self.patched_text.splitlines(keepends=True),
                fromfile=f"a/{self.target_path}",
                tofile=f"b/{self.target_path}",
            )
        )

    def changed_lines(self) -> int:
        return sum(
            1
            for line in self.unified_diff().splitlines()
            if line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
        )


@dataclass(frozen=True, slots=True)
class ProposalBounds:
    max_changed_lines: int = 40
    max_files_touched: int = 1
    require_claim_traceability: bool = True


@dataclass(frozen=True, slots=True)
class VerificationReport:
    applied: bool
    compiled: bool
    focused_tests_passed: bool
    architecture_checks_passed: bool
    duration_ms: float
    commands: tuple[str, ...] = ()
    findings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ProposalOutcome:
    request_id: str
    accepted_for_review: bool
    rejection_reasons: tuple[str, ...]
    bounds: ProposalBounds
    changed_lines: int
    files_touched: int
    claim_traceability: float
    verification: VerificationReport | None
    diff: str


def evaluate_bounds(request: ChangeRequest, bounds: ProposalBounds) -> tuple[str, ...]:
    reasons: list[str] = []
    if request.changed_lines() > bounds.max_changed_lines:
        reasons.append(
            f"changed lines {request.changed_lines()} exceed the bound {bounds.max_changed_lines}"
        )
    files_touched = 1 + len(request.extra_paths)
    if files_touched > bounds.max_files_touched:
        reasons.append(f"files touched {files_touched} exceed the bound {bounds.max_files_touched}")
    if bounds.require_claim_traceability and not request.claims:
        reasons.append("no claim is traced to recorded evidence")
    if not request.patched_text.strip():
        reasons.append("proposed change is empty")
    return tuple(reasons)


def claim_traceability(request: ChangeRequest) -> float:
    if not request.claims:
        return 0.0
    traced = sum(1 for _, evidence in request.claims if evidence.strip())
    return traced / len(request.claims)


def _copy_baseline(repo_root: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(
        repo_root,
        destination,
        ignore=shutil.ignore_patterns(*IGNORED_DIRECTORIES),
    )


def verify_in_scratch_copy(
    *,
    repo_root: Path,
    scratch_root: Path,
    request: ChangeRequest,
    focused_test_paths: tuple[str, ...],
) -> VerificationReport:
    """Apply the proposal to a scratch copy of the repository and run the frozen checks there."""

    _copy_baseline(repo_root, scratch_root)
    target = scratch_root / request.target_path
    if not target.exists():
        return VerificationReport(
            applied=False,
            compiled=False,
            focused_tests_passed=False,
            architecture_checks_passed=False,
            duration_ms=0.0,
            findings=(f"target path does not exist: {request.target_path}",),
        )
    target.write_text(request.patched_text, encoding="utf-8")
    started = perf_counter()
    commands: list[str] = []
    findings: list[str] = []

    compile_command = [sys.executable, "-m", "compileall", "-q", str(target)]
    commands.append(" ".join(compile_command))
    compile_result = subprocess.run(
        compile_command, cwd=scratch_root, capture_output=True, text=True, check=False
    )
    if compile_result.returncode != 0:
        findings.append(f"compileall failed: {compile_result.stdout}{compile_result.stderr}")

    test_command = [sys.executable, "-m", "pytest", *focused_test_paths, "-q"]
    commands.append(" ".join(test_command))
    test_result = subprocess.run(
        test_command, cwd=scratch_root, capture_output=True, text=True, check=False
    )
    if test_result.returncode != 0:
        findings.append(f"focused tests failed: {test_result.stdout[-500:]}")

    architecture_command = [sys.executable, "scripts/check_architecture.py"]
    commands.append(" ".join(architecture_command))
    architecture_result = subprocess.run(
        architecture_command, cwd=scratch_root, capture_output=True, text=True, check=False
    )
    if architecture_result.returncode != 0:
        findings.append(
            f"architecture checks failed: {architecture_result.stdout}{architecture_result.stderr}"
        )

    return VerificationReport(
        applied=True,
        compiled=compile_result.returncode == 0,
        focused_tests_passed=test_result.returncode == 0,
        architecture_checks_passed=architecture_result.returncode == 0,
        duration_ms=(perf_counter() - started) * 1000,
        commands=tuple(commands),
        findings=tuple(findings),
    )


def proposal_metrics(outcomes: tuple[ProposalOutcome, ...]) -> dict[str, float]:
    if not outcomes:
        raise ValueError("proposal evaluation requires at least one proposal")
    accepted = [outcome for outcome in outcomes if outcome.accepted_for_review]
    verified = [outcome.verification for outcome in outcomes if outcome.verification is not None]
    return {
        "proposal_count": float(len(outcomes)),
        "accepted_for_review_count": float(len(accepted)),
        "rejected_count": float(len(outcomes) - len(accepted)),
        "max_changed_lines": float(max(outcome.changed_lines for outcome in outcomes)),
        "verification_pass_rate": (
            sum(
                1
                for report in verified
                if report.compiled
                and report.focused_tests_passed
                and report.architecture_checks_passed
            )
            / len(verified)
            if verified
            else 0.0
        ),
        "claim_traceability": (
            sum(outcome.claim_traceability for outcome in outcomes) / len(outcomes)
        ),
    }


def describe_outcome(outcome: ProposalOutcome) -> dict[str, Any]:
    return {
        "request_id": outcome.request_id,
        "accepted_for_review": outcome.accepted_for_review,
        "rejection_reasons": list(outcome.rejection_reasons),
        "changed_lines": outcome.changed_lines,
        "files_touched": outcome.files_touched,
        "claim_traceability": outcome.claim_traceability,
        "verification": (
            {
                "applied": outcome.verification.applied,
                "compiled": outcome.verification.compiled,
                "focused_tests_passed": outcome.verification.focused_tests_passed,
                "architecture_checks_passed": outcome.verification.architecture_checks_passed,
                "duration_ms": outcome.verification.duration_ms,
                "findings": list(outcome.verification.findings),
            }
            if outcome.verification is not None
            else None
        ),
    }
