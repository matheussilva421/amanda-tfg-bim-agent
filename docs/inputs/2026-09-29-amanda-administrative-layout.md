# Amanda — administrative layout direction (2026-09-29)

Status: ACTIVE INPUT FOR R06 PREPARATION  
Authority: USER_DIRECTED for administrative arrangement and nominal dimensional targets  
Implementation gate: P7-T02 / R06 only after P7-T01 / R05 PASS  
Tracking issue: https://github.com/matheussilva421/amanda-tfg-bim-agent/issues/1

## Provenance

Amanda supplied two visual references and two dimensional tables in chat on 2026-09-29.

- Colored two-floor administrative plan attachment SHA-256: `7289ab919ef240d3fd80b22eb171600c2c87cb1cd37f900366e46681ec116bf2`.
- Dark CAD-like ground-floor sketch attachment SHA-256: `e660352e987d452fee8dda86948ada8e944bc6f485ddbe5cc05912f018709b3f`.

The raw chat attachments are not repository-addressable in this commit. The tables below are the repository transcription of Amanda's explicit dimensional direction. The visual references remain provenance/context; quantitative authority is defined below.

## Authority rule

1. `docs/source/programa_necessidades.pdf` remains authoritative for official room quantities and official areas.
2. The four canonical boards remain authoritative for architectural organization and spatial relationships.
3. Amanda's 2026-09-29 direction is USER_DIRECTED for the administrative arrangement and the nominal dimensional targets below.
4. The colored two-floor reference is consistent with the current Board-02 organization and is the visual direction for the admin layout.
5. The dark CAD sketch is reference-only for rough arrangement where it does not conflict. It is **not** quantitative authority because several labels/areas conflict with the official program and Amanda's table.

Nominal dimensions are clear-space/layout targets for R06. They are not guaranteed exterior wall-to-wall dimensions; wall thicknesses, structure, circulation, stair/elevator cores, and later Revit Room readback must be reconciled around them.

## Administrative envelope

Keep the P6 normalized-study administrative envelope at approximately **20.00 × 10.00 m per floor** unless a separately approved deviation is required.

### Ground floor — public intake and technical care

| Logical requirement | Ambiente | Official area | Amanda nominal target |
|---|---|---:|---:|
| REQ-04-01 | Psicologia | 10 m² | 2.50 × 4.00 m |
| REQ-04-02 | Serviço Social | 10 m² | 2.50 × 4.00 m |
| REQ-04-03 | Atendimento Jurídico | 10 m² | 2.50 × 4.00 m |
| REQ-04-04 | Sala de reunião | 15 m² | 3.75 × 4.00 m |
| REQ-05-03 | Copa de apoio comunitário | 8 m² | 2.00 × 4.00 m |
| REQ-04-06 | Arquivo e apoio técnico | 5 m² | 1.25 × 4.00 m |
| REQ-01-03 | Triagem/Acolhimento | 12 m² | 3.00 × 4.00 m |
| REQ-01-02 | Espera protegida | 15 m² | 5.00 × 3.00 m |
| REQ-01-04 | Registro/Entrevista inicial | 10 m² | 2.50 × 4.00 m |
| REQ-05-04 | Sanitário acessível | 5 m² | approx. 2.00 × 2.50 m |
| REQ-01-05 | Controle de acesso | 6 m² | 2.00 × 3.00 m |
| REQ-01-01 | Recepção | 10 m² | approx. 3.30 × 3.00 m |

Also preserve the protected entrance, circulation/corridor, stair and elevator/core required by the architectural reference. Those circulation/core areas are not new official program rooms.

### Upper floor — staff, coordination and group functions

| Requirement / classification | Ambiente | Area | Amanda nominal target |
|---|---|---:|---:|
| REQ-06-01 | Coordenação | 10 m² | 2.50 × 4.00 m |
| REQ-06-02 | Secretaria/Administrativo | 12 m² | 3.00 × 4.00 m |
| REQ-06-03 | Sala de equipe | 15 m² | 3.75 × 4.00 m |
| REQ-06-04 | Refeitório/Copa funcionários | 15 m² | 3.75 × 4.00 m |
| REQ-04-05 | Sala Multiuso/Grupos | 30 m² | 7.50 × 4.00 m |
| DERIVED-AMANDA-ADMIN-UPPER-SUPPORT | Apoio/Arquivo | 5 m² | approx. 2.00 × 2.50 m |
| REQ-06-05 | Sanitário/Vestiário funcionários | 10 m² | 2.50 × 4.00 m |
| SEMI_OPEN-AMANDA-ADMIN-VERANDA | Varanda protegida | 10 m² | e.g. 10.00 × 1.00 m |

Upper-floor caveats:

- `Apoio/Arquivo 5 m²` is a derived architectural support space requested/shown in the Amanda/board direction. It **does not create a second official REQ-04-06**; the one official REQ-04-06 remains mapped once on the ground floor.
- The 10 m² protected veranda is semi-open architectural area and **must not be added to the 626 m² official internal useful area**.
- Preserve stair/elevator/core and protected circulation without inventing new official program rooms.

## Dark CAD sketch conflicts

Do not use the dark sketch as area authority. It shows, among other differences:

| Item | Dark sketch | Current official/Amanda target |
|---|---:|---:|
| Sala de reunião | 19 m² | 15 m² |
| Copa | 10 m² | 8 m² |
| Arquivo | 6 m² | 5 m² |
| Espera protegida | 20 m² | 15 m² |
| DML | 6 m² on admin ground | not assigned to admin ground by the current reconciliation |
| Sanitário acessível | area not stated | 5 m² |

The sketch may inform rough adjacency only where it does not conflict with the current specification.

## Stage ownership

- R05 / P7-T01: architectural shell only. This input must not expand R05 into internal layout.
- R06 / P7-T02: internal partitions/layout using this direction plus the canonical boards/P1 reconciliation.
- R07 / P7-T03: hosted doors/windows/openings.
- R08 / P7-T04: formal Revit Rooms and official area schedule/readback.

No R06 write is authorized merely by recording this input.
