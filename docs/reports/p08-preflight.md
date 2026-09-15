# P08 — Preflight de produção

Data: 2026-09-15. Este relatório registra evidência observada no checkout
compartilhado. O estado final continua separado entre `STUDY` e `FINAL`; a
presença de um provider saudável não é tratada como evidência de escopo de
produção.

| check | comando | resultado | PASS|FAIL|PENDENTE | impacto |
| --- | --- | --- | --- | --- |
| P08-T01 doctor | `PYTHONIOENCODING=utf-8; .\.venv\Scripts\python.exe -m amanda_agent doctor` | exit 0; Git 2.53.0, Codex 0.154.0-alpha.6.2, PowerShell 5.1.26100.9444, .NET 8.0.422 e Revit detectados; `python312` ausente no relatório de ambiente | PASS | ausência do Python 3.12 foi classificada como não crítica para este comando; não é evidência de runtime de produção |
| P08-T01 status | `PYTHONIOENCODING=utf-8; .\.venv\Scripts\python.exe -m amanda_agent status` | exit 0; `PHASE_02`, status `PENDING`, próximo `P06-T01`, revisão 123, último `P09-T10`, writer lease livre; 5 bloqueadores de site | PASS | o grafo compartilhado ainda aponta P06; P08 não foi avançado neste bloco |
| P08-T01 task graph | `PYTHONIOENCODING=utf-8; .\.venv\Scripts\python.exe -m amanda_agent task-graph` | exit 0; 159 tarefas: 110 `PASS`, 1 `PASS_WITH_WARNINGS`, 42 `PENDING`, 6 `SUSPENDED`; P08 com 0/19 concluídas | PENDENTE | preflight não autoriza declarar a fase de produção pronta |
| P08-T01 MCP | `codex mcp list` | exit 0; 7 servidores listados; variáveis sensíveis mascaradas pela própria ferramenta | PASS | inventário de transporte não substitui validação de escopo, escrita, salvamento e leitura independente |
| P08-T01 suíte não-Revit | `PYTHONIOENCODING=utf-8; .\.venv\Scripts\python.exe -m pytest tests -m "not revit and not slow" -q -p no:cacheprovider --basetemp=.tmp-pytest-arya-p8` | exit 0; 726 testes passaram, 0 falharam, em 22,94 s | PASS | suíte não-Revit e não-slow verde |
| P08-T01 build Revit | comparação de `state/revit-metadata.json` com `state/bim-environment.lock.yaml` | `fileVersion=27.2.0.39` = `selected_build=27.2.0.39`; `productVersion=20260716_1515(x64)` igual ao lock | PASS | build exato confirmado; nenhuma instalação foi alterada |
| P08-T01 testes Revit | `PYTHONIOENCODING=utf-8; .\.venv\Scripts\python.exe -m pytest tests -m revit --collect-only -q -p no:cacheprovider --basetemp=.tmp-pytest-arya-p8-revit-collect` | exit 1; 726 testes deselecionados e nenhum teste marcado `revit` coletado | PENDENTE | não houve validação física/runtime do Revit nesta rodada |
| P08-T01 capabilities | auditoria de `state/capabilities.yaml` e hashes dos refs de evidência | 11 operações `PASS`; 14/14 hashes de evidência conferem; 0 entradas com `evidence_scope=PRODUCTION` (todas `PROVIDER`) | FAIL | não há base para promover capability de provider/lab para produção |
| P08-T01 fallback | leitura dos toolmaps e registros de saúde de Horizun, RevitCortex e custom API | Horizun tem cobertura de transporte/sessão e registros de lab; Cortex não cobre toda a cadeia e custom API cobre apenas operações parciais | PENDENTE | não há rota de fallback testada para cada capability requerida; manter fail-closed |
| P08-T01 writer lease | teste de existência de `state/locks/revit-writer.lock` | arquivo ausente; `writer_lease=absent` | PASS | nenhum lease obsoleto observado |
| P08-T01 source-manifest | `PYTHONIOENCODING=utf-8; .\.venv\Scripts\python.exe scripts/verify_ingested_sources.py .` | exit 0; 23 documentos, 23 `MATCH`, 0 falhas | PASS | provenance dos sources permanece íntegra |
| P08-T01 source-manifest hash | `Get-FileHash -Algorithm SHA256 project/provenance/source-manifest.yaml` comparado ao registro de `source-versions.yaml` | actual e registrado `0419094976aa7840f6bb5afc069cef133df07b58b3f6ce102271741a56740686`; `match=True` | PASS | manifesto e versão do source set estão vinculados por hash |
| P08-T01 Git | `git status --short` e `git rev-parse HEAD` | snapshot real: 34 arquivos modificados, 485 não rastreados; HEAD `a15518fd5599038d4df230c612cfe4bfc1015ae7`; há trabalho não commitado de outros agentes e deste bloco | PENDENTE | o commit do bloco cabe ao agente principal; não declarar checkout limpo |
| P08-T02 ingest validate | `PYTHONIOENCODING=utf-8; .\.venv\Scripts\python.exe -m amanda_agent ingest --validate-only` | exit 0; relatório `docs/reports/ingest-report.md`; `GO_WITH_LIMITATIONS` | PASS | fontes válidas para estudo; limitações e lacunas continuam registradas |
| P08-T02 source set | varredura de `TFG_Amanda_2026/**` e `docs/source/**` com comparação byte/hash | 46 arquivos inspecionados; 23 documentos do manifest; nenhum source novo; `source-set-v1` inalterado | PASS | não houve regeneração canônica porque o source set não mudou |
| P08-T02 PDF inputs | comparação de `TFG_Amanda_2026/**` e `docs/source/**` com o manifest | `programa_necessidades.pdf`: 31.004 bytes, hash `11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17`; TFG: 54.553.582 bytes, hash `16abe602ac50643482ce3c782780b4135fa8468b5ca814061fe426c8ca292a7e`; ambos source revision 1 | PASS | PDFs confirmados sem sobrescrever provenance |
| P08-T02 programa baseline | comparação de `project/requirements/program.json` com `SRC-PROGRAM-001` | PDF `programa_necessidades.pdf`, 20 pessoas, 626,0 m² úteis internos, 260,0 m² externos e 783–814 m² construídos; hash `11daa9efc4d1b022407d8bd02999e85b604a16539f29ae598dc45b339de14a17` | PASS | baseline escolhido em 2026-09-15 foi preservado; revisão do baseline não foi reaberta |
| P08-T03 site | inspeção somente de `project/site/**`, fontes da Amanda e `docs/source/**` | não há levantamento/topografia com datum, polígono cadastral, matrícula, pontos cotados ou arquivo georreferenciado; DXF/IFC estão nomeados como `HIPOTESE` | PASS_WITH_LIMITATIONS | resolução máxima é `PLANAR_PLACEHOLDER`; `SITE_TOPOGRAPHY` e `SITE_BOUNDARY` continuam bloqueadores finais |
| P08-T04 source principles/hypotheses | leitura e hash de `project/requirements/source-principles.yaml` e `design-hypotheses.yaml` | 5 fatos continuam `SOURCE_FACT` e 4 registros continuam hipóteses explicitamente não verificadas; arquivos foram revisados sem promoção indevida | PASS | design run permanece de estudo e source-backed |
| P08-T04 typology | registro `DEC-P08-T04-TYPOLOGY-001` em ambos os decision registers | decisão delegada, revisão Amanda pendente, `PROVISIONAL_ASSUMPTION`; tipologia: abrigo institucional temporário com interface pública controlada | PASS_WITH_LIMITATIONS | serve ao estudo; operação final, sigilo e programa executivo ainda exigem revisão humana |
| P08-T04 site boundary | registro `DEC-P08-T04-SITE-BOUNDARY-001` em ambos os decision registers | retângulo planar de 24.135 m² mantido como hipótese; decisão delegada, revisão Amanda pendente, `PROVISIONAL_ASSUMPTION`; decisão anterior preservada como `SUPERSEDED` | PASS_WITH_LIMITATIONS | não representa limite cadastral, disponibilidade do lote ou validação altimétrica |
| P08-T04 design engine tests | `PYTHONIOENCODING=utf-8; .\.venv\Scripts\python.exe -m pytest tests/solver tests/unit -q -p no:cacheprovider --basetemp=.tmp-pytest-arya-freeze` | exit 0; 607 testes passaram, 0 falharam, em 20,66 s | PASS | engine e contratos unitários verdes no commit congelado |
| P08-T04 freeze | `state/design-run-freeze.yaml` e hashes dos arquivos congelados | `P08-DESIGN-RUN-001`, `FROZEN_FOR_STUDY`; requirements `requirements-v1`, site `site-v1`, weights `1`, engine `design-engine-v1`, commit `a15518fd5599038d4df230c612cfe4bfc1015ae7` | PASS | inputs reproduzíveis para o estudo; freeze não promove o run a FINAL |

