# Amanda TFG BIM Agent — Current Specification

## Goal

Produce the Amanda TFG BIM project from the four canonical boards while preserving the official quantitative program.

## Authority

1. Current user direction.
2. The four canonical boards for geometry, organization, and spatial relationships.
3. `docs/source/programa_necessidades.pdf` for official program, capacity, and quantitative areas.
4. Verified site and regulatory evidence.
5. This current specification.

If evidence is missing, record the gap and stop the affected decision. Do not infer a site fact or change an immutable requirement to make a model pass.

## Official program

- Capacity: 20 people.
- Internal useful area: 626 m².
- Programmed external area: 260 m².
- Enclosed estimate: 783–814 m².
- Covered estimate: 850–950 m².
- The PDF remains the authority for each official room quantity and area. Board labels and areas are architectural inputs that require explicit reconciliation against it.

## Canonical sources

Exactly four current architectural boards define the source set. Their preserved source bytes and hashes are recorded in the recovery report; normalized active image paths are installed and hash-verified in Task 7.

| Board | Current meaning | Source SHA-256 |
|---|---|---|
| 01 | General implantation | `30D009357A095E7794E0E915DCD2FDB04CD6B9AAB9F4D13F5663ED54D6F20240` |
| 02 | Administrative / reception | `123B95633AE1BE643DA84F2226C6337D65A74F7D1337D6B27D94BDEAD1C3A263` |
| 03 | Residential pavilions | `5B96C2D5CC770742EE32D51B83B25993FE8B8A1638BF94DA56BA8EF771031381` |
| 04 | Services / capacitation | `C56B806F805D9C4AA1E6015BA6B56AC960204066721F93EF08CBADFB312C0386` |

The official program candidate has SHA-256 `11DAA9EFC4D1B022407D8BD02999E85B604A16539F29AE598DC45B339DE14A17`; the TFG source candidate has SHA-256 `16ABE602AC50643482CE3C782780B4135FA8468B5CA814061FE426C8CA292A7E`. Task 7 verifies these before installing the normalized source paths.

## Canonical architecture

- Board 01: implantation and zoning.
- Board 02: administration with a two-storey functional split.
- Board 03: four residential pavilion groupings.
- Board 04: curved, patio-centered services and capacitation block.

### Board 01 — General implantation

| Board requirement | Required interpretation | Official-program relation | Gate |
|---|---|---|---|
| Residential pavilions in protected northern zone | Keep the residential cluster north/deeper in the site | Compatible | Hard |
| Administration/reception at south/public edge | Public-facing block southwest/south | Compatible | Hard |
| Services/capacitation southeast | Independent block and service approach | Compatible | Hard |
| Child sector west/central-west | Child use and playground/green sector stay in this zone | PDF requires child sector 52 m² and playground 40 m² | Hard topology; implementation to reconcile |
| Therapeutic garden/convivência central | Central landscape void organizes the site | PDF lists therapeutic garden 80 m² and protected patio 80 m² | Hard |
| Community garden east/central-east | Horta in the east zone | PDF lists 30 m² | Hard |
| Public access from south | Main pedestrian/public approach at south edge | Functional | Hard |
| Service/load access southeast | Independent service approach | Functional | Hard |
| Parking along public/south band | Study arrangement | Not quantified by the PDF | Soft/study |
| Organic paths and covered links | Landscape circulation; not an enclosed linear corridor | Architectural intent | Hard |

Implantation invariants: no final linear-bar solution; residential use does not migrate to the public frontage; administration does not move behind the residential zone; service access stays independent of the protected primary arrival unless an explicit deviation is approved; and the central therapeutic landscape cannot become residual space.

### Board 02 — Administration / reception

The ground floor is the public intake and care sequence. The upper floor contains coordination, team, staff, and group functions. Board areas below are board inputs; official areas remain controlled by the program PDF.

| Ground-floor board space | Board area | Functional placement / PDF relation |
|---|---:|---|
| Recepção | 10 m² | Ground; direct match |
| Controle de Acesso | 6 m² | Ground; direct match |
| Triagem/Acolhimento | 12 m² | Ground; direct match |
| Espera Protegida | 15 m² | Ground; direct match |
| Registro/Entrevista Inicial | 10 m² | Ground; direct match |
| Psicologia | 10 m² | Ground; direct match |
| Serviço Social | 10 m² | Ground; direct match |
| Atendimento Jurídico | 10 m² | Ground; direct match |
| Sala de Reunião | 15 m² | Ground; direct match |
| Arquivo | 5 m² | Ground; direct/technical support |
| Copa | 8 m² | Ground; functional support, reconcile quantity |
| Sanitário Acessível | 5 m² | Ground; accessibility/support |

| Upper-floor board space | Board area | Functional placement / PDF relation |
|---|---:|---|
| Coordenação | 10 m² | Upper; direct match |
| Secretaria/Administrativo | 12 m² | Upper; direct match |
| Sala de Equipe | 15 m² | Upper; direct match |
| Refeitório/Copa Funcionários | 15 m² | Upper; direct match |
| Sala Multiuso/Grupos | 30 m² | Upper; direct match |
| Apoio/Arquivo | 5 m² | Upper; support |
| Sanitário/Vestiário Funcionários | 10 m² | Upper; direct match |
| Varanda protegida | Not specified | Upper; semi-open element |

