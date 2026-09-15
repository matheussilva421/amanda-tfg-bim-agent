import math


def test_one_meter_round_trips_through_revit_feet():
    from amanda_agent.bim.units import feet_to_meters, meters_to_feet

    assert math.isclose(feet_to_meters(meters_to_feet(1.0)), 1.0, rel_tol=0, abs_tol=1e-12)


def test_ten_meters_round_trips_through_revit_feet():
    from amanda_agent.bim.units import feet_to_meters, meters_to_feet

    assert math.isclose(feet_to_meters(meters_to_feet(10.0)), 10.0, rel_tol=0, abs_tol=1e-12)


def test_one_square_meter_round_trips_through_revit_square_feet():
    from amanda_agent.bim.units import sqft_to_sqm, sqm_to_sqft

    assert math.isclose(sqft_to_sqm(sqm_to_sqft(1.0)), 1.0, rel_tol=0, abs_tol=1e-12)


def test_twenty_four_square_meters_round_trips_through_revit_square_feet():
    from amanda_agent.bim.units import sqft_to_sqm, sqm_to_sqft

    assert math.isclose(sqft_to_sqm(sqm_to_sqft(24.0)), 24.0, rel_tol=0, abs_tol=1e-12)


def test_revit_foot_is_exactly_declared_metric_length():
    from amanda_agent.bim.units import feet_to_meters

    assert feet_to_meters(1.0) == 0.3048
