"""Deterministic sanity review for sheet and page PNG previews.

Raster findings are evidence for visual review only.  They cannot establish
normative or architectural acceptance, so every machine finding carries the
VISUAL_REVIEW classification and normative=False.
"""

from __future__ import annotations

import struct
import zlib
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class VisualFinding(BaseModel):
    """One machine-detected visual review signal."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    classification: str = "VISUAL_REVIEW"
    normative: bool = False
    severity: str = "REVIEW"


class HumanReviewItem(BaseModel):
    """A precise preview path that needs human or vision inspection."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    reason: str = Field(min_length=1)


class VisualReviewReport(BaseModel):
    """Machine signals and the human review queue for a preview set."""

    model_config = ConfigDict(extra="forbid")

    schema_version: int = 1
    previews: list[str] = Field(default_factory=list)
    findings: list[VisualFinding] = Field(default_factory=list)
    human_review_queue: list[HumanReviewItem] = Field(default_factory=list)
    image_inspection_available: bool = False
    normative_visual_pass: bool = False
    status: str = "BLOCKED_BY_INPUT"
    limitations: list[str] = Field(default_factory=list)


def collect_png_previews(root: str | Path) -> list[Path]:
    """Collect PNG previews in deterministic relative-path order."""

    base = Path(root)
    if not base.is_dir():
        return []
    return sorted(
        (path for path in base.rglob("*") if path.is_file() and path.suffix.lower() == ".png"),
        key=lambda path: path.relative_to(base).as_posix().casefold(),
    )


def _paeth(left: int, above: int, upper_left: int) -> int:
    estimate = left + above - upper_left
    left_distance = abs(estimate - left)
    above_distance = abs(estimate - above)
    upper_left_distance = abs(estimate - upper_left)
    if left_distance <= above_distance and left_distance <= upper_left_distance:
        return left
    if above_distance <= upper_left_distance:
        return above
    return upper_left


def _png_raster(path: Path) -> tuple[int, int, int, list[bytes]] | None:
    """Decode the common 8-bit PNG colour modes without optional packages."""

    data = path.read_bytes()
    if not data.startswith(b"\x89PNG\r\n\x1a\n"):
        return None
    offset = 8
    idat: list[bytes] = []
    width = height = bit_depth = colour_type = 0
    while offset + 12 <= len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        chunk_start = offset + 8
        chunk_end = chunk_start + length
        if chunk_end + 4 > len(data):
            return None
        chunk = data[chunk_start:chunk_end]
        offset = chunk_end + 4
        if kind == b"IHDR" and len(chunk) == 13:
            width, height, bit_depth, colour_type, _, _, _ = struct.unpack(
                ">IIBBBBB", chunk
            )
        elif kind == b"IDAT":
            idat.append(chunk)
        elif kind == b"IEND":
            break
    if not width or not height or bit_depth != 8 or colour_type not in {0, 2, 3, 4, 6}:
        return None
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colour_type]
    stride = width * channels
    try:
        decompressed = zlib.decompress(b"".join(idat))
    except zlib.error:
        return None
    if len(decompressed) < height * (stride + 1):
        return None
    rows: list[bytes] = []
    previous = bytes(stride)
    cursor = 0
    for _ in range(height):
        filter_type = decompressed[cursor]
        current = bytearray(decompressed[cursor + 1 : cursor + 1 + stride])
        cursor += stride + 1
        for index in range(stride):
            left = current[index - channels] if index >= channels else 0
            above = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                current[index] = (current[index] + left) & 0xFF
            elif filter_type == 2:
                current[index] = (current[index] + above) & 0xFF
            elif filter_type == 3:
                current[index] = (current[index] + ((left + above) // 2)) & 0xFF
            elif filter_type == 4:
                current[index] = (current[index] + _paeth(left, above, upper_left)) & 0xFF
            elif filter_type != 0:
                return None
        row = bytes(current)
        rows.append(row)
        previous = row
    return width, height, channels, rows


def _is_blank(path: Path) -> bool:
    raster = _png_raster(path)
    if raster is None:
        return False
    _, _, channels, rows = raster
    samples: list[int] = []
    for row in rows:
        for index in range(0, len(row), channels):
            colour = row[index : index + min(channels, 3)]
            samples.append(sum(colour) // len(colour))
    if not samples:
        return True
    return max(samples) - min(samples) <= 1


def _edge_occupancy(path: Path) -> float:
    raster = _png_raster(path)
    if raster is None:
        return 0.0
    width, height, channels, rows = raster
    if width < 2 or height < 2:
        return 0.0

    def occupied(row: bytes, index: int) -> bool:
        values = row[index * channels : index * channels + min(channels, 3)]
        return bool(values) and sum(values) / len(values) < 245

    edge_count = 0
    occupied_count = 0
    for x in range(width):
        for y in (0, height - 1):
            edge_count += 1
            occupied_count += occupied(rows[y], x)
    for y in range(1, height - 1):
        for x in (0, width - 1):
            edge_count += 1
            occupied_count += occupied(rows[y], x)
    return occupied_count / edge_count if edge_count else 0.0


def review_visuals(
    root: str | Path,
    *,
    image_inspection_available: bool = False,
    previews: Iterable[str | Path] | None = None,
) -> VisualReviewReport:
    """Review PNG previews and preserve an exact human-review queue."""

    base = Path(root)
    if previews is not None:
        paths: list[Path] = []
        for item in previews:
            path = Path(item)
            paths.append(path if path.is_absolute() else base / path)
    else:
        paths = collect_png_previews(base)
    relative_paths: list[str] = []
    findings: list[VisualFinding] = []
    queue: list[HumanReviewItem] = []
    for path in sorted(paths, key=lambda item: item.as_posix().casefold()):
        try:
            relative = path.relative_to(base).as_posix()
        except ValueError:
            relative = path.name
        relative_paths.append(relative)
        if _is_blank(path):
            findings.append(
                VisualFinding(
                    path=relative,
                    code="blank_page",
                    message="raster variance is below the blank-page threshold",
                    severity="HIGH",
                )
            )
        if _edge_occupancy(path) >= 0.90:
            findings.append(
                VisualFinding(
                    path=relative,
                    code="viewport_overflow",
                    message="dense content reaches nearly every viewport edge",
                )
            )
        if not image_inspection_available:
            queue.append(
                HumanReviewItem(
                    path=relative,
                    reason="Codex image inspection is unavailable; inspect the exact preview manually",
                )
            )
    limitations: list[str] = [
        "machine raster signals are VISUAL_REVIEW evidence, never normative proof"
    ]
    if not image_inspection_available:
        limitations.append("human visual inspection is pending for every collected preview")
    status = "BLOCKED_BY_INPUT" if queue else ("VISUAL_REVIEW" if findings else "REVIEWED")
    return VisualReviewReport(
        previews=relative_paths,
        findings=findings,
        human_review_queue=queue,
        image_inspection_available=image_inspection_available,
        normative_visual_pass=False,
        status=status,
        limitations=limitations,
    )


def analyze_visuals(root: str | Path, **kwargs: Any) -> VisualReviewReport:
    """Compatibility name for callers that use analysis terminology."""

    return review_visuals(root, **kwargs)


review_documentation_visuals = review_visuals


__all__ = [
    "HumanReviewItem",
    "VisualFinding",
    "VisualReviewReport",
    "analyze_visuals",
    "collect_png_previews",
    "review_documentation_visuals",
    "review_visuals",
]
