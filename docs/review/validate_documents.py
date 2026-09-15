"""Static documentation gates, not software or Revit acceptance tests."""
import argparse
import ast
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
NAMES = ["START_HERE_FOR_CODEX.md", "PLAN_SELF_REVIEW.md", "2026-09-11-amanda-tfg-bim-agent-design.md", "2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md"]

def validate():
    docs = {name: (ROOT / name).read_text(encoding="utf-8") for name in NAMES}
    start, review, design, plan = (docs[n] for n in NAMES)
    checks = []
    def check(name, ok, detail=""):
        checks.append({"check": name, "passed": bool(ok), "detail": detail})

    bad_links = []
    for name, body in docs.items():
        for target in re.findall(r"\[[^\]\n]+\]\(([^)\n]+)\)", body):
            target = unquote(target.strip("<>"))
            if re.match(r"https?://", target):
                continue
            path, _, anchor = target.partition("#")
            dest = ROOT / path if path else ROOT / name
            if not dest.is_file():
                bad_links.append(f"{name}: {target}")
            elif anchor and f'<a id="{anchor}"></a>' not in dest.read_text(encoding="utf-8"):
                bad_links.append(f"{name}: missing anchor {target}")
    check("local_links_resolve", not bad_links, "; ".join(bad_links))
    check("entry_uses_existing_combined_plan", NAMES[3] in start and "docs/superpowers/plans/00-master" not in start)
    check("no_phantom_spec_path", all("docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md" not in s for s in docs.values()))
    check("review_separates_static_from_runtime", "NOT_RUN" in review and "PASS — ready for execution handoff" not in review)
    check("program_conflict_is_explicit", all("20" in s and "42" in s and "PROGRAM_BASELINE" in s for s in (design, plan)))
    check("support_ifc_is_hypothesis", "07_modelo_BIM_HIPOTESE.ifc" in design and "DESIGN_HYPOTHESIS" in design)
    check("conceptual_gate_separate", all("CONCEPT_ONLY" in s and "approval_hash" in s for s in (design, plan)))
    check("state_includes_suspended", 'SUSPENDED = "SUSPENDED"' in plan)
    check("unimplemented_cli_nonzero", 'raise typer.Exit(code=2)' in plan)
    check("durable_execution_contract", "operation_id" in plan and "IN_DOUBT" in plan and "claim" in plan)
    check("capability_evidence_bound", "tool_schema_hash" in plan and "transport_provider" in plan and "tested_scope" in plan)
    check("solver_resolution_and_reproducibility", "num_search_workers = 1" in plan and "MACRO" in plan and "NOT_EVALUATED" in plan)
    check("private_snapshots_excluded", "state/snapshots/private/" in plan and "docs/source/" in plan)
    check("sdk_not_global_phase01_gate", "- .NET 10.0.400 available;" not in plan and "provider-specific SDK" in plan)
    check("review_execution_boundary", "REVIEW_ONLY" in start and "NOT_RUN" in start)
    check("delegated_design_decision", all("AGENT_DELEGATED" in s for s in (start, design, plan)) and "evidência humana vinculada" not in start and "Human selection gate" not in design)
    check("research_and_reversible_assumptions", all("PROVISIONAL_ASSUMPTION" in s and "decision-register" in s for s in (design, plan)) and "AMANDA_REVIEW_PENDING" in plan)
    blocks = re.findall(r"```python\n(.*?)\n```", plan, re.S)
    errors = []
    for i, block in enumerate(blocks, 1):
        try:
            ast.parse(block)
        except SyntaxError as exc:
            errors.append(f"block {i}: {exc}")
    check("python_examples_parse", not errors, "; ".join(errors))
    check("balanced_fences", all(sum(line.startswith("```") for line in s.splitlines()) % 2 == 0 for s in docs.values()))
    match = re.search(r"<!-- phase-dependencies -->\s*```json\s*(.*?)\s*```", plan, re.S)
    valid_graph = False
    detail = "Missing phase dependency contract"
    if match:
        try:
            graph = json.loads(match[1])
            done = set()
            while len(done) < len(graph):
                ready = {node for node, deps in graph.items() if node not in done and set(deps) <= done}
                if not ready:
                    raise ValueError("Cycle or unknown dependency")
                done |= ready
            valid_graph = all(k in graph for k in ("01", "02", "03", "04", "05", "06", "07A", "07B", "08", "09"))
            detail = f"{len(graph)} nodes, acyclic"
        except (ValueError, TypeError) as exc:
            detail = str(exc)
    check("phase_dependency_graph_acyclic", valid_graph, detail)
    ids = re.findall(r"^### Task .*?\[(P\d\d-T\d\d)\]", plan, re.M)
    check("unique_resumable_task_ids", len(ids) >= 150 and len(ids) == len(set(ids)), f"{len(ids)} IDs")
    return {"kind": "DOCUMENT_STATIC_CHECKS", "checks": checks, "total": len(checks), "passed": sum(c["passed"] for c in checks), "failed": sum(not c["passed"] for c in checks), "documents": {n: hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in NAMES}}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    result = validate()
    (ROOT / args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("kind", "total", "passed", "failed")}))
    print("Failures: " + ", ".join(c["check"] for c in result["checks"] if not c["passed"]))
    raise SystemExit(1 if result["failed"] else 0)
