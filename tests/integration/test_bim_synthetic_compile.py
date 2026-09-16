"""Synthetic R01-R13 compile regression for the BIM stage contracts."""

from __future__ import annotations

from pathlib import Path

from amanda_agent.bim.checkpoints import CheckpointManager
from amanda_agent.bim.current_state import CurrentElement, CurrentState
from amanda_agent.bim.diff import DiffAction, diff_states
from amanda_agent.bim.lab_fixture import (
    BUILD,
    RUN,
    SCHEMA,
    build_lab_fixture_plans,
    build_lab_fixture_registry,
)
from amanda_agent.bim.models import BimStage, DesiredState
from amanda_agent.bim.runner import RunStatus, execute_chain
from amanda_agent.bim.verification import verify_write

DOCUMENT = "synthetic-courtyard"


class DeterministicInvoker:
    """Synthetic provider double: records calls and never opens Revit."""

    def __init__(self) -> None:
        self.calls = []

    def invoke(self, call):
        self.calls.append(call)
        read_payload = {
            "unique_id": f"uid:{call.stage.name}:{call.logical_id}",
            "readback_verified": True,
        }
        for field in ("geometry", "properties"):
            if field in call.payload:
                read_payload[field] = call.payload[field]
        return {
            "provider": "synthetic-provider",
            "tool": "synthetic-write",
            "reported_success": True,
            "read_payload": read_payload,
        }


def _plans(root: Path):
    registry = build_lab_fixture_registry(
        root=root,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
    )
    return build_lab_fixture_plans(
        root=root,
        registry=registry,
        revit_build=BUILD,
        tool_schema_hash=SCHEMA,
    )


def _execute_and_verify(plans, invoker: DeterministicInvoker):
    all_verifications = []
    for plan in plans:
        # This helper performs only generic write verification for the existing
        # stage dispatcher assertions below.
        if hasattr(plan, "desired_state"):
            elements = plan.desired_state.by_logical_id()
            for operation in plan.operations:
                element = elements[operation.logical_id]
                all_verifications.extend(
                    verify_write(
                        logical_id=element.logical_id,
                        tool_reported_success=True,
                        query_result={
                            "unique_id": f"uid:{plan.stage.name}:{element.logical_id}",
                            "geometry": element.geometry,
                            "properties": element.properties,
                        },
                        expected_geometry=element.geometry,
                        expected_properties=element.properties,
                    )
                )
    return all_verifications


def test_synthetic_pipeline_runs_r01_to_r13_in_order_and_is_idempotent(tmp_path: Path):
    first_plans = _plans(tmp_path / "first")
    second_plans = _plans(tmp_path / "second")

    assert [plan.stage for plan in first_plans] == list(BimStage)[1:14]
    assert [
        plan.desired_state.model_dump(mode="json")
        for plan in first_plans
        if hasattr(plan, "desired_state")
    ] == [
        plan.desired_state.model_dump(mode="json")
        for plan in second_plans
        if hasattr(plan, "desired_state")
    ]

    first_invoker = DeterministicInvoker()
    second_invoker = DeterministicInvoker()
    assert len(first_plans) == 13

    from amanda_agent.bim.stages.accessibility import execute_accessibility_stage
    from amanda_agent.bim.stages.documentation import execute_documentation_stage
    from amanda_agent.bim.stages.furniture import execute_furniture_stage
    from amanda_agent.bim.stages.landscape import execute_landscape_stage
    from amanda_agent.bim.stages.layout import execute_layout_stage
    from amanda_agent.bim.stages.levels import execute_levels_stage
    from amanda_agent.bim.stages.massing import execute_massing_stage
    from amanda_agent.bim.stages.materials import execute_materials_stage
    from amanda_agent.bim.stages.openings import execute_openings_stage
    from amanda_agent.bim.stages.project import execute_project_initialization
    from amanda_agent.bim.stages.rooms import execute_rooms_stage
    from amanda_agent.bim.stages.shell import execute_shell_stage
    from amanda_agent.bim.stages.site import execute_site_stage

    execute_by_stage = {
        BimStage.R01: execute_project_initialization,
        BimStage.R02: execute_site_stage,
        BimStage.R03: execute_levels_stage,
        BimStage.R04: execute_massing_stage,
        BimStage.R05: execute_shell_stage,
        BimStage.R06: execute_layout_stage,
        BimStage.R07: execute_openings_stage,
        BimStage.R08: execute_rooms_stage,
        BimStage.R09: execute_accessibility_stage,
        BimStage.R10: execute_furniture_stage,
        BimStage.R11: execute_landscape_stage,
        BimStage.R12: execute_materials_stage,
        BimStage.R13: execute_documentation_stage,
    }
    first_records = []
    second_records = []
    for first, second in zip(first_plans, second_plans):
        first_records.extend(
            execute_by_stage[first.stage](first, invoker=first_invoker)
        )
        second_records.extend(
            execute_by_stage[second.stage](second, invoker=second_invoker)
        )

    assert [record.stage for record in first_records] == sorted(
        (record.stage for record in first_records),
        key=lambda stage: list(BimStage).index(stage),
    )
    assert [
        (record.stage, record.logical_id, record.semantic_capability, record.provider)
        for record in first_records
    ] == [
        (record.stage, record.logical_id, record.semantic_capability, record.provider)
        for record in second_records
    ]
    verification = _execute_and_verify(first_plans, first_invoker)
    assert verification and all(result.passed for result in verification)

    runner_invoker = DeterministicInvoker()
    runner_results = execute_chain(first_plans, invoker=runner_invoker)
    assert [result.stage for result in runner_results] == list(BimStage)[1:14]
    assert all(result.status is RunStatus.VERIFIED for result in runner_results)
    assert all(
        record.status is RunStatus.VERIFIED
        for result in runner_results
        for record in result.records
    )

    manager = CheckpointManager()
    source = tmp_path / "model.rvt"
    source.write_bytes(b"synthetic model baseline")
    manifests = []
    for index, plan in enumerate(first_plans, start=1):
        manifest = manager.create_checkpoint(
            source,
            tmp_path / f"stage-{index:02d}.rvt",
            stage=plan.checkpoint_label,
            document_id=DOCUMENT,
            reopen_verify=True,
        )
        manifests.append(manifest)
    assert len(manifests) == 13
    assert all(manifest.verify() for manifest in manifests)
    assert [manifest.stage for manifest in manifests] == [
        plan.checkpoint_label for plan in first_plans
    ]

    final_elements = {}
    for plan in first_plans:
        if hasattr(plan, "desired_state"):
            final_elements.update(
                {element.logical_id: element for element in plan.desired_state.elements}
            )
    elements = list(final_elements.values())
    desired = DesiredState(stage=BimStage.R13, generation_run=RUN, elements=elements)
    current = CurrentState(
        document_id=DOCUMENT,
        elements=[
            CurrentElement(
                logical_id=element.logical_id,
                category=element.category,
                geometry=element.geometry,
                properties=element.properties,
                unique_id=f"uid-current-{index:04d}",
                document_id=DOCUMENT,
            )
            for index, element in enumerate(elements, start=1)
        ],
    )
    diff = diff_states(desired, current, expected_document_id=DOCUMENT)
    assert diff.operations
    assert all(operation.action is DiffAction.NOOP for operation in diff.operations)
    assert len(invoker_write_ids := first_invoker.calls) > 0
    assert all(call.provider == "synthetic-provider" for call in invoker_write_ids)
