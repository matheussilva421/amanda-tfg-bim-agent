> GERADO de [2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md](../../../2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-04) em 2026-09-15. Edite o COMBINED e execute `docs/review/package_review.py`; não edite esta cópia. Caminhos operacionais no texto são relativos à raiz do projeto.

<a id="phase-04"></a>

# Generative Design Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:subagent-driven-development` or `superpowers:executing-plans`; TDD for all solver/geometry code; systematic debugging for infeasible models or nondeterminism.

**Goal:** Implement deterministic generation, validation, scoring, Pareto filtering, and explanation of architectural alternatives from canonical Amanda requirements/site data.

**Architecture:** OR-Tools CP-SAT solves discrete assignment decisions; Shapely is geometric truth; NetworkX handles graphs/path metrics. Resolution progresses site → macrozones → blocks → sectors → rooms. TopologicPy and Ladybug/Honeybee are optional enhancements and must not destabilize the core engine.

**Tech Stack:** Python 3.12, OR-Tools, Shapely, NetworkX, IfcOpenShell; optional TopologicPy, Ladybug/Honeybee.

**Spec:** [design specification](../../../2026-09-11-amanda-tfg-bim-agent-design.md)

## Global Constraints

- Same canonical input + engine version + seed = same output.
- Hard violation invalidates candidate.
- Soft constraints affect score only.
- No beauty score.
- Weights are versioned files.
- Source requirements are read-only.
- Gardens/external spaces are first-class program geometry.
- Detailed environmental simulation is finalist-only.

## File Structure

```text
src/amanda_agent/design/
├── models.py
├── geometry.py
├── constraints.py
├── adjacency.py
├── flows.py
├── privacy.py
├── archetypes.py
├── macrozones.py
├── blocks.py
├── rooms.py
├── external_spaces.py
├── environmental.py
├── scoring.py
├── pareto.py
├── generate.py
├── pipeline.py
└── explain.py

design-engine/config/
├── tolerances.yaml
├── weights.yaml
└── archetypes.yaml

tests/
├── geometry/
├── solver/
└── regression/fixtures/
```

---

### Task 1: Install and pin core design dependencies [P04-T01]

**Files:**
- Modify: `pyproject.toml`
- Create: `requirements.lock.txt`

- [ ] Add:

```toml
"ortools>=9.14,<10",
"shapely>=2.1,<3",
"networkx>=3.5,<4",
"ifcopenshell>=0.8,<1"
```

- [ ] Install:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

- [ ] Verify:

```powershell
.\.venv\Scripts\python.exe -c "import ortools, shapely, networkx, ifcopenshell; print('PASS')"
```

- [ ] Resolve these candidate ranges against available Windows/Python wheels before adopting them. Freeze exact resolved third-party packages, excluding editable absolute paths; rebuild a fresh venv from the lock and run import/core tests before claiming reproducibility:

```powershell
.\.venv\Scripts\python.exe -m pip freeze --exclude-editable | Sort-Object | Set-Content -Encoding utf8 requirements.lock.txt
```

- [ ] Commit.

---

### Task 2: Design solution models [P04-T02]

**Files:**
- Create: `src/amanda_agent/design/models.py`
- Test: `tests/solver/test_design_models.py`

**Interfaces:** `DesignSolution`, `MetricSet`, `ConstraintViolation`, `DesignStatus`.

- [ ] Write JSON round-trip test.
- [ ] Require fields: solution_id, run_id, seed, requirements_version, site_version, engine_version, archetype, geometry, metrics, hard_violations, soft_penalties, parents, status.
- [ ] Test APPROVED_FOR_BIM is explicit, content-bound and not default. AGENT_DELEGATED with valid decision evidence is eligible without Amanda approval; AMANDA_REVIEW_PENDING does not block BIM. Reject records falsely attributing personal approval or changing the fixed 20-person program.
- [ ] Commit.

---

### Task 3: Geometry primitives/tolerances [P04-T03]

**Files:**
- Create: `src/amanda_agent/design/geometry.py`
- Create: `design-engine/config/tolerances.yaml`
- Test: `tests/geometry/test_geometry.py`

