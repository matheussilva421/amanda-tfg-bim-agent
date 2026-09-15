"""One-time, exact-match editorial changes; preserve the original bundle."""
from pathlib import Path
import hashlib
import json
import re
import shutil

ROOT = Path(__file__).resolve().parents[2]
NAMES = ["START_HERE_FOR_CODEX.md", "PLAN_SELF_REVIEW.md", "2026-09-11-amanda-tfg-bim-agent-design.md", "2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md"]
BACKUP = ROOT / "docs/review/originals-2026-09-15"
BACKUP.mkdir(exist_ok=True)
for name in NAMES:
    dest = BACKUP / name
    if not dest.exists():
        shutil.copy2(ROOT / name, dest)
(BACKUP / "manifest.json").write_text(json.dumps({n: hashlib.sha256((BACKUP/n).read_bytes()).hexdigest() for n in NAMES}, indent=2)+"\n", encoding="utf-8")

design = (BACKUP / NAMES[2]).read_text(encoding="utf-8")
plan = (BACKUP / NAMES[3]).read_text(encoding="utf-8")

def replace(text, old, new):
    if old not in text:
        raise ValueError(f"Missing edit target: {old[:110]}")
    return text.replace(old, new)

design = replace(design, "**Status:** Approved design, pending written-spec review", "**Status:** REVISED_DOCUMENT — revisão documental em 2026-09-15; implementação e validação Revit NOT_RUN")
design = replace(design, "**Autonomy model:** Maximum autonomy; human intervention only for UAC, authentication/licensing, irreducible missing source data, architectural approval gates, or external irreversible actions", "**Autonomy model:** Maximum autonomy within the user's current authorized task; this document describes future implementation and does not itself authorize installs, process termination, cloud uploads, or final architectural selection")
design = replace(design, "# 12. Final approved architecture", "# 12. Proposed architecture after document review")
intro = '''
<a id="project-baseline"></a>
## 1.1 Contexto documental e decisões ainda abertas

O objeto é um centro de acolhimento temporário para mulheres em situação de violência e seus filhos em Natal/RN. O TFG articula abrigo, transição e cidade, privacidade, fluxos controlados e blocos relacionados a jardins. Esses princípios orientam alternativas; não aprovam automaticamente a implantação já desenhada nos materiais auxiliares.

Esta especificação trata da automação de arquitetura/BIM. A conclusão do software ou de um GOLDEN técnico não equivale à conclusão acadêmica do TFG. Visitas, definição tipológica, validação com a orientadora, autoria, datas de banca e submissão institucional têm responsáveis e evidências próprios.

| Fonte local examinada | Evidência | Tratamento no projeto |
|---|---|---|
| `TFG_Amanda Fernandes_ENTREGA 15.06.2026.pdf` | 82 páginas; capítulo 3 contém as diretrizes; capítulo 5 contém condicionantes e lacunas | Fonte do caderno nessa versão; cada afirmação conserva página e hash. Não é levantamento cadastral nem texto normativo primário. |
| `programa_necessidades.pdf`, pp. 1–2 | Até 20 pessoas; setores internos 53 + 209 + 52 + 80 + 81 + 151 = 626 m²; externos 260 m²; estimativas fechada 783–814 e coberta 850–950 m² | Programa de pré-dimensionamento, sujeito a decisão de baseline. Área unitária não é automaticamente mínimo normativo. |
| `TFG_Amanda_2026/4_PROJETO_E_CALCULOS/01_programa_de_necessidades.xlsx` | `Premissas!C15:C16` = 12 × 3,5; `C27` calcula 42 pessoas; entradas explicitamente hipotéticas | Versão alternativa, não soma nem substitui silenciosamente o PDF. Fórmula, valor de entrada e resultado recalculado ficam separados. |
| `TFG_Amanda_2026/1_COMECE_AQUI/01_COMECE_AQUI.pdf`, pp. 1–2 | Implantação, visitas e levantamento permanecem pendentes; desenhos HIPÓTESE não são decisões da autora | Registro de lacunas e orientações de apoio; conferir com Amanda. |
| `TFG_Amanda_2026/1_COMECE_AQUI/02_plano_de_acompanhamento.pdf`, pp. 2–5 | Tipologia, capacidade, terreno, pesquisa, estudo preliminar, anteprojeto e defesa | Matriz acadêmica separada, a confirmar no regulamento institucional e calendário vigentes. |
| `TFG_Amanda_2026/4_PROJETO_E_CALCULOS/06_implantacao_HIPOTESE.dxf` e `07_modelo_BIM_HIPOTESE.ifc` | Arquivos existentes, identificados como hipótese | `DESIGN_HYPOTHESIS`; servem para comparação/intercâmbio em cópias, não para contornar seleção ou provar topografia. |
| `TFG_Amanda_2026/3_VERIFICACAO_E_DADOS/01_verificacao_urbanistica_LC208.docx` | Parecer de apoio com artigos e ressalvas | Índice de questões a conferir em fontes oficiais; não converter seu título “verificação” em status `VERIFIED`. |
| `TFG_Amanda_2026/4_PROJETO_E_CALCULOS/02_memorial_de_calculo.xlsx` | Capacidade derivada da planilha; índices e reserva de incêndio hipotéticos; área de vagas digitada | Recalcular somente após baseline; confirmar normas/fontes e vínculos, sem importar resultados como conformidade. |

Decisões e bloqueadores que devem ser criados na ingestão:

- `PROGRAM_BASELINE`: selecionar explicitamente PDF de 20 pessoas, cenário hipotético de 42 ou nova versão conciliada. Até lá, permitir cenários separados e desenvolvimento sintético; bloquear congelamento do programa de produção. Pessoas, famílias, leitos, equipe e visitantes são grandezas distintas.
- `TYPOLOGY`: confirmar o modelo institucional e sua política de sigilo/acesso com Amanda/orientadora; a revisão não resolve a contradição apenas renomeando casa-abrigo como centro.
- `SITE_BOUNDARY`: os 24.135 m² informados e a divergência de três/quatro frentes precisam de documento/levantamento que defina polígono, confrontações, norte e área utilizável. Área escalar e imagem sem calibração não definem um lote executável.
- `SITE_OCCUPANCY`: registrar a ocupação mencionada da CPChoque e a realocação como premissa acadêmica a confirmar, sem presumir terreno vazio/disponível.
- `SITE_TOPOGRAPHY`: faltam cotas verificadas. `PLANAR_PLACEHOLDER` permite referência esquemática explicitamente artificial; não comprova terreno plano real.
- `REGULATION_APPLICABILITY`: verificar lei consolidada, anexos/mapas, uso, recuos, coeficientes, permeabilidade, altura, acessibilidade e incêndio aplicáveis. As conclusões sobre 22.500 m², 140 m, fruição pública ou área militar no apoio não são decisões legais desta revisão.

`SOURCE_FACT` significa “esta versão da fonte afirma X”, não “X é verdadeiro, vigente ou aprovado”. Além da classe, registrar `verification_status` (`UNVERIFIED`, `VERIFIED`, `DISPUTED`, `SUPERSEDED`) e `adoption_status` (`PROPOSED`, `ACCEPTED`, `REJECTED`). Uma hipótese contida em documento continua hipótese. Resolver conflito cria nova decisão/versionamento; preservar o registro original.

## 1.2 Autoridade documental

O ponto de entrada é [START_HERE_FOR_CODEX.md](START_HERE_FOR_CODEX.md). Este design define contratos; o [plano combinado](2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-00) contém o mestre e as nove fases. Não existem planos filhos separados nesta entrega. A [revisão](PLAN_SELF_REVIEW.md) registra achados e limites da validação. Caminhos `src/`, `state/`, `project/` e `bim/` descritos a seguir são saídas futuras, não arquivos já implementados.

'''
design = replace(design, "## 2. Scope", intro + "## 2. Scope")
design = replace(design, "No stage skipping.", "Every stage is accounted for. A stage may record supported checks plus explicit blocked checks under a STUDY profile; blocked checks never become PASS. FINAL requires every mandatory stage/check complete.")
design = replace(design, "- selected design approved;", "- execution mode valid: `CONCEPT_ONLY` for reviewed finalists through R04, `SYNTHETIC_LAB` for fixtures, or content-bound approval for detailed production;")
design = replace(design, "Only a solution with:\n\n```yaml\nstatus: APPROVED_FOR_BIM\n```\n\nmay enter detailed BIM compilation.", '''Detailed production R05–R16 requires an explicit selection record with approver, timestamp, solution ID, `approval_hash` of canonical geometry/program/site/constraints/material intent, and evidence of the decision. `APPROVED_FOR_BIM` is valid only while these contents match. Any substantive change invalidates approval and returns the candidate for review.

`CONCEPT_ONLY` permits validated finalists R00–R04 in separate candidate files before selection. It forbids detailed stages and release promotion. `SYNTHETIC_LAB` is restricted to fixtures and cannot authorize Amanda production.''')
design = replace(design, "No `RELEASE_CANDIDATE` without persistence verification.", "The RC path is initially provisional; R15 becomes verified only after cold reopen and QA. Hash the closed, finalized file. Compare semantic state on reopen; RVT bytes may change after a later save, which requires new hashes and evidence.")
design = replace(design, "GOLDEN files are immutable.", '''GOLDEN files are immutable. Assemble all exports, previews, reports and provenance in staging before publication; validate hashes and then publish a new directory without overwrite. Never add reports to an already sealed GOLDEN.

Release profiles: `STUDY` may contain declared missing survey/normative checks and must display those limitations. `FINAL` requires all mandatory checks and academic scope agreed for that release. A STUDY GOLDEN proves reproducibility of its stated scope, not final compliance or academic completion.''')
design = replace(design, "Block modifications when the file path indicates source/master/GOLDEN.", "Resolve the canonical path and file identity, enforce a configured writable-root allowlist, reject junction/symlink/hardlink escapes, and check the protected-source/baseline/checkpoint/release manifest. Filename tokens are a secondary guard only. Revalidate the active document identity immediately before mutation.")
design = replace(design, "Only one writer may own the Revit production session.", "Only one writer may own the Revit session. The lock lives in a shared local runtime root for this project, outside worktree-specific copies. All providers and worktrees use the same resource identity, owner token, PID/start time, heartbeat and fencing generation. A timeout alone cannot transfer ownership while Revit may still be writing.")
design = replace(design, "amanda-agent bim build", "amanda-agent bim plan\namanda-agent bim verify-plan\namanda-agent bim claim\namanda-agent bim record-result")
design = replace(design, "This written specification has been checked for:", "The 2026-09-15 document review checked the following; runtime acceptance is NOT_RUN (see PLAN_SELF_REVIEW.md):")
design = replace(design, "- primary and fallback Revit capabilities are tested;", "- every required operation has an eligible primary and tested recovery/fallback route; fallback dependencies and failure domains are explicit;")
design = replace(design, "- accessibility and program checks pass to the supported extent;", "- program checks pass and every mandatory accessibility/site check for the declared STUDY or FINAL profile is accounted for; blocked mandatory FINAL checks prevent FINAL;")
design = replace(design, "Human action is required only for:", "Human action follows existing session authorization. For future implementation, preserve these boundaries:")
design = replace(design, "- irreversible external actions.\n\nTechnical fallbacks", "- external publication, paid cloud use or data upload outside existing authorization;\n- platform permission limits and user-owned unsaved work;\n- irreversible external actions.\n\nTechnical fallbacks")
design = replace(design, "1. finish or explicitly suspend task;", "1. finish or persist task as `SUSPENDED` with reason and resume conditions;")
design = replace(design, "7. commit source/config changes;", "7. update the incremental handoff; commit reviewed source/config/report changes and push to the configured remote when possible, excluding private sources/secrets/runtime files;")
design = replace(design, "Automatic fallback is permitted only to a provider already marked `PASS` or otherwise explicitly approved in the registry.", "Automatic fallback requires an evidence-bound PASS or accepted PASS_WITH_WARNINGS capability matching current provider/build/schema, operation scope and persistence requirements. DEGRADED, stale, incomplete and UNTESTED entries are not production-eligible. A custom script hosted by Cortex still depends on Cortex transport; it is not an independent remedy for a dead bridge.")
design = replace(design, "revit/\n├── lab/", "revit/\n├── lab/")

