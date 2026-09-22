# Handoff — R05 live persistence and pre-R06 checkpoint

## Resumo

Reconciliado o delivery state contra o Revit live. O Horizun está saudável no
Revit 2027 build `27.2.0.39`, PID `25996`, e o alvo ativo é o RVT timestampado
de R05. O modelo foi salvo, fechado com ativação segura do anchor, reaberto e
lido novamente. O readback repetiu 3674 elementos, 104 walls, 3 floors, 1 roof,
1 mass, 3 levels, 2 grids e 23 views, com cobertura completa e zero ilegíveis.

Foi criado checkpoint pós-persistência para proteger o próximo write. A
comparação linear/compacta versus pavilhões/cluster foi registrada, assim como
a pesquisa oficial e as hipóteses reversíveis de site.

## Arquivos criados

- `docs/reports/delivery-mode/reconciliation.json`
- `docs/reports/delivery-mode/R05-live-persistence-2026-09-22.json`
- `docs/reports/delivery-mode/R05-design-comparison-2026-09-22.md`
- `docs/reports/delivery-mode/research-decision-2026-09-22.md`
- `revit/production/previews/R05-live-Nivel-1-20260922.png`
- `revit/production/evidence/` foi preparado para evidências posteriores
- `revit/production/checkpoints/AMANDA_WORKING_001.20260921-213302/R05-live-persisted-20260922.rvt` e seu manifest

## Decisões

- Não substituir `revit/production/working/AMANDA_WORKING_001.rvt`; ele não tem
  evidência live R05 vinculada.
- Continuar no alvo timestampado reaberto e comprovado.
- Seleção permanece `AMANDA-RUN-001-S01`, `AGENT_DELEGATED`,
  `AMANDA_REVIEW_PENDING`, `APPROVED_FOR_BIM`, approval hash
  `bf7dcca735de166f100a6687f441ac7247ccf31f5e9e28a1bd4837591acba7ef`.
- O modelo linear foi mantido porque a alternativa de duas alas/pavilhões mede
  cerca de 1050 m² fechados, acima do limite oficial 783–814 m². A comparação
  não copia dimensões das imagens de referência.

## Testes e evidência

- Horizun health live: PASS, build 27.2.0.39, PID 25996, zero outros clients.
- Save: `saved_verified`; SHA antes `634e8d2c…`, depois `10df1cb1…`.
- Close/reopen/readback: PASS; o close exigiu ativar o anchor porque o Revit não
  fecha o documento ativo diretamente.
- Checkpoint manager: PASS; checkpoint e manifest publicados com SHA
  `10df1cb1be4a147218a822330a9efac5e540513fdee3d95d1173bbab7447228f`.
- Preview real de `Nível 1`: PASS visual, `STUDY`, não calibrado; hash
  `bb2d9b7b…`.
- A tentativa posterior de hash direto do RVT aberto foi bloqueada pelo lock do
  Revit; isso não invalida o checkpoint, que verificou os bytes após a cópia.

## Pendência e retomada exata

1. Rodar testes focados da seleção/compilador e do driver antes do write R06.
2. Confirmar health e active document novamente; não abrir outro writer.
3. Criar/usar o plano R06 para paredes internas no alvo timestampado, com
   `WRITE → READ → VERIFY`; parar se qualquer operação não for verificada.
4. Salvar, consultar contagens/áreas, capturar novo preview e criar checkpoint
   R06 antes de R07.
5. Atualizar `PROJECT_STATE.yaml`, dashboard e este handoff com o resultado.

## Git

HEAD observado: `e6f0e4e` em `main`/`origin/main`. O worktree continua com
alterações preexistentes e deletions ACL-visible em `revit/lab/exports/...`;
elas não foram restauradas, apagadas ou staged. Os arquivos deste bloco devem
ser commitados seletivamente depois da verificação focada.
