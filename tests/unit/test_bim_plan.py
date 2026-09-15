from pathlib import Path

import pytest


def _evidence_ref(root: Path, name: str, content: str) -> tuple[str, dict]:
    """Write a real evidence artifact and return its hashed reference."""
    import hashlib

    path = root / name
    path.write_text(content, encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"{path}::sha256={digest}", {"path": path, "digest": digest}


def _registry(root: Path, capabilities=None):
    from amanda_agent.models.capability import CapabilityRegistry, ProviderCapability

    entries = capabilities or [
        {
            "provider": "horizun",
            "status": "PASS",
            "priority": 1,
            "provider_commit": "abc" * 21,
            "transport_provider": "mcp",
            "tool_schema_hash": "hash-1",
            "tested_scope": {"operation": "revit.create_element", "writes": True},
            "evidence_scope": "PROVIDER",
            "revit_build": "2027",
            "save_reopen": True,
            "independent_query": True,
            "evidence": [_evidence_ref(root, "room.evidence.json", "room queried back")[0]],
        }
    ]
    return CapabilityRegistry(entries=[ProviderCapability(**entry) for entry in entries])


def _diff_result():
    from amanda_agent.bim.desired_state import DesiredState
    from amanda_agent.bim.diff import diff_states
    from amanda_agent.bim.models import DesiredElement

    desired = DesiredState(
        elements=[
            DesiredElement(
                logical_id="ROOM-01",
                category="Rooms",
                geometry={"bounds": [0.0, 0.0, 3.0, 4.0]},
                properties={"name": "Acolhimento"},
                requirement_id="REQ-ROOM-001",
                design_option="OPTION-A",
                generation_run="run-001",
            )
        ]
    )
    return diff_states(
        desired,
        {"document_id": "doc-001", "elements": []},
        expected_document_id="doc-001",
    )


def test_every_operation_carries_the_required_fields(tmp_path: Path):
    from amanda_agent.bim.plan import generate_bim_plan

    result = _diff_result()
    plan = generate_bim_plan(
        result,
        registry=_registry(tmp_path),
        revit_build="2027",
        tool_schema_hash="hash-1",
    )

    assert len(plan.operations) == 1
    operation = plan.operations[0]
    assert operation.task_id
    assert operation.logical_id == "ROOM-01"
    assert operation.action == "CREATE"
    assert operation.semantic_capability
    assert operation.desired_payload["logical_id"] == "ROOM-01"
    assert operation.verification_rules
    assert operation.preferred_provider == "horizun"
    assert operation.fallback_providers == []


def test_ordering_is_stable_across_generations(tmp_path: Path):
    from amanda_agent.bim.desired_state import DesiredState
    from amanda_agent.bim.diff import diff_states
    from amanda_agent.bim.models import DesiredElement
    from amanda_agent.bim.plan import generate_bim_plan

    elements = [
        DesiredElement(
            logical_id=f"ROOM-{index:02d}",
            category="Rooms",
            geometry={"bounds": [0.0, 0.0, index, 4.0]},
            properties={"name": f"Room {index}"},
            requirement_id="REQ",
            design_option="A",
            generation_run="run",
        )
        for index in range(1, 6)
    ]
    result = diff_states(
        DesiredState(elements=elements),
        {"document_id": "doc-001", "elements": []},
        expected_document_id="doc-001",
    )
    first = generate_bim_plan(result, registry=_registry(tmp_path), revit_build="2027", tool_schema_hash="hash-1")
    second = generate_bim_plan(result, registry=_registry(tmp_path), revit_build="2027", tool_schema_hash="hash-1")

    assert [operation.logical_id for operation in first.operations] == [
        operation.logical_id for operation in second.operations
    ]
    assert first.operations[-1].task_id == second.operations[-1].task_id


def test_all_untested_or_failed_providers_reject_the_chain(tmp_path: Path):
    from amanda_agent.bim.plan import PlanGenerationError, generate_bim_plan

    with pytest.raises(PlanGenerationError, match="no usable capability"):
        generate_bim_plan(
            _diff_result(),
            registry=_registry(
                tmp_path,
                [
                    {
                        "provider": "horizun",
                        "status": "UNTESTED",
                        "priority": 1,
                        "provider_commit": "abc" * 21,
                        "transport_provider": "mcp",
                        "tool_schema_hash": "hash-1",
                            "tested_scope": {"operation": "revit.create_element", "writes": True},
                        "evidence_scope": "SYNTHETIC",
                        "revit_build": "2027",
                        "save_reopen": False,
                        "independent_query": False,
                        "evidence": [],
                    }
                ]
            ),
            revit_build="2027",
            tool_schema_hash="hash-1",
        )


def test_plan_generation_is_read_only(tmp_path: Path):
    from amanda_agent.bim.plan import generate_bim_plan

    plan = generate_bim_plan(
        _diff_result(),
        registry=_registry(tmp_path),
        revit_build="2027",
        tool_schema_hash="hash-1",
    )

    assert plan.to_file(tmp_path / "BIM_PLAN.json") is not None
    assert (tmp_path / "BIM_PLAN.json").is_file()


def test_human_summary_markdown_is_written_alongside_json(tmp_path: Path):
    from amanda_agent.bim.plan import generate_bim_plan, write_plan_set

    plan = generate_bim_plan(
        _diff_result(),
        registry=_registry(tmp_path),
        revit_build="2027",
        tool_schema_hash="hash-1",
    )

    json_path, markdown_path = write_plan_set(plan, tmp_path)

    assert json_path.name == "BIM_PLAN.json"
    assert markdown_path.name == "BIM_PLAN.md"
    assert markdown_path.read_text(encoding="utf-8").find("ROOM-01") >= 0


def _capability(root: Path, operation: str, *, provider: str = "horizun", priority: int = 1):
    from amanda_agent.models.capability import ProviderCapability

    reference, _ = _evidence_ref(root, f"{provider}-{operation.replace('.', '-')}.json", operation)
    return ProviderCapability(
        provider=provider,
        status="PASS",
        priority=priority,
        provider_commit="abc" * 21,
        transport_provider="mcp",
        tool_schema_hash="hash-1",
        tested_scope={"operation": operation, "writes": True},
        evidence_scope="PROVIDER",
        revit_build="2027",
        save_reopen=True,
        independent_query=True,
        evidence=[reference],
    )


def test_plan_is_ordered_by_stage_and_has_a_rollback_for_each_command(tmp_path: Path):
    from amanda_agent.bim.diff import DiffAction, DiffOperation, DiffResult
    from amanda_agent.bim.models import BimStage, DesiredElement
    from amanda_agent.bim.plan import generate_bim_plan
    from amanda_agent.models.capability import CapabilityRegistry

    project = DesiredElement(
        logical_id="PRJ-0001",
        category="Project",
        geometry={},
        properties={"name": "AMANDA"},
        requirement_id="REQ-PROJECT",
        design_option="OPTION-A",
        generation_run="run-001",
    )
    level = DesiredElement(
        logical_id="LEVEL-01",
        category="Levels",
        geometry={"elevation_m": 0.0},
        properties={"name": "Térreo"},
        requirement_id="REQ-LEVEL",
        design_option="OPTION-A",
        generation_run="run-001",
    )
    result = DiffResult(
        document_id="doc-001",
        managed_count=1,
        operations=[
            DiffOperation(
                logical_id=level.logical_id,
                action=DiffAction.CREATE,
                desired=level,
                semantic_capability="revit.create_level",
            ),
            DiffOperation(
                logical_id=project.logical_id,
                action=DiffAction.CREATE,
                desired=project,
                semantic_capability="revit.create_project",
            ),
        ],
    )
    registry = CapabilityRegistry(
        entries=[
            _capability(tmp_path, "revit.create_level"),
            _capability(tmp_path, "revit.create_project"),
        ]
    )

    plan = generate_bim_plan(
        result,
        registry=registry,
        revit_build="2027",
        tool_schema_hash="hash-1",
        stage=BimStage.R01,
    )

    assert [operation.stage for operation in plan.operations] == [BimStage.R01, BimStage.R03]
    assert [operation.logical_id for operation in plan.operations] == ["PRJ-0001", "LEVEL-01"]
    assert all(operation.rollback is not None for operation in plan.operations)
    assert plan.operations[0].rollback.semantic_capability == "revit.delete_element"
    assert plan.operations[0].rollback.payload["logical_id"] == "PRJ-0001"


def test_equal_current_state_is_not_replanned(tmp_path: Path):
    from amanda_agent.bim.desired_state import DesiredState
    from amanda_agent.bim.diff import diff_states
    from amanda_agent.bim.models import DesiredElement
    from amanda_agent.bim.plan import generate_bim_plan

    element = DesiredElement(
        logical_id="ROOM-01",
        category="Rooms",
        geometry={"bounds": [0.0, 0.0, 3.0, 4.0]},
        properties={"name": "Acolhimento"},
        requirement_id="REQ-ROOM-001",
        design_option="OPTION-A",
        generation_run="run-001",
    )
    result = diff_states(
        DesiredState(elements=[element]),
        {
            "document_id": "doc-001",
            "elements": [
                {
                    "logical_id": "ROOM-01",
                    "category": "Rooms",
                    "geometry": {"bounds": [0.0, 0.0, 3.0, 4.0]},
                    "properties": {"name": "Acolhimento"},
                    "unique_id": "uid-1",
                    "document_id": "doc-001",
                }
            ],
        },
        expected_document_id="doc-001",
    )
    plan = generate_bim_plan(
        result,
        registry=_registry(tmp_path),
        revit_build="2027",
        tool_schema_hash="hash-1",
    )

    assert plan.operations == []
    assert plan.skipped_noops == ["ROOM-01"]


def test_plan_refuses_execution_mode_outside_its_scope(tmp_path: Path):
    from amanda_agent.bim.models import BimStage
    from amanda_agent.bim.plan import PlanGenerationError, generate_bim_plan
    from amanda_agent.bim.stages import ExecutionMode

    with pytest.raises(PlanGenerationError, match="CONCEPT_ONLY.*R04"):
        generate_bim_plan(
            _diff_result(),
            registry=_registry(tmp_path),
            revit_build="2027",
            tool_schema_hash="hash-1",
            stage=BimStage.R05,
            execution_mode=ExecutionMode.CONCEPT_ONLY,
        )

    with pytest.raises(PlanGenerationError, match="fixture"):
        generate_bim_plan(
            _diff_result(),
            registry=_registry(tmp_path),
            revit_build="2027",
            tool_schema_hash="hash-1",
            execution_mode=ExecutionMode.SYNTHETIC_LAB,
            fixture=False,
        )

    with pytest.raises(PlanGenerationError, match="content-bound"):
        generate_bim_plan(
            _diff_result(),
            registry=_registry(tmp_path),
            revit_build="2027",
            tool_schema_hash="hash-1",
            execution_mode=ExecutionMode.DETAILED_BIM,
            solution=None,
        )