# Combined plan: preserve useful task detail, repair contracts and order.
plan = plan.replace("`docs/superpowers/specs/2026-09-11-amanda-tfg-bim-agent-design.md`", "[design specification](2026-09-11-amanda-tfg-bim-agent-design.md)")
plan = replace(plan, "**Architecture:** One orchestration plan plus independent child plans.", "**Status:** REVISED_DOCUMENT on 2026-09-15; implementation and Revit acceptance NOT_RUN.\n\n**Architecture:** One canonical combined file containing a master section and nine phase sections.")
plan = replace(plan, "- Maximum local autonomy; stop only for UAC, authentication/licensing, essential missing source data, final architectural selection, or irreversible external action.", "- Maximum autonomy within the current user-authorized task. Document review is REVIEW_ONLY; future execution follows recorded authorization and platform permissions. Preserve user work, architecture selection and external data/publication boundaries.")
plan = replace(plan, "- Every task ends in `PASS`", "- Tasks can pause as `SUSPENDED` with persisted resume conditions; completed attempts end in `PASS`")
plan = replace(plan, "## Current upstream contracts to re-check before installation", "## Upstream evidence and revalidation before installation")
plan = replace(plan, "At execution time, Codex must re-open these upstream sources, record their current commit/release, then pin the exact commit used:", "Reviewed against primary documentation on 2026-09-15. These are upstream statements, not local installation evidence. Before execution, re-open the sources and pin the selected commit/release plus artifact hashes; use local `codex mcp add --help` for CLI syntax (confirmed in this review).")
plan = replace(plan, "  - Current `AGENTS.md` requires exact .NET SDK `10.0.400` for the source build.", "  - Source build currently pins SDK `10.0.400` via `global.json`; confirm the selected commit and official SDK availability. This is a provider-specific SDK requirement, not a generic Revit installation/Plan 01 gate. Runtime .NET and build SDK are distinct.")
plan = replace(plan, "  - Current source install command:", "  - Upstream now recommends its hash-verified published installer for ordinary installation; retain source build when needed for development/audit and record that choice. Source install command:")
start_map = plan.index("## Plan Map")
end_map = plan.index("### Task M1:", start_map)
plan = plan[:start_map] + '''## Plan map and executable dependency contract

Read each phase through its anchor below. Files named as child plans in older copies were never supplied separately.

| Phase | Content | Dependency / completion |
|---|---|---|
| [00](#phase-00) | Master and bootstrap of repository | Documentation only |
| [01](#phase-01) | Foundation and durable state | Local Python/core tests; probes report Revit availability |
| [07A](#phase-07) | Tasks 1–6, 10–13 and 16 | After 01; policy, task graph, redaction and maintenance safeguards before installs |
| [03](#phase-03) | Source intelligence | After 01; independent of Revit |
| [02](#phase-02) | Provider Tool Lab | After 07A; missing Revit blocks this branch |
| [04](#phase-04) | Design engine | After 03; synthetic work may proceed with scoped input blockers |
| [05](#phase-05) | BIM compiler | After 02 and 04 |
| [06](#phase-06) | QA and synthetic release | After 05 |
| [07B](#phase-07) | Tasks 7–9, 14–15 and 17–19 | After 06; integrated recovery and fresh-session drills |
| [08](#phase-08) | Amanda production | After 06 and 07B plus resolved production input/selection gates |
| [09](#phase-09) | Rendering and cloud fallback | Optional post-release rendering; APS exception described below |

<!-- phase-dependencies -->
```json
{"01": [], "07A": ["01"], "03": ["01"], "02": ["07A"], "04": ["03"], "05": ["02", "04"], "06": ["05"], "07B": ["06"], "08": ["06", "07B"], "09": ["08"]}
```

This graph governs the normal route. Optional APS Tasks 6–10 may be evaluated in a synthetic sandbox after 07A for an evidenced local tool blocker, without requiring a GOLDEN that the blocker prevents. This exception never promotes a local-only phase GO: record changed deployment scope, authorization, costs and verified output contract; re-evaluate dependent gates. Other branches continue. Rendering may be tested after a synthetic release in 06.

Task IDs use `P<phase>-T<two-digit task>`; IDs, dependencies and explicit section anchors are stored in the future task graph. 07A/07B are gates over disjoint tasks in section 07, not duplicated implementations.

'''+plan[end_map:]
m1start = plan.index("### Task M1:")
m1end = plan.index("### Task M2:", m1start)
plan = plan[:m1start]+'''### Task M1: Establish the repository without relocating the input bundle

**Inputs:** the four Markdown files in this root and the supplied academic materials. **Outputs:** a local Git repository when needed, private-data exclusions, source inventory, initial documentation commit.

- [ ] Verify `Get-Location`, local instructions, `git rev-parse --show-toplevel`, `git status --short --branch` and `git remote -v`. As of this review, the supplied folder is not a Git repository and has no known remote.
- [ ] Keep this root. For an existing repository, preserve unrelated work and use an isolated worktree if useful. For a new repository, initialize here, commit the safe baseline, then create a worktree if needed. Do not nest another project or assume a worktree can exist before the first commit.
- [ ] Retain these root docs as canonical. Do not copy them into competing `docs/superpowers` trees. If a later split is warranted, generate it with checked boundaries and update all links in the same change.
- [ ] Before staging, create `.gitignore` with at least:

```gitignore
.venv/
.venv-*/
.tools/
vendor/
__pycache__/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.env
.env.*
!.env.example
docs/source/
docs/review/source-extracts/
TFG_Amanda_2026/
/programa_necessidades.pdf
/TFG_Amanda*.pdf
project/provenance/extracted/
state/snapshots/private/
state/locks/
logs/raw/
*.rvt
*.rfa
*.rte
*.slog
```

- [ ] Keep raw source documents, extracts, private config backups and live locks local. Commit only reviewed code, nonsecret metadata, reports and the handoff. New nonpublic files must be classified before staging; ignore rules alone do not protect previously tracked files.
- [ ] Run `git init -b main` only if no enclosing repository exists. Stage explicit reviewed paths, inspect `git diff --cached --stat`, commit, then push only to an identified remote. If no remote is configured, record the blocker and the exact commands after its URL becomes known; do not invent a GitHub destination.
- [ ] Retain source and document hashes and update `docs/notes/YYYY-MM-DD-escopo-handoff.md` with status and next task.

---

'''+plan[m1end:]
m2start = plan.index("- [ ] Execute Plan 01.")
m2end = plan.index("\n---", m2start)
plan = plan[:m2start]+'''- [ ] Follow the dependency contract above: 01 → 07A → 02; 01 → 03 → 04; (02 + 04) → 05 → 06 → 07B → 08.
- [ ] Evaluate gates per branch and intended deliverable scope. Revit unavailable must not block source reconciliation or synthetic solver development.
- [ ] Production preflight requires every required operation's evidence and recovery route, not merely a provider-level green label.
- [ ] Execute optional 09 only under its rendering/APS need gates.
'''+plan[m2end:]
plan = replace(plan, "Get-Content bim/releases/GOLDEN-001/manifest.json | ConvertFrom-Json | Format-List", ".\\.venv\\Scripts\\python.exe -m amanda_agent release verify --release-id GOLDEN-001")
plan = replace(plan, "3. read only the child plan for the current phase plus interfaces it consumes;", "3. read the current phase section in this combined file plus interfaces it consumes;")
plan = replace(plan, "8. update `PROJECT_STATE.yaml` after task completion;", "8. update `PROJECT_STATE.yaml` and incremental handoff after significant work; commit and push safe changes when a remote is available;")
plan = replace(plan, "- Revit is already installed; do not reinstall it.", "- Revit 2027 Education is the target, not verified installed/licensed state. Detect it read-only; do not reinstall it as part of foundation.")
plan = replace(plan, "- Plan 02 source-build of Horizun requires exact .NET SDK 10.0.400.", "- Install a provider-specific SDK only after auditing that provider's pinned build inputs in Plan 02; Plan 01 inventories SDKs.")

