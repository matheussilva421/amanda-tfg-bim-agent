"""Contract tests for the compiler-to-Horizun provider bridge.

The fake transport below speaks the same envelope as ``McpProbe.call`` but
never starts Revit or an MCP process.
"""

from __future__ import annotations

import json
from typing import Any

import pytest

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.providers.horizun import (
    HorizunInvoker,
    HorizunRequestError,
    HorizunUnsupportedCapability,
    StageToolResult,
)
from amanda_agent.bim.stages import StageToolCall


class FakeMcpTransport:
    """Deterministic MCP transport double; no subprocess or Revit access."""

    def __init__(self, *replies: dict[str, Any]) -> None:
        self.replies = list(replies)
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def call(self, tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
        self.calls.append((tool, arguments))
        if not self.replies:
            raise AssertionError("fake transport received an unexpected call")
        return self.replies.pop(0)


def _reply(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "isError": False,
            "structuredContent": payload,
            "content": [{"type": "text", "text": json.dumps(payload)}],
        },
    }


def _wall_call(**payload: Any) -> StageToolCall:
    values = {
        "target_document": "LAB_AMANDA",
        "units": "m",
        "geometry": {
            "start": [0.0, 0.0, 0.0],
            "end": [10.0, 0.0, 0.0],
            "level_id": 311,
            "height": 3.0,
        },
        "properties": {"type_id": 398, "structural": False},
        "idempotency_key": "op-wall-001",
        "dry_run": False,
        "confirmation_token": "confirm-wall-001",
    }
    values.update(payload)
    return StageToolCall(
        stage=BimStage.R05,
        logical_id="WALL-001",
        semantic_capability="revit.create_wall",
        provider="horizun",
        payload=values,
    )


def test_invoker_translates_stage_wall_to_typed_horizun_create_elements():
    expected_read = {"created_ids": [328657], "all_verified": True}
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": [{"element_id": 311}, {"element_id": 398}]}),
        _reply(expected_read),
        _reply(
            {
                "rows": [
                    {"element_id": 328657, "unique_id": "uid-wall", "category": "Paredes"}
                ]
            }
        ),
    )
    invoker = HorizunInvoker(transport=transport)

    result = invoker.invoke(_wall_call())

    assert isinstance(result, StageToolResult)
    assert result.provider == "horizun"
    assert result.reported_success is True
    assert transport.calls == [
        ("get_document_info", {}),
        (
            "horizun_query_model",
            {
                "element_ids": [311, 398],
                "response_mode": "compact",
                "cache_mode": "bypass",
            },
        ),
        (
            "horizun_create_elements",
            {
                "target_document": "LAB_AMANDA",
                "units": "m",
                "elements": [
                    {
                        "kind": "wall",
                        "start": [0.0, 0.0, 0.0],
                        "end": [10.0, 0.0, 0.0],
                        "level_id": 311,
                        "height": 3.0,
                        "type_id": 398,
                        "structural": False,
                        "parameters": {
                            "ALL_MODEL_MARK": "WALL-001",
                            "ALL_MODEL_INSTANCE_COMMENTS": "Amanda WALL-001 (revit.create_wall)",
                        },
                    }
                ],
                "dry_run": False,
                "confirmation_token": "confirm-wall-001",
                "idempotency_key": "op-wall-001",
            },
        ),
        (
            "horizun_query_model",
            {
                "parameters": [
                    {"name": "ALL_MODEL_MARK", "operator": "equals", "value": "WALL-001"}
                ],
                "return_fields": [
                    "unique_id",
                    "name",
                    "category",
                    "type",
                    "type_id",
                    "level",
                    "source_kind",
                    "source_model",
                    "source_reference",
                ],
                "response_mode": "compact",
                "cache_mode": "bypass",
            },
        ),
    ]
    payload = result.read_payload
    assert payload["created_ids"] == [328657]
    assert payload["all_verified"] is True
    assert payload["readback_verified"] is True
    assert payload["element_id"] == 328657
    assert payload["unique_id"] == "uid-wall"


def test_typed_create_readback_reports_unverified_when_the_mark_matches_many_rows():
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA"}),
        _reply({"rows": [{"element_id": 311}, {"element_id": 398}]}),
        _reply({"created_ids": [328657]}),
        _reply(
            {
                "rows": [
                    {"element_id": 328657, "unique_id": "uid-wall-a"},
                    {"element_id": 328658, "unique_id": "uid-wall-b"},
                ]
            }
        ),
    )
    invoker = HorizunInvoker(transport=transport)

    result = invoker.invoke(_wall_call())

    assert result.reported_success is True
    payload = result.read_payload
    assert payload["readback_verified"] is False
    assert "element_id" not in payload
    assert payload["readback_rows"] == [
        {"element_id": 328657, "unique_id": "uid-wall-a"},
        {"element_id": 328658, "unique_id": "uid-wall-b"},
    ]


def test_mutating_horizun_call_requires_or_propagates_orchestrator_key():
    transport = FakeMcpTransport(_reply({"created_ids": [1]}))
    invoker = HorizunInvoker(transport=transport)

    with pytest.raises(HorizunRequestError, match="idempotency_key"):
        invoker.invoke(_wall_call(idempotency_key=None))

    assert transport.calls == []


