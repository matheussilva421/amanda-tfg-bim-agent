# P2-T01 — Nova identidade canônica

**Resultado:** identidade de solução atribuída e vinculada às fontes; nenhum layout ou artefato BIM foi criado.

## Identidade e vínculos

- ID: `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`
- Fingerprint determinístico das fontes: `4b1275558a6c2c40828dbba1422c0063703c182fd9d7b800b36a448499a073c4`
- Registro: [`canonical-solution-identity.yaml`](../../project/requirements/canonical-solution-identity.yaml)
- Pranchas: exatamente `01_implantacao.png`, `02_administrativo.png`, `03_residencial.png` e `04_servicos.png`, cada uma com o SHA-256 registrado no manifesto.
- Programa oficial: `docs/source/programa_necessidades.pdf`, SHA-256 `11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17`.
- Reconciliação vinculada: `P1-T01`, relatório `docs/reports/P1-T01-four-board-reconciliation.md`, SHA-256 `8d297d9c35e0fcdec8b36e5857e03c9e992cbfeb9dab082dddf2106a2ed5025b`.

A identidade deriva deterministicamente dos caminhos e hashes das quatro pranchas, do PDF oficial e do relatório P1-T01. A repetição da geração produz o mesmo ID e fingerprint; o escritor recalcula os vínculos das fontes atuais, aceita a persistência idempotente do mesmo registro e recusa fontes incorretas, registros inválidos ou divergentes.

## Limites P2

`selected_design` e `SELECTION_SOLUTION_ID` permanecem nulos. `approval_hash` também permanece nulo; o fingerprint de identidade não é hash de aprovação. Não há layout, `DesignSolution`, BIM-00 ou autorização de Revit. S02 continua `STALE_BY_CANONICAL_REFERENCE_EXPANSION`; os dois S01 históricos e outros IDs lineares não são elegíveis.

Nenhum acesso a Revit/RVT, escrita no modelo, R04 ou R05 ocorreu. O programa oficial e suas áreas permaneceram inalterados.

## Verificação

- `.venv/Scripts/python.exe -m pytest tests/unit/test_canonical_solution_identity.py tests/unit/test_production_selection.py tests/unit/test_canonical_state_migration.py tests/project/test_repository_hygiene.py tests/policy/test_plan_order.py -q` — **41 passed**.
- `.venv/Scripts/ruff.exe check src/amanda_agent/production/canonical_identity.py tests/unit/test_canonical_solution_identity.py tests/unit/test_canonical_state_migration.py tests/project/test_repository_hygiene.py` — **All checks passed**.
- `git diff --check` nos arquivos P2 versionados — passou.
- Revisão independente final, somente leitura — **APPROVE** após correção da validação de hashes vivos e da referência histórica no handoff.

## Divergências ainda abertas

P2 não altera a reconciliação do P1. Permanecem registradas no relatório P1-T01: a prancha residencial desenha seis células de banheiro comum para cinco unidades oficiais, sem identificar a célula excedente; a prancha de serviços inclui usos sem sala/área equivalentes no programa (informática, costura/artesanato e empreendedorismo) e várias áreas/quantidades gráficas divergentes; rótulos combinados de depósitos e apoios não correspondem univocamente às linhas oficiais. As áreas e quantidades do PDF continuam autoritativas.

## Próxima tarefa

`P3-T01` é a próxima tarefa autorizada e permanece pendente: executar a QA canônica não-Revit e, somente se os hard checks passarem, gerar o layout e os hashes de aprovação P3. Ela não foi iniciada no fechamento de P2-T01.
