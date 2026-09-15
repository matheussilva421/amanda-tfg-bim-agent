> GERADO de [2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-03) em 2026-09-15. Edite o COMBINED e execute `docs/review/package_review.py`; não edite esta cópia. Caminhos operacionais no texto são relativos à raiz do projeto.

<a id="phase-03"></a>

# Project Intelligence and Source Ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; TDD for parser/schema code; systematic debugging for reconciliation failures.

**Goal:** Convert Amanda's TFG, program of needs, site material, and verified normative/source files into canonical structured project data with immutable provenance and an explicit missing-data registry.

**Architecture:** Source files are immutable. Extraction produces three separate classes: `SOURCE_FACT`, `DERIVED_CONSTRAINT`, and `DESIGN_HYPOTHESIS`. Canonical JSON/YAML is schema-validated and becomes the only input consumed by the Design Engine.

**Tech Stack:** Python 3.12, Pydantic, PyYAML, local PDF parser, Shapely/GeoJSON.

**Spec:** [design specification](../../../2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- Preserve original source bytes and SHA-256.
- Never silently “correct” Amanda's source values.
- Every `SOURCE_FACT` has a source reference.
- Missing topography remains missing.
- Numeric normative rules enter hard constraints only from a verified source/version.

## File Structure

```text
src/amanda_agent/
├── ingest/
│   ├── manifest.py
│   ├── provenance.py
│   ├── pdf.py
│   └── pipeline.py
├── requirements/
│   ├── models.py
│   ├── relations.py
│   ├── regulations.py
│   └── validators.py
└── site/
    ├── models.py
    ├── geometry.py
    └── transform.py

project/
├── requirements/
├── site/
├── regulations/
├── references/
└── provenance/

docs/source/
```

---

### Task 1: Source manifest and hashing [P03-T01]

**Files:**
- Create: `src/amanda_agent/ingest/manifest.py`
- Test: `tests/unit/test_source_manifest.py`

**Interfaces:** `sha256_file(Path) -> str`, `SourceDocument`.

- [ ] Write SHA-256 fixture test using `abc` known digest.
- [ ] Implement streaming file hash (1 MiB chunks; no full-file load required).
- [ ] Define `SourceDocument` fields: source_id, filename, sha256, mime_type, ingested_at, immutable_path.
- [ ] Test round-trip.
- [ ] Commit.

---

### Task 2: Provenance model [P03-T02]

**Files:**
- Create: `src/amanda_agent/ingest/provenance.py`
- Test: `tests/unit/test_provenance.py`

**Interfaces:**

```python
class FactClass(StrEnum):
    SOURCE_FACT = "SOURCE_FACT"
    DERIVED_CONSTRAINT = "DERIVED_CONSTRAINT"
    DESIGN_HYPOTHESIS = "DESIGN_HYPOTHESIS"
```

Each `SourceReference` includes source ID/hash, page/paragraph/table or sheet/cell locator, extraction method, confidence and note. Add verification_status and adoption_status from design section 1.1; a source statement may be DISPUTED and a documented hypothesis remains DESIGN_HYPOTHESIS.

- [ ] Test `SOURCE_FACT` without source ID is rejected.
- [ ] Test a hypothesis cannot claim fact class.
- [ ] Implement.
- [ ] Commit.

---

### Task 3: Immutable ingest command [P03-T03]

**Files:**
- Create: `src/amanda_agent/commands/ingest.py`
- Modify: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_ingest_command.py`

**Interfaces:** `amanda-agent ingest PATH...`

- [ ] Test source copied byte-for-byte into `docs/source/`.
- [ ] Test same content hash is recognized and not duplicated unnecessarily.
- [ ] Test a different file cannot overwrite an existing immutable source path.
- [ ] Generate/update `project/provenance/source-manifest.yaml` atomically.
- [ ] Commit.

---

### Task 4: Inventory and reconcile all supplied Amanda sources [P03-T04]

**Expected sources:** the root TFG/program PDFs and the 21-file `TFG_Amanda_2026/` supporting package. Follow the source table in design section 1.1. Inventory DOCX/XLSX/SVG/DXF/IFC/PPTX/HTML as well as PDFs; do not execute embedded scripts or follow external links during extraction.

- [ ] Search the explicitly provided input folder/path, not the entire user's home drive.
- [ ] Treat support documents as source assertions/hypotheses, not primary verified regulation or approved architecture. `PROGRAM_BASELINE = RESOLVED`: the user explicitly selected **20 people according to programa_necessidades.pdf** on 2026-09-15. Adopt its full program (626 m² internal useful area, 260 m² programmed external area); preserve the spreadsheet's 42-person hypothesis as not adopted. Persist the selection with source SHA256 and this decision's provenance; do not ask for the same choice again or merge spreadsheet quantities into the PDF baseline.
- [ ] If either core PDF source is absent, set production blocker `BLOCKED_BY_INPUT:SOURCE_DOCUMENTS`, but keep synthetic development usable.
- [ ] When present, assign stable IDs `SRC-TFG-001`, `SRC-PROGRAM-001` for this source version.
- [ ] Compute hashes.
- [ ] Verify copied bytes match hashes.
- [ ] Keep PDFs private/local; commit them only if repository policy explicitly allows source documents. Manifests can be committed independently.

---

### Task 5: PDF text extraction adapter [P03-T05]

**Files:**
- Create: `src/amanda_agent/ingest/pdf.py`
- Test: `tests/unit/test_pdf_adapter.py`

- [ ] Add a local parser dependency only after a small compatibility test; prefer PyMuPDF or pypdf based on actual extraction quality. Install and lock the tested Shapely version here before site-schema validation (Plan 04 reuses this lock), plus DOCX/XLSX adapters when needed. Dependencies required by this phase cannot first be installed in Phase 04.
- [ ] Create fixture PDF with two pages and known text.
- [ ] Test page-number-preserving extraction.
- [ ] Store extracted text under `project/provenance/extracted/` with source hash.
- [ ] Never treat OCR output as authoritative when selectable text exists.
- [ ] Add tested DOCX paragraph/table and XLSX sheet/cell/formula adapters. Distinguish formulas, cached values and independently recalculated values; a stale cache is not proof. Inspect drawings/IFC units and provenance in read-only copies. Retain placeholders/conflicts with locators.
- [ ] Commit parser choice/version to environment lock.

---

### Task 6: Program requirement schema [P03-T06]

**Files:**
- Create: `src/amanda_agent/requirements/models.py`
- Test: `tests/unit/test_requirement_models.py`

**Interfaces:** `SpaceRequirement`, `SectorRequirement`, `ProgramRequirementSet`.

- [ ] Write tests rejecting zero/negative canonical area/quantity, empty provenance, NaN/infinity, invalid ranges and duplicate IDs. Use a separate draft-extraction schema with nulls for unknowns; canonical compilation blocks required unknown fields instead of inventing them.
- [ ] Implement:

```python
from pydantic import BaseModel, Field, model_validator

class SpaceRequirement(BaseModel):
    logical_id: str
    name: str
    sector: str
    quantity: int = Field(ge=1)
    target_area_m2: float = Field(gt=0)
    min_area_m2: float | None = Field(default=None, gt=0)
    max_area_m2: float | None = Field(default=None, gt=0)
    privacy_level: int | None = Field(default=None, ge=0, le=5)
    accessible: bool | None = None
    source_refs: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def valid_range(self):
        if self.min_area_m2 is not None and self.target_area_m2 < self.min_area_m2:
            raise ValueError("target below minimum")
        if self.max_area_m2 is not None and self.target_area_m2 > self.max_area_m2:
            raise ValueError("target above maximum")
        return self
```

- [ ] Test and commit.

---

### Task 7: Compile the program of needs into canonical JSON [P03-T07]

**Files:**
- Create at runtime: `project/requirements/program.json`
- Create: `project/requirements/program-summary.md`
- Test: `tests/project/test_amanda_program.py`

- [ ] Extract every program line item exactly from source.
- [ ] Assign one requirement ID per source row and expand quantity into stable instance IDs only at generation. Explicitly tag internal/external area and whether target_area_m2 is per unit; every total is quantity × unit area. Avoid double expansion.
- [ ] Record source quantity/target-area facts.
- [ ] Import the selected PDF baseline for up to 20 simultaneously accommodated people. Preserve its room quantities and per-unit area targets; distribution of women/children/beds needs layout validation. Record the 42-person spreadsheet as an unselected hypothesis; adapt derived calculations from the adopted inputs instead of importing the other scenario's totals. User selection resolves adoption, not normative verification or APPROVED_FOR_BIM.
- [ ] Reconcile source subtotals and overall internal/external totals.
- [ ] Add tests for known source totals and presence of accessible bedroom/bathroom requirements.
- [ ] Generate markdown summary from canonical JSON, never the reverse.
- [ ] Commit canonical JSON and tests.

---

### Task 8: Relations schema [P03-T08]

**Files:**
- Create: `src/amanda_agent/requirements/relations.py`
- Test: `tests/unit/test_relations.py`

Relation enum:
- `MUST_ADJOIN`
- `SHOULD_ADJOIN`
- `SHOULD_BE_NEAR`
- `CAN_BE_NEAR`
- `NEUTRAL`
- `SHOULD_BE_SEPARATED`
- `MUST_BE_SEPARATED`

- [ ] Test self-relations rejected unless explicitly whitelisted for group relation.
- [ ] Add weight and optional max/preferred distance.
- [ ] Add flow-network enum: resident, child, staff, visitor, service, emergency.
- [ ] Commit.

---

### Task 9: Compile source-backed principles separately from design hypotheses [P03-T09]

**Files:**
- Create: `project/requirements/source-principles.yaml`
- Create: `project/requirements/design-hypotheses.yaml`
- Test: `tests/project/test_fact_separation.py`

- [ ] Extract only TFG-supported principles into source-principles, including the stated shelter/transition/city logic, block/garden parti, privacy/security concepts, and stated climate orientation findings.
- [ ] Put inferred room adjacency proposals into design-hypotheses.
- [ ] Every source principle gets source refs.
- [ ] Validator forbids a `DESIGN_HYPOTHESIS` object from appearing in source-principles.
- [ ] Commit.

---

### Task 10: Canonical site schema [P03-T10]

**Files:**
- Create: `src/amanda_agent/site/models.py`
- Test: `tests/unit/test_site_models.py`

Fields:
- boundary polygon;
- design coordinate origin;
- true north;
- frontages/roads;
- candidate access points;
- buildable area if verified;
- setbacks if verified;
- topography state;
- provenance.

Source topography enum: `MISSING`, `VERIFIED_TOPOGRAPHY`. Separate representation enum: `PLANAR_PLACEHOLDER`, `VERIFIED_TOPOGRAPHY`. A local drawing plane may use z=0 as a design convention, but no surveyed elevation points are emitted for MISSING sources. If needed to develop a sloping-site study, store hypothetical elevations in a separate versioned scenario override with PROVISIONAL_ASSUMPTION, never in the verified/source point set; test replacement by later survey data and invalidation of affected checks.

- [ ] Test invalid self-intersecting boundary is rejected by Shapely.
- [ ] Test `MISSING` cannot carry invented elevation points.
- [ ] Commit.

---

### Task 11: Compile known site facts and missing-data registry [P03-T11]

**Files:**
- Create: `project/site/site.json`
- Create: `project/site/missing-data.yaml`

- [ ] Record reported site area 24,135 m² as a source assertion, with SITE_BOUNDARY/SITE_OCCUPANCY blockers for legal boundary, current use and relocation premise. If no verified calibrated polygon/north exists after research, create an explicitly provisional study reconstruction with uncertainty/source rationale; never claim an equal-area rectangle is the real cadastral boundary. Separate the scenario geometry from verified site data.
- [ ] Record the conflicting three/four-frontage assertions with locators. Verify actual boundary/frontages before freezing site_version; do not resolve them by counting names in prose.
- [ ] Record true north/orientation only from verified source drawing/data.
- [ ] If no verified survey/topographic file is supplied, set `topography = MISSING`.
- [ ] Add blocker:

```yaml
id: SITE_TOPOGRAPHY
state: MISSING
blocks:
  - final_grading
  - final_altimetric_accessibility_validation
allows:
  - 2d_macrozoning
  - schematic_massing_on_planar_reference
```

- [ ] Commit.

---

### Task 12: Regulation source registry [P03-T12]

**Files:**
- Create: `src/amanda_agent/requirements/regulations.py`
- Create: `project/regulations/registry.yaml`
- Test: `tests/unit/test_regulation_registry.py`

Statuses: `IDENTIFIED`, `SOURCE_ACQUIRED`, `VERIFIED`, `SUPERSEDED`.

- [ ] Seed regulation names identified by Amanda's TFG without copying remembered numerical rules.
- [ ] Require applicable primary source/version/date/article/map, extracted rule, unit, scope and verification evidence before a normative number becomes DERIVED_CONSTRAINT. Acquisition alone is not verification. The supplied LC208 DOCX and XLSX 'ATENDE' cells are secondary references only.
- [ ] Test an unverified numeric rule cannot be compiled as hard constraint.
- [ ] Commit.

---

### Task 13: Provenance integrity suite [P03-T13]

**Files:** `tests/project/test_provenance_integrity.py`

- [ ] Every source fact has source ref.
- [ ] Every requirement logical ID unique.
- [ ] No unresolved numeric source placeholder silently became a number.
- [ ] No hypothesis exists in source-fact files.
- [ ] Source file hashes still match immutable copies.
- [ ] Program subtotal/global reconciliation passes.
- [ ] Commit.

---

### Task 14: One-command validation report [P03-T14]

**Files:**
- Modify: `src/amanda_agent/commands/ingest.py`
- Runtime: `docs/reports/ingest-report.md`

- [ ] `amanda-agent ingest --validate-only` validates source hashes, canonical schemas, provenance, program totals, site status, regulation registry.
- [ ] Expected missing topography yields `GO_WITH_LIMITATIONS`, not corruption.
- [ ] Malformed canonical data yields nonzero exit.
- [ ] Report exact blocker IDs.
- [ ] Commit.

---

### Task 15: Academic deliverable and decision register [P03-T15]

**Files:** future `project/requirements/academic-deliverables.yaml`, `project/requirements/decisions.yaml`; tests `tests/project/test_deliverable_scope.py`.

- [ ] Map caderno revision, visits, metaprojeto, preliminary study, anteprojeto, pranchas, descriptive/calculation memorials, defense, authorship and institutional submission from the support plan to owner/source/status/evidence.
- [ ] Record the support claim of 4–6 A1 landscape synthesis boards as provisional until the institutional regulation is acquired. Keep dates unknown until the official calendar is available.
- [ ] Assign BIM-generated outputs versus human-authored/validated deliverables. No automated signatures, field visits or institutional submissions are implied by software completion.
- [ ] Test that an unresolved mandatory academic deliverable prevents a claim of TFG_COMPLETE while technical STUDY releases remain possible.
- [ ] Record TYPOLOGY, PROGRAM_BASELINE, SITE_BOUNDARY, SITE_OCCUPANCY and REGULATION_APPLICABILITY separately from finalist selection in `project/requirements/decision-register.yaml`, following design section 6.15.
- [ ] Implement research tasks using available read-only search/source tools: official maps/cadastral material, applicable consolidated regulation/anexos and institutional/project references. Persist queries, sources, applicability and conclusions. The agent decides routine architectural questions without waiting for preferences.
- [ ] Test that AGENT_DELEGATED can select an evidence-backed option and continue; unverified data can be recorded as PROVISIONAL_ASSUMPTION within DESIGN_HYPOTHESIS for a STUDY scenario, never VERIFIED source data. Keep normative numbers from unverified sources out of verified hard constraints.
- [ ] Test that missing source input blocks only the affected verified check, while a separately labeled provisional study can proceed; FINAL stays blocked by unresolved mandatory verification. Test later replacement of the assumption propagates to affected geometry/BIM/exports and preserves prior versions.
- [ ] Test Amanda feedback creates a new decision revision, takes precedence over delegated preferences, invalidates obsolete approval_hash and schedules the dependent validations without overwriting protected originals/releases.

## Phase 03 Verification Gate

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit tests/project -q
.\.venv\Scripts\python.exe -m amanda_agent ingest --validate-only
```

### GO
Canonical program/site/provenance valid and sufficient for intended design stage.

### GO_WITH_LIMITATIONS
Survey/topography or a normative source is missing, but schematic design remains valid within declared limits.

### NO_GO
Program/site source cannot be reconciled or source provenance is unreliable.
