# Handoff — relatório completo do projeto para o próximo agente

**Data:** 2026-09-16 (sessão de análise). **HEAD analisado e de partida:** `1e10f7c0008cc630006b56849104666673379cbe`.

## O que foi feito

Análise completa, somente leitura, de todo o projeto (estado, planos, specs, código, testes, laboratório, estudo e ambiente), com o objetivo de produzir um insumo para outro agente continuar sem reconstruir contexto.

**Entrega principal:** [`docs/reports/2026-09-16-relatorio-completo-para-proximo-agente.md`](../reports/2026-09-16-relatorio-completo-para-proximo-agente.md) — 11 seções: método, veredito, arquitetura, o que já foi feito, o que falta, 12 problemas (P-01…P-12) com evidência, travas, roteiro, comandos de verificação, limites e anexo de números.

## Arquivos criados

- `docs/reports/2026-09-16-relatorio-completo-para-proximo-agente.md` (relatório completo).
- `docs/notes/2026-09-16-relatorio-completo-handoff.md` (este handoff).

Nenhum arquivo existente foi alterado: `state/`, `PROJECT_STATE.yaml`, planos, tarefas, RVTs e artefatos GOLDEN ficaram intactos.

## Testes e validações executados

| Comando | Resultado |
| --- | --- |
| `.\.venv\Scripts\python.exe -m pytest -q` | **1 failed, 822 passed** em 62,86 s — `tests/unit/test_topologic_spike.py` (falha pré-existente, dependente de rede/PyPI) |
| Reprodução isolada de `_build_geometry` + `_export_geometry` do spike com caminhos em diretório temporário | geometria OK (12 vértices, 30 arestas, 20 faces, 24 m², 72 m³); `TypeError: can only concatenate str (not "NoneType") to str` em `topologicpy.Topology.OBJString` (`"# topologicpy " + Helper.Version()`) porque `Helper.CheckVersion` não alcança o PyPI |
| `git status --short`, `git diff`, `git ls-files`, `git show HEAD:<path>` | 34 entradas ` D` em `revit/lab/exports/p06t14/GOLDEN/RC01` (ACL quebrada) + 2 arquivos de estado modificados; trabalho de terceiros não tocado |
| Inspeção de processos (`Get-Process Revit*, horizun*`) | sem `Revit.exe`; apenas `RevitAccelerator` e 6 servidores MCP órfãos |
| ACLs (`Get-Acl`, `icacls`) em `revit/lab/exports/p06t14/GOLDEN/RC01` | `Acesso negado` / `Attempted to perform an unauthorized operation` |
| Leitura de `state/*`, `PROJECT_STATE.yaml`, `docs/superpowers/plans/00..09`, `solutions/finalists/comparison.md`, `project/**` | consolidada no relatório |

Não executei `doctor`, `status`, `advance`, `phase-gate` nem qualquer comando que reescreva estado, justamente para não alterar `state/*`.

## Efeito colateral tratado

A suíte reescreve o arquivo rastreado `tool-lab/topologic/results/topologic-spike.json` (o spike grava `BLOCKED` sem rede). O arquivo foi **restaurado byte a byte a partir do HEAD** nesta sessão: `git hash-object` = `git rev-parse HEAD:<path>` = `0687547c4bc4270cebedcf6410bbd322e8af9681` e `git diff` vazio; o ` M` residual no `git status` é apenas stat/CRLF do índice. Mesma prática registrada em `2026-09-15-luna-v7-e-compilador-handoff.md:85`.

## Problemas encontrados (resumo; detalhe no relatório)

1. **P-01 [MÉDIO-ALTO]** `revit/lab/exports/p06t14/GOLDEN/RC01` perdeu a herança de ACL: fora do sandbox o dono lê os 36 arquivos normalmente (integridade conferida por SHA-256) e o `git status` é limpo; dentro do sandbox o diretório é ilegível e o `git status` mostra **34 deleções fantasma**. **Nunca commitar essa deleção** nem usar `git restore` nesses caminhos.
2. **P-02 [ALTO]** suíte não é verde offline (1 falha em `test_topologic_spike`, dependência de PyPI dentro do `topologicpy`).
3. **P-03 [ALTO]** `.git` com `Deny Write` para o grupo do sandbox: `git add/commit/push` exigem escalação.
4. **P-04 [MÉDIO]** `PROJECT_STATE.yaml` (PHASE_06/PENDING) e `RESUME_AFTER_REBOOT.md` (PHASE_02, next P06-T01) divergem do grafo vivo (next `P08-T08`).
5. **P-05 [ALTO]** sem Revit vivo e com MCP órfãos; `.horizun/discovery` vazio.
6. **P-06 [ALTO]** `revit.create_grid` e `revit.create_roof` sem `registered_entry`; 11 capabilities, 0 `PRODUCTION`.
7. **P-07 [ALTO]** não existe driver de candidato conceitual; `bim execute` só aceita `SYNTHETIC_LAB`.
8. **P-08 [MÉDIO]** finalistas empatados em `0.8415491821831452` apesar de 490 m² de diferença de envelope.
9. **P-09 a P-12 [MÉDIO/BAIXO]** ACLs quebradas fora do repo e scratch local, `.codex/config.toml` untracked pedindo `danger-full-access`, dispersão documental, scripts de laboratório mal interpretáveis como produção.

## Status do GitHub

Commit e push desta sessão: ver a mensagem final do agente. Antes da entrega, o worktree (visto do sandbox) mostrava 34 deleções em `GOLDEN/RC01` — **fantasma**, o diretório está íntegro fora do sandbox —, além de `state/environment-report.json`, `state/status.md` e um ` M` cosmético em `tool-lab/topologic/results/topologic-spike.json`. Tudo preservado como estava, fora do commit deste relatório.

## Pendências e próximos passos

1. Decidir sobre a ACL de `revit/lab/exports/p06t14/GOLDEN/RC01`: se agentes sandbox precisarem ler o pacote selado, conceder `RX` a `CodexSandboxUsers` em processo elevado (o dono já lê normalmente).
2. Reconciliar `PROJECT_STATE.yaml`/`RESUME_AFTER_REBOOT.md` com o grafo e decidir sobre os dois arquivos de estado modificados (`doctor`/`status` os reescrevem; commitar junto ou reverter com decisão registrada).
3. Fechar o crosswalk (`grid`, `roof`) com prova viva e `registered_entry`.
4. Abrir o Revit 2027 em documento descartável e executar `P08-T08` (teste RED do driver + `scripts/bim_concept_candidates.py`).
5. `P08-T09` → `P08-T19` → `P08-T18` conforme o plano 08; depois `P07-T17`/`P07-T19` em sessão e inicialização realmente novas.

## Como retomar

Ler nesta ordem: `AGENTS.md` → `PROJECT_STATE.yaml` → `state/status.md` → `docs/notes/2026-09-16-o-que-falta-simples-v16.md` → `docs/reports/2026-09-16-relatorio-completo-para-proximo-agente.md` → último handoff desta cadeia. Os comandos de verificação de início de sessão estão na seção 9 do relatório.