- [ ] Define tolerances in meters/percent; no feet inside Design Engine.
- [ ] Test containment, overlap, minimum distance, area delta, centroid.
- [ ] Implement with Shapely, not hand-rolled polygon math.
- [ ] Test a self-intersecting polygon fails early.
- [ ] Commit.

---

### Task 4: Hard-constraint engine [P04-T04]

**Files:**
- Create: `src/amanda_agent/design/constraints.py`
- Test: `tests/solver/test_hard_constraints.py`

**Interfaces:** `validate_candidate(candidate, requirements, site) -> list[ConstraintViolation]`.

- [ ] Test room outside buildable site → violation.
- [ ] Test overlap → violation.
- [ ] Test required room missing → violation.
- [ ] Test required accessible room missing → violation.
- [ ] Test `MUST_BE_SEPARATED` broken → violation.
- [ ] Implement validators by resolution: MACRO validates sector capacities/boundary/separation; BLOCK validates block geometry and gross-area budget; ROOM validates expanded room instances, net areas and traversable routes. Checks unavailable at that resolution are NOT_EVALUATED, never PASS. Do not reject every macro candidate merely because rooms do not exist yet.
- [ ] Assert hard violations are never converted to numeric soft penalties.
- [ ] Commit.

---

### Task 5: Adjacency graph [P04-T05]

**Files:**
- Create: `src/amanda_agent/design/adjacency.py`
- Test: `tests/solver/test_adjacency.py`

- [ ] Build NetworkX graph from canonical relations.
- [ ] Test `MUST_ADJOIN` pass/fail.
- [ ] Test `SHOULD_BE_NEAR` penalty monotonically worsens with distance.
- [ ] Test `MUST_BE_SEPARATED` stays hard.
- [ ] Commit.

---

### Task 6: Flow graphs [P04-T06]

**Files:**
- Create: `src/amanda_agent/design/flows.py`
- Test: `tests/solver/test_flows.py`

- [ ] Implement independent resident/child/staff/visitor/service/emergency graphs.
- [ ] Synthetic visitor route crossing private residential node must fail when policy forbids it.
- [ ] Service/resident path crossing may be a weighted soft penalty when configured.
- [ ] Derive traversable graph edges from actual corridors, portals/doors, widths, obstacles and access permissions, with vertical connections where applicable. An adjacency or centroid line is not an accessible route. Compute path lengths/crossings deterministically and reject disconnected routes.
- [ ] Commit.

---

### Task 7: Privacy gradient metric [P04-T07]

**Files:**
- Create: `src/amanda_agent/design/privacy.py`
- Test: `tests/solver/test_privacy.py`

- [ ] Test direct public→privacy-5 transition is strongly penalized/invalid per configuration.
- [ ] Test public→controlled→technical→transition→residential scores better.
- [ ] Keep raw transition sequence in evidence.
- [ ] Commit.

---

### Task 8: Archetype configuration [P04-T08]

**Files:**
- Create: `design-engine/config/archetypes.yaml`
- Create: `src/amanda_agent/design/archetypes.py`
- Test: `tests/solver/test_archetypes.py`

Archetypes:
- COURTYARD
- LINEAR_SPINE
- CLUSTER
- PRIVACY_GRADIENT
- DOUBLE_COURTYARD
- COMB

- [ ] Define each as initialization/relationship rules, not a fixed drawing.
- [ ] Synthetic rectangular site: each archetype must produce a valid macro seed.
- [ ] Make gradient/courtyard/cluster exploration explicit for Amanda without forcing winner.
- [ ] Commit.

---

### Task 9: OR-Tools macrozone solver [P04-T09]

**Files:**
- Create: `src/amanda_agent/design/macrozones.py`
- Test: `tests/solver/test_macrozones.py`

- [ ] Write a three-sector RED test.
- [ ] Model sector-to-region assignment with CP-SAT.
- [ ] Encode bounded integer-grid variables/scaling for CP-SAT, sector capacity and separation/adjacency. Define discretization/rounding tolerance and revalidate resulting metric polygons with Shapely; reject grid-feasible but geometrically invalid results. Record solver status and infeasibility evidence separately.
- [ ] Set solver random seed from run seed.
- [ ] Test two executions with same seed produce same assignment/order.
- [ ] Commit.

