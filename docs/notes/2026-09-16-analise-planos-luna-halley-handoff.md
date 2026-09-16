# Handoff - analise dos planos (subagente LUNA) e limpeza local

Data: 2026-09-16. Pedido do dono: criar um subagente para analisar os planos e
dizer de forma simples o que falta, e limpar a pasta local do que nao e necessario.

## 1. Resultado em uma linha

O subagente LUNA XHIGH Halley (01a0a890-835f-7e81-b88d-cdea52d5f57d, agent_type
luna, fork_context false) produziu o relatorio simples v10 em
docs/notes/2026-09-16-o-que-falta-simples-v10.md (8.272 bytes) e foi fechado com
close_agent. Grafo conferido: 159 tarefas = 136 PASS + 2 PASS_WITH_WARNINGS + 13
PENDING + 8 SUSPENDED + 0 FAIL. next_task: P06-T14 (PROJECT_STATE.yaml:10).

## 2. O que falta, em linguagem simples

1. Ensaio de entrega no Revit de laboratorio: salvar, fechar, reabrir, exportar e
   conferir hashes - P06-T14.
2. Retomada segura: sessao nova do Codex (P07-T17) e reinicio real autorizado
   (P07-T19).
3. Massas do estudo F01/F02, escolha registrada e depois o RVT de trabalho -
   P08-T08, P08-T09, P08-T10.
4. Modelagem principal R01-R13, QA R14, candidato R15, exportacoes, pacote e
   GOLDEN-001 - P08-T11 ate P08-T18.
5. Dados que faltam e travam a verificacao final (nao a massa): topografia com
   cotas e datum, limite cadastral do terreno, ocupacao atual do lote, numero de
   frentes e norte verdadeiro.
6. Render/Blender e APS/nuvem permanecem suspensos de proposito e nao fazem parte
   do caminho local.

## 3. Medicoes feitas neste turno

- Revit vivo confirmado: LAB_R01_TEMPLATE aberto a partir de
  revit/lab/probe/LAB_R01_TEMPLATE.rte, build 27.2.0.39, 3231 elementos.
  horizun_health respondeu healthy, Horizun 1.3.3, contract_hash
  8b9600f5274d7dffb6e5bd5f.
- Desvio de build explicado (nao e defeito real): o catalogo
  state/capabilities.yaml grava revit_build 20260716_1515(x64) e o Revit vivo
  reporta 27.2.0.39. Os dois campos vem do mesmo arquivo state/revit-metadata.json:
  productVersion 20260716_1515(x64) e fileVersion 27.2.0.39, mesma instalacao em
  C:/Program Files/Autodesk/Revit 2027. A comparacao entry.revit_build != revit_build
  (src/amanda_agent/models/capability.py:294) ainda e textual, entao os dois valores
  precisam convergir por decisao explicita, nao por heuristica.
- Causa medida do PROVIDER_UNREACHABLE no transporte stdio do projeto: o arquivo de
  descoberta C:/Users/slvma/.horizun/discovery/revit-2027-30736.json (2.689 bytes)
  existe, mas read_text() dentro do sandbox devolve PermissionError [Errno 13]. O
  token do sandbox esta negado nesse arquivo; o MCP do app nao esta (ele responde
  saudavel). O PowerShell le o mesmo arquivo pelo MCP do app; o processo Python do
  .venv dentro do sandbox nao consegue.
- Os pipes do add-in existem: Horizun-30736 e
  revit5c6548f7-ebdc-4ee3-9fd5-d8547bfa7cb0_30736.
- Preflight do drill: scripts/bim_lab_drill.py --rvt revit/lab/release/LAB_RELEASE.rvt
  --preflight retornou PROVIDER_UNREACHABLE (horizun health reported an MCP error).
  Alvo novo de laboratorio criado: revit/lab/release/LAB_RELEASE.rvt, copia de
  revit/lab/baseline/LAB_R00_EMPTY.rvt, sha256
  15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D. O sentinel de
  seguranca recusou revit/lab/baseline/ como alvo gravavel (fail-closed correto:
  protected filename/path component baseline).

