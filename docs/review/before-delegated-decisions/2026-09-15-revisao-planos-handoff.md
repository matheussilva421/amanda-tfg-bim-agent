# Handoff da revisão dos planos Amanda

Data: 2026-09-15. Status: CONCLUIDO_DOCUMENTALMENTE. Implementação e runtime Revit: NOT_RUN.

## Escopo autorizado

Analisar e corrigir os quatro Markdown da raiz, consultando os documentos da pasta para entender o TFG. A revisão não executa o plano BIM nem instala ferramentas ou altera Revit/configuração do Codex.

## Estado inicial verificado

- Os quatro arquivos existem na raiz, com underscores normais nos nomes.
- A pasta não é um repositório Git; `git status --short --branch` e `git remote -v` falharam com `not a git repository`. Não há remoto conhecido para commit/push.
- Inicialmente os planos separados não estavam extraídos. O ZIP recebido depois contém mestre e nove filhos: quatro arquivos idênticos aos originais da raiz, dez seções correspondentes ao COMBINED e 15/15 hashes válidos. A ausência era da disposição na pasta, não do pacote original.
- A autorrevisão declara PASS sem relatório de execução anexado.
- Consulta pontual da memória por Amanda/TFG/BIM sem resultados relevantes.

## Trabalho concluído

- Revisados os quatro documentos, com 32 achados/correções descritos em PLAN_SELF_REVIEW.md.
- Quatro Markdown da raiz canônicos; dez planos por fase gerados em docs/superpowers/plans, com links e 159 IDs únicos de tarefa.
- Extraídos 13 PDF/DOCX/XLSX com locadores/hashes e lidas as partes relevantes. Inventário dos 21 arquivos do pacote acadêmico; cabeçalho/unidades do IFC HIPÓTESE inspecionados. Fontes intactas.
- Conflito identificado: PDF prevê 20 pessoas, 626 m² internos/260 m² externos; planilha pressupõe 12 famílias × 3,5 = 42 pessoas. Em continuação de 2026-09-15, o usuário selecionou explicitamente “20 pessoas, conforme o PDF”: PROGRAM_BASELINE = RESOLVED. Adotar o programa completo de programa_necessidades.pdf; preservar a hipótese de 42 sem usá-la no dimensionamento adotado.
- Corrigidos gates de fontes/terreno/tipologia, dependências 07A/07B, ingestão sem bloqueio Revit, TDD, aprovação por hash, massas CONCEPT_ONLY, journal IN_DOUBT, lock compartilhado, atomicidade, segurança de arquivos, unidades, solver/scoring e publicação completa de GOLDEN.
- STUDY/FINAL e conclusão acadêmica separados. Revisão estática não representa aceite real.
- Conferidas fontes primárias técnicas e help local de Codex MCP sem instalar/configurar ferramentas.
- ZIP recebido preservado. Gerado amanda-tfg-bim-agent-planos-REVISADOS-2026-09-15.zip, com documentos e evidências estáticas, sem fontes acadêmicas privadas.

## Arquivos criados ou alterados

- Alterados: START_HERE_FOR_CODEX.md, PLAN_SELF_REVIEW.md, 2026-09-11-amanda-tfg-bim-agent-design.md e 2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md.
- Criados: este handoff, dez planos derivados, ZIP revisado e scripts/relatórios em docs/review.
- Backups exatos dos quatro originais: docs/review/originals-2026-09-15, com manifest.json.
- Extrações privadas locais: docs/review/source-extracts. Previews das duas páginas do programa: docs/review/previews. Não incluídos no ZIP.

## Validação e retomada

Não existe aplicação implementada; nenhuma suíte do futuro agente foi executada. Comandos rodados com o Python disponibilizado pelo runtime Codex:

- `docs/review/validate_documents.py --report docs/review/validation-before.json`: 19 verificações, 3 passaram e 16 falharam por lacunas esperadas.
- `docs/review/validate_documents.py --report docs/review/validation-after.json`: 19 verificações, 19 passaram e 0 falharam. Links/âncoras, AST dos exemplos Python, contratos textuais, grafo acíclico e 159 IDs únicos. Não prova implementação dos contratos.
- `docs/review/inspect_archive.py`: quatro originais idênticos, dez seções correspondentes e 15/15 hashes válidos.
- `docs/review/package_review.py`: dez filhos sincronizados, 15 Markdown conferidos, zero links locais quebrados, 23 entradas e 22 hashes válidos no ZIP.
- Releitura dos 13 hashes de fontes: todos preservados.
- `pdftoppm -f 1 -l 2 -scale-to 1400 -png programa_necessidades.pdf docs/review/previews/program`: duas páginas renderizadas e inspecionadas visualmente; capacidade/áreas conferidas. Sem QA visual integral do TFG/modelos.

