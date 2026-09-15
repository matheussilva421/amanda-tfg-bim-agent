# Amanda TFG BIM Agent — Design Specification

**Status:** REVISED_DOCUMENT — revisão documental em 2026-09-15; implementação e validação Revit NOT_RUN  
**Target workstation:** Windows + Autodesk Revit 2027 Education (exact build to be detected at runtime)  
**Primary operating model:** Local-first, cloud only as fallback  
**Autonomy model:** Maximum autonomy within the user's current authorized task; this document describes future implementation and does not itself authorize installs, process termination, cloud uploads, or external actions beyond current authorization; architectural research and selection are delegated to the agent as defined in section 6.15  
**Primary Revit integration:** Horizun Revit MCP, subject to local validation  
**Secondary Revit integration:** RevitCortex, subject to local validation  
**Ultimate local fallback:** Custom Revit API automation (Python/C#)  
**Interchange fallback:** IFC/DXF/JSON/GeoJSON as appropriate  
**Cloud fallback:** Autodesk APS/Revit Automation only when local options are exhausted and justified  

---

## 1. Purpose

Build a persistent, auditable, fault-tolerant Codex-driven architecture/BIM system capable of taking Amanda's TFG source material, extracting and structuring requirements, generating and comparing architectural alternatives, validating constraints, creating a selected design in Autodesk Revit 2027, testing and repairing the resulting BIM, producing documentation and exports, and preserving reproducibility across sessions.

The system must maximize automation without sacrificing model integrity, provenance, architectural reasoning, or source fidelity.

The Codex agent is the orchestrator. It must not be the sole computational authority for geometry, constraints, adjacency, optimization, unit conversion, or BIM validation.

Core principle:

> **The LLM interprets; deterministic tools calculate; Revit materializes; QA verifies.**

---


<a id="project-baseline"></a>
## 1.1 Contexto documental e decisões ainda abertas

O objeto é um centro de acolhimento temporário para mulheres em situação de violência e seus filhos em Natal/RN. O TFG articula abrigo, transição e cidade, privacidade, fluxos controlados e blocos relacionados a jardins. Esses princípios orientam alternativas; não aprovam automaticamente a implantação já desenhada nos materiais auxiliares.

Esta especificação trata da automação de arquitetura/BIM. A conclusão do software ou de um GOLDEN técnico não equivale à conclusão acadêmica do TFG. Visitas, definição tipológica, validação com a orientadora, autoria, datas de banca e submissão institucional têm responsáveis e evidências próprios.

| Fonte local examinada | Evidência | Tratamento no projeto |
|---|---|---|
| `TFG_Amanda Fernandes_ENTREGA 15.06.2026.pdf` | 82 páginas; capítulo 3 contém as diretrizes; capítulo 5 contém condicionantes e lacunas | Fonte do caderno nessa versão; cada afirmação conserva página e hash. Não é levantamento cadastral nem texto normativo primário. |
| `programa_necessidades.pdf`, pp. 1–2 | Até 20 pessoas; setores internos 53 + 209 + 52 + 80 + 81 + 151 = 626 m²; externos 260 m²; estimativas fechada 783–814 e coberta 850–950 m² | Programa adotado por escolha explícita do usuário em 2026-09-15. Continua pré-dimensionamento; área unitária não é automaticamente mínimo normativo. |
| `TFG_Amanda_2026/4_PROJETO_E_CALCULOS/01_programa_de_necessidades.xlsx` | `Premissas!C15:C16` = 12 × 3,5; `C27` calcula 42 pessoas; entradas explicitamente hipotéticas | Versão alternativa, não soma nem substitui silenciosamente o PDF. Fórmula, valor de entrada e resultado recalculado ficam separados. |
| `TFG_Amanda_2026/1_COMECE_AQUI/01_COMECE_AQUI.pdf`, pp. 1–2 | Implantação, visitas e levantamento permanecem pendentes; desenhos HIPÓTESE não são decisões da autora | Registro de lacunas e orientações de apoio; conferir com Amanda. |
| `TFG_Amanda_2026/1_COMECE_AQUI/02_plano_de_acompanhamento.pdf`, pp. 2–5 | Tipologia, capacidade, terreno, pesquisa, estudo preliminar, anteprojeto e defesa | Matriz acadêmica separada, a confirmar no regulamento institucional e calendário vigentes. |
| `TFG_Amanda_2026/4_PROJETO_E_CALCULOS/06_implantacao_HIPOTESE.dxf` e `07_modelo_BIM_HIPOTESE.ifc` | Arquivos existentes, identificados como hipótese | `DESIGN_HYPOTHESIS`; servem para comparação/intercâmbio em cópias, não para contornar seleção ou provar topografia. |
| `TFG_Amanda_2026/3_VERIFICACAO_E_DADOS/01_verificacao_urbanistica_LC208.docx` | Parecer de apoio com artigos e ressalvas | Índice de questões a conferir em fontes oficiais; não converter seu título “verificação” em status `VERIFIED`. |
| `TFG_Amanda_2026/4_PROJETO_E_CALCULOS/02_memorial_de_calculo.xlsx` | Capacidade derivada da planilha; índices e reserva de incêndio hipotéticos; área de vagas digitada | Recalcular somente após baseline; confirmar normas/fontes e vínculos, sem importar resultados como conformidade. |

Decisões e bloqueadores que devem ser registrados na ingestão:

Fonte da decisão PROGRAM_BASELINE: `programa_necessidades.pdf`, SHA256 `11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17`, conferido em 2026-09-15. Evidência de adoção: seleção explícita do usuário nesta conversa de “20 pessoas, conforme o PDF”. A ingestão deve conferir esse hash antes de reaplicar a decisão à fonte.

- `PROGRAM_BASELINE = RESOLVED`: escolha explícita do usuário em 2026-09-15: **20 pessoas, conforme programa_necessidades.pdf**. `adoption_status = ACCEPTED` para o programa do PDF; hipótese de 42 pessoas da planilha não adotada, preservada para histórico. Na ingestão, vincular a decisão ao hash do PDF e importar seus ambientes/quantidades/áreas sem mesclar a planilha. Pessoas acolhidas incluem a capacidade conjunta do público atendido, não 20 famílias; distribuição entre mulheres, crianças e leitos ainda precisa ser detalhada no layout. Equipe/visitantes têm dimensionamento próprio. A escolha resolve o conflito de baseline, mas não valida normas, terreno nem arquitetura finalista.
- `TYPOLOGY`: pesquisar referências institucionais e adotar pelo agente um modelo coerente com acolhimento temporário e proteção das usuárias; justificar a política de sigilo/acesso. Não basta renomear o equipamento: explicitar consequências espaciais e operacionais. Revisão de Amanda é posterior, não pré-condição para desenvolver o estudo.
- `SITE_BOUNDARY`: os 24.135 m² informados e a divergência de três/quatro frentes precisam de documento/levantamento que defina polígono, confrontações, norte e área utilizável. Área escalar e imagem sem calibração não comprovam um lote real executável. O agente pesquisa geometrias disponíveis e pode produzir uma reconstrução esquemática identificada como PROVISIONAL_ASSUMPTION para continuar o estudo, mantendo rastreável sua incerteza e substituição futura.
- `SITE_OCCUPANCY`: registrar a ocupação mencionada da CPChoque e a realocação como premissa acadêmica a confirmar, sem presumir terreno vazio/disponível.
- `SITE_TOPOGRAPHY`: faltam cotas verificadas. `PLANAR_PLACEHOLDER` permite referência esquemática explicitamente artificial; não comprova terreno plano real.
- `REGULATION_APPLICABILITY`: verificar lei consolidada, anexos/mapas, uso, recuos, coeficientes, permeabilidade, altura, acessibilidade e incêndio aplicáveis. As conclusões sobre 22.500 m², 140 m, fruição pública ou área militar no apoio não são decisões legais desta revisão.

`SOURCE_FACT` significa “esta versão da fonte afirma X”, não “X é verdadeiro, vigente ou aprovado”. Além da classe, registrar `verification_status` (`UNVERIFIED`, `VERIFIED`, `DISPUTED`, `SUPERSEDED`) e `adoption_status` (`PROPOSED`, `ACCEPTED`, `REJECTED`). Uma hipótese contida em documento continua hipótese. Resolver conflito cria nova decisão/versionamento; preservar o registro original.

## 1.2 Autoridade documental

O ponto de entrada é [START_HERE_FOR_CODEX.md](START_HERE_FOR_CODEX.md). Este design define contratos; o [plano combinado](2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-00) contém o mestre e as nove fases. O ZIP original, recebido durante a revisão, contém planos separados; nesta revisão eles são regenerados em docs/superpowers/plans a partir do COMBINED, sem edição independente. A [revisão](PLAN_SELF_REVIEW.md) registra achados e limites da validação. Caminhos `src/`, `state/`, `project/` e `bim/` descritos a seguir são saídas futuras, não arquivos já implementados.

## 2. Scope

### 2.1 In scope

The system should automate, whenever technically possible:

- environment detection;
- Revit build detection;
- MCP/add-in discovery;
- dependency installation;
- source-code builds;
- configuration backup;
- MCP registration;
- tool smoke tests;
- capability benchmarking;
- requirements extraction;
- source-fact provenance;
- adjacency and flow modeling;
- hard/soft constraint modeling;
- design-option generation;
- design-option scoring;
- Pareto analysis;
- environmental heuristics;
- finalist refinement;
- conceptual Revit generation;
- selected-design BIM compilation;
- site/toposolid generation when reliable source data exists;
- walls, floors, roofs, rooms, doors, windows;
- accessibility checks;
- furniture placeholders;
- landscaping;
- material assignment;
- views, sections, elevations;
- schedules;
- sheets;
- dimensions and tags;
- model QA;
- export QA;
- RVT/IFC/DWG/PDF release;
- recovery after tool/Revit/Codex failure;
- persistent state between sessions;
- logging and provenance;
- controlled tool discovery if a capability is missing.

### 2.2 Explicitly out of scope unless later approved

- inventing missing survey/topography data;
- silently altering Amanda's source requirements;
- hiding agent-made choices or falsely attributing approval to Amanda; use the delegated decision record and later review instead;
- bypassing Autodesk authentication or licensing;
- installing untrusted binaries without source/reputation checks;
- disabling antivirus/firewall as a convenience;
- using cracked software;
- treating a successful tool return value as proof of model success;
- claiming normative/legal compliance without verified source material;
- cloud-first workflows;
- destructive changes to GOLDEN or source RVT files.

---

## 3. Architectural principles

### 3.1 Integrity over completion

If a requested action cannot be completed reliably, the system must preserve the last known-good checkpoint and report the blocker.

### 3.2 Source facts are immutable

Facts extracted from Amanda's documents are distinct from derived rules and design hypotheses.

Classes:

- `SOURCE_FACT`
- `DERIVED_CONSTRAINT`
- `DESIGN_HYPOTHESIS`

The optimization engine may not rewrite source facts.

### 3.3 Typed-tool-first

Preferred execution hierarchy:

1. verified typed Horizun capability;
2. controlled retry;
3. verified typed RevitCortex capability;
4. verified custom Revit API capability;
5. verified interchange strategy;
6. verified local external automation;
7. Autodesk APS/Revit Automation;
8. blocked task report.

### 3.4 Capability-driven routing

The system does not ask “which tool sounds better?”.  
It consults a tested Capability Registry.

### 3.5 Single writer for Revit

Only one active BIM executor may modify the owned Revit process/document at a time across providers, worktrees and sessions. Serialize reads too where required by Revit's API/UI thread.

### 3.6 Desired-state BIM

The BIM Compiler should compare desired state with current state and make the smallest safe diff.

### 3.7 Every write is verified

Mandatory pattern:

`WRITE → READ → VERIFY`

For important lab tests and milestones:

`WRITE → READ → VERIFY → SAVE → CLOSE → REOPEN → VERIFY`

---

# 4. System decomposition

The project is divided into eight major subsystems.

## 4.1 `environment-bootstrap`

Responsibility:

- inspect Windows environment;
- detect exact Revit version/build;
- detect install path and API assemblies;
- detect Codex CLI;
- detect Git, Python, PowerShell, .NET, Node when needed;
- inspect current MCP config;
- inspect Revit add-ins;
- create configuration snapshots;
- establish rollback instructions.

Primary outputs:

```text
state/environment-report.json
state/environment-report.md
state/snapshots/
state/bim-environment.lock.yaml
```

This subsystem must never design or edit Amanda's production RVT.

---

## 4.2 `revit-tool-lab`

Disposable proving ground for every Revit-facing capability.

Structure:

```text
revit/
├── lab/
│   ├── horizun/
│   ├── revitcortex/
│   ├── custom-api/
│   ├── fixtures/
│   ├── logs/
│   ├── screenshots/
│   └── exports/
└── production/
```

No unverified provider may be promoted directly into production use.

---

## 4.3 `capability-registry`

Authoritative record of what works on this machine.

Each capability records:

- logical capability name;
- provider;
- provider version/commit;
- Revit build;
- test date;
- tested parameters;
- reliability status;
- persistence result;
- model cleanliness;
- performance;
- known limitations;
- workarounds;
- tested fallbacks;
- evidence paths.

Possible states:

- `PASS`
- `PASS_WITH_WARNINGS`
- `DEGRADED`
- `UNTESTED`
- `FAIL`
- `RETIRED`

Illustrative record before testing (not production-eligible):

```yaml
create_wall:
  preferred: null
  providers:
    horizun:
      status: UNTESTED
      save_reopen: false
    revitcortex:
      status: UNTESTED
    custom_csharp:
      status: UNTESTED
```

---

## 4.4 `project-intelligence`

Converts project sources into structured, traceable project data.

Inputs may include:

- TFG PDF;
- program of needs;
- site drawings;
- survey/topography;
- DWG/DXF;
- legislation/normative references;
- images;
- climate studies;
- project references.

Outputs:

```text
project/
├── requirements/
│   ├── program.json
│   ├── adjacency.json
│   ├── flows.json
│   ├── privacy.json
│   ├── regulations.json
│   └── environmental.json
├── site/
├── references/
└── provenance/
```

Missing information must be explicit, never silently inferred as fact.

---

## 4.5 `design-engine`

Computational architecture subsystem.

Components:

```text
design-engine/
├── schemas/
├── constraints/
├── geometry/
├── adjacency/
├── circulation/
├── environmental/
├── optimizer/
├── scoring/
├── pareto/
└── tests/
```

Candidate technology stack:

- Python;
- Pydantic / JSON Schema;
- OR-Tools CP-SAT;
- Shapely;
- NetworkX;
- TopologicPy;
- Ladybug;
- Honeybee where justified;
- IfcOpenShell.

The final implementation may replace a candidate only after tool evaluation. Layout diagrams describe responsibilities; importable Python lives only under src/amanda_agent as specified in the plan. Top-level subsystem folders hold configuration/artifacts, avoiding duplicate implementations.

---

## 4.6 `bim-compiler`

Transforms an approved design state into Revit desired state.

Input:

```text
solutions/selected/solution.json
```

Output progression:

```text
R00 → R01 → ... → R16
```

It must not change architectural intent on its own.

Provider selection is delegated to the Capability Registry.

---

## 4.7 `qa-validation`

Three principal classes:

### Geometric/model QA

- overlaps;
- duplicates;
- invalid hosts;
- room enclosure;
- level mismatches;
- objects outside site;
- bad geometry;
- unexpected warnings.

### Programmatic QA

- required environments exist;
- quantities match;
- modeled areas are within tolerance;
- required accessible spaces exist;
- external-program areas exist.

### Architectural QA

- privacy gradient;
- controlled access;
- public/private separation;
- service flow;
- circulation;
- accessibility;
- environmental relationship;
- garden relationships;
- concept/parti consistency.

---

## 4.8 `deliverables`

Produces verified releases:

```text
deliverables/
├── RVT/
├── IFC/
├── DWG/
├── PDF/
├── schedules/
├── renders/
├── diagrams/
└── reports/
```

A release is not final merely because an RVT file exists.

---

# 5. Failure model and fallback policy

## 5.1 Failure classification

Minimum taxonomy:

| Code | Meaning |
|---|---|
| E01 | invalid argument/input |
| E02 | provider unavailable |
| E03 | timeout |
| E04 | Revit transaction aborted |
| E05 | partial mutation |
| E06 | declared success but divergent state |
| E07 | model inconsistency/corruption |
| E08 | suspected/confirmed Revit hang |
| E09 | Revit crash |
| E10 | missing capability |
| E11 | environment/dependency error |
| E12 | insufficient source data |

`E12` must never trigger fabricated source data.

---

## 5.2 Retry budget

Read-only/idempotent operations may use up to three controlled retries.

Mutating operations:

1. inspect post-failure state;
2. if no mutation occurred, retry may be allowed;
3. if partial mutation occurred, rollback first;
4. never blindly repeat create/update/delete.

---

## 5.3 Transaction wrapper

Logical operations are treated as transaction-like tasks.

Example:

```text
BEGIN CREATE_ROOM_WITH_DOOR
checkpoint
create walls
verify
create door
verify
create room
verify enclosure
QA
COMMIT
```

On failure:

```text
ROLLBACK
```

---

## 5.4 Circuit breaker

Three consecutive equivalent provider failures for one capability should open the breaker for that provider/capability during the session.

States:

- `CLOSED`
- `OPEN`
- `HALF_OPEN`

---

## 5.5 Rollback triggers

Mandatory rollback for:

- crash;
- model corruption;
- unexpected deletion;
- critical QA failure;
- partial transaction;
- success/result mismatch;
- unreopenable RVT;
- destructive unexpected delta;
- missing essential elements;
- uncontrolled warning explosion.

---

## 5.6 Tool swap policy

Automatic fallback requires an evidence-bound PASS or accepted PASS_WITH_WARNINGS capability matching current provider/build/schema, operation scope and persistence requirements. DEGRADED, stale, incomplete and UNTESTED entries are not production-eligible. A custom script hosted by Cortex still depends on Cortex transport; it is not an independent remedy for a dead bridge.

If all alternatives are `UNTESTED`, return to Tool Lab first.

---

## 5.7 Ultimate blocked-task behavior

If every approved path fails, generate:

```text
BLOCKED_TASK_REPORT.md
```

including:

- requested operation;
- providers attempted;
- failure classification;
- last known-good checkpoint;
- model integrity result;
- recommended next investigation.

---

# 6. Design Engine specification

## 6.1 Data model

Each environment should include, where known:

- logical ID;
- name;
- sector;
- quantity;
- target area;
- area tolerance;
- minimum dimensions;
- privacy level;
- noise generation/sensitivity;
- natural light preference;
- ventilation preference;
- accessibility;
- mandatory adjacency;
- desired adjacency;
- forbidden adjacency;
- exterior relation;
- preferred orientation;
- undesirable orientation;
- allowed flow types;
- provenance.

Schemas must reject invalid data.

---

## 6.2 Site model

Canonical site representation should include:

- boundary polygon;
- true north;
- project north;
- roads;
- potential access points;
- setbacks;
- buildable zone;
- existing objects;
- verified topography when available;
- infrastructure references;
- orientation data;
- geospatial transform where applicable.

Coordinate convention:

```text
X = East
Y = North
Z = elevation
Design units = meters
```

Revit-unit conversion must occur in one dedicated library.

---

## 6.3 Privacy model

Illustrative scale:

```text
0 = urban/public
1 = controlled access
2 = institutional
3 = technical service
4 = protected accommodation
5 = intimate/residential
```

The optimizer should strongly penalize direct public-to-residential transitions.

---

## 6.4 Adjacency graph

Relation classes:

- `MUST_ADJOIN`
- `SHOULD_ADJOIN`
- `SHOULD_BE_NEAR`
- `CAN_BE_NEAR`
- `NEUTRAL`
- `SHOULD_BE_SEPARATED`
- `MUST_BE_SEPARATED`

Relations may include weight and maximum/preferred distance.

---

## 6.5 Flow graphs

Independent networks:

- resident;
- child;
- staff;
- visitor;
- service;
- emergency.

Unauthorized access to private residential circulation may be a hard violation.

---

## 6.6 Hard vs soft constraints

Hard violations invalidate a solution.

Examples:

- required environment missing;
- geometry outside site;
- physical overlap;
- impossible route;
- missing accessible room;
- forbidden adjacency;
- access contradiction.

Soft violations create penalties.

Examples:

- nonideal orientation;
- longer staff route;
- less-preferred adjacency.

---

## 6.7 Progressive resolution

Design order:

```text
site
→ macrozones
→ blocks
→ sectors
→ rooms
→ walls/openings
→ BIM
```

The system must not start by randomly placing all rooms.

---

## 6.8 Design families

Initial candidate families may include:

- courtyard;
- linear spine;
- cluster;
- privacy gradient;
- double courtyard;
- comb.

For Amanda, gradient/courtyard/cluster combinations deserve explicit exploration but not forced dominance.

---

## 6.9 Candidate generation

Initial recommended scale:

- approximately 120–240 macro alternatives;
- hard-filter invalid candidates;
- rank roughly top 15;
- refine top 5;
- run more expensive environmental analysis on top 3–5;
- create conceptual BIM for top 3;
- let the agent select and record the best justified architecture before detailed BIM, with Amanda's review afterward.

Every run has:

```text
run_id
seed
requirements_version
site_version
engine_version
```

---

## 6.10 Scoring

Score must be multidimensional.

Possible dimensions:

- program compliance;
- privacy/security;
- adjacency;
- circulation;
- accessibility;
- solar;
- ventilation;
- green integration;
- compactness;
- constructability;
- concept fidelity.

No fabricated “beauty score”.

Weights must be versioned in files, not hidden in prompts.

---

## 6.11 Pareto frontier

Preserve non-dominated alternatives instead of collapsing every criterion into one opaque total.

---

## 6.12 Environmental analysis

Two-stage approach:

### Stage A

Fast heuristics for all candidates.

### Stage B

More expensive Ladybug/Honeybee/Radiance-style evaluation only for finalists when justified.

Full CFD is not baseline.

---

## 6.13 Gardens as first-class program elements

The system must not treat external areas as residual geometry.

Objects should include, at minimum when required by source program:

- protected courtyard;
- therapeutic garden;
- community garden;
- exercise area;
- playground.

---

## 6.14 Explainability

Each finalist must include:

```text
WHY_THIS_OPTION.md
```

covering:

- strengths;
- weaknesses;
- tradeoffs;
- hard violations;
- soft penalties;
- provenance;
- source-derived rationale.

---

## 6.15 Delegated research and architectural decisions

The user explicitly delegated research and architectural decisions on 2026-09-15: the agent researches, chooses and develops the proposal; Amanda may change it afterward. This delegation replaces the former mandatory human finalist-selection gate. Keep the selected PDF program for 20 people.

Detailed R05–R16 may proceed with `APPROVED_FOR_BIM`, `selection_authority = AGENT_DELEGATED`, decision timestamp, solution ID, rationale and `approval_hash` binding geometry/program/site/constraints/material intent. Here APPROVED_FOR_BIM means authorized for execution under delegated authority, not personally approved by Amanda or certified compliant. Store Amanda's review separately as `AMANDA_REVIEW_PENDING`; it does not block the agent's work. A later explicit acceptance can set AMANDA_ACCEPTED; requested changes create a new revision.

Research and decision workflow:

1. Search the supplied sources, then current official/primary sources for cadastral maps, urban rules, accessibility/fire requirements and institutional references. Record URLs or file hashes, version/date, article/page/map and applicability; follow material conflicts to their origin. Do not use this document as proof of a current legal rule.
2. Compare feasible alternatives using the fixed 20-person program, protection/privacy, flows, comfort, site evidence and constructability. Research precedents/material options and select the best justified proposal without asking routine preference questions.
3. Record each material choice in future `project/requirements/decision-register.yaml`: decision_id, topic, alternatives, selected option, rationale, source references, confidence, affected requirements/files, selection_authority, timestamp, supersedes, validation status and revision procedure.
4. If research cannot verify an input, choose a reversible `PROVISIONAL_ASSUMPTION` for a STUDY scenario and record its rationale/uncertainty. This is a treatment within DESIGN_HYPOTHESIS, not a fourth fact class. Keep actual survey/cadastral/normative verification pending and carry its affected-check list into BIM and reports. Hypothetical terrain levels may appear only in a clearly marked separate study scenario, never in VERIFIED_TOPOGRAPHY.
5. Continue unrelated tasks and detailed study development; missing preference, family layout, finish choice or uncertainty that can be represented provisionally must not stop the whole pipeline. Unknown mandatory compliance remains NOT_EVALUATED/BLOCKED_BY_INPUT and prevents an unsupported FINAL claim, not production of a labeled STUDY model.
6. Present the developed proposal with plans/previews and a concise decision summary. Amanda can revise it later; preserve previous sources, candidates, checkpoints and sealed releases. Her feedback takes precedence over delegated preferences. Regenerate the affected geometry/BIM/exports through a new version and re-run relevant checks. A substantive change invalidates the old hash; the agent may issue a new delegated decision after validation without waiting for another preference approval.

The agent selects typology, provisional site interpretation, implantation, massing, layouts, circulation, materials and design expression within the fixed brief. It does not fabricate official measurements, source statements, visits, legal compliance or Amanda's personal endorsement. Authentication, platform permissions and external actions outside existing authorization retain their own operational boundaries.

`CONCEPT_ONLY` permits validated finalists R00–R04 in separate candidate files before selection. It forbids detailed stages and release promotion. `SYNTHETIC_LAB` is restricted to fixtures and cannot authorize Amanda production.

Hybrid alternatives may be generated from selected parents but must re-enter the complete validation pipeline.

---

# 7. BIM pipeline specification

## 7.1 Formal RVT states

```text
R00 EMPTY_SANDBOX
R01 PROJECT_INITIALIZED
R02 SITE
R03 LEVELS_AND_REFERENCES
R04 MASSING
R05 ARCHITECTURAL_SHELL
R06 INTERNAL_LAYOUT
R07 OPENINGS
R08 ROOMS
R09 ACCESSIBILITY
R10 FURNITURE
R11 LANDSCAPE
R12 MATERIALS
R13 DOCUMENTATION
R14 QA
R15 RELEASE_CANDIDATE
R16 GOLDEN
```

Every stage is accounted for. A stage may record supported checks plus explicit blocked checks under a STUDY profile; blocked checks never become PASS. FINAL requires every mandatory stage/check complete.

---

## 7.2 Revit provider validation

Before Amanda production use, test:

### Horizun

- health;
- document query;
- level;
- wall;
- floor;
- room;
- door;
- window;
- view;
- section;
- sheet;
- schedule;
- dimension;
- site/toposolid where supported;
- save/reopen;
- PDF;
- IFC;
- DWG/image exports where supported.

### RevitCortex

At minimum:

- equivalent basic read/write operations;
- custom C# route;
- family-related workflows;
- IFC reconstruction workflows;
- audit/query behavior.

### Custom Revit API

Prove one simple query/write/persistence test and one geometric operation in sandbox.

---

## 7.3 Benchmarking

For critical capabilities, compare providers using identical inputs.

Evaluation order:

1. reliability;
2. model quality;
3. persistence;
4. observability/debuggability;
5. speed.

---

## 7.4 Load tests

Where relevant:

```text
1 → 10 → 100 → 500 elements
```

depending on capability.

---

## 7.5 Atomicity/fault injection

Tool Lab must deliberately test:

- invalid IDs;
- nonexistent types;
- impossible geometry;
- missing host;
- duplicate names;
- read-only file;
- provider disconnect;
- Revit closed;
- forced mid-batch error;
- crash-recovery drill.

---

## 7.6 Project preflight

Before each production BIM stage:

- execution mode valid: `CONCEPT_ONLY` for reviewed finalists through R04, `SYNTHETIC_LAB` for fixtures, or content-bound approval for detailed production;
- requirements versions match;
- site version matches;
- coordinates defined;
- units validated;
- solution geometry valid;
- no hard constraints violated;
- Capability Registry healthy;
- Revit health green;
- last checkpoint verified.

---

## 7.7 Template and naming

If Amanda supplies a template, test only a copy first.

Otherwise create a project baseline from a suitable installed architectural template.

Naming systems for views, sheets, rooms, families, materials, and stages must be explicit and deterministic.

---

## 7.8 Units and tolerances

All metric-to-Revit conversion must route through a dedicated unit layer.

Tolerance values must be configurable and tested.

---

## 7.9 Site

Preferred terrain workflow depends on actual source data.

Possible inputs:

- survey DWG;
- XYZ/CSV;
- DXF;
- GeoJSON;
- converted LandXML or equivalent.

If verified topography is unavailable:

```text
SITE_MODE = PLANAR_PLACEHOLDER
```

The system may proceed with 2D/schematic design but may not claim final grading or altimetric validity.

---

## 7.10 Massing

The selected design's blocks are converted to simplified Revit geometry first.

QA compares:

- centroid;
- area;
- dimensions;
- rotation;
- spacing;
- site containment.

A 3D preview is exported for visual sanity checking.

---

## 7.11 Architectural shell

Progression:

```text
approved block geometry
→ walls
→ floors
→ roofs
```

Controlled type catalogs prevent uncontrolled type proliferation.

---

## 7.12 Internal layout

Stable logical IDs identify every room/environment independently of Revit ElementId.

Example:

```text
TECH-PSY-01
RES-BED-DOUBLE-02
```

Revit IDs are runtime mappings only.

---

## 7.13 Openings and hosted elements

Doors/windows must be verified for:

- existence;
- host;
- correct wall;
- intended room relationship;
- clearance;
- collisions.

---

## 7.14 Rooms

All required rooms must be:

- placed;
- enclosed;
- named;
- numbered;
- mapped to a requirement.

Model/program reconciliation is mandatory.

---

## 7.15 Accessibility

Accessibility QA must be geometric, not visual guesswork.

The system should test, when normative data is verified:

- door clear widths;
- circulation widths;
- turning spaces;
- accessible bathrooms;
- accessible room;
- route continuity;
- level changes;
- ramps.

Normative values must come from verified applicable sources, not LLM memory.

---

## 7.16 Furniture

Furniture is added only after geometry and clearances stabilize.

It serves representation and spatial QA.

---

## 7.17 Landscape

External program spaces retain logical IDs and QA targets just like rooms.

Vegetation may initially use controlled placeholders.

---

## 7.18 Materials

Material assignment occurs after geometry is stable.

Material choices must be explicit, reviewable, and tied to project intent.

---

## 7.19 Documentation

Generate as appropriate:

- site plan;
- floor plan;
- roof plan;
- meaningful sections;
- elevations;
- 3D views;
- room schedule;
- door schedule;
- window schedule;
- area summaries;
- sheets;
- dimensions;
- tags.

Sections must be selected for architectural value, not arbitrary quantity.

---

## 7.20 Sheet QA

Export sheet previews and inspect for:

- viewport overflow;
- overlaps;
- bad crop;
- illegible dimensions;
- tag collisions;
- titleblock conflicts.

---

## 7.21 Full QA before release

Required categories:

- model;
- program;
- site;
- accessibility;
- architectural concept;
- documentation;
- warnings;
- persistence;
- exports.

---

## 7.22 Release persistence

Before RC:

```text
save
close
restart Revit
reopen
full QA
```

The RC path is initially provisional; R15 becomes verified only after cold reopen and QA. Hash the closed, finalized file. Compare semantic state on reopen; RVT bytes may change after a later save, which requires new hashes and evidence.

---

## 7.23 Export validation

### IFC

Inspect with IfcOpenShell or another verified parser for expected storeys/spaces/elements.

### PDF

Render/review pages.

### DWG

Verify valid file, reasonable extents, expected layers/data.

---

## 7.24 Golden release

A GOLDEN release includes at least:

```text
Amanda_TFG_GOLDEN_001.rvt
Amanda_TFG_GOLDEN_001.ifc
DWG/
PDF/
manifest.json
QA_REPORT.md
PROGRAM_COMPLIANCE.md
ACCESSIBILITY_REPORT.md
CAPABILITY_REPORT.md
EXPORT_REPORT.md
provenance.json
```

Record SHA-256 for key artifacts.

GOLDEN files are immutable. Assemble all exports, previews, reports and provenance in staging before publication; validate hashes and then publish a new directory without overwrite. Never add reports to an already sealed GOLDEN.

Release profiles: `STUDY` may contain declared missing survey/normative checks and must display those limitations. `FINAL` requires all mandatory checks and academic scope agreed for that release. A STUDY GOLDEN proves reproducibility of its stated scope, not final compliance or academic completion.

---

# 8. Autonomous Codex operation

## 8.1 `AGENTS.md`

The master rules must include:

1. preserve model integrity above task completion;
2. never edit GOLDEN;
3. never use UNTESTED capability on production;
4. every BIM write requires read+verify;
5. never invent missing source data;
6. distinguish source facts from hypotheses;
7. requirements are immutable during optimization;
8. do not update dependencies mid-production;
9. prefer typed verified tools;
10. use only registered fallbacks;
11. checkpoint before destructive work;
12. formalize task outcome;
13. never claim success without evidence.

---

## 8.2 Persistent project state

Primary file:

```text
PROJECT_STATE.yaml
```

Minimum contents:

- current phase;
- phase status;
- last completed task;
- next task;
- selected design;
- current Revit stage;
- active checkpoint;
- blockers;
- tool health;
- capability registry location;
- last verified git commit.

---

## 8.3 Session start protocol

Every fresh Codex session:

1. read `AGENTS.md`;
2. read `PROJECT_STATE.yaml`;
3. read current phase plan;
4. inspect git status;
5. verify environment lock;
6. verify Revit if BIM phase;
7. verify active provider health;
8. read blockers;
9. continue the next READY task.

Chat history is not authoritative project state.

---

## 8.4 Session end protocol

Before ending a long session:

1. finish or persist task as `SUSPENDED` with reason and resume conditions;
2. run tests;
3. persist logs;
4. update project state;
5. update blockers;
6. save checkpoint where needed;
7. update the incremental handoff; commit reviewed source/config/report changes and push to the configured remote when possible, excluding private sources/secrets/runtime files;
8. write next task.

---

## 8.5 Subagents

Useful roles:

- Research Agent;
- Environment Agent;
- Tool-Lab Agent;
- Requirements Agent;
- Design Agent;
- QA Agent;
- BIM Executor;
- Documentation Agent.

Only one BIM Executor may hold the Revit writer lease.

---

## 8.6 Parallel work

Parallelize only dependency-independent tasks.

All tasks declare dependencies.

No parallel writes to the same RVT.

---

## 8.7 Git policy

Recommended branches:

```text
main
experiment/horizun
experiment/cortex
experiment/design-engine
feature/*
```

`main` must remain known-good.

Commits should be small and semantic.

---

## 8.8 Binary RVT policy

Code/config/state live in Git.

RVT checkpoints may live outside standard Git tracking, with:

- paths;
- SHA-256;
- stage;
- manifest;
- provenance.

Git LFS may be evaluated later.

---

## 8.9 Tool discovery

If production becomes `BLOCKED_BY_TOOL`, Codex may research alternatives.

Search targets may include:

- GitHub;
- MCP registries;
- Autodesk official samples/docs;
- Revit add-ins;
- NuGet/PyPI packages;
- issue trackers and discussions.

No candidate is promoted before trust review and Tool Lab validation.

---

## 8.10 Tool trust review

Evaluate:

- maintainer transparency;
- recent maintenance;
- license;
- Revit 2027 compatibility;
- Codex/MCP compatibility;
- test coverage;
- issue quality;
- release provenance;
- binary signing/provenance;
- security posture;
- API scope.

Prefer source-first builds where reasonable.

---

## 8.11 Installation policy

Codex may autonomously use, when justified:

- Git;
- PowerShell;
- winget;
- dotnet;
- Python package tools;
- Node package tools.

All installations must log:

- source;
- version/commit;
- install target;
- config changes;
- rollback.

---

## 8.12 Human intervention boundaries

Human action follows existing session authorization. For future implementation, preserve these boundaries:

- UAC approval;
- Autodesk login/MFA/licensing;
- source data that cannot be researched or represented provisionally, only for the specifically dependent verified/final task; architectural preference and finalist selection are already delegated;
- external publication, paid cloud use or data upload outside existing authorization;
- platform permission limits and user-owned unsaved work;
- irreversible external actions.

Technical fallbacks do not require human permission if already approved by the architecture.

---

## 8.13 Secrets

Secrets must never enter:

- Git;
- logs;
- `AGENTS.md`;
- reports.

Use appropriate local secret storage and redact sensitive headers/tokens from logs.

---

## 8.14 Budgets

Tasks define:

- retry budget;
- fallback budget;
- soft time budget;
- hard time budget.

Repeated equivalent failure must trigger debugging or fallback, not endless retries.

---

## 8.15 Testing strategy

Test pyramid:

```text
few E2E Revit tests
more integration tests
many unit/schema/geometry/solver tests
```

Directories:

```text
tests/unit/
tests/geometry/
tests/solver/
tests/providers/
tests/revit/
tests/e2e/
tests/regression/
```

---

## 8.16 Regression rules

Any meaningful update to:

- Revit;
- MCP;
- Revit API layer;
- BIM Compiler;
- geometry engine;
- solver;

requires regression before promotion.

---

## 8.17 Environment updates

Do not update Revit/MCPs/dependencies during production merely because a newer version exists.

Updates occur in maintenance branches, followed by Tool Lab regression.

---

## 8.18 Recovery

### Reboot

Persist state and write `RESUME_AFTER_REBOOT.md`.

### Codex crash

New session reconstructs state from filesystem and Git.

### Revit crash

Recovery Manager:

1. detect crash;
2. find last PASS checkpoint;
3. validate;
4. restart Revit;
5. reconnect provider;
6. healthcheck;
7. resume or fallback.

---

## 8.19 Locking

Use:

```text
state/locks/revit-writer.lock
```

Only one writer may own the Revit session. The lock lives in a shared local runtime root for this project, outside worktree-specific copies. All providers and worktrees use the same resource identity, owner token, PID/start time, heartbeat and fencing generation. A timeout alone cannot transfer ownership while Revit may still be writing.

---

## 8.20 Safety sentinel

Before destructive writes, verify the target path.

Resolve the canonical path and file identity, enforce a configured writable-root allowlist, reject junction/symlink/hardlink escapes, and check the protected-source/baseline/checkpoint/release manifest. Filename tokens are a secondary guard only. Revalidate the active document identity immediately before mutation.

This should be enforced in code, not only in prompt instructions.

---

## 8.21 Operational CLI

The finished system should expose one central entry point, preferably Python-based.

Conceptual commands:

```text
amanda-agent bootstrap
amanda-agent doctor
amanda-agent tool-lab
amanda-agent ingest
amanda-agent design
amanda-agent compare
amanda-agent bim plan
amanda-agent bim verify-plan
amanda-agent bim claim
amanda-agent bim record-result
amanda-agent qa
amanda-agent export
amanda-agent status
amanda-agent resume
amanda-agent rollback
```

Implementation syntax may change, but the one-entry-point principle should remain.

---

# 9. Recommended repository layout

```text
amanda-tfg-bim-agent/
│
├── AGENTS.md
├── README.md
├── PROJECT_STATE.yaml
├── pyproject.toml
│
├── docs/
│   ├── source/
│   ├── architecture/
│   ├── superpowers/
│   └── reports/
│
├── state/
│   ├── environment-report.json
│   ├── capabilities.yaml
│   ├── tool-health.yaml
│   ├── blockers.yaml
│   ├── bim-environment.lock.yaml
│   ├── locks/
│   └── snapshots/
│
├── bootstrap/
│
├── tool-lab/
│   ├── horizun/
│   ├── revitcortex/
│   ├── custom-api/
│   ├── ifc/
│   └── fixtures/
│
├── project/
│   ├── requirements/
│   ├── site/
│   ├── regulations/
│   ├── references/
│   └── provenance/
│
├── design-engine/
│   ├── schemas/
│   ├── constraints/
│   ├── geometry/
│   ├── environmental/
│   ├── optimizer/
│   ├── scoring/
│   └── pareto/
│
├── solutions/
│   ├── candidates/
│   ├── finalists/
│   └── selected/
│
├── bim/
│   ├── compiler/
│   ├── providers/
│   ├── families/
│   ├── templates/
│   ├── checkpoints/
│   └── releases/
│
├── qa/
│   ├── geometric/
│   ├── programmatic/
│   ├── architectural/
│   ├── accessibility/
│   └── environmental/
│
├── recovery/
├── logs/
├── tests/
└── deliverables/
```

---

# 10. Definition of Done

The overall project is complete only when:

- environment is detected and locked;
- every required operation has an eligible primary and tested recovery/fallback route; fallback dependencies and failure domains are explicit;
- source requirements are structured with provenance;
- missing-data registry exists;
- design engine passes synthetic and project tests;
- alternatives are generated and ranked;
- finalists are explainable;
- one design is approved for BIM;
- selected design is compiled to Revit;
- BIM stages pass QA;
- program checks pass and every mandatory accessibility/site check for the declared STUDY or FINAL profile is accounted for; blocked mandatory FINAL checks prevent FINAL;
- model survives save/close/restart/reopen;
- exports are validated;
- reports and provenance are generated;
- a GOLDEN release and manifest exist;
- the system can resume from persistent state in a fresh Codex session;
- `doctor`, `status`, `resume`, and `rollback` are operational.

---

# 11. Definition of autonomy

“Codex does everything” means the system should automate:

- research;
- installation;
- configuration;
- testing;
- fallback;
- source ingestion;
- requirement structuring;
- generative design;
- comparative evaluation;
- BIM generation;
- QA;
- documentation;
- export;
- recovery;
- reporting.

It does **not** mean:

- inventing missing facts;
- hiding architectural decisions or claiming Amanda approved them personally; delegated decisions are recorded and revisable;
- bypassing licensing/authentication;
- faking normative verification;
- sacrificing model integrity to mark a task complete.

---

# 12. Proposed architecture after document review

```text
                             CODEX
                               │
                      ┌────────┴────────┐
                      │  ORCHESTRATOR   │
                      └────────┬────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
    PERSISTENT STATE       TOOL LAB           PROJECT DATA
          │                    │                    │
          │                    ▼                    ▼
          │            CAPABILITY REGISTRY     REQUIREMENTS
          │                                         │
          │                                         ▼
          │                                   DESIGN ENGINE
          │                                         │
          │                                  GENERATE + RANK
          │                                         │
          │                                       TOP 3
          │                                         │
          │                                  AGENT SELECTION
          │                                         │
          └─────────────────────┬───────────────────┘
                                ▼
                           BIM COMPILER
                                │
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                 HORIZUN     CORTEX      CUSTOM API
                    │           │           │
                    └───────────┼───────────┘
                                ▼
                              REVIT
                                │
                                ▼
                               QA
                            ↙       ↘
                      ROLLBACK       PASS
                                      │
                                     RC
                                      │
                               SAVE/REOPEN
                                      │
                                   GOLDEN
                                      │
                       ┌──────────────┼──────────────┐
                       ▼              ▼              ▼
                      RVT            IFC            PDF
```

Cross-cutting concerns:

```text
Git
State
Logs
Checkpoints
Tests
Recovery
Security
Provenance
Capability Registry
```

---

## Spec review checklist

The 2026-09-15 document review checked the following; runtime acceptance is NOT_RUN (see PLAN_SELF_REVIEW.md):

- unresolved design placeholders;
- contradiction between local-first and APS fallback;
- contradiction between autonomy and human gates;
- separation of source facts from design hypotheses;
- separation of design engine from BIM compiler;
- explicit provider fallback policy;
- Revit single-writer policy;
- model rollback and persistence verification;
- update/regression policy;
- missing source-data handling;
- production/lab isolation;
- completion criteria.

No implementation commands are prescribed here beyond conceptual interfaces; concrete commands, task order, test scripts, provider installation steps, acceptance tests, and fallbacks belong in the implementation plan that follows this spec.