Fail the layout if psychology, social work, legal service, or meeting is placed upstairs; if coordination, administration, or team space is inserted into the public ground-floor intake sequence without approved deviation; or if the main public arrival logic is lost.

### Board 03 — Residential / dormitory pavilions

| Pavilion | Board membership | Required organization |
|---|---|---|
| A — upper-left sleeping pavilion | 2 double rooms at 12 m² each; 2 individual rooms at 10 m² each; 3 common WC cells shown | Independent sleeping pavilion |
| B — lower-left family pavilion | 2 triple rooms at 15 m² each; 1 family room at 18 m²; common WC support | Independent family pavilion |
| C — lower-right accessible/mixed pavilion | 1 accessible room at 16 m²; 1 double room at 12 m²; common WCs; 1 accessible WC at 4.5 m² | Independent accessible/mixed pavilion |
| D — upper-right communal pavilion | Living room 30 m²; support pantry 12 m²; residential dining 25 m² | Communal use, not sleeping rooms |

Keep four independent volumes legible. Preserve the unbuilt central garden/patio. Covered and landscape connections remain external or semi-open, not a closed double-loaded corridor. Reconcile room types and quantities exactly with the official PDF before generating a new solution.

### Board 04 — Services and capacitation

The final organization is a curved/patio-centered composition, not a rectangular room pack: two curved wings embrace a central garden/patio; covered circulation links the composition; public/campus and service/load approaches remain separate; capacitation occupies primary wings; support functions occupy a secondary wing; and landscape is part of the block.

| Board label | Board area | Official-program relation and required reconciliation |
|---|---:|---|
| Recepção/Orientação | 25 m² | Derived arrival/support function; map to the PDF without inventing an official standalone room |
| Informática | 30 m² | Not explicit in the PDF; represent as a capacitation mode/subdivision if approved |
| Sala Multiuso | 50 m² | PDF has a multiuse/community room at a different area; PDF controls official area |
| Costura/Artesanato | 40 m² | Not explicit in the PDF; derived capacitation use |
| Prática/Empreendedorismo | 40 m² | Not explicit in the PDF; derived capacitation use |
| Sanitários | 18 + 18 m² | Reconcile to official sanitary quantities and areas |
| Apoio/Depósito | 12 m² | Partial match; reconcile support allocation |
| DML | 6 m² | PDF DML is smaller; official area wins unless baseline changes |
| Rouparia/Almox | 15 m² | Reconcile to combined official support areas |
| Lavanderia | 20 m² | PDF laundry is smaller; official area wins unless baseline changes |
| Copa | 15 m² | PDF support pantry is smaller; official area wins unless baseline changes |

Hard rules: no final rectangular `box(*bounds)` footprint; retain a real central patio and curved/formal organization; separate service access; represent board functional identities as modes/subzones when needed while the PDF controls official quantities and areas.

### Child-sector reconciliation

The west/green board zone must remain the child sector and playground/green zone. The official PDF also requires brinquedoteca 24 m², apoio pedagógico 18 m², banheiro 6 m², and depósito 4 m². P1 must select and record one content-bound implementation: (1) a small child pavilion integrated into the west/green sector, or (2) indoor rooms in an adjacent canonical block while preserving the external child sector. Do not add an arbitrary seventh generic box without architectural rationale.

## Conflict rule

Boards govern form and organization; the official PDF governs official quantitative program. Every material mismatch is an explicit reconciliation, never a silent substitution. User-approved requirements remain immutable during optimization.

## Current stale state

`AMANDA-RUN-002-PAVILION-S02` is `STALE_BY_CANONICAL_REFERENCE_EXPANSION`. It was bound to three canonical source hashes; the current architecture is four-board. S02 is not authorized to advance to R05. The historical linear R12 is superseded and cannot be reused as the final solution. No new solution identity is selected during repository recovery.

## Site limitations

Survey boundary, topography, occupancy, frontage count, and true north remain limited or unverified. The exact blockers and their severity are in `PROJECT_STATE.yaml`. Resolve them with verified evidence before a decision that depends on them.

## Revit contract

One production writer. Every BIM mutation follows WRITE → independent READ → VERIFY. The next production sequence is: reconcile four boards → create a new solution identity bound to all four current board hashes and the official program → generate canonical QA and approval hash → BIM-00 for that exact solution/target → R04 save/close/reopen/query → real four-board visual/geometric acceptance → only then R05 and later stages. Repository recovery performs no Revit or model work.

## Definition of Done

Recovery is done when the single current-document flow is installed, preserved sources/evidence/RVTs are accounted for, obsolete active instructions and packages are removed only after migration, focused validation passes, and Git/worktree/remote state is verified. Architectural production is done only when a new four-board-bound solution reaches verified Revit production and later GOLDEN after every required gate, without reintroducing the linear solution or stale S02 authority.