# TDD bootstrap steps actually run RED before behavior is supplied.
plan = replace(plan, "- [ ] **Step 3: Create minimal CLI**", "- [ ] **Step 3: Prepare the test harness, run RED, then create minimal CLI**\n\nCreate package/import skeleton and Typer app with no commands, then perform Steps 4–5 to obtain the venv before the first test invocation. Run `tests/unit/test_cli.py`; record its expected failing assertion for absent commands. Import/dependency failure alone is harness setup, not the intended behavioral RED. Only after that failure, add the commands below; they explicitly fail until implemented.")
for cmd in ("doctor", "status", "resume", "rollback"):
    plan = replace(plan, f'    typer.echo("{cmd}: bootstrap implementation pending")', f'    typer.echo("{cmd}: not implemented", err=True)\n    raise typer.Exit(code=2)')
plan = replace(plan, "- [ ] **Step 6: Verify test RED→GREEN**", "- [ ] **Step 6: Verify GREEN and unsupported-command behavior**\n\nAdd tests that each stub exits 2 and never reports success. Later tasks replace stubs with behavior-specific failing tests first; the Phase 01 gate rejects remaining stubs.")
plan = replace(plan, '    PENDING = "PENDING"', '    SUSPENDED = "SUSPENDED"\n    PENDING = "PENDING"')
plan = replace(plan, '    next_task: str = "ENV-001"', '    next_task: str = "P01-T01"\n    schema_version: int = 1\n    state_revision: int = 0\n    phase_gate: PhaseGate | None = None')
store_start = plan.index("- [ ] Write round-trip test and assert no `.tmp` remains.")
store_end = plan.index("\n---", store_start)
plan = plan[:store_start]+'''- [ ] RED: round-trip, invalid schema, interrupted write, stale revision and two-process concurrent update tests. A failed save must leave the previous valid state readable.
- [ ] Implement unique temporary files in the destination directory, flush + `os.fsync`, atomic `os.replace`, and cleanup on failure. Use a separate state-store lock and compare-and-swap `state_revision` so atomic replacement cannot silently lose another writer's updates.
- [ ] Persist schema version; migrate with a backup and tested migration, never reset invalid state to defaults. Keep operation journal/checkpoint references consistent with the saved revision and reconcile after interruption.
- [ ] GREEN: run `tests/unit/test_state_store.py`, record counts, then commit.
'''+plan[store_end:]
plan = replace(plan, "- [ ] Implement exclusive file creation with owner/PID/host/timestamp JSON.", "- [ ] Implement OS-backed exclusive ownership plus owner token, PID/start time, host, document identity, heartbeat and fencing generation in a shared local runtime root. Project worktrees/providers use the same lock; a worktree-local copy is only a diagnostic pointer. Test two processes in different worktrees and reuse of a PID.")
plan = replace(plan, "- [ ] Test release and stale lock inspection.", "- [ ] Test owner-only release and stale-lock inspection; expiry never permits a second writer until the old process/in-flight operation is proved inactive. Keep acquisition/release atomic and recover abandoned OS handles after process death.")
plan = replace(plan, "- [ ] Gate `NO_GO` if no Revit 2027 install is returned.", "- [ ] Normalize zero/one/many probe results, check executable metadata rather than directory name alone, and record the selected exact build. Missing/ambiguous install blocks Plan 02, not non-Revit branches; installed files do not prove a valid license or successful launch.")
sdkstart = plan.index("- [ ] Ensure exact SDK `10.0.400` exists")
sdkend = plan.index("\n---", sdkstart)
plan = plan[:sdkstart]+'''- [ ] Record SDK inventory without installation. Plan 02 discovers the selected source build's `global.json`, project target frameworks and installer needs before requesting a provider-specific SDK.
- [ ] A missing SDK affects only that source-build route. Official download existence/version must be verified at execution time; never silently roll forward a pinned compiler or reinstall Revit to satisfy it.
- [ ] Commit probe code and nonsecret inventory, not tool binaries.
'''+plan[sdkend:]
snapstart = plan.index("- [ ] Snapshot current config before provider installation:")
snapend = plan.index("\n---", snapstart)
plan = plan[:snapstart]+'''- [ ] Resolve active Codex home from `CODEX_HOME` when set, otherwise the documented user default; do not change the variable. Record the effective configuration source without exposing its content.
- [ ] Keep a byte-preserving config backup under ignored `state/snapshots/private/<timestamp>/`, restricted to the local user. Produce a separate redacted summary for Git. Redacting the only backup would prevent exact rollback.
- [ ] Inventory both `%ProgramData%/Autodesk/Revit/Addins/2027` and `%APPDATA%/Autodesk/Revit/Addins/2027`, referenced assemblies and bundle locations relevant to the chosen installer. Save paths, hashes, versions and intended writes.
- [ ] Test nested secrets, command arguments and headers; scan all staged metadata before commit. Never bulk-stage raw snapshots.
- [ ] Verify restoration on a disposable config fixture; commit only code and sanitized summaries.
'''+plan[snapend:]
plan = replace(plan, "- [ ] Test missing Revit 2027 is critical.\n- [ ] Test missing .NET 10.0.400 is critical before Plan 02.", "- [ ] Test phase-aware results: missing Revit blocks BIM/provider work, while source/solver commands remain usable.\n- [ ] Test missing provider-specific SDK blocks only a selected source build; core `doctor` reports it as inventory, not a universal failure.")
plan = replace(plan, "- [ ] `resume` refuses when a blocker starts with `BLOCKING:`.", "- [ ] `resume` resolves typed blocker IDs and task dependencies; it blocks only affected tasks. Reject unknown dependencies and cycles, and never infer severity from a string prefix.")
plan = replace(plan, "- [ ] `rollback` rejects target filenames containing `golden`, `master`, `source` case-insensitively.", "- [ ] `rollback` enforces resolved writable roots/protected-file identity and the shared writer lease; rejects existing targets, junction/hardlink escapes, active-document mismatch and source/checkpoint destinations. Filename tokens are secondary guards. Require quiescent Revit before restore.")
plan = replace(plan, "- [ ] Initialize topography as `UNKNOWN_UNTIL_INGEST`, not as a numeric value.", "- [ ] Before ingestion, source topography status is null/uninspected; afterward use `MISSING` or `VERIFIED_TOPOGRAPHY`. Representation `PLANAR_PLACEHOLDER` is separate from source verification and never upgrades MISSING.")
plan = replace(plan, "- exact Revit 2027 build recorded;", "- Revit detection result recorded; absent/ambiguous builds produce a scoped Plan 02 blocker;")
plan = replace(plan, "- .NET 10.0.400 available;", "- SDK inventory recorded; provider-specific prerequisites deferred to the audited build route;")
plan = replace(plan, "Any critical item above fails. Plan 02 must not begin.", "Core state/path/CLI/redaction failure blocks all dependent phases. Missing Revit or license blocks Plan 02 only; 03 and 04 may proceed within their source gates.")

