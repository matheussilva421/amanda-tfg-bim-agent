from __future__ import annotations

from shapely.geometry import box

from amanda_agent.design.pipeline import run_pipeline

REQUIREMENTS = {
    "sectors": [
        {"logical_id": "public", "spaces": [{"target_area_m2": 50, "quantity": 1, "sector": "public"}]},
        {"logical_id": "controlled", "spaces": [{"target_area_m2": 50, "quantity": 1, "sector": "controlled"}]},
        {"logical_id": "residential", "spaces": [{"target_area_m2": 50, "quantity": 1, "sector": "residential"}]},
    ]
}


def test_progressive_pipeline_uses_configured_small_counts_and_records_rejections():
    result = run_pipeline(
        REQUIREMENTS,
        box(0, 0, 30, 20),
        seeds=[1, 2, 3, 4],
        config={"macro_candidates": 4, "top_macro": 2, "top_rooms": 1, "top_finalists": 1},
    )

    assert result.counts == {"macro": 4, "top_macro": 2, "rooms": 1, "finalists": 1}
    assert result.stages["macro"]
    assert result.stages["finalists"]
    assert result.stages["rooms"][0]["rooms"]
    assert all(item.reason for item in result.rejected)


def test_pipeline_contains_no_revit_dependency_and_preserves_stage_order():
    result = run_pipeline(
        REQUIREMENTS,
        box(0, 0, 30, 20),
        seeds=[1],
        config={"macro_candidates": 1, "top_macro": 1, "top_rooms": 1, "top_finalists": 1},
    )

    assert result.stage_order == ["macro", "hard_filter", "top_macro", "rooms", "finalists", "detailed"]
    assert result.revit_calls == 0
