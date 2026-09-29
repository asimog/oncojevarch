import pytest

from oncolab.capabilities import (
    ApplicabilityCheck,
    CapabilityKind,
    CapabilityRecord,
    CapabilityRegistry,
    EngineeringReadiness,
    ScientificReadiness,
)


def _registry() -> CapabilityRegistry:
    registry = CapabilityRegistry()
    registry.register(
        CapabilityRecord(
            capability_id="gdc_metadata_source",
            kind=CapabilityKind.SOURCE,
            version="1",
            source_identity="git:abc",
            engineering_readiness=EngineeringReadiness.VERIFIED,
            scientific_readiness=ScientificReadiness.VALIDATED_FOR_DEFINED_DOMAIN,
            applicability=("public metadata", "gdc"),
            purpose="read-only GDC project metadata and facet counts",
            domain_owner="oncologie-sources",
            inputs=("project id",),
            outputs=("metadata records", "facet counts"),
            evaluated_domain="GDC public metadata, one data release",
        )
    )
    registry.register(
        CapabilityRecord(
            capability_id="shortlist_reranker",
            kind=CapabilityKind.JEV,
            version="2",
            source_identity="git:def",
            engineering_readiness=EngineeringReadiness.TESTED,
            applicability=("shortlist reranking",),
            purpose="bounded semantic reranking of a high-recall shortlist",
            domain_owner="search",
        )
    )
    return registry


def test_search_returns_ranked_summaries_for_a_need() -> None:
    candidates = _registry().search("gdc metadata facets")

    assert candidates[0].capability_id == "gdc_metadata_source"
    assert candidates[0].purpose == "read-only GDC project metadata and facet counts"
    assert candidates[0].kind is CapabilityKind.SOURCE


def test_search_is_deterministic_and_bounded() -> None:
    registry = _registry()

    first = registry.search("reranking", limit=1)
    second = registry.search("reranking", limit=1)

    assert first == second
    assert [summary.capability_id for summary in first] == ["shortlist_reranker"]


def test_search_filters_by_kind_and_readiness() -> None:
    registry = _registry()

    assert registry.search("metadata", kind=CapabilityKind.JEV) == ()
    assert registry.search("reranking", min_engineering=EngineeringReadiness.VERIFIED) == ()
    assert [
        summary.capability_id
        for summary in registry.search("reranking", min_engineering=EngineeringReadiness.TESTED)
    ] == ["shortlist_reranker"]


def test_search_miss_and_invalid_inputs_are_explicit() -> None:
    registry = _registry()

    assert registry.search("spatial transcriptomics deconvolution") == ()
    with pytest.raises(ValueError, match="need"):
        registry.search("   ")
    with pytest.raises(ValueError, match="limit"):
        registry.search("metadata", limit=0)


def test_common_words_do_not_create_false_hits() -> None:
    registry = _registry()

    assert registry.search("call the thing in a pair from a site") == ()


def test_an_unanticipated_capability_registers_without_core_changes() -> None:
    registry = CapabilityRegistry()
    registry.register(
        CapabilityRecord(
            capability_id="spatial_niche_mapper",
            kind=CapabilityKind.METHOD,
            version="0.1",
            source_identity="git:xyz",
            applicability=("spatial niches",),
            purpose="map spatial tissue niches from an unanticipated measurement class",
            inputs=("cell coordinates",),
            outputs=("niche assignments",),
        )
    )

    found = registry.search("unanticipated spatial measurement", limit=3)

    assert [summary.capability_id for summary in found] == ["spatial_niche_mapper"]


def test_applicability_check_reports_unmet_tags() -> None:
    registry = _registry()

    check = registry.check_applicability(
        "gdc_metadata_source", "1", ("gdc", "molecular profiles")
    )

    assert isinstance(check, ApplicabilityCheck)
    assert check.unmet == ("molecular profiles",)
    assert check.eligible is False
    assert registry.check_applicability("gdc_metadata_source", "1", ("gdc",)).eligible is True
