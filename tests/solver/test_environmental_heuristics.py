from __future__ import annotations

from amanda_agent.design.environmental import evaluate_environmental_heuristics


def test_true_north_changes_facade_orientation_calculation():
    north_aligned = evaluate_environmental_heuristics(
        {"facade_orientation_deg": 0}, true_north_deg=0, preferred_solar_orientation_deg=0
    )
    rotated_site = evaluate_environmental_heuristics(
        {"facade_orientation_deg": 0}, true_north_deg=90, preferred_solar_orientation_deg=0
    )

    assert north_aligned.solar_score > rotated_site.solar_score
    assert north_aligned.labels == {"solar": "HEURISTIC", "ventilation": "HEURISTIC"}


def test_east_west_and_wind_exposure_have_expected_relative_changes():
    east = evaluate_environmental_heuristics(
        {"facade_orientation_deg": 90, "opening_ratio": 0.6},
        preferred_solar_orientation_deg=0,
        wind_direction_deg=90,
    )
    west = evaluate_environmental_heuristics(
        {"facade_orientation_deg": 270, "opening_ratio": 0.6},
        preferred_solar_orientation_deg=0,
        wind_direction_deg=90,
    )
    sheltered = evaluate_environmental_heuristics(
        {"facade_orientation_deg": 90, "opening_ratio": 0.6, "wind_exposure": 0.1},
        wind_direction_deg=90,
    )

    assert east.solar_score == west.solar_score
    assert east.ventilation_score > sheltered.ventilation_score
    assert all(value == "HEURISTIC" for value in east.labels.values())

