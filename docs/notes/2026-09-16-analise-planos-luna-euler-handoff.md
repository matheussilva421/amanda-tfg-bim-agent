# Handoff - analise simples dos planos (subagente LUNA) e limpeza local

Data: 2026-09-16 (America/Fortaleza). Escopo: pedido do dono no turno - "crie um subagent para analisar os planos e me dizer de forma simples o que falta", limpar o que nao e mais necessario em `C:\Users\slvma\Downloads\Github\Projeto Amanda`, nada pago/premium, confirmar se o Revit continua em uso.

## 1. Resultado principal

Subagente LUNA XHIGH **Euler** (`01a0a8a0-03a7-7b52-bffd-07c1a06067b9`), com `fork_context=false`, executado sozinho e fechado com `close_agent` (retornou `previous_status.completed`). Antes dele, `wait_agent` mostrou os 7 subagentes antigos (`Planck`, `Sartre`, `Heisenberg`, `Newton`, `Bacon`, `Pasteur`, `Boole`) como `completed`; todos foram fechados.

Entregavel: [docs/notes/2026-09-16-o-que-falta-simples-v11.md](2026-09-16-o-que-falta-simples-v11.md) (8.818 bytes, criado 02:18). Continua a v10 (`2026-09-16-o-que-falta-simples-v10.md`, 8.272 bytes, 02:01), que nao foi alterada.

Resumo do que falta (confirmado no grafo em 2026-09-16):

- 159 tarefas: 136 PASS, 2 PASS_WITH_WARNINGS, 13 PENDING, 8 SUSPENDED, 0 FAIL; `next_task: P06-T14` (`PROJECT_STATE.yaml:10`).
- Pending: P06-T14 (ensaio de entrega), P07-T17 e P07-T19 (retomada segura), P08-T08 e P08-T09 (massing e escolha), P08-T10 a P08-T19 (RVT, R01-R13, QA R14, RC R15, exports, pacote, GOLDEN R16).
- Suspensas de proposito: P09-T03 a P09-T09 (Blender e APS/nuvem) - nao travam o caminho local.
- Faltam dados do dono: topografia, limite do lote, ocupacao atual, numero de frentes e norte verdadeiro.
- Portoes tecnicos abertos: `revit.create_grid` e `revit.create_roof` sem entrada registrada; build `20260716_1515(x64)` (productVersion) vs `27.2.0.39` (fileVersion) a reconciliar por decisao explicita; zero capacidades com escopo `PRODUCTION`; crosswalk semantico ainda nao ligado ao caminho de producao (a v11 reconfirmou por busca estatica).

## 2. Limpeza local (executada)

Comandos e resultados:

- `pwsh -NoProfile -File scripts\cleanup-local.ps1` (dry run): `cleanup plan: 0 targets, 0 MB, plus 11 __pycache__ directories`.
- `pwsh -NoProfile -File scripts\cleanup-local.ps1 -Apply`: `removed 0 targets and 11 __pycache__ directories`; `remaining scratch=0 pycache=0` (11 caches removidos agora; 21 no passe do turno anterior = 32 neste dia).
- Nada mais no repositorio casa com "nao necessario" pelas regras do proprio projeto: `TFG_Amanda_2026`, `docs/source`, `vendor`, `.dotnet`, `.venv*` e `tool-lab` sao fonte, evidencia de laboratorio ou ferramenta.
- **Candidato unico que sobrou, nao removido:** `TFG_Amanda Fernandes_ENTREGA 15.06.2026.pdf` (54.553.582 bytes) e `programa_necessidades.pdf` (31.004 bytes) na raiz, byte-identicos aos de `docs/source/` (hashes 16ABE6...292A7E e 11DAA9...4A17, conferidos duas vezes nesta sessao). Sao itens de `project/provenance/source-manifest.yaml`, logo sao fonte: nao foram apagados sem autorizacao. O `.gitignore` (linhas 26-27) ignora exatamente esses dois caminhos da raiz. Se o dono autorizar, um comando resolve (economia de ~99,5 MB); `docs/source/` continua intacto e os testes `tests/project/test_provenance_integrity.py` conferem os hashes por `immutable_path` (docs/source).

## 3. Revit - continua em uso (resposta ao dono)

- `horizun_health`: `status healthy`, Horizun `1.3.3`, `contract_hash 8b9600f5274d7dffb6e5bd5f`.
- `get_document_info`: `LAB_R01_TEMPLATE`, build `27.2.0.39`, 3231 elementos, documento aberto em `revit\lab\probe\LAB_R01_TEMPLATE.rte`.
- A ponte viva funciona. O que trava escrita pela rota stdio do projeto e a ACL do arquivo de descoberta `C:\Users\slvma\.horizun\discovery\revit-2027-30736.json` (2689 bytes; `Get-Content` dentro do sandbox devolve "Access to the path ... is denied").

## 4. Testes e validacoes deste turno

- Contagem do grafo: `rg -o 'status: [A-Z_]+' state/task-graph.yaml | ...` -> PASS 136, PASS_WITH_WARNINGS 2, PENDING 13, SUSPENDED 8.
- `project/provenance/source-inventory.json`: `entry_count 28`; as 28 entradas sao os quatro Markdown canonicos, `docs/notes/2026-09-15-revisao-planos-handoff.md`, os 21 arquivos de `TFG_Amanda_2026/` e `programa_necessidades.pdf` + `TFG_Amanda*.pdf` da raiz (lido com `utf-8-sig`, o arquivo tem BOM).
- Hashes dos PDFs das duas localizacoes: iguais (16ABE6... e 11DAA9...).
- `git ls-files`: os dois PDFs da raiz e o conteudo de `docs/source` nao sao rastreados (ignorados por intencao). Os dois `.zip` da raiz sao rastreados, portanto foram mantidos.
- Nao houve chamada de escrita ao Revit, nem pytest neste turno (o subagente fez analise documental pura).

## 5. GitHub

- `git status --short --branch`: `main...origin/main`, 14 modificados e ~33 nao rastreados (herdados de turnos anteriores), mais `docs/notes/2026-09-16-o-que-falta-simples-v11.md` deste turno.
- `git add` falha com `Unable to create '.../.git/index.lock': Permission denied` (ACL do `.git`). Nada foi commitado nem enviado.
- O repositorio remoto `amanda-tfg-bim-agent` ja existe e `origin/main` esta configurado.

## 6. Pendencias

- Autorizacao (opcional) para remover os dois PDFs duplicados da raiz (~99,5 MB).
- Decidir entre usar a ponte viva do app para o ensaio P06-T14 ou resolver a ACL do arquivo de descoberta para a rota stdio do projeto.
- Manter a nota simples atualizada a cada bloco (v11 e a atual).

## 7. Proximo passo

1. Se o dono autorizar, apagar os dois PDFs duplicados da raiz com verificacao de hash antes.
2. Executar P06-T14 em documento descartavel de laboratorio (salvar, fechar, reabrir, exportar IFC/PDF/DWG, hashes e recusa de sobrescrita do GOLDEN).
3. Fechar os portoes tecnicos (nomes `create_grid`/`create_roof`, build, escopo PRODUCTION e crosswalk no caminho de producao) antes de P08-T08/P08-T09.

Retomada: ler este handoff, a v11, `state/task-graph.yaml` (tarefa P06-T14) e `PROJECT_STATE.yaml`; nada em `state/` foi alterado por este turno.

