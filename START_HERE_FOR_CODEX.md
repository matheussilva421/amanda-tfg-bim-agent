# Comece aqui — projeto Amanda TFG BIM

**Revisão:** 2026-09-15. **Estado atual:** REVIEW_ONLY; implementação, instalações e validação real no Revit = NOT_RUN.

Este pacote contém a especificação e o plano de uma futura automação BIM. O usuário delegou ao agente a pesquisa e as decisões de projeto para futura execução, com revisão posterior por Amanda. Esta atualização registra essa delegação; implementação e instalações ainda não foram executadas.

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
- `TYPOLOGY`: o agente pesquisa as referências e adota a solução institucional/de acessos mais coerente com o centro de acolhimento temporário e o programa de 20 pessoas; registra justificativa, fontes e possibilidade de revisão por Amanda.
- `SITE_BOUNDARY` e `SITE_OCCUPANCY`: o agente pesquisa bases oficiais, mapas e documentos disponíveis, registra a melhor evidência e assume uma base provisória identificada quando faltar confirmação. Premissas de realocação e implantação são revisáveis; somente verificações dependentes da confirmação permanecem pendentes.
- Topografia e normas verificadas: manter dados ausentes como ausentes e limitar o escopo do estudo.
- `APPROVED_FOR_BIM`: o agente pode selecionar e desenvolver a alternativa com `selection_authority = AGENT_DELEGATED`, justificativa e approval_hash. Amanda revisa depois (`AMANDA_REVIEW_PENDING`), sem bloquear a geração do BIM. CONCEPT_ONLY continua disponível para comparar massas até R04.

O DXF/IFC HIPÓTESE, a planilha de cálculo e os pareceres auxiliares não são aprovação da autora, levantamento ou prova automática de conformidade.

## Pesquisa e decisões delegadas

O agente deve pesquisar, comparar alternativas, decidir e continuar, sem pedir confirmação rotineira sobre implantação, setorização, fluxos, materiais, linguagem ou preferência estética. Registrar as escolhas no futuro `project/requirements/decision-register.yaml`, com fontes, alternativas consideradas, motivo, limitações e arquivos afetados. Quando faltar evidência, usar `PROVISIONAL_ASSUMPTION` para o estudo; não apresentar hipótese como levantamento ou conformidade comprovada. O programa de 20 pessoas permanece fixo.

Amanda pode mudar o que não gostar: criar nova revisão, manter a anterior e revalidar os elementos afetados. O agente não precisa aguardar esse retorno para desenvolver e apresentar a proposta.

## Continuidade e integridade

Na implementação, ler `PROJECT_STATE.yaml` se existir, conferir Git/ambiente/bloqueadores e retomar o próximo ID READY. O estado é versionado; um arquivo ausente ou corrompido não deve ser substituído por um falso estado verde. Usar um único executor Revit e lock compartilhado entre worktrees/provedores. Toda escrita segue WRITE → READ → VERIFY; originais, baselines, checkpoints e GOLDEN ficam protegidos.

Após cada bloco, registrar testes/evidências, atualizar estado e handoff, revisar os arquivos a versionar, fazer commit e push quando houver remoto. Fontes privadas, backups brutos, credenciais e locks vivos ficam fora do Git. Se não for possível publicar, registrar motivo e comandos de retomada.

## Pedido sugerido para a próxima etapa

```text
Execute M1 e a fase 01 do plano combinado revisado, seguindo o grafo nas etapas posteriores. Comece pelo estado real da pasta, preserve fontes e trabalho alheio, siga TDD e atualize o handoff. Na pesquisa/projeto, tome as decisões delegadas e avance com premissas provisórias identificadas quando necessário; Amanda revisa depois. Mantenha o programa de 20 pessoas. Registre bloqueios somente nas verificações dependentes. Não instale provedores antes de 07A e dos pré-requisitos específicos da fase 02.
```

Para falhas Revit/MCP, preservar checkpoint e journal, classificar a falha e reconciliar operações IN_DOUBT antes de repetir ou trocar provedor. Consultar apenas capacidades com evidência válida para o build/esquema/escopo atual; novas capacidades voltam ao Tool Lab.
