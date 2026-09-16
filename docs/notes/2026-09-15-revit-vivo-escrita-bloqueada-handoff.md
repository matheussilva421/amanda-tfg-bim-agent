# Handoff - Revit vivo, escrita bloqueada pelo revisor automatico

Data: 2026-09-15 (sessao do app Codex, continuacao da auditoria V4).

## Medicoes desta sessao (evidencia fresca)

- Revit 2027 pid 30736, iniciado 15/09 17:03, build 27.2.0.39.
- Documento ativo: `revit/lab/probe/LAB_R01_TEMPLATE.rte` (template de laboratorio do proprio repo), nao workshared, 3230 elementos, 2 niveis, `matched_total=3230`, `coverage_complete=true`, 0 links, 0 ilegiveis.
- `horizun_health` pela ferramenta do app: `healthy`, versao 1.3.3, `contract_hash 8b9600f5274d7dffb6e5bd5f`, python runtime `ready`; add-in em `%APPDATA%\Autodesk\Revit\Addins\2027\Horizun\Horizun.Revit.dll` sha256 `3f70b2d5929d345573e039f47858b3d51b23a82ccf67cb03d0ab0116671a7218`.
- `C:\Users\slvma\.horizun\settings.json`: `permission_profile=full_write`, `execute_python_ui_granted=true`.
- Duas rotas tipadas vivas na sessao do app: `horizun_revit` (80 ferramentas) e `revitcortex` (~290).
- O dialogo Security (NotSigned) foi resolvido pelo dono com Always Load (anotacao dele: "pronto").

## Bloqueio novo, com evidencia

- `horizun_document_session{operation:"save", dry_run:true}` foi RECUSADO pelo revisor automatico do app: `Automatic approval review failed: Provider error 400 ... "This response_format type is unavailable now" ... invalid_request_error`. E o mesmo defeito que recusou `git add` nesta sessao.
- Consequencia: LEITURA funciona; QUALQUER ESCRITA no Revit esta bloqueada enquanto o revisor automatico falhar. Nao e fail-closed de politica, e falha de infraestrutura do revisor. Nao tentar caminho indireto para o mesmo efeito.
- ACL: `C:\Users\slvma\.horizun` concede `Modify` a `CodexSandboxUsers` e ao SID do perfil, mas o arquivo `discovery\revit-2027-30736.json` nao herda (`Get-Acl` e `Get-Content` negam). Por isso o `McpProbeTransport` (transporte do projeto) responde "no Revit is reachable" mesmo com o add-in saudavel: o caminho tipado do projeto esta BLOCKED por ACL do sandbox, nao por Revit.
- `gh auth status`: token INVALIDO para `matheussilva421`. O push exige `gh auth login` do dono.

## Mapa de escrita para P08-T08

- `src/amanda_agent/bim/providers/horizun.py:38-39`: `revit.create_toposolid` e `revit.create_mass` apontam para `horizun_execute_python`.
- Estagios R01-R04: `plan_project_initialization`, `plan_site_stage`, `plan_levels_stage`, `plan_massing_stage` em `src/amanda_agent/bim/stages/`. A cadeia R01-R13 inteira esta montada em `src/amanda_agent/bim/lab_fixture.py:201+` (`build_lab_fixture_plans`), ainda com um bloco sintetico 8x4.
- `docs/superpowers/plans/08-amanda-production-run.md:136-145` (Task 8): RVT candidato separado por finalista, modo `CONCEPT_ONLY` (R01-R04), verificar metricas contra o solution JSON, exportar preview, salvar/fechar/reabrir, registrar ferramentas/fallbacks, recusar R05-R16 e liberar o lease.
- Numeros medidos no finalista F01 (`design-engine/runs/AMANDA-RUN-001/finalists/AMANDA-RUN-001-F01/solution.json`): 6 blocos somando 626,0 m2, footprint bruto 779,26 m2, externos 260,0 m2, 1 pavimento, fator 0,8033. Batem com o programa fixo.
- Caminho permitido para o RVT candidato (sem token protegido): `revit/production/candidates/AMANDA-RUN-001-F01/`.

## Acoes humanas pendentes

1. Reautorizar escrita no Revit (permitir edicao para as ferramentas `horizun_*`) ou reparar o revisor automatico. Sem isso nenhum RVT candidato pode ser criado, salvo ou exportado.
2. `gh auth login -h github.com` (token invalido) e depois `git add -A` + commit + push. Ha 9 modificados e cerca de 25 novos nao commitados.
3. Opcional: dar heranca/ACL de leitura em `C:\Users\slvma\.horizun\discovery\revit-2027-30736.json` para `CodexSandboxUsers`, para o caminho tipado do projeto voltar a falar com o Revit.

## Estado e limites

- Subagente LUNA XHIGH (agent_type `luna`, `gpt-5.6-luna` em esforco xhigh) concluiu a auditoria de planos: `docs/notes/2026-09-15-o-que-falta-simples-v5.md` (retrato simples com tabela de 17 itens) e `docs/notes/2026-09-15-luna-v5-plan-analysis-handoff.md`. A V4 ficou marcada como SUPERSEDED. Conclusao confirmada por leitura independente do grafo: `P06-T14` depende de `P06-T15` (`state/task-graph.yaml:1980-1981`) e `P08-T08` depende so de `P08-T07` (`state/task-graph.yaml:2408-2409`), portanto o ensaio de laboratorio nao bloqueia o inicio da obra real.
- Limpeza final: segunda passada do `scripts/cleanup-local.ps1 -Apply` removeu os 9 `__pycache__` recriados pelas execucoes desta sessao; `remaining scratch=0 pycache=0`.
- Maiores pastas restantes e por que ficam: `.dotnet` 770 MB (SDK 10.0.401 que publica o plugin C# do revitcortex para o Revit 2027, usado por `tool-lab/revitcortex/deploy-revitcortex-2027.ps1`), `.venv-environmental` 451 MB (tool-lab/environmental), `.venv` 442 MB, `.venv-topologic` 376 MB (exigido por `tests/unit/test_topologic_spike.py`), `vendor/` 354 MB, `tool-lab` 172 MB (evidencias), `revit` 100 MB (laboratorios, preservado por contrato do script). Nada disso e lixo; e o custo de reconstrucao que decide.
- Limpeza: `scripts/cleanup-local.ps1 -Apply` removeu `.pytest_cache` e 30 `__pycache__`; `remaining scratch=0 pycache=0`. `revit/lab`, `.venv*`, `vendor/`, `.dotnet/`, `docs`, `state` e arquivos rastreados intactos.
- `tool-lab/topologic/results/topologic-spike.json`: blob identico ao HEAD (`3890efa4638b14d49eed182dea0634da74db064a`); apenas metadado de arquivo mudou.
- NENHUMA escrita no Revit foi provada nesta sessao. Nenhum PASS novo foi promovido. P06-T14 e P08-T08 continuam PENDING.
- Proximo passo assim que a escrita for permitida: montar a cadeia R01-R04 do F01 (`CONCEPT_ONLY`), executar pela rota do app, verificar metricas contra o solution JSON, salvar/fechar/reabrir e liberar o lease.
