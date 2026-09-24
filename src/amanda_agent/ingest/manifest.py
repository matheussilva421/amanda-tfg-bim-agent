"""Immutable source metadata and streaming file hashing."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path, PurePosixPath

from pydantic import BaseModel, Field

HASH_CHUNK_SIZE = 1024 * 1024


def sha256_file(path: Path) -> str:
    """Return a file's SHA-256 without loading the whole file into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while chunk := stream.read(HASH_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


class SourceDocument(BaseModel):
    """The immutable identity and location of one ingested source file."""

    source_id: str = Field(min_length=1)
    filename: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-fA-F]{64}$")
    mime_type: str = Field(min_length=1)
    ingested_at: datetime
    immutable_path: str = Field(min_length=1)


class SourceManifest(BaseModel):
    """Versioned collection persisted at ``project/provenance``."""

    schema_version: int = 1
    documents: list[SourceDocument] = Field(default_factory=list)


def source_inventory_paths(root: Path, manifest: SourceManifest) -> set[str]:
    """Combine immutable ingested sources with the supplemental source catalog."""
    paths: set[str] = set()
    for document in manifest.documents:
        relative = PurePosixPath(document.immutable_path)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "\\" in document.immutable_path
            or relative.parts[:2] != ("docs", "source")
            or len(relative.parts) <= 2
        ):
            raise ValueError(
                "immutable source path must remain under docs/source: "
                + document.immutable_path
            )
        paths.add(PurePosixPath(*relative.parts[2:]).as_posix())

    catalog_path = Path(root) / "docs/source/SOURCE_MANIFEST.json"
    if not catalog_path.is_file():
        return paths
    if catalog_path.is_symlink():
        raise ValueError("supplemental source catalog must not be a symlink")
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("supplemental source catalog is invalid") from exc
    if not isinstance(catalog, dict) or catalog.get("schema_version") != 1:
        raise ValueError("supplemental source catalog schema is invalid")
    assets = catalog.get("assets")
    if not isinstance(assets, list):
        raise ValueError("supplemental source catalog assets must be a list")

    catalog_paths: set[str] = set()
    for asset in assets:
        if not isinstance(asset, dict) or not isinstance(asset.get("path"), str):
            raise ValueError("supplemental source catalog path is invalid")
        raw_path = asset["path"]
        relative = PurePosixPath(raw_path)
        if (
            relative.is_absolute()
            or ".." in relative.parts
            or "\\" in raw_path
            or relative.parts[:2] != ("docs", "source")
            or len(relative.parts) <= 2
        ):
            raise ValueError("supplemental asset path must remain under docs/source")
        catalog_relative = PurePosixPath(*relative.parts[2:]).as_posix()
        if catalog_relative in catalog_paths:
            raise ValueError("supplemental source catalog paths must be unique")
        catalog_paths.add(catalog_relative)

    paths.update(catalog_paths)
    paths.add("SOURCE_MANIFEST.json")
    return paths