def test_real_typed_create_requests_the_bridge_plan_and_spends_its_token():
    expected_read = {"created_ids": [328657], "all_verified": True}
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA"}),
        _reply({"rows": [{"element_id": 311}, {"element_id": 398}]}),
        _reply(
            {
                "dry_run": True,
                "plan_resolved": {"create": 1, "fingerprint": "plan-fingerprint-1"},
                "confirmation_token": "hz-token-1",
                "confirmation_expires_utc": "2026-09-15 21:31:12Z",
            }
        ),
        _reply(expected_read),
        _reply(
            {
                "rows": [
                    {"element_id": 328657, "unique_id": "uid-wall", "category": "Paredes"}
                ]
            }
        ),
    )
    invoker = HorizunInvoker(transport=transport)

    result = invoker.invoke(_wall_call(confirmation_token=None))

    assert result.reported_success is True
    plan_call = transport.calls[2]
    apply_call = transport.calls[3]
    assert plan_call[1]["dry_run"] is True
    assert plan_call[1]["idempotency_key"] == "op-wall-001:dry-run"
    assert "confirmation_token" not in plan_call[1]
    assert apply_call[1]["dry_run"] is False
    assert apply_call[1]["confirmation_token"] == "hz-token-1"
    assert apply_call[1]["idempotency_key"] == "op-wall-001"
    payload = result.read_payload
    assert payload["readback_verified"] is True
    assert payload["element_id"] == 328657
    assert payload["plan"]["confirmation_expires_utc"] == "2026-09-15 21:31:12Z"
    assert payload["plan"]["change_preview_fingerprint"] is None
    assert payload["plan"]["plan_resolved"]["fingerprint"] == "plan-fingerprint-1"


def test_real_typed_create_without_a_plan_token_is_refused_instead_of_invented():
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA"}),
        _reply({"rows": [{"element_id": 311}]}),
        _reply({"dry_run": True, "state": "refused", "confirmation_state": "Unknown"}),
    )
    invoker = HorizunInvoker(transport=transport)

    result = invoker.invoke(_wall_call(confirmation_token=None))

    assert result.reported_success is False
    assert result.error["type"] == "HorizunRequestError"
    assert "confirmation token" in result.error["message"]
    assert all(item[1].get("dry_run") is not False for item in transport.calls)


def test_dry_run_stage_call_never_asks_for_a_confirmation_token():
    transport = FakeMcpTransport(
        _reply({"rows": [{"element_id": 311}, {"element_id": 398}]}),
        _reply({"dry_run": True, "state": "rehearsed"}),
    )
    invoker = HorizunInvoker(transport=transport)

    result = invoker.invoke(_wall_call(confirmation_token=None, dry_run=True))

    assert result.reported_success is True
    assert [name for name, _ in transport.calls] == [
        "horizun_query_model",
        "horizun_create_elements",
    ]
    assert transport.calls[1][1]["dry_run"] is True
    assert "confirmation_token" not in transport.calls[1][1]


def test_read_call_returns_structured_content_without_inventing_write_metadata():
    expected_read = {"rows": [{"element_id": 328657, "unique_id": "uid-wall"}]}
    transport = FakeMcpTransport(_reply(expected_read))
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=BimStage.R14,
        logical_id="WALL-001",
        semantic_capability="revit.query_model",
        provider="horizun",
        payload={
            "target_document": "LAB_AMANDA",
            "element_ids": [328657],
            "response_mode": "compact",
            "cache_mode": "bypass",
        },
    )

    result = invoker.invoke(call)

    assert result.reported_success is True
    assert result.read_payload == expected_read
    assert transport.calls == [
        (
            "horizun_query_model",
            {
                "element_ids": [328657],
                "response_mode": "compact",
                "cache_mode": "bypass",
            },
        )
    ]


def test_open_call_carries_revit_version_guard_and_idempotency_key():
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "C:/lab/LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"opened": True, "running_revit_version": "2027"})
    )
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=BimStage.R01,
        logical_id="PRJ-0001",
        semantic_capability="revit.open_document",
        provider="horizun",
        payload={
            "path": "C:/lab/LAB_AMANDA.rvt",
            "idempotency_key": "open-001",
        },
    )

    result = invoker.invoke(call)

    assert result.reported_success is True
    assert transport.calls == [
        ("get_document_info", {}),
        (
            "horizun_open_document",
            {
                "path": "C:/lab/LAB_AMANDA.rvt",
                "expected_version": "2027",
                "idempotency_key": "open-001",
            },
        )
    ]


def test_mcp_error_is_returned_as_failed_tool_result_with_read_payload():
    transport = FakeMcpTransport(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "error": {"code": -32000, "message": "no Revit is reachable"},
        }
    )
    invoker = HorizunInvoker(transport=transport)

    result = invoker.invoke(_wall_call())

    assert result.provider == "horizun"
    assert result.reported_success is False
    assert result.read_payload == {"error": {"code": -32000, "message": "no Revit is reachable"}}
    assert result.error == {"code": -32000, "message": "no Revit is reachable"}


