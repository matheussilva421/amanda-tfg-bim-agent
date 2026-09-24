"""Load and validate the user-directed canonical architectural references."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import Any

import yaml

_PROFILE_PATH = Path("docs/source/references/CANONICAL_REFERENCE_PROFILE.yaml")
_MANIFEST_PATH = Path("docs/source/SOURCE_MANIFEST.json")
_CANONICAL_ROLE = "CANONICAL_DESIGN_REFERENCE"
_REQUIRED_SUPERSEDES = {"AMANDA-RUN-001-S01", "COURTYARD_DOUBLE_LOADED_BAR"}
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$", re.IGNORECASE)


class CanonicalReferenceError(ValueError):
    """The canonical reference profile or one of its source assets is invalid."""


def _freeze(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType(
            {str(key): _freeze(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    return value


def _require_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise CanonicalReferenceError(f"{label} must be a mapping")
    return value


@dataclass(frozen=True)
class CanonicalReferenceProfile:
    """Validated canonical direction plus content identities for its boards."""

    status: str
    supersedes: tuple[str, ...]
    canonical_images: tuple[str, ...]
    source_hashes: tuple[str, ...]
    data: Mapping[str, Any] = field(repr=False)

    @property
    def single_linear_bar_allowed(self) -> bool:
        return bool(self.data["required_parti"]["single_linear_bar_allowed"])

    @property
    def admin_public_edge(self) -> bool:
        return bool(self.data["required_parti"]["admin_public_edge"])

    @property
    def admin_storeys_target(self) -> int:
        return int(self.data["required_parti"]["admin_storeys_target"])

    @property
    def residential_pavilion_count_target(self) -> int:
        cluster = self.data["required_parti"]["residential_cluster"]
        return int(cluster["pavilion_count_target"])

    @property
    def sleeping_pavilions_target(self) -> int:
        cluster = self.data["required_parti"]["residential_cluster"]
        return int(cluster["sleeping_pavilions_target"])

    @property
    def communal_pavilions_target(self) -> int:
        cluster = self.data["required_parti"]["residential_cluster"]
        return int(cluster["communal_pavilions_target"])

    @property
    def central_garden_required(self) -> bool:
        cluster = self.data["required_parti"]["residential_cluster"]
        return bool(cluster["central_garden_required"])

    @classmethod
    def load(cls, root: Path) -> CanonicalReferenceProfile:
        """Load profile and source manifest relative to a repository root."""
        root = Path(root)
        profile_path = root / _PROFILE_PATH
        manifest_path = root / _MANIFEST_PATH
        try:
            profile_value = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise CanonicalReferenceError(
                f"cannot read canonical profile: {profile_path}"
            ) from exc
        except yaml.YAMLError as exc:
            raise CanonicalReferenceError(
                f"invalid canonical profile YAML: {profile_path}"
            ) from exc

        try:
            manifest_value = json.loads(manifest_path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise CanonicalReferenceError(
                f"cannot read source manifest: {manifest_path}"
            ) from exc
        except json.JSONDecodeError as exc:
            raise CanonicalReferenceError(
                f"invalid source manifest JSON: {manifest_path}"
            ) from exc

        profile = _require_mapping(profile_value, "canonical profile")
        manifest = _require_mapping(manifest_value, "source manifest")
        if profile.get("schema_version") != 1 or manifest.get("schema_version") != 1:
            raise CanonicalReferenceError(
                "unsupported canonical profile or source manifest schema"
            )

        status = profile.get("status")
        if status != "CANONICAL_DESIGN_REFERENCE":
            raise CanonicalReferenceError(
                "profile status must be CANONICAL_DESIGN_REFERENCE"
            )
        supersedes_value = profile.get("supersedes")
        if not isinstance(supersedes_value, list) or not _REQUIRED_SUPERSEDES.issubset(
            set(supersedes_value)
        ):
            raise CanonicalReferenceError(
                "profile must supersede the linear R12 solution and bar archetype"
            )

        parti = _require_mapping(profile.get("required_parti"), "required_parti")
        cluster = _require_mapping(
            parti.get("residential_cluster"), "required_parti.residential_cluster"
        )
        required_flags = {
            "single_linear_bar_allowed": False,
            "admin_public_edge": True,
            "admin_storeys_target": 2,
            "child_sector_green_interface": True,
            "service_block_separate": True,
            "service_access_separate": True,
            "covered_external_paths_required": True,
            "landscape_is_program": True,
        }
        for key, expected in required_flags.items():
            actual = parti.get(key)
            if actual != expected or isinstance(actual, bool) != isinstance(
                expected, bool
            ):
                raise CanonicalReferenceError(
                    f"required canonical parti value is invalid: {key}"
                )
        required_cluster = {
            "required": True,
            "pavilion_count_target": 4,
            "sleeping_pavilions_target": 3,
            "communal_pavilions_target": 1,
            "central_garden_required": True,
        }
        for key, expected in required_cluster.items():
            actual = cluster.get(key)
            if actual != expected or isinstance(actual, bool) != isinstance(
                expected, bool
            ):
                raise CanonicalReferenceError(
                    f"required canonical residential cluster value is invalid: {key}"
                )

        images_value = profile.get("canonical_images")
        if not isinstance(images_value, list) or len(images_value) != 4:
            raise CanonicalReferenceError(
                "profile must declare exactly four canonical images"
            )
        if any(not isinstance(item, str) or not item for item in images_value):
            raise CanonicalReferenceError(
                "canonical image paths must be non-empty strings"
            )
        if len(set(images_value)) != len(images_value):
            raise CanonicalReferenceError("canonical image paths must be unique")

        assets_value = manifest.get("assets")
        if not isinstance(assets_value, list):
            raise CanonicalReferenceError("source manifest assets must be a list")
        canonical_assets: dict[str, Mapping[str, Any]] = {}
        for asset_value in assets_value:
            asset = _require_mapping(asset_value, "source manifest asset")
            if asset.get("role") != _CANONICAL_ROLE:
                continue
            path_value = asset.get("path")
            if not isinstance(path_value, str) or path_value in canonical_assets:
                raise CanonicalReferenceError(
                    "canonical source manifest paths must be unique strings"
                )
            canonical_assets[path_value] = asset

        expected_manifest_paths: list[str] = []
        hashes: list[str] = []
        references_root = (root / "docs/source/references").resolve()
        for image in images_value:
            relative = PurePosixPath(image)
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or "\\" in image
                or not image.startswith("canonical/")
            ):
                raise CanonicalReferenceError(f"invalid canonical image path: {image}")
            source_path = "docs/source/references/" + relative.as_posix()
            expected_manifest_paths.append(source_path)
            asset = canonical_assets.get(source_path)
            if asset is None:
                raise CanonicalReferenceError(
                    f"missing canonical source manifest entry: {source_path}"
                )
            expected_hash = asset.get("sha256")
            if not isinstance(expected_hash, str) or not _SHA256_PATTERN.fullmatch(
                expected_hash
            ):
                raise CanonicalReferenceError(
                    f"invalid canonical source hash: {source_path}"
                )
            image_path = (references_root / Path(*relative.parts)).resolve()
            try:
                image_path.relative_to(references_root)
            except ValueError as exc:
                raise CanonicalReferenceError(
                    f"invalid canonical image path: {image}"
                ) from exc
            if not image_path.is_file():
                raise CanonicalReferenceError(f"missing canonical image: {source_path}")
            actual_hash = hashlib.sha256(image_path.read_bytes()).hexdigest()
            if actual_hash.lower() != expected_hash.lower():
                raise CanonicalReferenceError(
                    f"canonical image hash mismatch: {source_path}"
                )
            expected_bytes = asset.get("bytes")
            if (
                not isinstance(expected_bytes, int)
                or isinstance(expected_bytes, bool)
                or expected_bytes <= 0
            ):
                raise CanonicalReferenceError(
                    f"invalid canonical source size: {source_path}"
                )
            if expected_bytes != image_path.stat().st_size:
                raise CanonicalReferenceError(
                    f"canonical image size mismatch: {source_path}"
                )
            hashes.append(actual_hash)

        if set(expected_manifest_paths) != set(canonical_assets):
            raise CanonicalReferenceError(
                "source manifest canonical assets must match the four profile images exactly"
            )
        return cls(
            status=status,
            supersedes=tuple(supersedes_value),
            canonical_images=tuple(images_value),
            source_hashes=tuple(hashes),
            data=_freeze(dict(profile)),
        )
