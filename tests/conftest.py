from __future__ import annotations

import json
from pathlib import Path

import pytest

from amanda_agent.design.canonical_pavilion_layout import (
    build_canonical_pavilion_layout,
)
from amanda_agent.design.canonical_reference import CanonicalReferenceProfile

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
            "canonical/01_implantacao_geral_canonica.png",
            "canonical/02_bloco_residencial_canonico.png",
            "canonical/03_bloco_administrativo_canonico.png",
        ),
        source_hashes=("a" * 64, "b" * 64, "c" * 64),
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
