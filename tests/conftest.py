from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from amanda_agent.design.canonical_pavilion_layout import (
    build_canonical_pavilion_layout,
)
from amanda_agent.design.canonical_reference import CanonicalReferenceProfile
from amanda_agent.production.canonical_identity import (
    OFFICIAL_PROGRAM_PATH,
    RECONCILIATION_REPORT_PATH,
    CanonicalSolutionIdentity,
    SourceHashBinding,
)
from amanda_agent.requirements.program import PROGRAM_SOURCE_SHA256

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def canonical_program() -> dict:
    return json.loads(
        (ROOT / "project" / "requirements" / "program.json").read_text(encoding="utf-8")
    )


@pytest.fixture(scope="session")
def canonical_profile() -> CanonicalReferenceProfile:
    cluster = {
        "required": True,
        "pavilion_count_target": 4,
        "sleeping_pavilions_target": 3,
        "communal_pavilions_target": 1,
        "central_garden_required": True,
    }
    parti = {
        "single_linear_bar_allowed": False,
        "admin_public_edge": True,
        "admin_storeys_target": 2,
        "residential_cluster": cluster,
        "child_sector_green_interface": True,
        "service_block_separate": True,
        "service_access_separate": True,
        "covered_external_paths_required": True,
        "landscape_is_program": True,
    }
    return CanonicalReferenceProfile(
        status="CANONICAL_DESIGN_REFERENCE",
        supersedes=("AMANDA-RUN-001-S01", "COURTYARD_DOUBLE_LOADED_BAR"),
        canonical_images=(
            "canonical/01_implantacao.png",
            "canonical/02_administrativo.png",
            "canonical/03_residencial.png",
            "canonical/04_servicos.png",
        ),
        source_hashes=("a" * 64, "b" * 64, "c" * 64, "d" * 64),
        data={
            "program": {
                "people": 20,
                "net_internal_m2": 626.0,
                "external_programmed_m2": 260.0,
                "enclosed_estimate_m2": [783.0, 814.0],
                "covered_estimate_m2": [850.0, 950.0],
            },
            "required_parti": parti,
        },
    )


@pytest.fixture(scope="session")
def canonical_layout(canonical_program, canonical_profile):
    return build_canonical_pavilion_layout(canonical_program, canonical_profile)


@pytest.fixture(scope="session")
def canonical_test_identity(canonical_profile):
    """Synthetic but source-bound identity for non-executing planner tests."""
    boards = tuple(
        SourceHashBinding(path=f"docs/source/{path}", sha256=digest)
        for path, digest in zip(
            canonical_profile.canonical_images,
            canonical_profile.source_hashes,
            strict=True,
        )
    )
    program = SourceHashBinding(
        path=OFFICIAL_PROGRAM_PATH,
        sha256=PROGRAM_SOURCE_SHA256,
    )
    report = SourceHashBinding(
        path=RECONCILIATION_REPORT_PATH,
        sha256="e" * 64,
    )
    material = {
        "canonical_boards": [item.model_dump(mode="json") for item in boards],
        "program_source": program.model_dump(mode="json"),
        "reconciliation_id": "P1-T01",
        "reconciliation_report": report.model_dump(mode="json"),
    }
    encoded = json.dumps(
        material, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    fingerprint = hashlib.sha256(encoded).hexdigest()
    return CanonicalSolutionIdentity(
        solution_id="AMANDA-RUN-003-PAVILION-CANONICAL-" + fingerprint[:12].upper(),
        identity_fingerprint=fingerprint,
        canonical_boards=boards,
        program_source=program,
        reconciliation_id="P1-T01",
        reconciliation_report=report,
    )
