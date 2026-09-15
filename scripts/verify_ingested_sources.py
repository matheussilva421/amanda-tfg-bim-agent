"""Re-verify that every manifest entry still matches its immutable copy."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import yaml


def main(root: Path) -> int:
    manifest_path = root / "project" / "provenance" / "source-manifest.yaml"
    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    documents = manifest["documents"]
    print(f"documents: {len(documents)}")
    failures = 0
    for document in documents:
        relative = document["immutable_path"]
        path = root / relative
        if not path.is_file():
            print(f"MISSING  {document['source_id']}  {relative}")
            failures += 1
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        status = "MATCH" if digest == document["sha256"] else "MISMATCH"
        if status == "MISMATCH":
            failures += 1
        print(
            f"{status:8s} {document['source_id']:16s} {path.stat().st_size:>10d}  "
            f"{relative}"
        )
    print(f"failures: {failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1] if len(sys.argv) > 1 else ".")))