---

### Task 10: Block polygon generator [P04-T10]

**Files:**
- Create: `src/amanda_agent/design/blocks.py`
- Test: `tests/solver/test_blocks.py`

- [ ] Blocks remain inside buildable area.
- [ ] Blocks do not overlap.
- [ ] Block area matches sector demand within configured band.
- [ ] Sector splitting is allowed only by archetype/configuration.
- [ ] Reject sliver polygons under minimum width.
- [ ] Commit.

---

### Task 11: Room refinement [P04-T11]

**Files:**
- Create: `src/amanda_agent/design/rooms.py`
- Test: `tests/solver/test_rooms.py`

- [ ] Start with synthetic 3-room rectangle.
- [ ] Enforce canonical area/min-dimension constraints only when they exist.
- [ ] Preserve room logical IDs.
- [ ] Reject overlaps and unreachable/orphan spaces.
- [ ] Separate net room area from gross footprint, wall thickness, shafts and circulation; assign each area once and report the net-to-gross factor as a hypothesis until modeled. Test multi-storey and single-storey accounting; outside gardens do not count as enclosed internal area.
- [ ] Commit.

---

### Task 12: External spaces as first-class geometry [P04-T12]

**Files:**
- Create: `src/amanda_agent/design/external_spaces.py`
- Test: `tests/solver/test_external_spaces.py`

- [ ] Required external logical IDs appear exactly once.
- [ ] Programmed area targets/tolerances respected.
- [ ] Protected/therapeutic external spaces respect privacy policy.
- [ ] Playground/child relations tested.
- [ ] No “leftover polygon = garden” shortcut.
- [ ] Commit.

---

### Task 13: Versioned scoring [P04-T13]

**Files:**
- Create: `src/amanda_agent/design/scoring.py`
- Create: `design-engine/config/weights.yaml`
- Test: `tests/solver/test_scoring.py`

Raw dimensions:
- program compliance;
- privacy/security;
- adjacency;
- circulation;
- accessibility;
- solar heuristic;
- ventilation heuristic;
- green integration;
- compactness;
- constructability;
- concept fidelity.

- [ ] Unknown score dimension is rejected.
- [ ] Give each metric unit, min/max direction, normalization bounds, missing-data rule and evidence source in the versioned configuration. Apply weights to normalized comparable values; never mix raw metres and percentages. Missing environmental inputs yield NOT_EVALUATED and exclude/rebalance that dimension transparently across the whole comparison. Weight changes alter total but never raw metrics.
- [ ] Store raw metrics and weighted total.
- [ ] Explicitly no aesthetics/beauty metric.
- [ ] Commit.

---

### Task 14: Pareto frontier [P04-T14]

**Files:**
- Create: `src/amanda_agent/design/pareto.py`
- Test: `tests/solver/test_pareto.py`

- [ ] Known dominated vector fixture.
- [ ] Deterministic non-dominated filtering.
- [ ] Preserve tradeoff alternatives even when weighted total lower.
- [ ] Commit.

---

### Task 15: Fast solar/ventilation heuristics [P04-T15]

**Files:**
- Create: `src/amanda_agent/design/environmental.py`
- Test: `tests/solver/test_environmental_heuristics.py`

- [ ] True-north-aware facade orientation.
- [ ] Apply source-backed Amanda orientation/wind findings as **project heuristics**, not universal truth.
- [ ] Label outputs `HEURISTIC`.
- [ ] Test expected relative score changes for east/west and wind exposure on synthetic case.
- [ ] Commit.

---

### Task 16: Deterministic generation [P04-T16]

**Files:**
- Create: `src/amanda_agent/design/generate.py`
- Test: `tests/solver/test_generation_reproducibility.py`

- [ ] Generate fixed set with run ID and seed list.
- [ ] Canonicalize JSON ordering/float rounding before hash.
- [ ] Set `num_search_workers = 1`, pinned OR-Tools/runtime, fixed seed, deterministic search budget and ordered inputs. Record OPTIMAL/FEASIBLE/INFEASIBLE/UNKNOWN separately; wall-clock timeout UNKNOWN is not proof of infeasibility. Same input/version/solver configuration produces the same geometry hash in the supported environment; exclude timestamps, paths, durations and run IDs from the semantic digest.
- [ ] On a fixture with multiple known feasible options, test diversity of the configured generator. Different seeds do not guarantee different optima; deduplicate geometry hashes and report actual candidate count.
- [ ] Store every seed with candidate.
- [ ] Commit.