def test_mass_uses_execute_python_after_prewrite_document_and_model_reads():
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": []}),
        _reply({"status": "self_reported_verified", "created_ids": [901]}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=BimStage.R04,
        logical_id="MASS-001",
        semantic_capability="revit.create_mass",
        provider="horizun",
        payload={
            "target_document": "LAB_AMANDA",
            "geometry": {
                "footprint": [[0.0, 0.0], [4.0, 0.0], [4.0, 3.0], [0.0, 3.0]],
                "base_elevation_m": 0.0,
                "height_m": 3.0,
            },
            "properties": {"name": "Courtyard mass"},
            "idempotency_key": "mass-001",
        },
    )

    result = invoker.invoke(call)

    assert result.reported_success is True
    assert [tool for tool, _ in transport.calls] == [
        "get_document_info",
        "horizun_query_model",
        "horizun_execute_python",
    ]
    assert transport.calls[1][1]["categories"] == ["OST_Mass"]
    python_arguments = transport.calls[2][1]
    assert python_arguments["target_document"] == "LAB_AMANDA"
    assert python_arguments["idempotency_key"] == "mass-001"
    assert "revit.create_mass" in python_arguments["code"]
    assert "__output__" in python_arguments["code"]


def test_typed_wall_resolves_logical_level_and_type_ids_and_caches_stage_reads():
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": [{"element_id": 311, "logical_id": "LEVEL-01", "name": "Térreo"}]}),
        _reply({"rows": [{"element_id": 398, "type_id": 398, "type_name": "EXT_WALL_01"}]}),
        _reply({"rows": [{"element_id": 311}, {"element_id": 398}]}),
        _reply({"created_ids": [901]}),
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": [{"element_id": 311}, {"element_id": 398}]}),
        _reply({"created_ids": [902]}),
    )
    invoker = HorizunInvoker(transport=transport)

    def wall(logical_id: str, key: str) -> StageToolCall:
        return StageToolCall(
            stage=BimStage.R05,
            logical_id=logical_id,
            semantic_capability="revit.create_wall",
            provider="horizun",
            payload={
                "target_document": "LAB_AMANDA",
                "geometry": {
                    "start": [0.0, 0.0, 0.0],
                    "end": [4.0, 0.0, 0.0],
                    "level_id": "LEVEL-01",
                    "height": 3.0,
                },
                "properties": {"type_id": "EXT_WALL_01"},
                "idempotency_key": key,
            },
        )

    invoker.invoke(wall("WALL-001", "wall-001"))
    invoker.invoke(wall("WALL-002", "wall-002"))

    assert [tool for tool, _ in transport.calls] == [
        "get_document_info",
        "horizun_list_elements",
        "horizun_list_elements",
        "horizun_query_model",
        "horizun_create_elements",
        "get_document_info",
        "horizun_query_model",
        "horizun_create_elements",
    ]
    assert transport.calls[1][1]["category"] == "OST_Levels"
    assert transport.calls[2][1]["category"] == "OST_Walls"
    assert transport.calls[3][1]["element_ids"] == [311, 398]
    second_row = transport.calls[7][1]["elements"][0]
    assert second_row["level_id"] == 311
    assert second_row["type_id"] == 398


@pytest.mark.parametrize(
    ("capability", "stage", "category"),
    [
        ("revit.create_toposolid", BimStage.R02, "OST_Toposolid"),
        ("revit.create_mass", BimStage.R04, "OST_Mass"),
        ("revit.create_reference", BimStage.R03, "OST_ReferencePlanes"),
        ("revit.create_accessibility_element", BimStage.R09, "OST_GenericModel"),
        ("revit.create_furniture_element", BimStage.R10, "OST_Furniture"),
        ("revit.create_landscape_element", BimStage.R11, "OST_GenericModel"),
        ("revit.assign_material", BimStage.R12, "OST_GenericModel"),
        ("revit.create_documentation_element", BimStage.R13, "OST_Views"),
    ],
)
def test_untyped_capability_uses_only_the_explicit_python_fallback(
    capability: str, stage: BimStage, category: str
):
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": []}),
        _reply({"status": "self_reported_verified", "element_id": 901}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=stage,
        logical_id=f"{stage.name}-001",
        semantic_capability=capability,
        provider="horizun",
        payload={
            "target_document": "LAB_AMANDA",
            "geometry": {"location": [1.0, 2.0, 0.0]},
            "properties": {"name": f"{stage.name} marker"},
            "idempotency_key": f"{stage.name.lower()}-001",
        },
    )

    result = invoker.invoke(call)

    assert result.reported_success is True
    assert [tool for tool, _ in transport.calls] == [
        "get_document_info",
        "horizun_query_model",
        "horizun_execute_python",
    ]
    assert transport.calls[1][1]["categories"] == [category]
    python_arguments = transport.calls[2][1]
    assert python_arguments["idempotency_key"] == f"{stage.name.lower()}-001"
    assert capability in python_arguments["code"]
    assert "__output__" in python_arguments["code"]


