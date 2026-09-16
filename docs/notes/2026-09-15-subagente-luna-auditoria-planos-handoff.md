# Handoff — subagente LUNA: auditoria dos planos e preflight BIM

Data: 2026-09-15
Workspace: C:\Users\slvma\Downloads\Github\Projeto Amanda

## Pedido do dono

Consolidar as notas de 2026-09-15 em um único resumo simples do que falta,
corrigir o retrato após auditoria adversarial, remover somente notas redundantes
e preparar um preflight fail-closed para P06-T14. Não usar serviço pago,
dependência nova, Revit, commit, push ou a suíte ampla.

## Subagentes LUNA usados

- Auditoria adversarial LUNA: revisão somente leitura dos planos, grafo, estado e
  entregas ausentes; apontou as correções de retrato registradas abaixo.
- Este worker LUNA: consolidou a documentação e implementou o teste/preflight no
  write set autorizado. Nenhum novo subagente foi criado neste worker.

## Resultado da auditoria

### Retrato confirmado

- Revit 2027 está instalado: `state/bim-environment.lock.yaml:5-8` e
  `state/environment-report.json:14-28`; o painel registra build em uso em
  `state/status.md:26-27`. O que falta são os RVTs de produção.
- As duas tarefas READY são P06-T14 e P08-T08, com P06-T14 como próxima oficial:
  `state/status.md:9-11`. O grafo confirma P06-T14 em
  `state/task-graph.yaml:1976-1984` e P08-T08 em `:2404-2412`.
- P07-T17 está SUSPENDED em `state/task-graph.yaml:2213-2233`; P07-T19 também
  está SUSPENDED em `state/task-graph.yaml:2261-2274`.
- A avaliação ambiental dos finalistas é HEURISTIC, sem simulação: grafo em
  `state/task-graph.yaml:2401-2403` e regra do plano em
  `docs/superpowers/plans/08-amanda-production-run.md:127-132`.
- Há divergência conhecida: `PROJECT_STATE.yaml:1` traz `blockers: []`, enquanto
  `state/blockers.yaml:2-5,29-31,54-57,78-80,101-103` lista cinco bloqueios.

### Lacunas de entrega que faltavam

- P05 ainda não deixou no disco `BIM_PLAN.md` e `BIM_PLAN.json`; o plano exige o
  resumo em `docs/superpowers/plans/05-bim-compiler.md:175`.
- A CLI `bim claim`/`bim record-result` é exigida em
  `docs/superpowers/plans/05-bim-compiler.md:382-383`, mas a implementação de
  journal durável também continua ausente conforme `:389`.
- `tool-lab/reports/bim-compiler-e2e.md` é exigido em
  `docs/superpowers/plans/05-bim-compiler.md:409` e não foi encontrado.
- Na verificação final, esse relatório apareceu como arquivo não rastreado de
  outro agente, com status declarado `PASS_FIXTURE`; não foi editado nem validado
  por este worker. O achado de ausência acima é o retrato da auditoria e o
  integrador deve validar esse artefato antes de considerar a lacuna encerrada.
- Também seguem ausentes os RVTs de produção, a comparação final e o pacote
  `GOLDEN-001`; a lista simples está no arquivo canônico abaixo.

### Lista simples do que falta

- Fazer P06-T14 e provar QA, persistência a frio, exports e integridade no laboratório.
- Fazer P07-T17 em sessão nova e P07-T19 após reboot real autorizado.
- Fazer P08-T08 e P08-T09: massas conceituais, comparação e escolha única.
- Criar o RVT de produção e compilar P08-T10..P08-T14.
- Fazer QA, RC, exports, relatórios e GOLDEN-001 em P08-T15..P08-T19.
- Resolver os cinco dados do terreno e concluir a revisão/entrega acadêmica humana.
- Manter Blender/render e APS/cloud suspensos enquanto forem opcionais.

## Correções aplicadas

- Atualizado `docs/notes/2026-09-15-o-que-falta-simples-v3.md:1-42` em pt-BR,
  com Revit instalado/em uso, READYs corretas, P07-T17 suspensa, HEURISTIC,
  divergência de blockers, lacunas P05, próximo passo e rodapé de auditoria.
- Atualizado somente a linha stale `state/status.md:33` para registrar o
  Horizun como UNREACHABLE diante do erro MCP vivo; build e demais estado foram
  preservados.
- Apagados apenas `docs/notes/2026-09-15-o-que-falta-simples-v2.md` e
  `docs/notes/2026-09-15-o-que-falta-luna-v3.md`.
- A listagem de notas não encontrou arquivo duplicado/stub de 2026-09-15 com
  menos de 600 bytes. Handoffs únicos não foram apagados.

## Achado Revit/MCP

O contexto vivo informado pelo dono registra o add-in Horizun carregado no Revit
PID 30736 e o named pipe `\\.\pipe\Horizun-30736` existente, mas
`tool-lab/horizun/hz_call.py get_document_info` retorna `Error: no Revit is
reachable` desde aproximadamente 21:26. Este worker não chamou o MCP nem tocou
no Revit. O preflight trata essa fronteira como `PROVIDER_UNREACHABLE`, código 3,
sem registrar PASS; a execução P06-T14 permanece pendente até um health real.

## Preflight implementado

`scripts/bim_lab_drill.py` ganhou `run_preflight()` e a flag `--preflight`.
O fluxo somente leitura valida alvo no laboratório, lock ausente e health
injetável, nessa ordem. Recusa local/lock com código 2, provider inalcançável com
código 3 e só imprime PASS quando os três gates passam. Não adquire lock, não
cria journal e não invoca o drill.

## Testes executados

- RED: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_bim_lab_drill_preflight.py -q`
  falhou na coleta com `ImportError: cannot import name 'run_preflight'`, como
  esperado antes da implementação.
- GREEN: o mesmo comando -> 6 testes aprovados, 0 falhados, exit 0.
- Regressão autorizada: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_bim_runner.py -q`
  -> 7 testes aprovados, 0 falhados, exit 0.
- Total GREEN deste bloco: 13 aprovados, 0 falhados. A suíte ampla não foi
  executada. Dependências não foram instaladas.

## Status do GitHub

Não foram executados `git add`, `git commit` ou `git push`, conforme pedido.
O estado observado continua `main...origin/main`, com alterações e arquivos de
outros agentes preservados. Este handoff e o teste/preflight permanecem no
working tree para o integrador.

## Pendências

- P06-T14 não pode ser declarado PASS enquanto o health MCP continuar retornando
  `no Revit is reachable`; nenhum RVT foi escrito ou alterado neste worker.
- Permanecem as cinco lacunas do terreno, a revisão humana, os RVTs de produção,
  o fluxo P08-T08..P08-T19 e as lacunas P05 descritas acima.
- O integrador deve decidir o commit conjunto sem incluir ou reverter mudanças de
  outros agentes.

## Retomada exata

1. Ler `AGENTS.md`, este handoff e
   `docs/notes/2026-09-15-o-que-falta-simples-v3.md`.
2. Confirmar novamente `state/status.md`, `state/blockers.yaml`, o lock e o health
   do provider, sem tocar no Revit durante o diagnóstico.
3. Quando o MCP estiver alcançável, executar o preflight com um alvo de laboratório:
   `.\.venv\Scripts\python.exe scripts\bim_lab_drill.py --rvt <RVT_LAB> --preflight`.
4. Só com exit 0 e mensagem PASS, avaliar a autorização do agente principal para
   seguir o `--execute` com `--fixture-root`; registrar WRITE→READ→VERIFY e
   atualizar o handoff correspondente.