## Registro das fontes das decisões

As decisões estão registradas nos dois decision registers e vinculadas às
seguintes fontes, com versão/aplicabilidade explícitas:

| decisão | fonte e versão observada | aplicabilidade registrada |
| --- | --- | --- |
| `DEC-P08-T04-TYPOLOGY-001` | `SRC-TFG-001`, `source-set-v1`, revision 1, páginas 8–9 e 54–61; [Manual MDS](https://fnas.mds.gov.br/wp-content/uploads/2025/06/MANUAL-DE-ORIENTACOES-DE-PROJETOS-ARQUITETONICOS.pdf), publicação 2025-06; [serviço MDS](https://www.gov.br/mds/pt-br/acoes-e-programas/suas/unidades-de-atendimento/servico-de-acolhimento-para-mulheres-em-situacao-de-violencia), página consultada em 2026-09-15 | suporte ao estudo de abrigo institucional temporário com núcleo residencial protegido e interface pública controlada; revisão Amanda pendente; não é aprovação operacional FINAL |
| `DEC-P08-T04-SITE-BOUNDARY-001` | `SRC-TFG-001`, `source-set-v1`, revision 1, páginas 56–61; [GeoNatal](https://geomapas.natal.rn.gov.br/), camadas oficiais consultadas em 2026-09-15; [Plano Diretor LC 208/2022](https://www.natal.rn.gov.br/storage/app/media/semurb/legislacao/Plano_Diretor_LC_208_2022.pdf), versão publicada da LC 208/2022; [requerimento de limites SEMURB](https://www2.natal.rn.gov.br/semurb/paginas/File/Formularios/SEMURB-RequerimentoDGSIG.pdf), formulário consultado em 2026-09-15 | sustenta manter o retângulo de 24.135 m² como `STUDY` enquanto faltam polígono, datum e levantamento; não sustenta limite cadastral, disponibilidade, licenciamento ou validação FINAL |

## Veredito

`PENDENTE — STUDY FROZEN / PRODUCTION NO-GO`.

Os inputs do design engine estão congelados para estudo e as fontes canônicas
estão íntegras. O preflight não fecha produção porque não há evidência de
capability em escopo de produção, não há fallback completo por capability, não
houve teste Revit marcado/runtime e o checkout compartilhado está sujo por
trabalho pendente. Os bloqueadores de topografia, boundary e validações finais
permanecem ativos.