# Registry must reject an attractive PASS label without physical evidence.
teststart = plan.index("```python\nfrom pathlib import Path\nfrom amanda_agent.models.capability")
testend = plan.index("\n```", teststart+4)+4
plan = plan[:teststart]+'''Write RED cases using fixture evidence records with synthetic scope clearly marked: FAIL is never selected; a bare PASS with no build/schema/evidence/persistence is rejected; stale build or tool schema is rejected; a valid matching capability wins deterministically. Test production selection against synthetic evidence to ensure it is refused.'''+plan[testend:]
plan = replace(plan, '    provider_commit: str | None = None', '    provider_commit: str | None = None\n    transport_provider: str | None = None\n    tool_schema_hash: str | None = None\n    tested_scope: dict = Field(default_factory=dict)\n    evidence_scope: str = "SYNTHETIC"')
plan = replace(plan, "  1. select only `PASS` or `PASS_WITH_WARNINGS`;", "  1. validate evidence paths/hashes, installed artifact and provider commit, exact Revit build, tool_schema_hash, tested_scope (operation/types/units/limits), and transport health; write operations require independent query and persistence; reject incomplete/stale or synthetic-only evidence for production;\n  2. then select only `PASS` or explicitly accepted `PASS_WITH_WARNINGS`;")
plan = replace(plan, "  2. prefer `PASS`;\n  3. lowest numeric priority wins;\n  4. provider name is deterministic tie-breaker.", "  3. prefer `PASS`;\n  4. lowest numeric priority wins;\n  5. provider name is deterministic tie-breaker.\n\nThe model snippet permits recording UNTESTED/FAIL entries; promotion/selection validators enforce all evidence invariants. A status field alone is never promotion.")
plan = replace(plan, "- [ ] An OPEN breaker prevents further same-provider calls for the capability in the current session.", "- [ ] Persist breaker scope (provider/build/capability/error signature) across sessions. OPEN blocks calls until a controlled read-only HALF_OPEN probe after cooldown/remediation; close only on independent success. Input errors do not count as provider-health failures.")
plan = replace(plan, "- [ ] **Step 4: Verify exact .NET SDK**", "- [ ] **Step 4: Verify the pinned source-build SDK and deployment isolation**")
plan = replace(plan, "Expected: `10.0.400` available. If project-local, prepend `.tools\\dotnet` to PATH for this build.", "Read the pinned `global.json` (reviewed upstream currently requests `10.0.400`) and confirm official availability. If absent, download Microsoft's installer to a local file, inspect it and install the exact SDK under `.tools/dotnet`; verify with the absolute `dotnet.exe` and set PATH only for this build process. Record source/version/hash. Do not substitute another SDK silently. Revit and client restarts require a persisted handoff first.")
plan = replace(plan, "$HorizunExe = Get-ChildItem \"$env:LOCALAPPDATA\\Programs\\Horizun\\MCP\" -Recurse -Filter horizun-mcp.exe -ErrorAction Stop |\n  Select-Object -First 1 -ExpandProperty FullName\n$HorizunExe\nGet-FileHash $HorizunExe -Algorithm SHA256", "# Resolve the exact path from the audited installer manifest/status.\n# Fail if absent, ambiguous, outside the intended install root or hash-mismatched.\n# Persist it as HorizunExe only after checking the installed version/commit.")
plan = replace(plan, "Snapshot `$env:USERPROFILE\\.codex\\config.toml` first.", "Snapshot the active Codex config location resolved in Plan 01 first. Coordinate a separate resume session if the installer requires Codex closed; it cannot close its own active session and then continue inline.")
plan = replace(plan, "$CortexExe = Get-ChildItem vendor/RevitCortex -Recurse -Filter RevitCortex.Server.exe |\n  Sort-Object LastWriteTime -Descending |\n  Select-Object -First 1 -ExpandProperty FullName\n$CortexExe", "# Publish the audited server project/configuration to one isolated output directory.\n# Resolve CortexExe from that publish manifest; verify framework, version and hash.\n# Fail on ambiguity instead of choosing the newest executable in the repository.")
plan = replace(plan, "- [ ] Execute only through a provider's verified code-execution capability in disposable file.", "- [ ] Execute through a verified host in a disposable file and record `transport_provider`. A custom script using Cortex/Horizun inherits that host's outage; for an independent fallback, test a separate Revit ExternalCommand/ExternalEvent add-in. Python outside Revit cannot invoke document mutations directly.")
plan = replace(plan, "- A typed fallback is verified for core operations.", "- Each required core operation has a tested fallback/recovery route. Record transport dependencies; a custom API route is eligible only for its tested scope. Missing a second typed provider is a scoped limitation if an independent tested recovery route covers the required operation.")
plan = replace(plan, "- Both MCPs source-pinned and connected.", "- Installed providers are pinned and connected; every required operation is covered by at least one eligible provider.")
plan = replace(plan, "Only noncore capability (for example Toposolid or one documentation feature) is degraded and a safe tested alternative exists.", "Any missing preferred/secondary provider or noncore capability is explicitly scoped; a tested eligible route covers every operation required by the next stage. No missing critical operation is waived.")
plan = replace(plan, "- [ ] Terminate only the disposable Revit session unexpectedly.", "- [ ] Before simulated crash, prove the owned PID/start time has only disposable documents, no user model, and a verified checkpoint; terminate only that process. If ownership cannot be proved, block the destructive drill and preserve user work.")

