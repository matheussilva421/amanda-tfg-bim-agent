# Delivery research and decision note — 2026-09-22

## Sources consulted

- Ministério do Desenvolvimento e Assistência Social: [Serviço de
  Acolhimento para Mulheres em Situação de Violência](https://www.gov.br/mds/pt-br/acoes-e-programas/suas/unidades-de-atendimento/servico-de-acolhimento-para-mulheres-em-situacao-de-violencia).
  The official service description frames the unit as provisional protection,
  with a domestic character, discreet location and accessibility.
- Prefeitura do Natal: [Plano Diretor de Natal — legislation
  page](https://planodiretor.natal.rn.gov.br/paginas/menu/aba5/pagina3).
  The municipal page identifies LC 208/2022 and the LC 055/2004 Code of Works;
  the consolidated text and applicable annexes remain a licensing check, not a
  permission to invent setbacks or site parameters here.
- Local evidence: `project/site/site.json`, `project/site/missing-data.yaml`,
  `project/regulations/registry.yaml`, the official programme PDF and
  `docs/source/references/VISUAL_REFERENCES_2026-09-22.md` inside the delivery
  package.

## Applied architectural principles

The research supports keeping a domestic, protected and accessible reading for
the shelter typology, with a controlled arrival/triage interface and a clear
privacy gradient. The visual references support covered paths, gardens and
small-scale transitions, but they are not factual site data. The live R05 model
therefore keeps a protected patio and gallery while avoiding claims about real
frontage, north, terrain or cadastral geometry.

## Reversible assumptions

- `PROVISIONAL_ASSUMPTION`: the placeholder planar coordinate system is used only
  to continue architectural development; impact is unknown site fit and true
  grading, and resolution requires a surveyed/cadastral source.
- `PROVISIONAL_ASSUMPTION`: the gallery/patio arrangement is a study-level
  privacy and accessibility strategy; impact is unverified fire, accessibility,
  environmental and operational compliance.

The unresolved blockers remain `SITE_TOPOGRAPHY`, `SITE_BOUNDARY`,
`SITE_OCCUPANCY`, `SITE_FRONTAGE_COUNT` and `SITE_TRUE_NORTH`. They do not stop
R06 internal-layout work, but they prevent a final implantation or regulatory
claim.
