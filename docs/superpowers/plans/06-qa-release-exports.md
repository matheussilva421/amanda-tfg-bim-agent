> GERADO de [2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-06) em 2026-09-15. Edite o COMBINED e execute `docs/review/package_review.py`; não edite esta cópia. Caminhos operacionais no texto são relativos à raiz do projeto.

<a id="phase-06"></a>

# QA, Persistence, Export, and GOLDEN Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; TDD for QA/release code; verification-before-completion is mandatory before RC/GOLDEN promotion.

**Goal:** Implement model/program/architecture/accessibility/documentation QA, warning baselines, export validation, cold persistence tests, release manifests, hashes, and immutable GOLDEN promotion.

**Architecture:** QA consumes Revit query evidence and exported files. It does not trust write responses. A release candidate must survive save→close→process exit→restart→reopen→critical QA. GOLDEN promotion is a one-way new-directory operation.

**Tech Stack:** Python 3.12, Pydantic, IfcOpenShell, local PDF parser/renderer, verified Revit query/export capabilities.

**Spec:** [design specification](../../../2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- QA may block a build; it does not silently change requirements.
- Unknown warnings are never auto-ignored.
- GOLDEN is immutable.
- File existence is not sufficient export validation.
- IFC must parse.
- PDF page count/content preview must be checked.
- RC cannot promote without persistence evidence.

---

### Task 1: QA typed models [P06-T01]

**Files:**
- Create: `src/amanda_agent/qa/models.py`
- Test: `tests/unit/test_qa_models.py`

Severities: `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`.
Result: `PASS`, `PASS_WITH_WARNINGS`, `FAIL`, `BLOCKED_BY_INPUT`.

- [ ] Write serialization/aggregation tests.
- [ ] A CRITICAL issue or failed mandatory HIGH check forces overall FAIL; aggregation includes scope/mandatory flag. Missing mandatory checks block the relevant release profile, even when no defects are present.
- [ ] A missing-input issue cannot be converted to PASS.
- [ ] Commit.

---

### Task 2: Program reconciliation QA [P06-T02]

**Files:**
- Create: `src/amanda_agent/qa/program.py`
- Test: `tests/unit/test_program_qa.py`

- [ ] Missing required room → FAIL.
- [ ] Quantity mismatch → FAIL.
- [ ] Room area within configured range → PASS.
- [ ] Area outside soft tolerance but above hard minimum → warning according to config.
- [ ] Area below verified hard minimum → FAIL.
- [ ] External programmed-space quantities/areas reconciled too.
- [ ] Commit.

---

### Task 3: Model/geometric QA [P06-T03]

**Files:**
- Create: `src/amanda_agent/qa/model.py`
- Test: `tests/unit/test_model_qa.py`

- [ ] Duplicate managed logical IDs → CRITICAL.
- [ ] Hosted element without host → HIGH/CRITICAL.
- [ ] Managed room unplaced/not enclosed/redundant → HIGH.
- [ ] Managed element outside site when prohibited → HIGH.
- [ ] Level mismatch → severity by stage.
- [ ] Unexpected massive element-count delta → CRITICAL.
- [ ] Commit.

---

### Task 4: Warning baseline/delta [P06-T04]

**Files:**
- Create: `src/amanda_agent/qa/warnings.py`
- Create: `state/known-warnings.yaml`
- Test: `tests/unit/test_warning_delta.py`

- [ ] Baseline warning remains known, not “new”.
- [ ] New warning is emitted as delta.
- [ ] Known pattern severity map is versioned.
- [ ] Unknown warning defaults to reviewable severity, not ignore.
- [ ] Record warning ID/text/provider query evidence.
- [ ] Commit.

---

### Task 5: Architecture/concept QA [P06-T05]

**Files:**
- Create: `src/amanda_agent/qa/architecture.py`
- Test: `tests/unit/test_architecture_qa.py`

- [ ] Compare BIM logical adjacency graph to approved solution graph.
- [ ] Verify private residential zone has no unauthorized public-flow edge.
- [ ] Verify service-flow policy.
- [ ] Verify programmed therapeutic/protected garden relations.
- [ ] Verify shelter/transition/city sequence metrics did not collapse during BIM compile.
- [ ] Commit.

---

### Task 6: Accessibility QA status discipline [P06-T06]

**Files:**
- Create: `src/amanda_agent/qa/accessibility.py`
- Test: `tests/unit/test_accessibility_qa.py`

- [ ] Route-continuity checks use geometry/graph data.
- [ ] Numeric dimensional checks use only VERIFIED regulation rules.
- [ ] Missing rule/source → `BLOCKED_BY_INPUT` for that check.
- [ ] Report unsupported checks explicitly.
- [ ] Commit.

---

### Task 7: IFC validator [P06-T07]

**Files:**
- Create: `src/amanda_agent/qa/ifc.py`
- Test: `tests/unit/test_ifc_qa.py`

- [ ] Build or store a tiny valid IFC fixture.
- [ ] Parse via IfcOpenShell.
- [ ] Reject zero-byte/unparseable file.
- [ ] Count expected storeys/spaces/walls/doors on fixture.
- [ ] Production validator compares units, geospatial/project transforms, extents, storeys/spaces, openings and logical-ID mapping under the pinned export settings. Legitimate splits/merges need explicit mapping; counts alone cannot prove fidelity.
- [ ] Commit.

---

### Task 8: PDF validator [P06-T08]

**Files:**
- Create: `src/amanda_agent/qa/pdf.py`
- Test: `tests/unit/test_pdf_qa.py`

- [ ] Reject missing/zero-byte PDF.
- [ ] Verify expected minimum/exact page count from export manifest.
- [ ] Render every page to PNG with the locally validated PDF library/tool.
- [ ] Store previews in release `preview/pdf/`.
- [ ] Detect blank pages by raster variance threshold as a machine sanity signal; do not use this as sole visual quality test.
- [ ] Commit.

---

### Task 9: DWG sanity validator [P06-T09]

**Files:**
- Create: `src/amanda_agent/qa/dwg.py`
- Test: `tests/unit/test_dwg_qa.py`

- [ ] Verify path/nonzero size.
- [ ] If a compatible local DWG parser is already available/tested, inspect header/extents/layers.
- [ ] Otherwise verify export result, file signature/size and explicitly report `LIMITED_DWG_VALIDATION`; do not install AutoCAD solely for QA.
- [ ] Commit.

---

### Task 10: Persistence coordinator [P06-T10]

**Files:**
- Create: `src/amanda_agent/qa/persistence.py`
- Test: `tests/unit/test_persistence_plan.py`

Required sequence:
1. save RC;
2. wait for save completion;
3. close Revit normally and hash the closed stable file;
4. confirm process exits;
5. start Revit 2027 executable detected by Plan 01;
6. open RC;
7. reconnect preferred provider;
8. provider health;
9. critical model/program QA;
10. compare semantic state expectations; if an intentional later save changes file bytes, regenerate hashes/exports and revalidate before sealing.

- [ ] Test promotion object refuses incomplete sequence.
- [ ] Commit.

---

### Task 11: Release manifest [P06-T11]

**Files:**
- Create: `src/amanda_agent/release/manifest.py`
- Test: `tests/unit/test_release_manifest.py`

Fields include:
- project/release;
- timestamp;
- Revit product/file build;
- provider repo commits + installed hashes;
- Design Engine version/commit;
- selected solution ID/run/seed;
- requirements/site/regulation versions;
- QA summary;
- persistence summary;
- exports and hashes;
- release_profile STUDY or FINAL, required versus optional checks/artifacts, accepted limitations and approval evidence;
- content hashes for every artifact except the manifest itself (avoid recursive self-hash), and source-to-export identity/coordinate map.

- [ ] Deterministic sorted JSON serialization.
- [ ] Missing required artifact hash blocks GOLDEN.
- [ ] Commit.

---

### Task 12: GOLDEN promoter [P06-T12]

**Files:**
- Create: `src/amanda_agent/release/promote.py`
- Test: `tests/unit/test_release_promotion.py`

- [ ] QA FAIL and any unwaived mandatory blocked check prevent promotion. STUDY may explicitly retain missing survey/normative checks, with visible limitations; FINAL cannot waive them into compliance. Never infer acceptance from an empty issue list.
- [ ] Persistence incomplete blocks promotion.
- [ ] Mandatory export validation incomplete blocks promotion.
- [ ] Existing GOLDEN directory cannot be overwritten.
- [ ] Assemble the complete RVT/exports/previews/reports/provenance in a new staging directory; verify every hash and mandatory result, then publish with a no-overwrite atomic directory operation where supported (otherwise a tested completion marker protocol). Interrupted staging is never a GOLDEN. All reports exist before sealing; later corrections create a new release.
- [ ] Commit.

---

### Task 13: QA/export CLI [P06-T13]

**Files:**
- Create: `src/amanda_agent/commands/qa.py`
- Create: `src/amanda_agent/commands/export.py`
- Modify: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_release_cli.py`

Commands:
- `amanda-agent qa --model-manifest PATH`
- `amanda-agent export plan --release-id RC01`
- `amanda-agent export verify --release-id RC01`
- `amanda-agent release promote --release-id RC01`
- `amanda-agent release verify --release-id GOLDEN-001`

Create `src/amanda_agent/commands/release.py` and register its Typer group. `release verify` recomputes actual artifact hashes, required-file presence and manifest/QA/profile invariants; printing JSON is not validation.

- [ ] `qa` writes JSON + Markdown.
- [ ] export plan is read-only.
- [ ] promotion guard tested from CLI.
- [ ] Commit.

---

### Task 14: Synthetic R14→R16 release drill [P06-T14]

**Artifacts:** lab release directories.

- [ ] Use Plan 05 synthetic R13 model.
- [ ] Run full supported QA; create R14 report.
- [ ] Save to a new provisional RC path; certify R15 only after the cold-reopen verification below.
- [ ] Hash RC.
- [ ] Close Revit; verify exit.
- [ ] Restart cold; reopen RC; reconnect provider.
- [ ] Re-run critical QA.
- [ ] Export IFC; parse with IfcOpenShell.
- [ ] Export PDF; validate pages/previews.
- [ ] Export DWG; run supported validator.
- [ ] Generate manifest and artifact hashes.
- [ ] Complete required visual review (Task 15), reports and provenance in staging before promoting lab GOLDEN R16.
- [ ] Attempt to promote over same GOLDEN path and assert rejection.

---

### Task 15: Visual-documentation review protocol [P06-T15]

**Files:** `src/amanda_agent/qa/visual.py`, tests where deterministic.

- [ ] Collect sheet/page PNG previews.
- [ ] When current Codex environment supports image inspection, inspect for viewport overflow, crop errors, obvious tag/cota collisions, blank views, titleblock collisions.
- [ ] Store machine/vision findings as `VISUAL_REVIEW`, not normative proof.
- [ ] If Codex image inspection is unavailable, produce a human-review queue with exact preview files rather than claiming visual PASS.
- [ ] Commit.

---

## Phase 06 Verification Gate

### GO
Synthetic GOLDEN exists, is immutable, survived cold Revit restart, and has validated IFC/PDF plus supported DWG evidence.

### GO_WITH_LIMITATIONS
A declared STUDY profile may accept limited DWG-depth checks with evidence. Required sheet visual review and mandatory exports cannot be silently skipped; a pending review blocks that deliverable's final acceptance.

### NO_GO
RC can promote without persistence/QA, GOLDEN can be overwritten, or invalid exports are accepted.
