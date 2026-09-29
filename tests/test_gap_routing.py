from oncolab.gaps import Gap, GapKind, GapRoute


def test_each_gap_routes_to_distinct_work() -> None:
    expected = {
        GapKind.METHOD: GapRoute.SCIENTIFIC_RESEARCH,
        GapKind.CAPABILITY: GapRoute.ENGINEERING,
        GapKind.DECISION: GapRoute.JEV_DESIGN_EVAL,
        GapKind.HARNESS: GapRoute.HARNESS_ENGINEERING,
    }
    assert {kind: Gap(str(i), kind, "need").route for i, kind in enumerate(GapKind)} == expected
