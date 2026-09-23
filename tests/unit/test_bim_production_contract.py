"""Regression tests for production registry loading and measured build pins."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml
from typer.testing import CliRunner

from amanda_agent.bim.models import BimStage
from amanda_agent.bim.stages import (
    CheckStatus,
    EvidenceScope,
    ExecutionMode,
    PreflightRequest,
    run_preflight,
)
from amanda_agent.commands.bim import bim_app
from amanda_agent.models.capability import (
    CapabilityRegistry,
    CapabilityStatus,
    ProviderCapability,
    SelectionRefused,
)

ROOT = Path(__file__).resolve().parents[2]
LIVE_BUILD = "27.2.0.39"
SCHEMA_HASH = "sha256:" + "a" * 64
runner = CliRunner()


def _write_registry(root: Path, *, operation: str = "wall") -> Path:
    evidence = root / "evidence.json"
    evidence.write_text("measured evidence", encoding="utf-8")
    registry_path = root / "state" / "capabilities.yaml"
    CapabilityRegistry(
        entries=[
            ProviderCapability(
                provider="horizun",
                status=CapabilityStatus.PASS,
                priority=10,
                provider_commit="cc4ea04",
                transport_provider="horizun-revit-mcp",
                tool_schema_hash=SCHEMA_HASH,
                tested_scope={"operation": operation, "writes": True},
                evidence_scope=EvidenceScope.PROVIDER,
                revit_build=LIVE_BUILD,
                save_reopen=True,
                independent_query=True,
                evidence=[
                    f"{evidence}::sha256={hashlib.sha256(evidence.read_bytes()).hexdigest()}"
                ],
            )
        ]
    ).save(registry_path)
    return registry_path


def _write_crosswalk(root: Path, rows: list[dict]) -> Path:
    path = root / "state" / "providers" / "semantic-crosswalk.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"schema_version": 1, "rows": rows}, sort_keys=False),
        encoding="utf-8",
    )
    return path


def test_load_with_crosswalk_binds_semantic_name_without_promoting_scope(tmp_path: Path):
    registry_path = _write_registry(tmp_path)
    crosswalk_path = _write_crosswalk(
        tmp_path,
        [
            {
                "semantic": "revit.create_wall",
                "route": "horizun_create_elements",
                "registered_entry": "wall",
                "writes": True,
            }
        ],
    )

    registry = CapabilityRegistry.load_with_crosswalk(registry_path, crosswalk_path)

    selected = registry.preferred(
        operation="revit.create_wall",
        revit_build=LIVE_BUILD,
        tool_schema_hash=SCHEMA_HASH,
        scope=EvidenceScope.PROVIDER,
    )
    assert selected.provider == "horizun"
    assert selected.evidence_scope is EvidenceScope.PROVIDER


def test_crosswalk_gap_is_named_by_stage_preflight(tmp_path: Path):
    registry_path = _write_registry(tmp_path)
    crosswalk_path = _write_crosswalk(
        tmp_path,
        [
            {
                "semantic": "revit.create_grid",
                "route": "horizun_create_elements",
                "registered_entry": None,
                "writes": True,
                "gap": "route proven but no registered entry",
            }
        ],
    )
    registry = CapabilityRegistry.load_with_crosswalk(registry_path, crosswalk_path)
    request = PreflightRequest(
        mode=ExecutionMode.CONCEPT_ONLY,
        stage=BimStage.R01,
        registry=registry,
        revit_build=LIVE_BUILD,
        tool_schema_hash=SCHEMA_HASH,
        expected_build=LIVE_BUILD,
        expected_tool_schema_hash=SCHEMA_HASH,
        required_operations=("revit.create_grid",),
        evidence_scope=EvidenceScope.PROVIDER,
    )

    report = run_preflight(request)

    assert report.get("capability_registry").status is CheckStatus.FAIL
    assert "revit.create_grid" in report.get("capability_registry").detail
    assert "gap declarado no crosswalk" in report.get("capability_registry").detail

    with pytest.raises(SelectionRefused, match="gap declarado no crosswalk"):
        registry.preferred(
            operation="revit.create_grid",
            revit_build=LIVE_BUILD,
            tool_schema_hash=SCHEMA_HASH,
            scope=EvidenceScope.PROVIDER,
        )


def test_production_loader_uses_crosswalk_and_falls_back_explicitly(tmp_path: Path):
    _write_registry(tmp_path)
    _write_crosswalk(
        tmp_path,
        [
            {
                "semantic": "revit.create_wall",
                "route": "horizun_create_elements",
                "registered_entry": "wall",
                "writes": True,
            }
        ],
    )

    registry, warnings = CapabilityRegistry.load_for_production(tmp_path)

    assert warnings == ()
    assert len(registry.for_operation("revit.create_wall")) == 1

    (tmp_path / "state" / "providers" / "semantic-crosswalk.yaml").unlink()
    fallback, warnings = CapabilityRegistry.load_for_production(tmp_path)

    assert warnings
    assert "semantic crosswalk" in warnings[0].lower()
    assert "not found" in warnings[0].lower()
    assert "without semantic aliases" in warnings[0].lower()
    assert fallback.for_operation("revit.create_wall") == []


def test_preflight_request_can_load_the_production_registry(tmp_path: Path):
    _write_registry(tmp_path)
    _write_crosswalk(
        tmp_path,
        [
            {
                "semantic": "revit.create_wall",
                "route": "horizun_create_elements",
                "registered_entry": "wall",
                "writes": True,
            }
        ],
    )

    request = PreflightRequest.from_production_state(
        tmp_path,
        mode=ExecutionMode.CONCEPT_ONLY,
        stage=BimStage.R01,
        revit_build=LIVE_BUILD,
        tool_schema_hash=SCHEMA_HASH,
        expected_build=LIVE_BUILD,
        expected_tool_schema_hash=SCHEMA_HASH,
        required_operations=("revit.create_wall",),
        evidence_scope=EvidenceScope.PROVIDER,
    )

    report = run_preflight(request)

    assert report.get("capability_registry").status is CheckStatus.PASS


def test_bim_status_loads_the_production_registry_when_project_root_is_given(
    tmp_path: Path,
):
    _write_registry(tmp_path)
    _write_crosswalk(tmp_path, [])

    result = runner.invoke(bim_app, ["status", "--project-root", str(tmp_path)])

    assert result.exit_code == 0
    assert "semantic crosswalk: loaded" in result.stdout.lower()


def test_repository_capability_build_matches_metadata_and_environment_lock():
    capabilities = yaml.safe_load((ROOT / "state" / "capabilities.yaml").read_text())
    metadata = json.loads(
        (ROOT / "state" / "revit-metadata.json").read_text(encoding="utf-8-sig")
    )
    environment = yaml.safe_load(
        (ROOT / "state" / "bim-environment.lock.yaml").read_text()
    )

    measured = metadata["installations"][0]["fileVersion"]
    selected = environment["revit"]["selected_build"]
    builds = {entry["revit_build"] for entry in capabilities["entries"]}

    assert builds == {measured}
    assert selected == measured


def test_custom_api_local_schema_hash_records_unmeasured_limitation():
    capabilities = yaml.safe_load((ROOT / "state" / "capabilities.yaml").read_text())
    custom_api = next(
        entry for entry in capabilities["entries"] if entry["provider"] == "custom-api"
    )

    assert custom_api["tool_schema_hash"] == "sha256:local"
    assert any(
        "schema hash was not measured" in limitation.lower()
        for limitation in custom_api["limitations"]
    )

def test_production_registry_binds_r04_mass_and_preview_visibility_to_lab_proof():
    from pathlib import Path

    from amanda_agent.bim.stages import select_capability
    from amanda_agent.models.capability import CapabilityRegistry, EvidenceScope

    root = Path(__file__).parents[2]
    registry, _warnings = CapabilityRegistry.load_for_production(root)

    mass, _ = select_capability(
        registry,
        "revit.create_mass",
        revit_build="27.2.0.39",
        tool_schema_hash="sha256:8b9600f5274d7dffb6e5bd5f",
        scope=EvidenceScope.PROVIDER,
    )
    visibility, _ = select_capability(
        registry,
        "revit.set_view_category_visibility",
        revit_build="27.2.0.39",
        tool_schema_hash="sha256:8b9600f5274d7dffb6e5bd5f",
        scope=EvidenceScope.PROVIDER,
    )

    assert mass.provider == "horizun"
    assert mass.operation == "mass"
    assert mass.evidence_scope is EvidenceScope.PROVIDER
    assert any("p08-can-t07-r04-mass-capability-20260923.json::sha256=" in item for item in mass.evidence)
    assert visibility.provider == "horizun"
    assert visibility.operation == "view_category_visibility"
    assert visibility.evidence_scope is EvidenceScope.PROVIDER
    assert any("p08-can-t07-r04-mass-capability-20260923.json::sha256=" in item for item in visibility.evidence)