---

### Task 17: Progressive pipeline [P04-T17]

**Files:**
- Create: `src/amanda_agent/design/pipeline.py`
- Test: `tests/solver/test_pipeline.py`

Default production intent:
- 120–240 macro candidates;
- hard filter;
- top ~15;
- room refinement;
- top ~5;
- detailed finalist stage;
- top 3.

- [ ] Counts are config values.
- [ ] Unit test uses smaller values.
- [ ] Every rejected candidate records exact hard rejection reason.
- [ ] No Revit call in pipeline.
- [ ] Commit.

---

### Task 18: Explainability [P04-T18]

**Files:**
- Create: `src/amanda_agent/design/explain.py`
- Test: `tests/solver/test_explain.py`

- [ ] Generate strengths from actual high raw metrics.
- [ ] Generate tradeoffs from actual penalties/relative comparisons.
- [ ] List hard violations (finalists must have none).
- [ ] Distinguish source principle vs design hypothesis.
- [ ] Produce `WHY_THIS_OPTION.md` from structured data; no unsupported prose claim.
- [ ] Commit.

---

### Task 19: Core regression fixtures [P04-T19]

**Directories:**
- `tests/regression/fixtures/simple-3-room/`
- `courtyard/`
- `two-access/`
- `privacy-gradient/`
- `accessible-route/`

For each fixture:
- [ ] input JSON;
- [ ] seed;
- [ ] expected invariants JSON;
- [ ] expected canonical hash when stable enough;
- [ ] regression test.

Commit fixtures.

---

### Task 20: Optional TopologicPy spike [P04-T20]

- [ ] Create isolated `.venv-topologic` so core solver cannot be broken.
- [ ] Install an exact evaluated TopologicPy version with its own dependency lock; record package availability before installation.
- [ ] Run minimal topology/graph operation.
- [ ] Record package/dependency versions, license, install conflicts, runtime value.
- [ ] Promote only if it adds a proven capability over NetworkX/Shapely.
- [ ] Otherwise keep capability UNTESTED or DEGRADED according to evidence and set scheduling decision `DEFERRED_OPTIONAL` outside CapabilityStatus; core engine remains GO.

---

### Task 21: Optional Ladybug/Honeybee finalist environment [P04-T21]

- [ ] Create isolated `.venv-environmental`.
- [ ] Install `ladybug-core` and `lbt-honeybee`.
- [ ] Verify imports/CLI.
- [ ] Verify EPW station/timezone/year/hash plus the actual Radiance/EnergyPlus executables and versions needed by the selected recipe. Package imports alone do not prove a simulation engine. Run one synthetic reproducible case and validate outputs.
- [ ] Label genuine solver output `SIMULATED` only after reproducible run.
- [ ] Failure does not block core heuristic engine.

---

### Task 22: CLI `design` and `compare` [P04-T22]

**Files:**
- Create: `src/amanda_agent/commands/design.py`
- Create: `src/amanda_agent/commands/compare.py`
- Modify: `src/amanda_agent/cli.py`
- Test: `tests/unit/test_design_cli.py`

- [ ] `design --run-id RUN-001` reads canonical requirements/site and creates run directory.
- [ ] Reject mutable/invalid source state.
- [ ] `compare RUN-001` prints and saves finalist matrix.
- [ ] Source files remain unchanged; assert before/after hashes.
- [ ] Commit.

---

## Phase 04 Verification Gate

```powershell
.\.venv\Scripts\python.exe -m pytest tests/geometry tests/solver tests/regression -q
```

### GO
Core engine deterministic, hard constraints enforced, finalists explainable, no Revit dependency.

### GO_WITH_LIMITATIONS
Optional TopologicPy or detailed Ladybug/Honeybee unavailable while OR-Tools/Shapely/NetworkX core is green.

### NO_GO
Hard constraints can leak, requirements mutate, or same-seed reproducibility fails.