# Ingestion across heterogeneous and conflicting supplied material.
plan = replace(plan, "### Task 4: Ingest the two known Amanda documents when available to Codex", "### Task 4: Inventory and reconcile all supplied Amanda sources")
plan = replace(plan, "**Expected sources:** Amanda TFG PDF and program-of-needs PDF.", "**Expected sources:** the root TFG/program PDFs and the 21-file `TFG_Amanda_2026/` supporting package. Follow the source table in design section 1.1. Inventory DOCX/XLSX/SVG/DXF/IFC/PPTX/HTML as well as PDFs; do not execute embedded scripts or follow external links during extraction.")
plan = replace(plan, "- [ ] If either source is absent, set production blocker", "- [ ] Treat support documents as source assertions/hypotheses, not primary verified regulation or approved architecture. Require `PROGRAM_BASELINE` resolution before production: PDF = 20 people and 626 m² internal/260 m² external; spreadsheet = 12 × 3.5 = 42 hypothetical people. Preserve both versions and record the chosen decision.\n- [ ] If either core PDF source is absent, set production blocker")
plan = replace(plan, "- [ ] Commit parser choice/version to environment lock.", "- [ ] Add tested DOCX paragraph/table and XLSX sheet/cell/formula adapters. Distinguish formulas, cached values and independently recalculated values; a stale cache is not proof. Inspect drawings/IFC units and provenance in read-only copies. Retain placeholders/conflicts with locators.\n- [ ] Commit parser choice/version to environment lock.")
plan = replace(plan, "Each `SourceReference` includes source ID, page/line locator when available, extraction method, confidence, note.", "Each `SourceReference` includes source ID/hash, page/paragraph/table or sheet/cell locator, extraction method, confidence and note. Add verification_status and adoption_status from design section 1.1; a source statement may be DISPUTED and a documented hypothesis remains DESIGN_HYPOTHESIS.")
plan = replace(plan, "    privacy_level: int = Field(ge=0, le=5)\n    accessible: bool = False\n    source_refs: list[str]", "    privacy_level: int | None = Field(default=None, ge=0, le=5)\n    accessible: bool | None = None\n    source_refs: list[str] = Field(min_length=1)")
plan = replace(plan, "- [ ] Write tests rejecting zero/negative area and quantity.", "- [ ] Write tests rejecting zero/negative canonical area/quantity, empty provenance, NaN/infinity, invalid ranges and duplicate IDs. Use a separate draft-extraction schema with nulls for unknowns; canonical compilation blocks required unknown fields instead of inventing them.")
plan = replace(plan, "- [ ] Assign stable logical IDs by sector/space instance.", "- [ ] Assign one requirement ID per source row and expand quantity into stable instance IDs only at generation. Explicitly tag internal/external area and whether target_area_m2 is per unit; every total is quantity × unit area. Avoid double expansion.")
plan = replace(plan, "- [ ] Record source capacity reference (up to 20 simultaneous residents) as a fact.", "- [ ] Preserve the PDF's reference to up to 20 simultaneously accommodated people, including the unresolved distribution of women/children/leitos; reconcile it against the 42-person spreadsheet hypothesis through PROGRAM_BASELINE. Neither is automatically adopted.")
plan = replace(plan, "- [ ] Record the four named street/frontage relationships as facts.", "- [ ] Record the conflicting three/four-frontage assertions with locators. Verify actual boundary/frontages before freezing site_version; do not resolve them by counting names in prose.")
plan = replace(plan, "- [ ] Record source-backed total site area/frontages.", "- [ ] Record reported site area 24,135 m² as a source assertion, with SITE_BOUNDARY/SITE_OCCUPANCY blockers for legal boundary, current use and relocation premise. If no calibrated polygon/north exists, allow synthetic site work only; do not invent a rectangle of equal area.")
plan = replace(plan, "- [ ] Require source file/version/page/section before a numeric rule can become `DERIVED_CONSTRAINT`.", "- [ ] Require applicable primary source/version/date/article/map, extracted rule, unit, scope and verification evidence before a normative number becomes DERIVED_CONSTRAINT. Acquisition alone is not verification. The supplied LC208 DOCX and XLSX 'ATENDE' cells are secondary references only.")
plan = replace(plan, "## Phase 03 Verification Gate", '''### Task 15: Academic deliverable and decision register

**Files:** future `project/requirements/academic-deliverables.yaml`, `project/requirements/decisions.yaml`; tests `tests/project/test_deliverable_scope.py`.

- [ ] Map caderno revision, visits, metaprojeto, preliminary study, anteprojeto, pranchas, descriptive/calculation memorials, defense, authorship and institutional submission from the support plan to owner/source/status/evidence.
- [ ] Record the support claim of 4–6 A1 landscape synthesis boards as provisional until the institutional regulation is acquired. Keep dates unknown until the official calendar is available.
- [ ] Assign BIM-generated outputs versus human-authored/validated deliverables. No automated signatures, field visits or institutional submissions are implied by software completion.
- [ ] Test that an unresolved mandatory academic deliverable prevents a claim of TFG_COMPLETE while technical STUDY releases remain possible.
- [ ] Record TYPOLOGY, PROGRAM_BASELINE, SITE_BOUNDARY, SITE_OCCUPANCY and REGULATION_APPLICABILITY decisions separately from the later finalist selection.

## Phase 03 Verification Gate''')

# Design precision, reproducibility and missing information.
plan = replace(plan, '"shapely>=2.2,<3",', '"shapely>=2.1,<3",')
plan = replace(plan, "- [ ] Freeze exact resolved packages:", "- [ ] Resolve these candidate ranges against available Windows/Python wheels before adopting them. Freeze exact resolved third-party packages, excluding editable absolute paths; rebuild a fresh venv from the lock and run import/core tests before claiming reproducibility:")
plan = replace(plan, ".\\.venv\\Scripts\\python.exe -m pip freeze | Sort-Object | Set-Content requirements.lock.txt", ".\\.venv\\Scripts\\python.exe -m pip freeze --exclude-editable | Sort-Object | Set-Content -Encoding utf8 requirements.lock.txt")
plan = replace(plan, "- [ ] Same seed/input/version produces same hash.", "- [ ] Set `num_search_workers = 1`, pinned OR-Tools/runtime, fixed seed, deterministic search budget and ordered inputs. Record OPTIMAL/FEASIBLE/INFEASIBLE/UNKNOWN separately; wall-clock timeout UNKNOWN is not proof of infeasibility. Same input/version/solver configuration produces the same geometry hash in the supported environment; exclude timestamps, paths, durations and run IDs from the semantic digest.")
plan = replace(plan, "- [ ] Different seed yields at least one differing candidate on fixture.", "- [ ] On a fixture with multiple known feasible options, test diversity of the configured generator. Different seeds do not guarantee different optima; deduplicate geometry hashes and report actual candidate count.")
plan = replace(plan, "- [ ] Implement independent validators then aggregate.", "- [ ] Implement validators by resolution: MACRO validates sector capacities/boundary/separation; BLOCK validates block geometry and gross-area budget; ROOM validates expanded room instances, net areas and traversable routes. Checks unavailable at that resolution are NOT_EVALUATED, never PASS. Do not reject every macro candidate merely because rooms do not exist yet.")
plan = replace(plan, "- [ ] Encode required separation/adjacency and region capacity.", "- [ ] Encode bounded integer-grid variables/scaling for CP-SAT, sector capacity and separation/adjacency. Define discretization/rounding tolerance and revalidate resulting metric polygons with Shapely; reject grid-feasible but geometrically invalid results. Record solver status and infeasibility evidence separately.")
plan = replace(plan, "- [ ] Weight changes alter total but never raw metrics.", "- [ ] Give each metric unit, min/max direction, normalization bounds, missing-data rule and evidence source in the versioned configuration. Apply weights to normalized comparable values; never mix raw metres and percentages. Missing environmental inputs yield NOT_EVALUATED and exclude/rebalance that dimension transparently across the whole comparison. Weight changes alter total but never raw metrics.")
plan = replace(plan, "- [ ] Compute path lengths and crossings deterministically.", "- [ ] Derive traversable graph edges from actual corridors, portals/doors, widths, obstacles and access permissions, with vertical connections where applicable. An adjacency or centroid line is not an accessible route. Compute path lengths/crossings deterministically and reject disconnected routes.")
plan = replace(plan, "- [ ] Verify candidate room areas sum plausibly against block area including circulation allowance.", "- [ ] Separate net room area from gross footprint, wall thickness, shafts and circulation; assign each area once and report the net-to-gross factor as a hypothesis until modeled. Test multi-storey and single-storey accounting; outside gardens do not count as enclosed internal area.")
plan = replace(plan, "- [ ] Otherwise mark optional capability DEGRADED/DEFERRED; core engine remains GO.", "- [ ] Otherwise keep capability UNTESTED or DEGRADED according to evidence and set scheduling decision `DEFERRED_OPTIONAL` outside CapabilityStatus; core engine remains GO.")
plan = replace(plan, "- [ ] Install `topologicpy --upgrade`.", "- [ ] Install an exact evaluated TopologicPy version with its own dependency lock; record package availability before installation.")
plan = replace(plan, "- [ ] If a verified EPW is available, run one synthetic smoke simulation.", "- [ ] Verify EPW station/timezone/year/hash plus the actual Radiance/EnergyPlus executables and versions needed by the selected recipe. Package imports alone do not prove a simulation engine. Run one synthetic reproducible case and validate outputs.")

