"""Capability registry selection contracts (P02-T01).

The registry is the only place production may ask "which provider can do X".
A status field is never a promotion: selection must refuse synthetic-only
evidence, a missing build/schema/transport field, a stale Revit build, an
unhashed evidence file, and a write capability without independent query and
save/reopen persistence.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from amanda_agent.models.capability import (
    CapabilityRegistry,
    CapabilityStatus,
    EvidenceScope,
    ProviderCapability,
    SelectionRefused,
)

REVIT_BUILD = "20260716_1515(x64)"
SCHEMA_HASH = "sha256:" + "a" * 64
OTHER_SCHEMA_HASH = "sha256:" + "b" * 64


def evidence_ref(tmp_path: Path, name: str, content: str) -> str:
    """Write an evidence artifact and return a path::sha256 reference."""
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"{path}::sha256={digest}"


def capability(tmp_path: Path, **overrides: object) -> ProviderCapability:
    values: dict[str, object] = {
        "provider": "horizun",
        "status": CapabilityStatus.PASS,
        "priority": 10,
        "provider_commit": "cc4ea04",
        "transport_provider": "horizun-revit",
        "tool_schema_hash": SCHEMA_HASH,
        "tested_scope": {"operation": "create_level", "writes": False},
        "evidence_scope": EvidenceScope.PROVIDER,
        "revit_build": REVIT_BUILD,
        "save_reopen": False,
        "transport_healthy": True,
        "evidence": [evidence_ref(tmp_path, "read-evidence.json", "levels queried back")],
    }
    values.update(overrides)
    return ProviderCapability(**values)


def select(registry: CapabilityRegistry, **overrides: object) -> ProviderCapability:
    values: dict[str, object] = {
        "operation": "create_level",
        "revit_build": REVIT_BUILD,
        "tool_schema_hash": SCHEMA_HASH,
        "scope": EvidenceScope.PRODUCTION,
    }
    values.update(overrides)
    return registry.preferred(**values)


def test_fail_and_retired_statuses_are_never_selected(tmp_path: Path) -> None:
    failed = CapabilityRegistry(entries=[capability(tmp_path, status=CapabilityStatus.FAIL)])
    retired = CapabilityRegistry(
        entries=[
            capability(
                tmp_path,
                status=CapabilityStatus.RETIRED,
                evidence=[evidence_ref(tmp_path, "retired.json", "retired evidence")],
            )
        ]
    )

    with pytest.raises(SelectionRefused):
        select(failed)
    with pytest.raises(SelectionRefused):
        select(retired)


def test_bare_pass_without_build_schema_commit_or_evidence_is_refused(tmp_path: Path) -> None:
    bare = capability(
        tmp_path,
        provider_commit=None,
        tool_schema_hash=None,
        revit_build=None,
        transport_provider=None,
        evidence=[],
    )
    registry = CapabilityRegistry(entries=[bare])

    with pytest.raises(SelectionRefused, match="incomplete"):
        select(registry)


def test_stale_revit_build_is_refused(tmp_path: Path) -> None:
    registry = CapabilityRegistry(entries=[capability(tmp_path, revit_build="20250101_0900(x64)")])

    with pytest.raises(SelectionRefused, match="revit build"):
        select(registry)


def test_stale_tool_schema_is_refused(tmp_path: Path) -> None:
    registry = CapabilityRegistry(entries=[capability(tmp_path)])

    with pytest.raises(SelectionRefused, match="schema"):
        select(registry, tool_schema_hash=OTHER_SCHEMA_HASH)


def test_production_selection_refuses_synthetic_only_evidence(tmp_path: Path) -> None:
    synthetic = capability(tmp_path, evidence_scope=EvidenceScope.SYNTHETIC)
    registry = CapabilityRegistry(entries=[synthetic])

    with pytest.raises(SelectionRefused, match="synthetic"):
        select(registry)

    assert select(registry, scope=EvidenceScope.SYNTHETIC).provider == "horizun"


def test_unhealthy_transport_is_refused(tmp_path: Path) -> None:
    registry = CapabilityRegistry(entries=[capability(tmp_path, transport_healthy=False)])

    with pytest.raises(SelectionRefused, match="transport"):
        select(registry)


def test_write_capability_requires_independent_query(tmp_path: Path) -> None:
    writer = capability(
        tmp_path,
        tested_scope={"operation": "create_wall", "writes": True},
        independent_query=False,
        save_reopen=True,
    )
    registry = CapabilityRegistry(entries=[writer])

    with pytest.raises(SelectionRefused, match="independent"):
        select(registry, operation="create_wall")


def test_write_capability_requires_save_reopen_persistence(tmp_path: Path) -> None:
    writer = capability(
        tmp_path,
        tested_scope={"operation": "create_wall", "writes": True},
        independent_query=True,
        save_reopen=False,
    )
    registry = CapabilityRegistry(entries=[writer])

    with pytest.raises(SelectionRefused, match="save/reopen"):
        select(registry, operation="create_wall")


def test_evidence_hash_mismatch_is_refused(tmp_path: Path) -> None:
    ref = evidence_ref(tmp_path, "tampered.json", "original")
    path = ref.split("::sha256=")[0]
    Path(path).write_text("tampered", encoding="utf-8")
    registry = CapabilityRegistry(entries=[capability(tmp_path, evidence=[ref])])

    with pytest.raises(SelectionRefused, match="hash"):
        select(registry)


def test_missing_evidence_file_and_unhashed_reference_are_refused(tmp_path: Path) -> None:
    missing = str(tmp_path / "gone.json")
    registry = CapabilityRegistry(entries=[capability(tmp_path, evidence=[missing])])

    with pytest.raises(SelectionRefused, match="missing"):
        select(registry)

    unhashed = evidence_ref(tmp_path, "unhashed.json", "text").split("::sha256=")[0]
    registry = CapabilityRegistry(entries=[capability(tmp_path, evidence=[unhashed])])

    with pytest.raises(SelectionRefused, match="hash"):
        select(registry)


def test_pass_with_warnings_requires_explicit_acceptance(tmp_path: Path) -> None:
    warned = capability(tmp_path, status=CapabilityStatus.PASS_WITH_WARNINGS, warnings_delta=2)
    registry = CapabilityRegistry(entries=[warned])

    with pytest.raises(SelectionRefused, match="warnings"):
        select(registry)

    assert select(registry, accept_pass_with_warnings=True).status is (
        CapabilityStatus.PASS_WITH_WARNINGS
    )


def test_valid_matching_capability_wins_deterministically(tmp_path: Path) -> None:
    registry = CapabilityRegistry(
        entries=[
            capability(
                tmp_path,
                provider="revitcortex",
                priority=5,
                evidence=[evidence_ref(tmp_path, "cortex.json", "cortex levels")],
            ),
            capability(tmp_path, provider="horizun", priority=10),
        ]
    )

    chosen = select(registry)

    assert chosen.provider == "revitcortex"
    assert select(registry).provider == "revitcortex"


def test_plain_pass_beats_pass_with_warnings_and_lower_priority_wins(tmp_path: Path) -> None:
    registry = CapabilityRegistry(
        entries=[
            capability(
                tmp_path,
                provider="warned",
                priority=1,
                status=CapabilityStatus.PASS_WITH_WARNINGS,
                warnings_delta=1,
                evidence=[evidence_ref(tmp_path, "warned.json", "warned levels")],
            ),
            capability(tmp_path, provider="clean", priority=9),
            capability(
                tmp_path,
                provider="also-clean",
                priority=4,
                evidence=[evidence_ref(tmp_path, "also.json", "also levels")],
            ),
        ]
    )

    assert select(registry, accept_pass_with_warnings=True).provider == "also-clean"


def test_provider_name_breaks_a_priority_tie(tmp_path: Path) -> None:
    registry = CapabilityRegistry(
        entries=[
            capability(
                tmp_path,
                provider="zeta",
                priority=7,
                evidence=[evidence_ref(tmp_path, "z.json", "zeta levels")],
            ),
            capability(
                tmp_path,
                provider="alpha",
                priority=7,
                evidence=[evidence_ref(tmp_path, "a.json", "alpha levels")],
            ),
        ]
    )

    assert select(registry).provider == "alpha"


def test_registry_records_untested_fail_and_unrelated_operations(tmp_path: Path) -> None:
    registry = CapabilityRegistry()

    registry.record(capability(tmp_path, status=CapabilityStatus.UNTESTED))
    registry.record(
        capability(
            tmp_path,
            provider="revitcortex",
            status=CapabilityStatus.FAIL,
            tested_scope={"operation": "create_room", "writes": True},
        )
    )
    registry.record(capability(tmp_path, provider="bespoke", priority=1))

    assert len(registry.entries) == 3
    with pytest.raises(SelectionRefused):
        select(registry, operation="create_room")


def test_registry_round_trip_persists_equal_entries(tmp_path: Path) -> None:
    path = tmp_path / "capabilities.yaml"
    registry = CapabilityRegistry(entries=[capability(tmp_path)])

    registry.save(path)
    reloaded = CapabilityRegistry.load(path)

    assert reloaded.entries == registry.entries
    assert not list(tmp_path.glob("*.tmp"))


def test_registry_loads_the_repository_capability_file_when_present() -> None:
    repo_file = Path(__file__).resolve().parents[2] / "state" / "capabilities.yaml"
    if not repo_file.exists():
        pytest.skip("state/capabilities.yaml is created by the Revit Tool Lab")

    registry = CapabilityRegistry.load(repo_file)
    assert isinstance(registry.entries, list)
