"""Generate child plans from the canonical combined document and package safe docs."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from urllib.parse import unquote
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
COMBINED = "2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md"
NAMES = ["00-master-implementation-plan.md", "01-foundation-environment-state.md", "02-revit-tool-lab-providers.md", "03-project-intelligence.md", "04-design-engine.md", "05-bim-compiler.md", "06-qa-release-exports.md", "07-autonomy-recovery-security.md", "08-amanda-production-run.md", "09-optional-render-cloud.md"]
content = (ROOT/COMBINED).read_text(encoding="utf-8")
parts = re.split(r'(?=<a id="phase-\d\d"></a>)', content)
parts = [s for s in parts if s.strip()]
assert len(parts)==10
out = ROOT/"docs/superpowers/plans"
out.mkdir(parents=True,exist_ok=True)
generated=[]
for i,(name,section) in enumerate(zip(NAMES,parts)):
    assert section.startswith(f'<a id="phase-{i:02d}"></a>')
    section=section.rstrip()+"\n"
    def relink(match):
        label,target = match.groups()
        if target.startswith(("https://","http://")):
            return match[0]
        dest = COMBINED+target if target.startswith("#") else target
        return f"[{label}](../../../{dest})"
    derived = re.sub(r'\[([^\]\n]+)\]\(([^)\n]+)\)', relink, section)
    header=f"> GERADO de [{COMBINED}](../../../{COMBINED}#phase-{i:02d}) em 2026-09-15. Edite o COMBINED e execute `docs/review/package_review.py`; não edite esta cópia. Caminhos operacionais no texto são relativos à raiz do projeto.\n\n"
    target=out/name
    target.write_text(header+derived,encoding="utf-8")
    generated.append({"path":target.relative_to(ROOT).as_posix(), "canonical_section_sha256":hashlib.sha256(section.encode()).hexdigest(), "sha256":hashlib.sha256(target.read_bytes()).hexdigest()})
(ROOT/"docs/review/generated-plans-manifest.json").write_text(json.dumps(generated,indent=2)+"\n",encoding="utf-8")

paths=[ROOT/name for name in ("START_HERE_FOR_CODEX.md", "PLAN_SELF_REVIEW.md", "2026-09-11-amanda-tfg-bim-agent-design.md", COMBINED)]
paths += sorted(out.glob("*.md"))
paths += [ROOT/"docs/notes/2026-09-15-revisao-planos-handoff.md"]
paths += [ROOT/"docs/review"/name for name in ("validate_documents.py","package_review.py","validation-before.json","validation-after.json","archive-comparison.json","generated-plans-manifest.json")]
assert all(p.is_file() for p in paths)
bad=[]
for path in paths:
    if path.suffix!=".md": continue
    for target in re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)',path.read_text(encoding="utf-8")):
        if target.startswith(("https://","http://")):continue
        relative,_,anchor=unquote(target).partition("#")
        dest=(path.parent/relative).resolve() if relative else path
        if dest not in paths or not dest.is_file():bad.append(str(path)+": "+target)
        elif anchor and f'<a id="{anchor}"></a>' not in dest.read_text(encoding="utf-8"):
            bad.append(str(path)+": missing anchor "+target)
assert not bad,bad

archive=ROOT/"amanda-tfg-bim-agent-planos-REVISADOS-2026-09-15.zip"
entries={p.relative_to(ROOT).as_posix():p.read_bytes() for p in paths}
entries["README.md"]=("# Planos Amanda revisados em 2026-09-15\n\nLeia START_HERE_FOR_CODEX.md. Os quatro Markdown da raiz são canônicos; docs/superpowers/plans contém cópias por fase geradas do COMBINED. Este pacote contém documentação e evidências estáticas, não implementação nem fontes acadêmicas. O ZIP original foi preservado no workspace. Revit/runtime: NOT_RUN.\n").encode()
entries["SHA256SUMS.txt"]="".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name,data in sorted(entries.items())).encode()
with ZipFile(archive,"w",ZIP_DEFLATED) as z:
    for name,data in entries.items():z.writestr(name,data)
with ZipFile(archive) as z:
    assert z.testzip() is None
    assert all(z.read(name)==data for name,data in entries.items())
    for line in z.read("SHA256SUMS.txt").decode().splitlines():
        digest,name=line.split("  ",1)
        assert hashlib.sha256(z.read(name)).hexdigest()==digest
report={"generated_plans":10,"linked_markdown_files":sum(p.suffix==".md" for p in paths),"broken_local_links":0,"zip_entries":len(entries),"verified_hashes":len(entries)-1,"archive":archive.name,"archive_sha256":hashlib.sha256(archive.read_bytes()).hexdigest(),"status":"PASS_PACKAGE"}
(ROOT/"docs/review/package-validation.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print(json.dumps(report))
