from pathlib import Path

import pytest

from oncodex.capability_tools import (
    NO_APPLICABLE_CAPABILITY,
    build_capability_tools,
    load_capability_impl,
    record_gap_impl,
    search_capabilities_impl,
)
from oncolab.capabilities import CapabilityKind, CapabilityRecord, CapabilityRegistry
from oncolab.gaps import GapKind, GapLedger
from store.jsonl import AppendOnlyJsonlStore


def _registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register(
        CapabilityRecord(
            capability_id="gdc_metadata_source",
            kind=CapabilityKind.SOURCE,
            version="1",
            source_identity="git:abc",
            applicability=("gdc",),
            purpose="read-only GDC project metadata",
            inputs=("project id",),
            outputs=("metadata records",),
        )
    )
    return registry


def test_search_tool_returns_ranked_json_or_an_explicit_miss() -> None:
    found = search_capabilities_impl(_registry(), need="gdc metadata")

    assert "gdc_metadata_source" in found
    assert search_capabilities_impl(_registry(), need="spatial deconvolution") == (
        NO_APPLICABLE_CAPABILITY
    )


def test_search_tool_rejects_unknown_kind() -> None:
    result = search_capabilities_impl(_registry(), need="metadata", kind="modality")

    assert result.startswith("error: unknown capability kind")


def test_load_tool_returns_full_contract_or_not_found() -> None:
    loaded = load_capability_impl(_registry(), capability_id="gdc_metadata_source", version="1")

    assert "read-only GDC project metadata" in loaded
    assert load_capability_impl(_registry(), capability_id="nope", version="1").startswith(
        "not found:"
    )


def test_record_gap_tool_persists_inspectable_state(tmp_path: Path) -> None:
    ledger = GapLedger(AppendOnlyJsonlStore(tmp_path / "gaps.jsonl"))

    result = record_gap_impl(
        ledger,
        need="measure purity",
        kind="method",
        evidence=("confounding present",),
        unmet_requirements=("no validated purity method",),
        attempted=("proxy v1",),
        origin="inv-1",
    )

    assert '"route": "scientific_research"' in result
    recorded = ledger.recorded()
    assert recorded[0].kind is GapKind.METHOD
    assert recorded[0].unmet_requirements == ("no validated purity method",)
    assert recorded[0].origin == "inv-1"


def test_record_gap_tool_rejects_unknown_kind(tmp_path: Path) -> None:
    ledger = GapLedger(AppendOnlyJsonlStore(tmp_path / "gaps.jsonl"))

    result = record_gap_impl(ledger, need="x", kind="scientific")

    assert result.startswith("error: unknown gap kind")
    assert ledger.recorded() == ()


def test_agents_tool_wrappers_build_when_sdk_is_installed(tmp_path: Path) -> None:
    pytest.importorskip("agents")

    tools = build_capability_tools(
        registry=_registry(),
        ledger=GapLedger(AppendOnlyJsonlStore(tmp_path / "gaps.jsonl")),
    )

    assert [tool.name for tool in tools] == [
        "search_capabilities",
        "load_capability",
        "record_gap",
    ]
