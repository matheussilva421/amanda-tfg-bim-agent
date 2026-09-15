# Relatorio de validacao da ingestao

- Comando: `amanda-agent ingest --validate-only`
- Data: 2026-09-15
- Contagens: 9 verificacoes; 9 PASS; 0 FAIL; 5 limitacoes
- Veredito: **GO_WITH_LIMITATIONS**

## Verificacoes

- PASS — Manifesto e hashes das fontes: validado
- PASS — Schema de program.json: validado
- PASS — Schemas canonicos de requisitos: validado
- PASS — Schema de site.json: validado
- PASS — Registro de regulamentacao: validado
- PASS — Proveniencia: validado
- PASS — Totais do programa: validado
- PASS — Status do site: topografia MISSING aceita como limitacao de estudo; boundary STUDY_PLACEHOLDER permanece provisoria; true north pendente; conflito de frentes pendente; parte do registro normativo permanece identificada
- PASS — Bloqueadores abertos: validado

## Bloqueadores abertos

- SITE_TOPOGRAPHY
- SITE_BOUNDARY
- SITE_OCCUPANCY
- SITE_FRONTAGE_COUNT
- SITE_TRUE_NORTH
