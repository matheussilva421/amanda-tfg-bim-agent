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
    "canonical/01_implantacao.png",
    "canonical/02_administrativo.png",
    "canonical/03_residencial.png",
    "canonical/04_servicos.png",
)
EXPECTED_SOURCE_HASHES = (
    "30d009357a095e7794e0e915dcd2fdb04cd6b9aab9f4d13f5663ed54d6f20240",
    "123b95633ae1be643da84f2226c6337d65a74f7d1337d6b27d94bdead1c3a263",
    "5b96c2d5cc770742ee32d51b83b25993fe8b8a1638bf94da56ba8ef771031381",
    "c56b806f805d9c4aa1e6015ba6b56ac960204066721f93ef08cbadfb312c0386",
)
EXPECTED_SOURCE_BYTES = (
    3726070,
    3174816,
    3744066,
    3731032,
)


def _write_reference_inputs(root: Path) -> None:
    references_root = root / "docs/source/references"
    source_root = root / "docs/source"
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
        relative = Path("docs/source") / image_path
        image = source_root / image_path
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
    assert profile.canonical_images == IMAGE_PATHS
    assert len(profile.source_hashes) == 4
    assert all(len(value) == 64 for value in profile.source_hashes)
    assert profile.data["program"]["people"] == 20


def test_loads_hashes_of_the_local_private_canonical_boards():
    local_profile = yaml.safe_load((ROOT / PROFILE_RELATIVE).read_text(encoding="utf-8"))
    assert tuple(local_profile.get("canonical_images", ())) == IMAGE_PATHS

    profile = CanonicalReferenceProfile.load(ROOT)

    assert profile.source_hashes == EXPECTED_SOURCE_HASHES
    assert tuple(
        (ROOT / "docs/source" / image).stat().st_size
        for image in IMAGE_PATHS
    ) == EXPECTED_SOURCE_BYTES


def test_local_canonical_board_assets_match_expected_hashes_and_sizes():
    image_paths = tuple(
        ROOT / "docs/source" / image for image in IMAGE_PATHS
    )
    assert tuple(
        hashlib.sha256(image.read_bytes()).hexdigest() for image in image_paths
    ) == EXPECTED_SOURCE_HASHES
    assert tuple(image.stat().st_size for image in image_paths) == EXPECTED_SOURCE_BYTES


def test_local_program_and_tfg_sources_use_normalized_manifest_paths():
    manifest = json.loads((ROOT / MANIFEST_RELATIVE).read_text(encoding="utf-8"))
    expected = {
        "PROGRAM_OFFICIAL": (
            "docs/source/programa_necessidades.pdf",
            31004,
            "11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17",
        ),
        "TFG_SOURCE": (
            "docs/source/TFG.pdf",
            54553582,
            "16abe602ac50643482ce3c782780b4135fa8468b5ca814061fe426c8ca292a7e",
        ),
    }
    assets = {asset["role"]: asset for asset in manifest["assets"]}

    for role, (path, size, sha256) in expected.items():
        asset = assets[role]
        assert (asset["path"], asset["bytes"], asset["sha256"]) == (
            path,
            size,
            sha256,
        )
        source = ROOT / path
        if source.is_file():
            assert source.stat().st_size == size
            assert hashlib.sha256(source.read_bytes()).hexdigest() == sha256


def test_rejects_a_missing_canonical_image(tmp_path: Path):
    _write_reference_inputs(tmp_path)
    image = (
        tmp_path / "docs/source/canonical/01_implantacao.png"
    )
    image.unlink()

    with pytest.raises(CanonicalReferenceError, match="missing"):
        CanonicalReferenceProfile.load(tmp_path)


def test_rejects_a_canonical_image_whose_hash_does_not_match_manifest(tmp_path: Path):
    _write_reference_inputs(tmp_path)
    image = (
        tmp_path / "docs/source/canonical/01_implantacao.png"
    )
    image.write_bytes(image.read_bytes() + b"changed")

    with pytest.raises(CanonicalReferenceError, match="hash"):
        CanonicalReferenceProfile.load(tmp_path)


def test_rejects_a_canonical_manifest_path_not_declared_by_profile(tmp_path: Path):
    _write_reference_inputs(tmp_path)
    manifest_path = tmp_path / MANIFEST_RELATIVE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["assets"].append(
        {
            "path": "docs/source/canonical/extra.png",
            "role": "CANONICAL_DESIGN_REFERENCE",
            "bytes": 1,
            "sha256": "0" * 64,
        }
    )
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(CanonicalReferenceError, match="match the four profile images"):
        CanonicalReferenceProfile.load(tmp_path)


def test_rejects_a_canonical_manifest_entry_without_expected_size(tmp_path: Path):
    _write_reference_inputs(tmp_path)
    manifest_path = tmp_path / MANIFEST_RELATIVE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["assets"][-1].pop("bytes")
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(CanonicalReferenceError, match="size"):
        CanonicalReferenceProfile.load(tmp_path)


def test_rejects_a_canonical_image_whose_size_does_not_match_manifest(tmp_path: Path):
    _write_reference_inputs(tmp_path)
    manifest_path = tmp_path / MANIFEST_RELATIVE
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["assets"][-1]["bytes"] += 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(CanonicalReferenceError, match="size"):
        CanonicalReferenceProfile.load(tmp_path)
