def _expected_geometry():
    return {"bounds": [0.0, 0.0, 3.0, 4.0]}


def _expected_properties():
    return {"name": "Acolhimento", "area_m2": 12.0}


def _query_result(geometry=None, properties=None):
    return {
        "logical_id": "ROOM-01",
        "unique_id": "uid-1",
        "geometry": geometry if geometry is not None else _expected_geometry(),
        "properties": properties if properties is not None else _expected_properties(),
    }


def test_tool_success_but_query_misses_element_is_fail():
    from amanda_agent.bim.verification import VerificationLayer, verify_write

    results = verify_write(
        logical_id="ROOM-01",
        tool_reported_success=True,
        query_result=None,
    )

    existence = [result for result in results if result.layer is VerificationLayer.EXISTENCE]
    assert len(existence) == 1
    assert existence[0].passed is False
    assert any(not result.passed for result in results)


def test_geometry_beyond_tolerance_is_fail():
    from amanda_agent.bim.verification import VerificationLayer, verify_write

    results = verify_write(
        logical_id="ROOM-01",
        tool_reported_success=True,
        query_result=_query_result(geometry={"bounds": [0.0, 0.0, 3.0, 5.0]}),
        expected_geometry=_expected_geometry(),
    )

    geometry = [result for result in results if result.layer is VerificationLayer.GEOMETRY]
    assert len(geometry) == 1
    assert geometry[0].passed is False
    assert any(not result.passed for result in results)


def test_correct_element_is_pass():
    from amanda_agent.bim.verification import VerificationLayer, verify_write

    results = verify_write(
        logical_id="ROOM-01",
        tool_reported_success=True,
        query_result=_query_result(),
        expected_geometry=_expected_geometry(),
        expected_properties=_expected_properties(),
    )

    assert all(result.passed for result in results)
    assert {result.layer for result in results} == {
        VerificationLayer.EXISTENCE,
        VerificationLayer.PROPERTIES,
        VerificationLayer.GEOMETRY,
    }


def test_persistence_layer_fails_when_required_but_unproven():
    from amanda_agent.bim.verification import VerificationLayer, verify_write

    results = verify_write(
        logical_id="ROOM-01",
        tool_reported_success=True,
        query_result=_query_result(),
        expected_geometry=_expected_geometry(),
        require_persistence=True,
        persistence_evidence=False,
    )

    persistence = [result for result in results if result.layer is VerificationLayer.PERSISTENCE]
    assert len(persistence) == 1
    assert persistence[0].passed is False