## 4. Limpeza local aplicada

- scripts/cleanup-local.ps1 -Apply: removidos 21 diretorios __pycache__;
  remaining scratch=0 pycache=0.
- Removidas por autorizacao explicita do dono as duas copias identicas na raiz:
  TFG_Amanda Fernandes_ENTREGA 15.06.2026.pdf (54.553.582 bytes, sha256
  16ABE602AC50643482CE3C782780B4135FA8468B5CA814061FE426C8CA292A7E, identico ao de
  docs/source/) e programa_necessidades.pdf (31.004 bytes, sha256
  11DAA9EFC4D1B022407D8BD02999E85B604A16539F29AE598DC45B339DE14A17, identico ao de
  docs/source/). Os originais de docs/source/ foram preservados.
- Medido e mantido (tudo ignorado pelo git, nada apagado): .dotnet 769,9 MB (unico
  SDK que compila vendor/RevitCortex e vendor/horizun-revit-mcp),
  .venv-environmental 451,0 MB, .venv 441,9 MB, .venv-topologic 376,0 MB, vendor
  354,4 MB, tool-lab 171,9 MB, revit 103,3 MB, docs/source 52,8 MB. Cada um exige
  autorizacao propria antes de qualquer remocao.

## 5. Testes

- .venv/Scripts/python.exe -X utf8 -m pytest tests/unit/test_capability_registry.py
  tests/unit/test_evidence.py -q -p no:cacheprovider => 24 passed em 0,58 s. Verde.

## 6. GitHub

Sem commit e sem push. git status mostra main...origin/main alinhado em abe34c2,
com 14 arquivos modificados e 33 nao rastreados de trabalhos anteriores. O .git
continua com ACL Deny Write para o grupo do sandbox (index.lock Permission denied)
e as tentativas com escalacao foram rejeitadas pelo revisor automatico do Codex.
Nenhum workaround foi tentado.

## 7. Pendencias exatas e retomada

1. Ligar o crosswalk ao caminho de producao. Hoje so existe
   CapabilityRegistry.load_with_crosswalk() (src/amanda_agent/models/capability.py:214);
   nenhum ponto do app o chama (grep: apenas status_dashboard.py:79 e testes).
   Escrever teste RED antes.
2. Convergir o build do Revit. Decidir o valor canonico entre productVersion e
   fileVersion e registrar a prova, para o preflight de producao parar de recusar
   por revit build ... is not the requested.
3. Corrigir tool_schema_hash sha256:local da entrada custom-api/create_wall em
   state/capabilities.yaml; as outras usam sha256:8b9600f5274d7dffb6e5bd5f.
4. Registrar revit.create_grid e revit.create_roof. Sao rotas provadas em
   laboratorio mas sem entrada no catalogo; hoje estao declaradas como lacuna em
   state/providers/semantic-crosswalk.yaml (registered_entry null).
5. Resolver o acesso de leitura ao arquivo de descoberta para o processo Python
   fora do sandbox (caminho tipado stdio do projeto), ou seguir usando a rota viva
   do app. Sem isso o preflight e o drill --execute nao fecham.
6. P06-T14 depende de horizun_document_session e horizun_export, hoje barrados
   pelo revisor automatico nas chamadas MCP diretas.
7. Atualizar PROJECT_STATE.yaml, state/status.md e o handoff canonico
   docs/notes/2026-09-15-luna-v7-e-compilador-handoff.md depois de cada bloco.

## 8. Arquivos deste turno

- Criado: docs/notes/2026-09-16-o-que-falta-simples-v10.md (subagente Halley).
- Criado: docs/notes/2026-09-16-analise-planos-luna-halley-handoff.md (este).
- Criado: revit/lab/release/LAB_RELEASE.rvt (copia do baseline para o ensaio).
- Removidos: as duas copias identicas na raiz (ver secao 4).