# BIM contracts including host units, geometry and operation journaling.
plan = replace(plan, "- [ ] Keep all Design Engine data metric; convert only at Revit boundary.", "- [ ] Keep Design Engine data metric; record each discovered tool's input/output units. Typed providers may already accept metres: convert only for capabilities declaring internal feet. For direct Revit API use UnitUtils with declared spec/unit IDs. Test double conversion, area/volume/angle, linked-model transforms, project/true north and geospatial origin/CRS.")
plan = replace(plan, "- [ ] Implement case-insensitive filename/path policy.", "- [ ] Enforce canonical writable-root allowlist, protected source/baseline/checkpoint/release identities, active document ID/path and shared lease. Test renamed originals, hardlinks, junctions and stale document switches; deny ambiguous target identity. Filename matching is a secondary guard.")
plan = replace(plan, "- [ ] Unmanaged Revit elements are not deleted by default.", "- [ ] Unmanaged elements are not deleted. Map logical IDs to Revit UniqueId + document identity, keeping ElementId only for the active session; detect user divergence before overwrite. Test SaveAs/reopen/replacement and persistent metadata across process restart.")
plan = replace(plan, "- [ ] Threshold config lives in versioned YAML.", "- [ ] Count cascading host deletions/type changes, including unmanaged dependents, before mutation. Unknown cascade blocks execution. Define zero/small-denominator and absolute-count safeguards; destructive threshold release requires a concrete reviewed plan under current authorization. Threshold config lives in versioned YAML.")
plan = replace(plan, "- [ ] Preflight requires approved solution, healthy registry, correct Revit build.", "- [ ] Preflight checks mode: CONCEPT_ONLY permits validated finalists through R04 only; SYNTHETIC_LAB permits marked fixtures; detailed production requires APPROVED_FOR_BIM with matching approval_hash, selected input versions, healthy registry and exact build.")
plan = replace(plan, "- [ ] Exterior walls from approved polygons.", "- [ ] Derive shared wall topology once from net-room/gross-shell geometry, applying type thickness, location line, joins and host dependencies; adjacent rooms must not create duplicate coincident walls. Test two rooms sharing one wall, corners, openings and area reconciliation after wall creation.")
plan = replace(plan, "- [ ] Measure actual modeled room polygons.", "- [ ] At R06 measure boundary/enclosure geometry; actual Revit Room objects and computed areas are queried after R08. Distinguish finished-face room area from wall centreline geometry.")
plan = replace(plan, "- `amanda-agent bim status`", "- `amanda-agent bim status`\n- `amanda-agent bim claim --plan PATH`\n- `amanda-agent bim record-result --operation-id ID --evidence PATH`")
plan = replace(plan, "- [ ] Unapproved solution rejected.", "- [ ] Unapproved detailed production is rejected; CONCEPT_ONLY R00–R04 is allowed for eligible finalists and cannot promote a release. Test approval_hash invalidation on program/site/geometry changes.")
plan = replace(plan, "- [ ] Plan contains only tested provider chains.", "- [ ] Plan contains only evidence-bound eligible provider chains for the exact operation scope.\n- [ ] Implement a durable execution journal: operation_id, plan/input/checkpoint/document hashes, lease token, provider/schema versions, dependencies, intended delta and verifier. `claim` atomically marks the next READY operation; Codex invokes the actual MCP tool; `record-result` validates independent evidence before marking PASS.\n- [ ] Tests: duplicate claim/ack, result for wrong model/hash, out-of-order result, interrupted write, pending host transaction, expired lease and stale plan. A transport timeout becomes IN_DOUBT; hold the writer and reconcile actual state before retry, fallback or lock release. A JSON plan alone does not execute MCP.\n- [ ] Journal states are separate from TaskStatus: READY, CLAIMED, IN_DOUBT, VERIFIED, FAILED. Resume reconciles an in-doubt operation before dispatching any later mutation.")
plan = replace(plan, "- [ ] Test file copy hash equality.", "- [ ] Test file copy hash equality, refusal of an active/incomplete save, and failure before checkpoint manifest publication. Save/close the owned file normally (or use a separately proven snapshot API), hash stable bytes, reopen/verify when required, then publish the checkpoint manifest. A stale on-disk copy is not the current Revit state.")

# Release construction and scope.
plan = replace(plan, "- limitations/blockers accepted for release.", "- release_profile STUDY or FINAL, required versus optional checks/artifacts, accepted limitations and approval evidence;\n- content hashes for every artifact except the manifest itself (avoid recursive self-hash), and source-to-export identity/coordinate map.")
plan = replace(plan, "- [ ] QA FAIL blocks promotion.", "- [ ] QA FAIL and any unwaived mandatory blocked check prevent promotion. STUDY may explicitly retain missing survey/normative checks, with visible limitations; FINAL cannot waive them into compliance. Never infer acceptance from an empty issue list.")
plan = replace(plan, "- [ ] Promotion copies RC into a new release directory and verifies hash after copy.", "- [ ] Assemble the complete RVT/exports/previews/reports/provenance in a new staging directory; verify every hash and mandatory result, then publish with a no-overwrite atomic directory operation where supported (otherwise a tested completion marker protocol). Interrupted staging is never a GOLDEN. All reports exist before sealing; later corrections create a new release.")
plan = replace(plan, "- `amanda-agent release promote --release-id RC01`", "- `amanda-agent release promote --release-id RC01`\n- `amanda-agent release verify --release-id GOLDEN-001`\n\nCreate `src/amanda_agent/commands/release.py` and register its Typer group. `release verify` recomputes actual artifact hashes, required-file presence and manifest/QA/profile invariants; printing JSON is not validation.")
plan = replace(plan, "2. hash;\n3. close Revit normally;", "2. wait for save completion;\n3. close Revit normally and hash the closed stable file;")
plan = replace(plan, "10. compare hashes/state expectations.", "10. compare semantic state expectations; if an intentional later save changes file bytes, regenerate hashes/exports and revalidate before sealing.")
plan = replace(plan, "- [ ] Production validator compares expected high-level counts/IDs where export preserves them.", "- [ ] Production validator compares units, geospatial/project transforms, extents, storeys/spaces, openings and logical-ID mapping under the pinned export settings. Legitimate splits/merges need explicit mapping; counts alone cannot prove fidelity.")
plan = replace(plan, "### GO_WITH_LIMITATIONS\nOnly a nonmandatory visual/DWG-depth check is limited and explicitly reported.", "### GO_WITH_LIMITATIONS\nA declared STUDY profile may accept limited DWG-depth checks with evidence. Required sheet visual review and mandatory exports cannot be silently skipped; a pending review blocks that deliverable's final acceptance.")
plan = replace(plan, "- [ ] Save as new RC R15.", "- [ ] Save to a new provisional RC path; certify R15 only after the cold-reopen verification below.")
plan = replace(plan, "- [ ] Promote lab GOLDEN R16.", "- [ ] Complete required visual review (Task 15), reports and provenance in staging before promoting lab GOLDEN R16.")

