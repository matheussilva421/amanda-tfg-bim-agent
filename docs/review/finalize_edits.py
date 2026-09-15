"""Final editorial reconciliation after inspection of the supplied ZIP."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md"
D = ROOT / "2026-09-11-amanda-tfg-bim-agent-design.md"
p = P.read_text(encoding="utf-8")
d = D.read_text(encoding="utf-8")
p=p.replace("Every child plan produces", "Every phase produces")
p=p.replace("Topography enum:\n- `MISSING`\n- `PLANAR_PLACEHOLDER`\n- `VERIFIED_TOPOGRAPHY`", "Source topography enum: `MISSING`, `VERIFIED_TOPOGRAPHY`. Separate representation enum: `PLANAR_PLACEHOLDER`, `VERIFIED_TOPOGRAPHY`. A local drawing plane may use z=0 as a design convention, but no surveyed elevation points are emitted for MISSING sources.")
p=p.replace("- [ ] Test missing topography yields no Z points.", "- [ ] Test missing topography yields no claimed surveyed Z points; any local z=0 plane is explicitly a synthetic design reference.")
p=p.replace("- [ ] A CRITICAL issue forces overall FAIL.", "- [ ] A CRITICAL issue or failed mandatory HIGH check forces overall FAIL; aggregation includes scope/mandatory flag. Missing mandatory checks block the relevant release profile, even when no defects are present.")
p=p.replace('    revit_stage: str = "R00"', '    revit_stage: str | None = None  # no model before verified R00')
p=p.replace("- [ ] Set exactly one solution status to `APPROVED_FOR_BIM`.", "- [ ] Set exactly one solution for the current project/run baseline to APPROVED_FOR_BIM; retain earlier approvals as superseded and bind active selection to approval_hash.")
p=p.replace("task soft/hard time limits are per-task config;", "task soft/hard time limits are per-task config; hard timeout stops new dispatch and enters reconciliation, not automatic lock release or an overlapping fallback;")
p=p.replace("- [ ] Close Revit/Codex normally.", "- [ ] Persist handoff before closing owned Revit/Codex normally; following steps run in a new session with separate evidence.")
p=p.replace("Task IDs use `P<phase>-T<two-digit task>`;", "Within a phase, numeric order is reading order, not an implicit dependency. Explicit exceptions: P06-T14 promotion depends on P06-T15 visual review; P08-T19 preparation depends on P08-T17 exports, and P08-T18 sealing depends on P08-T19. Build the task DAG from actual inputs/outputs and reject cycles.\n\nTask IDs use `P<phase>-T<two-digit task>`;")
p=p.replace("## Global Constraints\n\n- Detect the exact installed Revit 2027 build;", "## Global Constraints\n\n- Every code task follows behavioral RED → minimal implementation → GREEN; run RED before the implementation snippet, distinguishing harness/import setup from the intended failing assertion. Record command/counts/evidence and commit/push status.\n- Shell blocks are conditional future steps, not one pasteable script. Check native exit codes and stop on failed clone/build/install before registration. Validate discovered paths/version variables before use; do not guess an executable by first match or newest timestamp.\n- Importable Python code lives only under src/amanda_agent; top-level subsystem folders hold configuration, fixtures or artifacts, not duplicate implementations.\n- Detect the exact installed Revit 2027 build;")
d=d.replace("Example:\n\n```yaml\ncreate_wall:", "Illustrative record before testing (not production-eligible):\n\n```yaml\ncreate_wall:")
d=d.replace("  preferred: horizun\n  providers:\n    horizun:\n      status: PASS\n      save_reopen: PASS\n    revitcortex:\n      status: PASS", "  preferred: null\n  providers:\n    horizun:\n      status: UNTESTED\n      save_reopen: false\n    revitcortex:\n      status: UNTESTED")
d=d.replace("The final implementation may replace a candidate only after tool evaluation.", "The final implementation may replace a candidate only after tool evaluation. Layout diagrams describe responsibilities; importable Python lives only under src/amanda_agent as specified in the plan. Top-level subsystem folders hold configuration/artifacts, avoiding duplicate implementations.")
d=d.replace("Only one active BIM executor may modify a given RVT at a time.", "Only one active BIM executor may modify the owned Revit process/document at a time across providers, worktrees and sessions. Serialize reads too where required by Revit's API/UI thread.")
P.write_text(p,encoding="utf-8")
D.write_text(d,encoding="utf-8")
print("Final cross-document edits applied")