def test_project_initialization_uses_document_session_open_with_version_guard():
    transport = FakeMcpTransport(
        _reply({"title": "LAB_R00_EMPTY", "path": "LAB_R00_EMPTY.rvt", "version": "2027"}),
        _reply({"operation": "open", "opened": True}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=BimStage.R01,
        logical_id="PRJ-0001",
        semantic_capability="revit.create_project",
        provider="horizun",
        payload={
            "template_path": "C:/templates/Architectural.rte",
            "idempotency_key": "project-001",
        },
    )

    result = invoker.invoke(call)

    assert result.reported_success is True
    assert transport.calls == [
        ("get_document_info", {}),
        (
            "horizun_document_session",
            {
                "operation": "open",
                "expected_version": "2027",
                "file_path": "C:/templates/Architectural.rte",
                "idempotency_key": "project-001",
            },
        ),
    ]


def test_document_session_open_forwards_the_template_as_file_path():
    """Live bridge evidence, run 2026-09-15.

    The installed horizun_document_session refuses the argument this route used
    to send: "Error: template_path is not applicable to operation 'open'.
    Nothing ran." Its schema has additionalProperties=false and lists file_path,
    not template_path, for open - template_path belongs to horizun_create_family.
    The route sends file_path and never template_path, so an R01 open is the
    bridge's own open and not a request the bridge rejects before it starts.
    """

    transport = FakeMcpTransport(
        _reply({"title": "Default_M_PTB", "path": "Default_M_PTB.rte", "version": "2027"}),
        _reply({"operation": "open", "opened": True}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=BimStage.R01,
        logical_id="PRJ-0001",
        semantic_capability="revit.create_project",
        provider="horizun",
        payload={
            "template_path": "C:/ProgramData/Autodesk/RVT 2027/Templates/Default_M_PTB.rte",
            "idempotency_key": "project-002",
        },
    )

    invoker.invoke(call)

    arguments = transport.calls[1][1]
    assert arguments["file_path"] == "C:/ProgramData/Autodesk/RVT 2027/Templates/Default_M_PTB.rte"
    assert "template_path" not in arguments


@pytest.mark.parametrize(
    ("capability", "api_marker"),
    [
        ("revit.create_toposolid", "Toposolid.Create"),
        ("revit.create_mass", "DirectShape.CreateElement"),
        ("revit.create_reference", "NewReferencePlane"),
        ("revit.create_accessibility_element", "DirectShape.CreateElement"),
        ("revit.create_furniture_element", "NewFamilyInstance"),
        ("revit.create_landscape_element", "DirectShape.CreateElement"),
        ("revit.assign_material", "Material.Create"),
        ("revit.create_documentation_element", "ViewSheet.Create"),
    ],
)
def test_python_routes_emit_operation_specific_revit_api_script(
    capability: str, api_marker: str
):
    stage = {
        "revit.create_toposolid": BimStage.R02,
        "revit.create_mass": BimStage.R04,
        "revit.create_reference": BimStage.R03,
        "revit.create_accessibility_element": BimStage.R09,
        "revit.create_furniture_element": BimStage.R10,
        "revit.create_landscape_element": BimStage.R11,
        "revit.assign_material": BimStage.R12,
        "revit.create_documentation_element": BimStage.R13,
    }[capability]
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": []}),
        _reply({"status": "self_reported_verified", "element_id": 901}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=stage,
        logical_id=f"{stage.name}-API-001",
        semantic_capability=capability,
        provider="horizun",
        payload={
            "target_document": "LAB_AMANDA",
            "geometry": {
                "location": [1.0, 2.0, 0.0],
                "footprint": [[0.0, 0.0], [4.0, 0.0], [4.0, 3.0], [0.0, 3.0]],
                "points": [[0.0, 0.0, 0.0], [4.0, 0.0, 0.5], [4.0, 3.0, 0.0]],
                "height_m": 3.0,
            },
            "properties": {"name": f"{stage.name} marker", "documentation_kind": "sheet"},
            "idempotency_key": f"{stage.name.lower()}-api-001",
        },
    )

    result = invoker.invoke(call)

    assert result.reported_success is True
    assert api_marker in transport.calls[-1][1]["code"]


def test_python_accessibility_route_translates_nested_room_logical_ids():
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": []}),
        _reply(
            {
                "rows": [
                    {"element_id": 101, "logical_id": "ROOM-A"},
                    {"element_id": 102, "logical_id": "ROOM-B"},
                ]
            }
        ),
        _reply({"rows": [{"element_id": 101}, {"element_id": 102}]}),
        _reply({"status": "self_reported_verified", "element_id": 903}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=BimStage.R09,
        logical_id="ACCESS-001",
        semantic_capability="revit.create_accessibility_element",
        provider="horizun",
        payload={
            "target_document": "LAB_AMANDA",
            "geometry": {"from": "ROOM-A", "to": "ROOM-B"},
            "properties": {"from_node": "ROOM-A", "to_node": "ROOM-B"},
            "idempotency_key": "access-001",
        },
    )

    result = invoker.invoke(call)

    assert result.reported_success is True
    assert transport.calls[2][0] == "horizun_list_elements"
    assert transport.calls[2][1]["category"] == "OST_Rooms"
    code = transport.calls[-1][1]["code"]
    assert '"revit_from_id":101' in code
    assert '"revit_to_id":102' in code


def test_unmapped_lookalike_capability_is_refused_without_transport_call():
    transport = FakeMcpTransport()
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=BimStage.R04,
        logical_id="MASS-LOOKALIKE-001",
        semantic_capability="revit.create_mass_like_wall",
        provider="horizun",
        payload={"target_document": "LAB_AMANDA", "idempotency_key": "lookalike-001"},
    )

    with pytest.raises(HorizunUnsupportedCapability):
        invoker.invoke(call)

    assert transport.calls == []


def test_python_self_reported_failure_is_not_promoted_to_success():
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": []}),
        _reply({"rows": [{"element_id": 901}]}),
        _reply({"status": "failed", "message": "no writable host parameter"}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=BimStage.R12,
        logical_id="MAT-FAILED-001",
        semantic_capability="revit.assign_material",
        provider="horizun",
        payload={
            "target_document": "LAB_AMANDA",
            "geometry": {"host_element": 901},
            "properties": {"material_name": "MAT-WALL"},
            "idempotency_key": "material-failed-001",
        },
    )

    result = invoker.invoke(call)

    assert result.reported_success is False
    assert result.error == {"status": "failed", "message": "no writable host parameter"}


def test_python_material_route_resolves_logical_host_before_execution():
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": []}),
        _reply({"rows": [{"element_id": 901, "logical_id": "WALL-001"}]}),
        _reply({"rows": [{"element_id": 901, "logical_id": "WALL-001"}]}),
        _reply({"status": "self_reported_verified", "element_id": 902}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=BimStage.R12,
        logical_id="WALL-001",
        semantic_capability="revit.assign_material",
        provider="horizun",
        payload={
            "target_document": "LAB_AMANDA",
            "geometry": {"host_element": "WALL-001"},
            "properties": {"material_name": "MAT-WALL"},
            "host_category": "OST_Walls",
            "idempotency_key": "material-001",
        },
    )

    result = invoker.invoke(call)

    assert result.reported_success is True
    assert [tool for tool, _ in transport.calls] == [
        "get_document_info",
        "horizun_query_model",
        "horizun_list_elements",
        "horizun_query_model",
        "horizun_execute_python",
    ]
    assert transport.calls[2][1]["category"] == "OST_Walls"
    assert transport.calls[3][1]["element_ids"] == [901]
    python_arguments = transport.calls[4][1]
    assert '"revit_host_id":901' in python_arguments["code"]


def test_typed_opening_translates_host_logical_id_and_diagonal_corners():
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": [{"element_id": 901, "logical_id": "WALL-001"}]}),
        _reply({"rows": [{"element_id": 901}]}),
        _reply({"created_ids": [902]}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=BimStage.R07,
        logical_id="DOOR-001",
        semantic_capability="revit.create_opening",
        provider="horizun",
        payload={
            "target_document": "LAB_AMANDA",
            "geometry": {
                "corner_1": [1.0, 0.0, 0.1],
                "corner_2": [1.9, 0.0, 2.1],
                "level_id": 311,
                "host_logical_id": "WALL-001",
            },
            "properties": {},
            "idempotency_key": "opening-001",
        },
    )

    result = invoker.invoke(call)

    assert result.reported_success is True
    row = transport.calls[3][1]["elements"][0]
    assert row["host_id"] == 901
    assert row["level_id"] == 311
    assert row["corner_1"] == [1.0, 0.0, 0.1]
    assert row["corner_2"] == [1.9, 0.0, 2.1]
    # Live probe evidence, .tmp-probe-live7.log: the bridge refused the whole
    # wall_opening batch with "parameters.ALL_MODEL_MARK: BuiltInParameter exists
    # but is not present on this type", so the mark is only sent where the type
    # really carries it.
    assert "ALL_MODEL_MARK" not in row.get("parameters", {})
    # The rerun of that probe (.tmp-probe-live8.log) then refused the same batch
    # for "parameters.ALL_MODEL_INSTANCE_COMMENTS: BuiltInParameter exists but is
    # not present on this type", so a wall_opening is sent with no parameters at
    # all and the element is identified by its returned ElementId instead.
    assert "parameters" not in row


def test_typed_type_translation_checks_declared_catalog_before_listing_elements():
    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"exists": True, "is_leaf": True, "code": "EXT_WALL_01"}),
        _reply({"rows": [{"element_id": 398, "type_name": "EXT_WALL_01"}]}),
        _reply({"rows": [{"element_id": 398}]}),
        _reply({"created_ids": [901]}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=BimStage.R05,
        logical_id="WALL-001",
        semantic_capability="revit.create_wall",
        provider="horizun",
        payload={
            "target_document": "LAB_AMANDA",
            "geometry": {
                "start": [0.0, 0.0, 0.0],
                "end": [4.0, 0.0, 0.0],
                "level_id": 311,
                "height": 3.0,
            },
            "properties": {"type_id": "EXT_WALL_01"},
            "type_catalog_path": "C:/catalog/families.csv",
            "idempotency_key": "wall-catalog-001",
        },
    )

    result = invoker.invoke(call)

    assert result.reported_success is True
    assert [tool for tool, _ in transport.calls] == [
        "get_document_info",
        "horizun_catalog_lookup",
        "horizun_list_elements",
        "horizun_query_model",
        "horizun_create_elements",
    ]
    assert transport.calls[1][1] == {
        "catalog_path": "C:/catalog/families.csv",
        "code": "EXT_WALL_01",
    }