# Recovery splitting and local isolation limitations.
plan = replace(plan, "## Global Constraints\n\n- One Revit production writer lease.", "## Execution subsets\n\n07A: Tasks 1–6, 10–13 and 16 after Plan 01, before provider installation. 07B: Tasks 7–9, 14–15 and 17–19 after synthetic release in Plan 06. Plan 01's minimal checkpoint/rollback protocol supports the earlier Tool Lab drill; these later tasks integrate and harden it. Tests use fixture contracts until a real dependency exists.\n\n## Global Constraints\n\n- One Revit production writer lease.")
plan = replace(plan, "- Create: `AGENTS.md`", "- Create or merge without discarding existing instructions: `AGENTS.md`")
plan = replace(plan, "- [ ] Requires next task ID.", "- [ ] Requires next task ID and incremental handoff including changes, evidence, tests, GitHub status, blockers and resume instructions; no reliance on chat memory.")
plan = replace(plan, "- [ ] Missing Autodesk login blocks cloud only, not local pipeline.", "- [ ] Missing APS authorization blocks cloud; missing/expired Revit licensing blocks local Revit as well. CPU-only ingestion/solver work remains possible.")
plan = replace(plan, "Allowed human gate reasons only:", "Human gate reasons (respect previously granted authorization; never use this enum to override platform/user limits):")
plan = replace(plan, "- `IRREVERSIBLE_EXTERNAL_ACTION`.\n\n- [ ] Routine", "- `IRREVERSIBLE_EXTERNAL_ACTION`;\n- `EXTERNAL_DATA_OR_COST`;\n- `PLATFORM_PERMISSION`;\n- `USER_WORK_AT_RISK`;\n- `PROGRAM_BASELINE`.\n\n- [ ] Routine")
plan = replace(plan, "- [ ] Change provider fixture/mock or update an upstream provider only there.", "- [ ] A Git worktree isolates source only: it does not isolate `%APPDATA%` add-ins, Codex config, ports, installed DLLs or Revit processes. Use a separate sandbox/deployment root or a backed-up maintenance window and one process owner for a real install. Otherwise change only fixtures/mocks in the worktree.")
plan = replace(plan, "- [ ] Force kill is last action after normal-close attempt and checkpoint/state persistence.", "- [ ] Force kill is last action after normal-close attempt and verified prior checkpoint/state persistence; require owned PID/start time and disposable/authorized documents. Do not attempt a new checkpoint from a hung process or kill unknown user work.")
plan = replace(plan, "- [ ] Close Codex completely.", "- [ ] Persist handoff and end the current session; a subsequent session performs the next steps. Closure of the current agent cannot be simulated by code that then claims to continue after restart.")

# Production count, conceptual exception, academic tracking and sealing order.
plan = replace(plan, '.\\.venv\\Scripts\\python.exe -m pytest tests -m "not slow" -q', '.\\.venv\\Scripts\\python.exe -m pytest tests -m "not revit and not slow" -q')
plan = replace(plan, "- [ ] Confirm preferred core capabilities are PASS.", "- [ ] Run separately marked Revit tests only on explicit disposable fixtures. Confirm production-scope evidence for every required capability, including build/schema/persistence, not just a core provider status.")
plan = replace(plan, "- [ ] Confirm core fallback provider is PASS.", "- [ ] Confirm each required operation's fallback/recovery route and its transport dependencies are tested.")
plan = replace(plan, "- [ ] freeze `requirements_version`;", "- [ ] Require resolved PROGRAM_BASELINE, TYPOLOGY and valid SITE_BOUNDARY for the chosen production scope; unresolved decisions permit separate exploratory scenarios only.\n- [ ] freeze `requirements_version`;")
plan = replace(plan, "- [ ] Configure `AMANDA-RUN-001` for exactly 144 initial macro candidates.", "- [ ] Configure 144 initial attempts (6 archetypes × 24 seeds), then record valid/invalid/unknown/duplicate counts. Do not fabricate candidates or relax hard rules to reach a quota.")
plan = replace(plan, "- [ ] Select top 5 for finalist analysis.", "- [ ] Select up to 5 distinct feasible candidates; keep the Pareto set across all feasible candidates and do not discard it solely by weighted cutoff. If fewer candidates exist, report counts and reasons.")
plan = replace(plan, "- [ ] create its own disposable production-candidate RVT;", "- [ ] acquire the shared writer lease and create a separate candidate RVT with execution mode CONCEPT_ONLY and no detailed-production approval;")
plan = replace(plan, "- [ ] do not create detailed rooms/families/sheets yet.", "- [ ] reject R05–R16 for CONCEPT_ONLY; finish verified save/reopen and release the lease before moving to the next candidate.")
plan = replace(plan, "- [ ] Record selected solution ID and selection note.", "- [ ] Record selected solution ID, approver, timestamp, approval evidence and approval_hash binding geometry/requirements/site/constraints and material intent. Changed content invalidates approval.")
plan = replace(plan, "- [ ] Hash RC.\n- [ ] Close Revit normally.", "- [ ] Wait for save completion.\n- [ ] Close Revit normally and hash the stable closed RC.")
plan = replace(plan, "- [ ] Copy RC into **new** `bim/releases/GOLDEN-001/`.", "- [ ] Prepare all Task 19 deliverables/reports in staging first; validate the declared STUDY/FINAL profile and mandatory checks, then publish the complete package into **new** `bim/releases/GOLDEN-001/` without overwrite.")
plan = replace(plan, "### Task 19: Final deliverable package", "### Task 19: Final deliverable package preparation before Task 18 promotion")
plan = replace(plan, "- [ ] Generate final `RUN_SUMMARY.md`.", "- [ ] Generate final `RUN_SUMMARY.md` and the academic-deliverables status from Plan 03 Task 15. Record caderno, memorials, boards, visits, authorship and submission separately; no TFG_COMPLETE while required academic work remains pending.")
plan = replace(plan, "GOLDEN release exists, reopens after a cold Revit restart, core QA passes, exports validate, provenance/provider/input versions are recorded.", "A sealed GOLDEN exists for its stated STUDY/FINAL scope; cold reopen, required QA, required exports and visual review have evidence; input/provider/provenance versions are recorded. This is pipeline/release success, not automatic TFG_COMPLETE.")
plan = replace(plan, "Missing verified topography/normative source remains explicitly reported and is not misrepresented as validated final grading/compliance.", "Only a STUDY release may retain explicitly identified missing survey/normative checks. FINAL stays blocked by any mandatory unresolved input/validation. Known program mismatch is never waived.")