## Problemas e soluções

- rg ignorava arquivos locais: buscas passaram a usar --no-ignore e caminhos literais.
- Script editorial confundiu comentários Python com títulos: seletor de fases corrigido antes da primeira gravação.
- Leitor de SHA256SUMS não normalizava ./ e stdout tinha encoding inadequado: corrigidos; resultado final 15/15.
- PyMuPDF indisponível: usado Poppler instalado. Criada pasta de previews após primeira tentativa; avisos de fontes não impediram previews legíveis.
- Patches com alvo duplicado ou trecho não encontrado foram rejeitados sem edição parcial; reaplicados em blocos válidos.
- Git confirmou ausência de repositório. Sem mudanças em configuração global, Revit, provedores, login/licença.

## GitHub

Commit/push NÃO REALIZADOS: pasta sem .git e remoto desconhecido. Não foi criado destino externo ou repo aninhado. Para publicar, após escolher o repositório correto e preparar exclusões privadas conforme M1, inicializar somente se ainda não houver Git e usar staging explícito:

```powershell
git init -b main
git add -- START_HERE_FOR_CODEX.md PLAN_SELF_REVIEW.md 2026-09-11-amanda-tfg-bim-agent-design.md 2026-09-11-amanda-tfg-bim-agent-COMBINED-plan.md docs/superpowers/plans docs/notes docs/review/validate_documents.py docs/review/package_review.py docs/review/validation-before.json docs/review/validation-after.json docs/review/archive-comparison.json docs/review/generated-plans-manifest.json
git diff --cached --stat
git commit -m "docs: revise Amanda BIM plans and handoff"
```

Depois de verificar a URL real, configurar origin com `git remote add origin URL_REAL_DO_REPOSITORIO` e executar `git push -u origin main`. URL_REAL_DO_REPOSITORIO é instrução para preenchimento, não destino existente; não executar literalmente. Se já existir checkout/branch/remoto, adaptar sem reinicializar ou sobrescrever trabalho.

## Retomada e pendências

1. Ler START_HERE_FOR_CODEX.md, este handoff e PLAN_SELF_REVIEW.md.
2. Alterar somente os canônicos e rerodar validate_documents.py/package_review.py para atualizar filhos/evidências/pacote. Não rerodar os scripts editoriais one-shot revise_documents.py/finalize_edits.py sobre novas edições; servem como registro da transformação desta revisão.
3. Se implementação for solicitada, executar M1/01 e o grafo revisado com TDD/handoff incremental.
4. PROGRAM_BASELINE já resolvido: PDF de 20 pessoas. Registrar seleção/hash na ingestão sem perguntar novamente. Resolver TYPOLOGY, SITE_BOUNDARY/SITE_OCCUPANCY, normas/topografia e seleção arquitetônica antes das tarefas dependentes.
5. Revit, instalação/build, solver, E2E, cold reopen e exports seguem NOT_RUN. Não promover capabilities nem declarar FINAL/TFG_COMPLETE com base nesta revisão.

## Continuação após seleção do programa

Em 2026-09-15, o usuário escolheu “20 pessoas, conforme o PDF”. Atualizados os quatro Markdown canônicos e este handoff para resolver PROGRAM_BASELINE; regenerados os dez filhos e o ZIP revisado. Fonte escolhida: programa_necessidades.pdf, SHA256 `11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17`. A planilha de 42 pessoas permanece intacta como hipótese não adotada; não recalcular nem sobrescrever as fontes nesta etapa documental.

Validação desta atualização: executar novamente validate_documents.py (19 verificações) e package_review.py (links, sincronização e hashes). O resultado final fica nos mesmos relatórios. Conferir adicionalmente que os quatro canônicos registram PROGRAM_BASELINE = RESOLVED e que o hash do PDF é o selecionado. Sem testes/Revit ou implementação do agente. Git continua sem repositório/remoto; instruções de publicação acima permanecem aplicáveis. Próximo passo: M1/01 se solicitado; a decisão de programa não é autorização para implementar ou selecionar arquitetura.

Backup imediatamente anterior a essa escolha: docs/review/before-program-baseline, incluindo os quatro docs, handoff e ZIP revisado anterior. Não usar esse backup para apagar a decisão vigente sem pedido do usuário.

Reversão documental: comparar/restaurar explicitamente os backups somente se desejado; depois regenerar filhos/ZIP. Fontes acadêmicas e ZIP recebido permanecem originais.