def test_python_routes_never_use_elementid_integervalue():
    """Revit 2027.2 exposes ElementId.Value; IntegerValue does not exist there.

    Live probe evidence: tool-lab/horizun/results/probe-elementid-api.json and
    probe-raw-reference2.json (AttributeError: 'ElementId' object has no
    attribute 'IntegerValue').  A generated route that reads IntegerValue can
    never commit a transaction on this build, so the script must be free of it.
    """

    for capability, stage in (
        ("revit.create_toposolid", BimStage.R02),
        ("revit.create_reference", BimStage.R03),
        ("revit.create_mass", BimStage.R04),
        ("revit.create_accessibility_element", BimStage.R09),
        ("revit.create_landscape_element", BimStage.R11),
        ("revit.assign_material", BimStage.R12),
        ("revit.create_documentation_element", BimStage.R13),
    ):
        transport = FakeMcpTransport(
            _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
            _reply({"rows": []}),
            _reply({"status": "self_reported_verified", "element_id": 901}),
        )
        invoker = HorizunInvoker(transport=transport)
        call = StageToolCall(
            stage=stage,
            logical_id=f"{stage.name}-ID-001",
            semantic_capability=capability,
            provider="horizun",
            payload={
                "target_document": "LAB_AMANDA",
                "geometry": {
                    "location": [0.0, 0.0, 0.0],
                    "points": [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0]],
                    "material_name": "AMANDA_M",
                },
                "properties": {"name": "marker", "material_name": "AMANDA_M"},
                "idempotency_key": f"{stage.name.lower()}-id-001",
            },
        )
        invoker.invoke(call)
        code = [
            arguments["code"]
            for tool_name, arguments in transport.calls
            if tool_name == "horizun_execute_python"
        ][-1]
        assert "IntegerValue" not in code, capability
        assert "def element_id_value(element_id):" in code, capability
        assert "int(element_id.Value)" in code, capability
        assert "element_id_value(" in code, capability


