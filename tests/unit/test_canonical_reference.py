from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from amanda_agent.design.canonical_reference import (
    CanonicalReferenceError,
    CanonicalReferenceProfile,
)

ROOT = Path(__file__).resolve().parents[2]
PROFILE_RELATIVE = Path("docs/source/references/CANONICAL_REFERENCE_PROFILE.yaml")
MANIFEST_RELATIVE = Path("docs/source/SOURCE_MANIFEST.json")
IMAGE_PATHS = (
    "canonical/01_implantacao_geral_canonica.png",
    "canonical/02_bloco_residencial_canonico.png",
    "canonical/03_bloco_administrativo_canonico.png",
)
EXPECTED_SOURCE_HASHES = (
    "d7db84c0696f0018ed0bc0525bcc2128378d05ece8e3e5c09e2162493793de7b",
    "12e35091f33352c21691eb083bf479ba2efd44af4c65774c89021b641de4a5c6",
    "80cdcccf99154d69ea87943950db420912e949d6320279695a2fd70d44ad286c",
)


def _write_reference_inputs(root: Path) -> None:
    references_root = root / "docs/source/references"
    references_root.mkdir(parents=True)
    profile = {
        "schema_version": 1,
        "status": "CANONICAL_DESIGN_REFERENCE",
        "supersedes": ["AMANDA-RUN-001-S01", "COURTYARD_DOUBLE_LOADED_BAR"],
        "program": {
            "people": 20,
            "net_internal_m2": 626.0,
            "external_programmed_m2": 260.0,
            "enclosed_estimate_m2": [783.0, 814.0],
            "covered_estimate_m2": [850.0, 950.0],
        },
        "required_parti": {
            "single_linear_bar_allowed": False,
            "admin_public_edge": True,
            "admin_storeys_target": 2,
            "residential_cluster": {
                "required": True,
                "pavilion_count_target": 4,
                "sleeping_pavilions_target": 3,
                "communal_pavilions_target": 1,
                "central_garden_required": True,
            },
            "child_sector_green_interface": True,
            "service_block_separate": True,
            "service_access_separate": True,
            "covered_external_paths_required": True,
            "landscape_is_program": True,
        },
        "privacy_gradient": [
            "PUBLIC_CITY",
            "CONTROLLED_ARRIVAL",
            "SUPPORT_TRANSITION",
            "COMMUNITY_GARDEN",
            "PROTECTED_RESIDENTIAL",
        ],
        "canonical_images": list(IMAGE_PATHS),
    }
    (references_root / PROFILE_RELATIVE.name).write_text(
        yaml.safe_dump(profile, sort_keys=False), encoding="utf-8"
    )

    assets = []
    for image_path in IMAGE_PATHS:
        relative = Path("docs/source/references") / image_path
        image = references_root / image_path
        image.parent.mkdir(parents=True, exist_ok=True)
        contents = f"synthetic reference: {image_path}".encode()
        image.write_bytes(contents)
        assets.append(
            {
                "path": relative.as_posix(),
                "role": "CANONICAL_DESIGN_REFERENCE",
                "bytes": len(contents),
                "sha256": hashlib.sha256(contents).hexdigest(),
            }
        )
    manifest = root / MANIFEST_RELATIVE
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps({"schema_version": 1, "assets": assets}), encoding="utf-8"
    )


def test_loads_user_directed_canonical_reference_profile(tmp_path: Path):
    _write_reference_inputs(tmp_path)

    profile = CanonicalReferenceProfile.load(tmp_path)

    assert profile.status == "CANONICAL_DESIGN_REFERENCE"
    assert {"AMANDA-RUN-001-S01", "COURTYARD_DOUBLE_LOADED_BAR"}.issubset(
        set(profile.supersedes)
    )
    assert profile.single_linear_bar_allowed is False
    assert profile.residential_pavilion_count_target == 4
    assert profile.admin_public_edge is True
    assert profile.admin_storeys_target == 2
    assert len(profile.canonical_images) == 3
    assert len(profile.source_hashes) == 3
    assert all(len(value) == 64 for value in profile.source_hashes)
    assert profile.data["program"]["people"] == 20


def test_loads_hashes_of_the_local_private_canonical_boards():
    if (
        not (ROOT / PROFILE_RELATIVE).is_file()
        or not (ROOT / MANIFEST_RELATIVE).is_file()
    ):
        pytest.skip("private canonical source bundle is not present in this checkout")

    profile = CanonicalReferenceProfile.load(ROOT)

    assert profile.source_hashes == EXPECTED_SOURCE_HASHES


def test_rejects_a_missing_canonical_image(tmp_path: Path):
    _write_reference_inputs(tmp_path)
    image = (
        tmp_path / "docs/source/references/canonical/01_implantacao_geral_canonica.png"
    )
    image.unlink()

    with pytest.raises(CanonicalReferenceError, match="missing"):
        CanonicalReferenceProfile.load(tmp_path)


def test_rejects_a_canonical_image_whose_hash_does_not_match_manifest(tmp_path: Path):
    _write_reference_inputs(tmp_path)
    image = (
        tmp_path / "docs/source/references/canonical/01_implantacao_geral_canonica.png"
    )
    image.write_bytes(image.read_bytes() + b"changed")

    with pytest.raises(CanonicalReferenceError, match="hash"):
        CanonicalReferenceProfile.load(tmp_path)
