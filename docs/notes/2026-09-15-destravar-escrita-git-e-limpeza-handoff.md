# Handoff — destravar escrita (Revit/Git) e limpeza local

Data: 2026-09-15. Bloco desta sessao: pedido do dono ("crie um subagent para analisar os planos e dizer de forma simples o que falta"), confirmacao de que o Revit continua em uso, politica "nada pago" e limpeza da pasta local.

## 1. Fato central: um unico revisor automatico travando duas frentes

O mesmo erro de infraestrutura do app aparece em dois pontos diferentes:

1. Escrita no Revit pela rota do app:
   `horizun_document_session{operation:"save", dry_run:true}` retorna
   `This action was rejected due to unacceptable risk. Reason: Automatic approval review failed: Provider error 400 ... "This response_format type is unavailable now" ... invalid_request_error`.
   Leitura no mesmo instante funciona (`get_document_info`: `LAB_R01_TEMPLATE.rte`, Revit 2027 build 27.2.0.39, 3230 elementos, nao workshared).
2. `git add -- <37 arquivos>` com `sandbox_permissions:"require_escalated"`: rejeitado no `CreateProcess` com o **mesmo** texto de provider 400.

Conclusao: nao e veredito de risco nem erro do Revit nem do repositorio. E o revisor automatico do app quebrado. A instrucao anexada a recusa proibe caminho indireto; portanto nada de escrita foi tentado por outro meio.

## 2. Estado medido agora

- Revit 2027 pid 30736 vivo; add-in saudavel; perfil `full_write` (herdado do bloco anterior).
- `git`: HEAD `abe34c2` == `origin/main` (0 a frente, 0 atras); remoto `https://github.com/matheussilva421/amanda-tfg-bim-agent.git`; **37 arquivos sujos**.
- `.git` tem `Deny Write` para o grupo do sandbox (ACL medida), por isso `git add` falha com `Unable to create '.git/index.lock': Permission denied` sem escalacao.
- `gh auth status`: token de `matheussilva421` **invalido** ("The token in default is invalid").
- Limpeza: `__pycache__=0`, `.pytest_cache`/`.mypy_cache`/`.ruff_cache` ausentes, scratch `.tmp-*`=0, sentinelas ausentes. Nada a remover nessa camada.

## 3. Limpeza de verdade: o que e candidato e o que nao e

`\.dotnet` (770 MB) e `vendor/` (354 MB: `RevitCortex` 199 MB + `horizun-revit-mcp` 133 MB) nao sao rastreados pelo git e por isso pareciam candidatos. Medicao do uso:

- `C:\Users\slvma\.codex\config.toml:130` -> `command = 'C:\Users\slvma\Downloads\Github\Projeto Amanda\vendor\RevitCortex\publish\server\RevitCortex.Server.exe'`. O servidor MCP do RevitCortex aponta para dentro de `vendor/`; `RevitCortex.Server.exe` existe.
- Consequencia: **nao apagar `vendor/`**. Sem ele, a rota `revitcortex` para de subir e a modelagem no Revit perde uma das duas rotas tipadas.
- `\.dotnet` e um SDK .NET instalado em 15/09/2026. Nenhum arquivo do repositorio o referencia (`rg '\.dotnet'` sem resultados). Nao comprovado que ainda seja necessario; so apagar com autorizacao explicita do dono.
- `revit/` (100 MB) e `tool-lab/` (172 MB) sao evidencia obrigatoria do projeto. `logs/` esta com 0 MB. `.venv*` sao ambientes provisionados por contrato dos planos.

## 4. Notas de analise consolidadas

Foi identificado um empilhamento de analises antigas do "o que falta". Em vez de apagar (irreversivel sem commit), as quatro geracoes antigas foram marcadas:
`2026-09-15-artemis-o-que-falta-simples.md`, `2026-09-15-arya-o-que-falta-simples.md`, `2026-09-15-daenerys-analise-do-que-falta.md` e `2026-09-15-o-que-falta-simples-v3.md` apontam para `2026-09-15-o-que-falta-simples-v5.md` e ficam como historico. A v4 ja estava marcada.

## 5. Subagente

LUNA XHIGH (`agent_type:"luna"`, `fork_context:false`) `01a0a7f3-7ed3-7973-a790-b5ef3dc250f1` ("Pasteur") foi disparado para o pedido do dono e **concluiu**. Escopo: checklist de entrega por artefato (RVT, plantas, cortes, elevacoes, pranchas, tabelas, IFC, PDF, DWG, previews, relatorios, proveniencia, pacote, GOLDEN-001), proximos 5 passos, o que nao precisa pagar e radar de limpeza.

Entrega: `docs/notes/2026-09-15-checklist-entrega-o-que-falta-v6.md` (11.810 bytes, 6 secoes, 14 artefatos). Resultado principal: so existem artefatos de estudo/laboratorio; producao, documentacao final, QA final e pacote GOLDEN estao ausentes ou parciais. Ordem que ele devolveu: `P06-T14`, `P08-T08`, `P08-T09`, `P08-T10`, `P08-T11`, depois R05 a R16, exports, relatorios, pacote e `GOLDEN-001`. Limpeza: nenhum candidato "seguro remover"; `vendor/`, `tool-lab/`, `revit/`, `TFG_Amanda_2026/`, `bootstrap/`, `project/` sao inseguros; `.dotnet/`, `logs/`, `.venv*`, `bim/` precisam de autorizacao. APS/Forge e render em nuvem seguem suspensos e o caminho obrigatorio local nao exige pagamento. Ele nao tocou Git.

## 6. Acoes humanas pendentes (ordem de impacto)

1. Destravar a escrita: consertar/liberar o revisor automatico do app. Enquanto ele responder 400, nenhuma escrita no Revit e nenhum `git add` escalado passam. Texto literal da recusa guardado no item 1.
2. `gh auth login -h github.com` para `matheussilva421`; depois disso o commit dos 37 arquivos pode ser tentado de novo (o indice ainda depende do item 1 para escrever).
3. Opcional: se o caminho tipado stdio do projeto voltar a ser necessario, herdar leitura de `discovery\revit-2027-30736.json` para o grupo do sandbox.
4. Decidir sobre `\.dotnet` (770 MB). Candidato a remocao, sem referencia no repo, mas nao comprovadamente dispensavel.

## 7. Retomada exata

- Se a escrita destravar: `P08-T08` (plano `docs/superpowers/plans/08-amanda-production-run.md:136-147`) — por finalista, writer lease, RVT candidato em `revit/production/candidates/AMANDA-RUN-001-F01/`, cadeia R01 a R04, verificar metricas contra `solution.json`, exportar preview, salvar/fechar/reabrir, registrar ferramentas/fallbacks, recusar R05 a R16, liberar lease.
- Se nao destravar: construir o compilador real que le `solution.json` e monta `plan_project_initialization` -> `plan_site_stage` -> `plan_levels_stage` -> `plan_massing_stage` (CONCEPT_ONLY) gravando `BIM_PLAN.json` — trabalho de codigo, sem depender da escrita.
- Antes de encerrar: repetir `scripts\cleanup-local.ps1` apos rodar testes (recria `__pycache__`).

## 8. Arquivos deste bloco

- Criado: este handoff; `docs/notes/2026-09-15-checklist-entrega-o-que-falta-v6.md` (subagente LUNA XHIGH).
- Editados (apenas 1a linha de cabecalho): as quatro notas antigas do item 4.