# Optional integrations must not deadlock the rescue route or float versions.
plan = replace(plan, "- Do not execute before local synthetic GOLDEN exists.", "- Rendering consumes a verified export/release. APS need/audit/synthetic testing may follow 07A when a concrete local blocker prevents reaching GOLDEN; use the explicit exception in the master dependency contract.")
plan = replace(plan, "mark Blender capability `DEFERRED_OPTIONAL`", "set Blender scheduling decision `DEFERRED_OPTIONAL` and leave untested capability `UNTESTED`")
plan = replace(plan, "mark APS `DEFERRED_OPTIONAL`", "set APS scheduling decision `DEFERRED_OPTIONAL` (capability remains UNTESTED)")
plan = replace(plan, 'powershell -c "irm https://astral.sh/uv/install.ps1 | iex"', '# Download the official installer to a local file, inspect it and record its hash.\n# Run the inspected file under the audited install scope; record version and rollback.')
plan = replace(plan, "codex mcp add blender -- uvx blender-mcp", "# Resolve UvxExe to the verified absolute executable path.\n# Resolve BlenderPackage to blender-mcp==<the exact evaluated version> from the lock.\ncodex mcp add blender -- $UvxExe --from $BlenderPackage blender-mcp")
plan = replace(plan, "uvx blender-mcp install-addon", "& $UvxExe --from $BlenderPackage blender-mcp install-addon")
plan = replace(plan, "- [ ] Audit credential locations, network/data flow, activity/AppBundle configuration, rollback.", "- [ ] Audit credential locations, network/data flow, activity/AppBundle configuration, rollback; verify the available APS engine version can read the target RVT before any cloud test.")
plan = replace(plan, "- [ ] Never upload unrelated source files.", "- [ ] Record user authorization for intended model/data upload, destination and cost limit unless already granted in this session. Use synthetic data for sandbox tests; never upload unrelated source files.")

# Stable phase anchors and task identifiers; original task titles retained.
titles = [m.start() for m in re.finditer(r"^# (?:Amanda|Foundation,|Revit Tool Lab,|Project Intelligence|Generative Design|BIM Compiler|QA, Persistence|Autonomous Operation|Optional Rendering)", plan, re.M)]
if len(titles) != 10:
    raise ValueError(f"Expected master + nine phases, got {len(titles)}")
sections = []
for phase, start in enumerate(titles):
    section = plan[start:titles[phase+1] if phase+1 < len(titles) else len(plan)]
    section = re.sub(r"^### Task (M?)(\d+): (.+)$", lambda m: f"### Task {m[1]}{m[2]}: {m[3]} [P{phase:02d}-T{int(m[2]):02d}]", section, flags=re.M)
    sections.append(f'<a id="phase-{phase:02d}"></a>\n\n'+section)
plan = "".join(sections)

start = '''# Comece aqui — projeto Amanda TFG BIM

**Revisão:** 2026-09-15. **Estado atual:** REVIEW_ONLY; implementação, instalações e validação real no Revit = NOT_RUN.

Este pacote contém a especificação e o plano de uma futura automação BIM. A revisão documental não aprova uma alternativa arquitetônica nem autoriza executar automaticamente as instalações descritas.

## Ordem de leitura

1. Instruções do usuário e `AGENTS.md`, se existir. Preserve instruções já estabelecidas.
2. [Handoff da revisão](docs/notes/2026-09-15-revisao-planos-handoff.md).
3. [Especificação e contexto das fontes](2026-09-11-amanda-tfg-bim-agent-design.md#project-baseline).
4. [Plano mestre combinado](2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-00), seguido da seção da fase atual.
5. [Revisão crítica e evidências](PLAN_SELF_REVIEW.md).

Os quatro Markdown canônicos estão na raiz. O COMBINED contém o mestre e as nove fases; não procure planos filhos em pastas ausentes. Caminhos de código/estado dentro dos planos são saídas futuras. A pasta não era um repositório Git no início da revisão; verificar novamente antes de inicializar e não inventar remoto.

## Antes de implementar

A futura execução começa por M1 e fase 01, seguindo o grafo de dependências do mestre. Segurança básica 07A precede instalações; ingestão 03 e solver 04 podem avançar sem Revit. A fase 07B valida recuperação integrada depois do release sintético. Disponibilidade de uma skill ou ferramenta deve ser verificada; na ausência de subagentes, execute sequencialmente com as mesmas revisões e testes, sem fingir uma revisão independente.

A implementação exige TDD: teste de comportamento, falha pelo motivo esperado, correção mínima e nova validação. Gates de laboratório/produção exigem evidências reais, reconsulta, salvamento e reabertura. Testes sintéticos ou revisão de Markdown não são PASS no Revit.

## Decisões de fonte que bloqueiam produção

- `PROGRAM_BASELINE`: PDF de 20 pessoas e planilha hipotética de 42 são cenários conflitantes. Preservar ambos até escolha explícita; não misturar áreas/capacidades.
- `TYPOLOGY`: confirmar o equipamento e sua política de sigilo/acesso.
- `SITE_BOUNDARY` e `SITE_OCCUPANCY`: confirmar polígono, frentes, área utilizável e premissa de realocação da ocupação existente.
- Topografia e normas verificadas: manter dados ausentes como ausentes e limitar o escopo do estudo.
- `APPROVED_FOR_BIM`: a seleção detalhada depende de evidência humana vinculada ao hash do conteúdo. Massas de finalistas podem usar CONCEPT_ONLY somente até R04.

O DXF/IFC HIPÓTESE, a planilha de cálculo e os pareceres auxiliares não são aprovação da autora, levantamento ou prova automática de conformidade.

## Continuidade e integridade

Na implementação, ler `PROJECT_STATE.yaml` se existir, conferir Git/ambiente/bloqueadores e retomar o próximo ID READY. O estado é versionado; um arquivo ausente ou corrompido não deve ser substituído por um falso estado verde. Usar um único executor Revit e lock compartilhado entre worktrees/provedores. Toda escrita segue WRITE → READ → VERIFY; originais, baselines, checkpoints e GOLDEN ficam protegidos.

Após cada bloco, registrar testes/evidências, atualizar estado e handoff, revisar os arquivos a versionar, fazer commit e push quando houver remoto. Fontes privadas, backups brutos, credenciais e locks vivos ficam fora do Git. Se não for possível publicar, registrar motivo e comandos de retomada.

## Pedido sugerido para a próxima etapa

```text
Execute M1 e a fase 01 do plano combinado revisado. Comece pelo estado real da pasta e pelas instruções existentes, preserve fontes e trabalho alheio, siga TDD e atualize o handoff. Registre bloqueios por dependência. Não instale provedores antes de 07A e dos pré-requisitos específicos da fase 02.
```

Para falhas Revit/MCP, preservar checkpoint e journal, classificar a falha e reconciliar operações IN_DOUBT antes de repetir ou trocar provedor. Consultar apenas capacidades com evidência válida para o build/esquema/escopo atual; novas capacidades voltam ao Tool Lab.
'''

# ZIP supplied mid-review confirms separate plans were available in the archive.
design = design.replace("Não existem planos filhos separados nesta entrega.", "O ZIP original, recebido durante a revisão, contém planos separados; nesta revisão eles são regenerados em docs/superpowers/plans a partir do COMBINED, sem edição independente.")
plan = plan.replace("Files named as child plans in older copies were never supplied separately.", "The original ZIP supplied during review contains the ten separate master/phase plans, identical to the original combined sections. Revised child files under docs/superpowers/plans are generated from this canonical combined file; regenerate after changes.")
plan = plan.replace("Do not copy them into competing `docs/superpowers` trees. If a later split is warranted, generate it with checked boundaries and update all links in the same change.", "Regenerate the derived phase files with docs/review/package_review.py and verify their section hashes; do not edit the generated files independently. The root specification remains canonical.")
start = start.replace("não procure planos filhos em pastas ausentes.", "o ZIP original também contém versões separadas. As cópias revisadas em `docs/superpowers/plans/` são geradas do COMBINED e não devem ser editadas independentemente.")
(ROOT / NAMES[0]).write_text(start, encoding="utf-8")
(ROOT / NAMES[2]).write_text(design, encoding="utf-8")
(ROOT / NAMES[3]).write_text(plan, encoding="utf-8")
print(json.dumps({"edited": [NAMES[i] for i in (0,2,3)], "backup": str(BACKUP), "task_ids": len(re.findall(r'\[P\d\d-T\d\d\]', plan))}))