def _python_call(capability: str, stage: BimStage, **payload: Any) -> StageToolCall:
    values: dict[str, Any] = {
        "target_document": "LAB_AMANDA",
        "idempotency_key": f"{capability.replace('.', '-')}-probe",
    }
    values.update(payload)
    return StageToolCall(
        stage=stage,
        logical_id="PROBE-001",
        semantic_capability=capability,
        provider="horizun",
        payload=values,
    )


def _python_code(transport: FakeMcpTransport) -> str:
    codes = [
        arguments["code"]
        for tool_name, arguments in transport.calls
        if tool_name == "horizun_execute_python"
    ]
    assert codes, "the route never reached horizun_execute_python"
    return codes[-1]


def _created_elements(transport: FakeMcpTransport) -> list[dict[str, Any]]:
    """Return the element batch the adapter handed to horizun_create_elements."""

    batches = [
        arguments["elements"]
        for tool_name, arguments in transport.calls
        if tool_name == "horizun_create_elements"
    ]
    assert batches, "the route never reached horizun_create_elements"
    return batches[-1]


def test_floor_profile_is_emitted_as_a_closed_loop_of_three_dimensional_points():
    """Live probe: "profile[0][0] must contain exactly three coordinates."

    The bridge accepts a floor slab footprint only as List[CurveLoop]; a flat
    ring of XY pairs is refused before anything is written, so the generated
    request has to close the ring and lift every point to 3D.
    """

    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": [{"element_id": 311}]}),
        _reply({"status": "self_reported_verified", "element_id": 902}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = _python_call(
        "revit.create_floor",
        BimStage.R06,
        geometry={
            "footprint": [[0.0, 0.0], [3.0, 0.0], [3.0, 3.0], [0.0, 3.0]],
            "level_id": 311,
        },
    )

    invoker.invoke(call)

    profile = _created_elements(transport)[0]["profile"]
    assert isinstance(profile[0][0], list), "a floor profile is a list of loops"
    assert all(
        len(point) == 3 for loop in profile for point in loop
    ), "every profile point needs three coordinates"
    assert profile[0][0] == profile[0][-1], "the loop must close on its first point"


def test_room_point_is_emitted_as_xy_because_revit_ignores_its_z():
    """Live probe: "room.point requires XY only; a room insertion does not apply Z"."""

    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": [{"element_id": 311}]}),
        _reply({"status": "self_reported_verified", "element_id": 903}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = _python_call(
        "revit.create_room",
        BimStage.R08,
        geometry={"point": [1.0, 1.0], "level_id": 311},
        properties={"name": "AMANDA_PROBE_ROOM", "number": "P-001"},
    )

    invoker.invoke(call)

    point = _created_elements(transport)[0]["point"]
    assert point == [1.0, 1.0], "a room point must stay two-dimensional"


def test_level_and_grid_never_write_a_mark_that_their_category_does_not_carry():
    """Live probe: System.ArgumentException "parameters.ALL_MODEL_MARK:
    BuiltInParameter exists but is not present on this type".

    Levels and grids carry no mark and no instance comments; the bridge
    refuses the whole batch when either is offered, so the adapter must send
    no automatic parameters at all for those two categories."""

    for capability, stage, geometry in (
        ("revit.create_level", BimStage.R01, {"elevation_m": 0.0}),
        (
            "revit.create_grid",
            BimStage.R01,
            {"start": [0.0, 0.0], "end": [5.0, 0.0]},
        ),
    ):
        transport = FakeMcpTransport(
            _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
            _reply({"rows": []}),
            _reply({"created_ids": [900], "all_verified": True}),
        )
        invoker = HorizunInvoker(transport=transport)
        invoker.invoke(
            StageToolCall(
                stage=stage,
                logical_id="PROBE-001",
                semantic_capability=capability,
                provider="horizun",
                payload={
                    "target_document": "LAB_AMANDA",
                    "geometry": geometry,
                    "properties": {"name": "AMANDA_PROBE"},
                    "idempotency_key": f"{capability}-probe",
                    "dry_run": False,
                    "confirmation_token": "confirm-001",
                },
            )
        )
        element = _created_elements(transport)[0]
        assert "parameters" not in element, capability


def test_room_keeps_comments_but_never_offers_a_mark_it_does_not_carry():
    """Live probe: a room refused "parameters.ALL_MODEL_MARK: BuiltInParameter
    exists but is not present on this type", which failed the whole batch."""

    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": [{"element_id": 311}]}),
        _reply({"created_ids": [905], "all_verified": True}),
    )
    invoker = HorizunInvoker(transport=transport)
    invoker.invoke(
        _python_call(
            "revit.create_room",
            BimStage.R08,
            geometry={"point": [1.0, 1.0], "level_id": 311},
            properties={"name": "AMANDA_PROBE_ROOM", "number": "P-001"},
            dry_run=False,
            confirmation_token="confirm-001",
        )
    )

    parameters = _created_elements(transport)[0].get("parameters") or {}
    assert "ALL_MODEL_MARK" not in parameters
    assert "ALL_MODEL_INSTANCE_COMMENTS" in parameters


def test_python_route_reads_parameters_through_a_guarded_helper():
    """Live probe: the bridge's Python context projects many document elements
    as plain Element, Material or View, which have no get_Parameter attribute;
    an unguarded scan therefore kills every Python route with AttributeError.
    The generated script must reach parameters through a guard instead."""

    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": []}),
        _reply({"status": "self_reported_verified", "element_id": 907}),
    )
    invoker = HorizunInvoker(transport=transport)
    invoker.invoke(
        _python_call(
            "revit.create_toposolid",
            BimStage.R02,
            geometry={"points": [[0.0, 0.0, 0.0], [3.0, 0.0, 0.2], [3.0, 3.0, 0.4]]},
        )
    )

    code = _python_code(transport)
    assert "def built_in_string(element, built_in):" in code
    assert "def built_in_parameter(element, built_in):" in code
    assert "built_in_string(candidate, BuiltInParameter.ALL_MODEL_MARK)" in code
    assert "candidate.get_Parameter(BuiltInParameter.ALL_MODEL_MARK).AsString()" not in code
    assert "candidate.get_Parameter(" not in code


