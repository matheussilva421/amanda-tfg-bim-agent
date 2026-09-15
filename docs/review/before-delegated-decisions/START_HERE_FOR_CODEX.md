# Comece aqui — projeto Amanda TFG BIM

**Revisão:** 2026-09-15. **Estado atual:** REVIEW_ONLY; implementação, instalações e validação real no Revit = NOT_RUN.

Este pacote contém a especificação e o plano de uma futura automação BIM. A revisão documental não aprova uma alternativa arquitetônica nem autoriza executar automaticamente as instalações descritas.

## Ordem de leitura

1. Instruções do usuário e `AGENTS.md`, se existir. Preserve instruções já estabelecidas.
2. [Handoff da revisão](docs/notes/2026-09-15-revisao-planos-handoff.md).
3. [Especificação e contexto das fontes](2026-09-11-amanda-tfg-bim-agent-design.md#project-baseline).
4. [Plano mestre combinado](2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md#phase-00), seguido da seção da fase atual.
5. [Revisão crítica e evidências](PLAN_SELF_REVIEW.md).

Os quatro Markdown canônicos estão na raiz. O COMBINED contém o mestre e as nove fases; o ZIP original também contém versões separadas. As cópias revisadas em `docs/superpowers/plans/` são geradas do COMBINED e não devem ser editadas independentemente. Caminhos de código/estado dentro dos planos são saídas futuras. A pasta não era um repositório Git no início da revisão; verificar novamente antes de inicializar e não inventar remoto.

## Antes de implementar

A futura execução começa por M1 e fase 01, seguindo o grafo de dependências do mestre. Segurança básica 07A precede instalações; ingestão 03 e solver 04 podem avançar sem Revit. A fase 07B valida recuperação integrada depois do release sintético. Disponibilidade de uma skill ou ferramenta deve ser verificada; na ausência de subagentes, execute sequencialmente com as mesmas revisões e testes, sem fingir uma revisão independente.

A implementação exige TDD: teste de comportamento, falha pelo motivo esperado, correção mínima e nova validação. Gates de laboratório/produção exigem evidências reais, reconsulta, salvamento e reabertura. Testes sintéticos ou revisão de Markdown não são PASS no Revit.

## Programa adotado e decisões ainda pendentes

- `PROGRAM_BASELINE = RESOLVED`: o usuário escolheu explicitamente **20 pessoas, conforme programa_necessidades.pdf**, em 2026-09-15. Adotar o programa completo do PDF: 626 m² úteis internos e 260 m² externos programados; estimativas fechada 783–814 m² e coberta 850–950 m². Preservar a planilha de 42 pessoas como hipótese não adotada; não misturar suas quantidades/áreas com a base escolhida. Essa decisão não aprova implantação, alternativa BIM ou conformidade normativa.
- `TYPOLOGY`: confirmar o equipamento e sua política de sigilo/acesso.
- `SITE_BOUNDARY` e `SITE_OCCUPANCY`: confirmar polígono, frentes, área utilizável e premissa de realocação da ocupação existente.
- Topografia e normas verificadas: manter dados ausentes como ausentes e limitar o escopo do estudo.
- `APPROVED_FOR_BIM`: a seleção detalhada depende de evidência humana vinculada ao hash do conteúdo. Massas de finalistas podem usar CONCEPT_ONLY somente até R04.

O DXF/IFC HIPÓTESE, a planilha de cálculo e os pareceres auxiliares não são aprovação da autora, levantamento ou prova automática de conformidade.

## Continuidade e integridade

Na implementação, ler `PROJECT_STATE.yaml` se existir, conferir Git/ambiente/bloqueadores e retomar o próximo ID READY. O estado é versionado; um arquivo ausente ou corrompido não deve ser substituído por um falso estado verde. Usar um único executor Revit e lock compartilhado entre worktrees/provedores. Toda escrita segue WRITE → READ → VERIFY; originais, baselines, checkpoints e GOLDEN ficam protegidos.

Após cada bloco, registrar testes/evidências, atualizar estado e handoff, revisar os arquivos a versionar, fazer commit e push quando houver remoto. Fontes privadas, backups brutos, credenciais e locks vivos ficam fora do Git. Se não for possível publicar, registrar motivo e comandos de retomada.

## Pedido sugerido para a próxima etapa

```text
Execute M1 e a fase 01 do plano combinado revisado. Comece pelo estado real da pasta e pelas instruções existentes, preserve fontes e trabalho alheio, siga TDD e atualize o handoff. Registre bloqueios por dependência. Não instale provedores antes de 07A e dos pré-requisitos específicos da fase 02.
```

Para falhas Revit/MCP, preservar checkpoint e journal, classificar a falha e reconciliar operações IN_DOUBT antes de repetir ou trocar provedor. Consultar apenas capacidades com evidência válida para o build/esquema/escopo atual; novas capacidades voltam ao Tool Lab.
