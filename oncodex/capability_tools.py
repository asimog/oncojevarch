from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any

from oncodex.research_loop import ResearchRuntime, run_research_step
from oncolab.capabilities import CapabilityKind, CapabilityRegistry
from oncolab.gaps import Gap, GapKind, GapLedger, gap_identity
from research.ledger import InvestigationLedger, investigation_payload

NO_APPLICABLE_CAPABILITY = (
    "no applicable capability found; record an explicit gap with record_gap instead of "
    "improvising a method"
)


def _dumps(value: object) -> str:
    return json.dumps(value, sort_keys=True)


def _parse_kind(kind: str) -> CapabilityKind | None:
    cleaned = kind.strip()
    if not cleaned:
        return None
    return CapabilityKind(cleaned)


def search_capabilities_impl(
    registry: CapabilityRegistry,
    *,
    need: str,
    kind: str = "",
    limit: int = 5,
) -> str:
    """Deterministic capability search returning ranked summaries or an explicit miss."""

    try:
        parsed = _parse_kind(kind)
    except ValueError:
        return f"error: unknown capability kind: {kind}"
    try:
        found = registry.search(need, kind=parsed, limit=limit)
    except ValueError as exc:
        return f"error: {exc}"
    if not found:
        return NO_APPLICABLE_CAPABILITY
    return _dumps([asdict(summary) for summary in found])


def load_capability_impl(
    registry: CapabilityRegistry,
    *,
    capability_id: str,
    version: str,
) -> str:
    """Load the full contract for one capability version."""

    try:
        record = registry.get(capability_id, version)
    except KeyError:
        return f"not found: capability {capability_id} version {version}"
    return _dumps(asdict(record))


def record_gap_impl(
    ledger: GapLedger,
    *,
    need: str,
    kind: str,
    evidence: tuple[str, ...] = (),
    unmet_requirements: tuple[str, ...] = (),
    attempted: tuple[str, ...] = (),
    origin: str = "",
) -> str:
    """Record an explicit capability gap with provenance."""

    try:
        parsed = GapKind(kind.strip())
    except ValueError:
        return (
            f"error: unknown gap kind: {kind} "
            "(expected method, capability, decision, or harness)"
        )
    gap = Gap(
        gap_id=gap_identity(need=need, kind=parsed, origin=origin),
        kind=parsed,
        need=need,
        evidence=evidence,
        unmet_requirements=unmet_requirements,
        attempted=attempted,
        origin=origin,
    )
    ledger.record(gap)
    return _dumps({"gap_id": gap.gap_id, "kind": gap.kind.value, "route": gap.route.value})


def inspect_investigation_impl(
    investigations: InvestigationLedger,
    *,
    investigation_id: str,
) -> str:
    """Read the latest persisted revision of an investigation."""

    latest = investigations.latest(investigation_id)
    if latest is None:
        return f"not found: investigation {investigation_id}"
    return _dumps(investigation_payload(latest))


def run_scientific_operation_impl(
    runtime: ResearchRuntime,
    *,
    investigation_id: str,
    operation_id: str,
) -> str:
    """Execute one registered scientific operation, or expose an explicit gap."""

    investigation = runtime.investigations.latest(investigation_id)
    if investigation is None:
        return f"not found: investigation {investigation_id}"
    try:
        operation = runtime.operations.get(operation_id)
    except KeyError:
        return f"not found: operation {operation_id}; search capabilities and record a gap"
    step = run_research_step(
        runtime=runtime,
        investigation=investigation,
        need=operation.context.measurement,
        operation_id=operation_id,
    )
    return _dumps(
        {
            "outcome": step.outcome,
            "investigation_id": step.investigation_id,
            "evidence_id": step.evidence_id,
            "gap_id": step.gap_id,
            "refusal_reasons": list(step.refusal_reasons),
            "search_candidates": list(step.search_candidates),
            "next_action": step.revision.next_action,
        }
    )


def build_capability_tools(
    *,
    registry: CapabilityRegistry,
    ledger: GapLedger,
) -> list[Any]:
    """Build Agents SDK function tools over the capability registry and gap ledger.

    The tools are deterministic, in-process, and free of network access; the same operations are
    available as plain functions for tests and non-agent runners.
    """

    try:
        from agents import function_tool
    except ImportError as exc:
        raise RuntimeError("install the agents extra: pip install -e '.[agents]'") from exc

    def search_capabilities(need: str, kind: str = "", limit: int = 5) -> str:
        """Search registered capabilities by need; an empty result is an explicit capability gap.

        Args:
            need: What information or operation is required.
            kind: Optional kind filter: agent, source, method, execution, jev, or harness.
            limit: Maximum number of candidate summaries to return.
        """
        return search_capabilities_impl(registry, need=need, kind=kind, limit=limit)

    def load_capability(capability_id: str, version: str) -> str:
        """Load the full contract for one capability version found by search_capabilities.

        Args:
            capability_id: Capability identifier from a search summary.
            version: Capability version from a search summary.
        """
        return load_capability_impl(registry, capability_id=capability_id, version=version)

    def record_gap(
        need: str,
        kind: str,
        evidence: list[str] | None = None,
        unmet_requirements: list[str] | None = None,
        attempted: list[str] | None = None,
        origin: str = "",
    ) -> str:
        """Record an explicit capability gap; never improvise a method instead.

        Args:
            need: What information or operation was required.
            kind: Gap kind: method, capability, decision, or harness.
            evidence: Evidence strings establishing the gap.
            unmet_requirements: Why existing capabilities could not satisfy the need.
            attempted: Capability ids or versions that were considered.
            origin: Investigation or caller identity that needs it.
        """
        return record_gap_impl(
            ledger,
            need=need,
            kind=kind,
            evidence=tuple(evidence or ()),
            unmet_requirements=tuple(unmet_requirements or ()),
            attempted=tuple(attempted or ()),
            origin=origin,
        )

    return [
        function_tool(name_override="search_capabilities")(search_capabilities),
        function_tool(name_override="load_capability")(load_capability),
        function_tool(name_override="record_gap")(record_gap),
    ]


def build_research_tools(
    *,
    runtime: ResearchRuntime,
) -> list[Any]:
    """Build Agents SDK tools for the session-independent research step.

    The tools read and write durable state through the runtime's ledgers; agent threads are not
    scientific memory.
    """

    try:
        from agents import function_tool
    except ImportError as exc:
        raise RuntimeError("install the agents extra: pip install -e '.[agents]'") from exc

    def inspect_investigation(investigation_id: str) -> str:
        """Inspect the latest persisted revision of an investigation.

        Args:
            investigation_id: Investigation identifier.
        """
        return inspect_investigation_impl(runtime.investigations, investigation_id=investigation_id)

    def run_scientific_operation(investigation_id: str, operation_id: str) -> str:
        """Execute one registered scientific operation, or expose an explicit gap.

        Args:
            investigation_id: Investigation the step belongs to.
            operation_id: Registered scientific operation to execute.
        """
        return run_scientific_operation_impl(
            runtime,
            investigation_id=investigation_id,
            operation_id=operation_id,
        )

    return [
        function_tool(name_override="inspect_investigation")(inspect_investigation),
        function_tool(name_override="run_scientific_operation")(run_scientific_operation),
    ]