def test_python_route_failure_keeps_the_revit_traceback_as_diagnostic_text():
    """The bridge returns the Python traceback as text content, not structured data.

    Live evidence: a deliberate failure answers isError true with the traceback
    in content[0].text. Dropping that text leaves a caller with a failure code
    and no cause, which is how an empty "failures" list hid real errors.
    """

    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": []}),
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "isError": True,
                "structuredContent": {"code": "python_execution_failed"},
                "content": [
                    {
                        "type": "text",
                        "text": "Traceback (most recent call last):\n  File \"<string>\", line 5\nRuntimeError: amanda deliberate diagnostic failure\n",
                    }
                ],
            },
        },
    )
    invoker = HorizunInvoker(transport=transport)
    call = _python_call("revit.create_mass", BimStage.R04, geometry={"footprint": [[0, 0], [1, 0], [1, 1]]})

    result = invoker.invoke(call)

    assert result.reported_success is False
    payload = result.read_payload
    assert "amanda deliberate diagnostic failure" in json.dumps(payload)


def test_python_routes_never_call_revit_apis_that_this_build_does_not_expose():
    """Live probe evidence, measured on Revit 2027.2 with a real document open.

    probe-api2-live.json shows GeometryCreationUtilities exposing
    CreateExtrusionGeometry and no CreateExtrusion at all; probe-api3-live.json
    shows ReferencePlane exposing no Create method, while document.Create does
    expose NewReferencePlane; probe-api6-live.json shows FreeFormElement.Create
    does not exist in a project document ("document is not a family document"),
    while a DirectShape in OST_Mass commits; and Material.Create returns an
    ElementId rather than a Material, so it must be re-read before use.
    """

    forbidden = {
        "GeometryCreationUtilities.CreateExtrusion(": "Revit exposes CreateExtrusionGeometry",
        "ReferencePlane.Create(": "a reference plane comes from document.Create.NewReferencePlane",
        "FreeFormElement.Create(": "a mass in a project document is a DirectShape, not a free form element",
    }
    routes = [
        ("revit.create_mass", BimStage.R04),
        ("revit.create_reference", BimStage.R03),
        ("revit.create_accessibility_element", BimStage.R09),
        ("revit.create_landscape_element", BimStage.R11),
        ("revit.assign_material", BimStage.R12),
    ]
    for capability, stage in routes:
        transport = FakeMcpTransport(
            _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
            _reply({"rows": []}),
            _reply({"status": "self_reported_verified", "element_id": 901}),
        )
        invoker = HorizunInvoker(transport=transport)
        call = _python_call(
            capability,
            stage,
            geometry={
                "footprint": [[0.0, 0.0], [4.0, 0.0], [4.0, 3.0]],
                "location": [1.0, 2.0, 0.0],
                "height_m": 3.0,
            },
            properties={"name": "API guard", "material_name": "MAT-GUARD"},
        )
        invoker.invoke(call)
        code = _python_code(transport)
        for needle, explanation in forbidden.items():
            assert needle not in code, f"{capability} calls {needle}: {explanation}"
        if "Material.Create(" in code:
            assert "GetElement(Material.Create(" in code, (
                "Material.Create returns an ElementId, so the created material must be re-read"
            )


