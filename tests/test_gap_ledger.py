from pathlib import Path

import pytest

from oncolab.gaps import Gap, GapKind, GapLedger, GapRoute, gap_identity
from store.jsonl import AppendOnlyJsonlStore


def _ledger(tmp_path: Path) -> GapLedger:
    return GapLedger(AppendOnlyJsonlStore(tmp_path / "gaps.jsonl"))


def test_gap_provenance_survives_recording(tmp_path: Path) -> None:
    ledger = _ledger(tmp_path)
    gap = Gap(
        gap_id=gap_identity(need="measure tumor purity", kind=GapKind.METHOD, origin="inv-7"),
        kind=GapKind.METHOD,
        need="measure tumor purity",
        evidence=("purity is confounded",),
        unmet_requirements=("no validated method for this assay",),
        attempted=("deterministic purity proxy v1",),
        origin="inv-7",
    )

    ledger.record(gap)

    recorded = ledger.recorded()
    assert recorded == (gap,)
    assert recorded[0].route is GapRoute.SCIENTIFIC_RESEARCH


def test_ledger_is_append_only_and_reloadable(tmp_path: Path) -> None:
    path = tmp_path / "gaps.jsonl"
    first = GapLedger(AppendOnlyJsonlStore(path))
    first.record(Gap(gap_id="g1", kind=GapKind.CAPABILITY, need="align reads"))
    first.record(Gap(gap_id="g2", kind=GapKind.HARNESS, need="resume a workspace op"))

    reloaded = GapLedger(AppendOnlyJsonlStore(path)).recorded()

    assert [(gap.gap_id, gap.kind) for gap in reloaded] == [
        ("g1", GapKind.CAPABILITY),
        ("g2", GapKind.HARNESS),
    ]
    assert [gap.route for gap in reloaded] == [
        GapRoute.ENGINEERING,
        GapRoute.HARNESS_ENGINEERING,
    ]


def test_empty_gap_need_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="need"):
        _ledger(tmp_path).record(Gap(gap_id="g", kind=GapKind.METHOD, need="  "))


def test_gap_identity_is_stable_and_origin_sensitive() -> None:
    one = gap_identity(need="measure purity", kind=GapKind.METHOD, origin="inv-7")
    two = gap_identity(need="measure purity", kind=GapKind.METHOD, origin="inv-7")
    other = gap_identity(need="measure purity", kind=GapKind.METHOD, origin="inv-8")

    assert one == two
    assert one != other
