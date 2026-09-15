from pathlib import Path
from zipfile import ZipFile
import sys
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
sys.stdout.reconfigure(encoding="utf-8")
archive = ROOT / "amanda-tfg-bim-agent-superpowers-plan.zip"
with ZipFile(archive) as z:
    files = {n: z.read(n) for n in z.namelist() if not n.endswith("/")}
    comparisons = []
    for original in (ROOT / "docs/review/originals-2026-09-15").glob("*.md"):
        matches = [n for n in files if n.endswith("/"+original.name)]
        comparisons.append({"file": original.name, "zip_entry": matches[0] if len(matches)==1 else None,
                            "identical": len(matches)==1 and files[matches[0]] == original.read_bytes()})
    prefix = "amanda-tfg-bim-agent-handoff/docs/superpowers/plans/"
    children = sorted(n for n in files if re.search(r"/\d\d-[^/]+\.md$", n))
    combined = files[prefix+"2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md"].decode("utf-8")
    child_checks = [{"entry": n, "contained_in_combined": files[n].decode("utf-8").strip() in combined} for n in children]
    sums = files["amanda-tfg-bim-agent-handoff/SHA256SUMS.txt"].decode("utf-8")
    checksums = []
    for line in sums.splitlines():
        digest, rel = line.split(maxsplit=1)
        entry = "amanda-tfg-bim-agent-handoff/" + rel.lstrip("* ").removeprefix("./")
        checksums.append({"entry": entry, "valid": entry in files and hashlib.sha256(files[entry]).hexdigest()==digest})
    result = {"archive": archive.name, "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
              "files": len(files), "comparisons": comparisons, "child_plans": child_checks, "checksums": checksums}
    (ROOT/"docs/review/archive-comparison.json").write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({"files": len(files), "root_identical": sum(c["identical"] for c in comparisons),
                      "child_plans": len(children), "children_in_combined": sum(c["contained_in_combined"] for c in child_checks),
                      "hashes_valid": sum(c["valid"] for c in checksums), "hashes_total": len(checksums)}))
    print(files["amanda-tfg-bim-agent-handoff/README.md"].decode("utf-8"))