def test_typed_opening_refuses_diagonal_corners_that_share_a_height():
    """Live probe evidence, tool-lab/horizun/results/probe-api7-live.json.

    document.Create.NewOpening refused the flat pair with "Failed to create an
    opening on the wall." and committed the same wall with corners at 0.1 m and
    2.1 m, so a request whose diagonal corners share a height can only fail after
    a real element id has already been reserved for it.
    """

    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": [{"element_id": 901, "logical_id": "WALL-001"}]}),
        _reply({"rows": [{"element_id": 901}]}),
        _reply({"created_ids": [902]}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = StageToolCall(
        stage=BimStage.R07,
        logical_id="DOOR-FLAT",
        semantic_capability="revit.create_opening",
        provider="horizun",
        payload={
            "target_document": "LAB_AMANDA",
            "geometry": {
                "corner_1": [1.0, 0.0, 0.0],
                "corner_2": [1.9, 0.0, 0.0],
                "host_logical_id": "WALL-001",
            },
            "properties": {},
            "idempotency_key": "opening-flat",
        },
    )

    with pytest.raises(HorizunRequestError) as failure:
        invoker.invoke(call)

    assert "different heights" in str(failure.value)
    assert all(tool != "horizun_create_elements" for tool, _ in transport.calls)



def test_python_furniture_route_falls_back_to_an_in_document_furniture_symbol():
    """Live probe evidence, .tmp-probe-live7.log.

    The document really carries furniture symbols (probe-api6-live.json lists
    '1525 x 762mm' 99774, '1830 x 915mm' 99776 and '1525 x 762mm Aluno' 99778) and
    NewFamilyInstance committed an instance from one of them, but the adapter
    raised "create_furniture_element requires a resolved furniture type" because no
    type_id was supplied. A route that refuses a request the document can satisfy
    is not proving the capability, so the script resolves the symbol from the
    document instead of demanding one the compiler never had.
    """

    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": []}),
        _reply({"status": "self_reported_verified", "element_id": 903}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = _python_call(
        "revit.create_furniture_element",
        BimStage.R10,
        geometry={"location": [1.0, 2.0, 0.0]},
        properties={"name": "FURN-001"},
    )

    result = invoker.invoke(call)

    assert result.reported_success is True
    code = _python_code(transport)
    assert "OST_Furniture" in code
    assert "not symbol_id" in code or "if symbol_id is None" in code


def test_python_furniture_route_never_reads_is_active_from_an_instance():
    """Live probe evidence, .tmp-probe-live9.log.

    The route failed live with "AttributeError: 'FamilyInstance' object has no
    attribute 'IsActive'" because the eliminated branch of the id lookup returns
    the first OST_Furniture element of the whole category, which can be an
    instance. Or-as-written only evaluates its left side when the requested
    prefix is not a furniture type name, so the failing read was never reached.
    Reading IsActive from a value that may be an instance is the defect, so the
    script must resolve a FamilySymbol before it touches activation state.
    """

    transport = FakeMcpTransport(
        _reply({"title": "LAB_AMANDA", "path": "LAB_AMANDA.rvt", "version": "2027"}),
        _reply({"rows": []}),
        _reply({"status": "self_reported_verified", "element_id": 904}),
    )
    invoker = HorizunInvoker(transport=transport)
    call = _python_call(
        "revit.create_furniture_element",
        BimStage.R10,
        geometry={"location": [1.0, 2.0, 0.0]},
        properties={"name": "FURN-002"},
    )

    result = invoker.invoke(call)

    assert result.reported_success is True
    code = _python_code(transport)
    assert "isinstance" in code and "FamilySymbol" in code, (
        "a resolved furniture id may be an instance, so the script must confirm it "
        "holds a FamilySymbol before it reads activation state"
    )
