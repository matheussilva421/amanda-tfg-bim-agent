"""Immutable source metadata and streaming file hashing."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

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
