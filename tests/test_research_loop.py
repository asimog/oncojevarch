from dataclasses import replace
from pathlib import Path

from evidence.models import Coverage
from execution.ports import ExecutionCapability, MeasuredResult
from experiments.architecture.fixture_capabilities import (
    FIXTURE_CAPABILITY_ID,
    FIXTURE_CAPABILITY_VERSION,
    FixtureMissingValueCapability,
    FixtureTokenCountCapability,
    fixture_context,
    fixture_investigation,
    fixture_operation,
    fixture_record,
    promote_capability,
)
from oncodex.research_loop import ResearchRuntime, run_research_step
from oncolab.admission import AdmissionContext
from oncolab.capabilities import CapabilityRegistry
from oncolab.gaps import GapKind, GapLedger
from oncolab.operations import OperationRegistry, ScientificOperation
from research.ledger import EvidenceLedger, InvestigationLedger
from store.jsonl import AppendOnlyJsonlStore


def _runtime(
    tmp_path: Path,
    *,
    promote: bool = True,
    executor: ExecutionCapability | None = None,
) -> ResearchRuntime:
    registry = CapabilityRegistry()
    registry.register(fixture_record())
    if promote:
        promote_capability(registry)
    store = AppendOnlyJsonlStore(tmp_path / "events.jsonl")
    operations = OperationRegistry()
    operations.register(fixture_operation(operation_id="op-1", evidence_id="ev-1"))
    executors: dict[str, ExecutionCapability] = {
        FIXTURE_CAPABILITY_ID: (
            executor if executor is not None else FixtureTokenCountCapability()
        )
    }
    return ResearchRuntime(
        registry=registry,
        operations=operations,
        executors=executors,
        gaps=GapLedger(store),
        investigations=InvestigationLedger(store),
        evidence=EvidenceLedger(store),
    )


def test_step_admits_evidence_and_persists_the_revision(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path)
    investigation = fixture_investigation(investigation_id="inv-1")
    runtime.investigations.record(investigation)

    step = run_research_step(
        runtime=runtime,
        investigation=investigation,
        need="count tokens in fixture documents",
        operation_id="op-1",
    )

    assert step.outcome == "evidence"
    assert step.evidence_id == "ev-1"
    assert runtime.evidence.get("ev-1") is not None
    latest = runtime.investigations.latest("inv-1")
    assert latest is not None
    assert latest.evidence_ids == ("ev-1",)


def test_step_records_a_routed_gap_when_no_capability_exists(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path)
    runtime.operations.register(
        ScientificOperation(
            operation_id="op-missing",
            capability_id="no_such_capability",
            version="1",
            inputs={},
            context=fixture_context(evidence_id="ev-missing"),
        )
    )
    investigation = fixture_investigation(investigation_id="inv-2")
    runtime.investigations.record(investigation)

    step = run_research_step(
        runtime=runtime,
        investigation=investigation,
        need="estimate tumor purity",
        operation_id="op-missing",
    )

    assert step.outcome == "gap"
    recorded = runtime.gaps.recorded()
    assert len(recorded) == 1
    assert recorded[0].kind is GapKind.CAPABILITY
    assert step.gap_id in (step.revision.next_action or "")


def test_unverified_capability_is_not_executed(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, promote=False)
    investigation = fixture_investigation(investigation_id="inv-3")
    runtime.investigations.record(investigation)

    step = run_research_step(
        runtime=runtime,
        investigation=investigation,
        need="count tokens in fixture documents",
        operation_id="op-1",
    )

    assert step.outcome == "gap"
    assert step.evidence_id == ""
    assert runtime.evidence.all() == ()


def test_refused_measurement_does_not_touch_investigation_state(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, executor=FixtureMissingValueCapability())
    investigation = fixture_investigation(investigation_id="inv-4")
    runtime.investigations.record(investigation)

    step = run_research_step(
        runtime=runtime,
        investigation=investigation,
        need="count tokens in fixture documents",
        operation_id="op-1",
    )

    assert step.outcome == "refused"
    assert step.refusal_reasons == ("unrepresentable_value",)
    assert len(runtime.investigations.revisions("inv-4")) == 1
    assert runtime.evidence.all() == ()


def test_unknown_operation_is_a_caller_error(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path)
    try:
        run_research_step(
            runtime=runtime,
            investigation=fixture_investigation(investigation_id="inv-5"),
            need="anything",
            operation_id="not-registered",
        )
    except KeyError:
        return
    raise AssertionError("unknown operation should raise KeyError")


def test_fixture_capability_version_is_referenced() -> None:
    record = fixture_record()

    assert (record.capability_id, record.version) == (
        FIXTURE_CAPABILITY_ID,
        FIXTURE_CAPABILITY_VERSION,
    )


class _DisclosingFixture(FixtureTokenCountCapability):
    def admission_context(
        self, *, result: MeasuredResult, base: AdmissionContext
    ) -> AdmissionContext:
        return replace(base, coverage=Coverage(requested=7, retrieved=7, assayed=7))


def test_capability_disclosure_completes_the_admission_context(tmp_path: Path) -> None:
    runtime = _runtime(tmp_path, executor=_DisclosingFixture())
    investigation = fixture_investigation(investigation_id="inv-6")
    runtime.investigations.record(investigation)

    step = run_research_step(
        runtime=runtime,
        investigation=investigation,
        need="count tokens in fixture documents",
        operation_id="op-1",
    )

    assert step.outcome == "evidence"
    evidence = runtime.evidence.get(step.evidence_id)
    assert evidence is not None
    assert evidence.coverage.requested == 7
