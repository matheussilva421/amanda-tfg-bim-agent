# Handoff — crosswalk no caminho de produção e build medido (2026-09-16)

## Resumo

Completado o bloco de TDD que o subagente LUNA «Dalton» deixou em RED antes de morrer por limite de uso da conta. Agora o crosswalk semântico é lido pelo caminho de produção, as lacunas declaradas são nomeadas em vez de mascaradas, e o catálogo de capabilities usa o build medido do Revit.

## O que foi feito

1. `CapabilityRegistry.declared_gaps` — as lacunas do crosswalk (`registered_entry: null`) passam a viajar com o registry em vez de serem descartadas em silêncio.
2. `SemanticCrosswalk.apply` — agora também coleta as lacunas com sua nota, além de continuar ligando os nomes semânticos às entradas registradas.
3. `CapabilityRegistry.load_for_production(project_root)` — novo caminho de produção: lê `state/capabilities.yaml` + `state/providers/semantic-crosswalk.yaml`, cai para nomes de provider com aviso explícito quando o crosswalk não existe, e devolve as lacunas como warnings. Nunca inventa alias nem promove escopo de evidência.
4. `CapabilityRegistry.gap_note(operation)` — consulta da lacuna declarada.
5. `CapabilityRegistry.refusals` / `preferred` — operation sem entrada registrada mas com lacuna declarada agora levanta `SelectionRefused` citando «gap declarado no crosswalk», em vez de «no capability recorded».
6. `capability_is_selectable` — mesma nomeação para o portão de preflight.
7. `PreflightRequest.registry_warnings` + `PreflightRequest.from_production_state(project_root, ...)` — o pedido de preflight passa a carregar o registry de produção e seus avisos.
8. `bim status --project-root` — informa se o crosswalk foi carregado, quantas entradas o catálogo tem, os builds registrados e cada lacuna declarada.
9. `state/capabilities.yaml` — as 11 entradas passaram de `revit_build: 20260716_1515(x64)` (productVersion) para `27.2.0.39` (fileVersion medido, igual a `state/revit-metadata.json` e ao `selected_build` do lock). O custom-api ganhou a limitação explícita de que o `tool_schema_hash: sha256:local` não foi medido — o valor é local, não um contrato de provider.
10. Removida a definição duplicada de `load_with_crosswalk` e os campos duplicados de `CapabilityRegistry` no `capability.py`.

## Arquivos alterados

- `src/amanda_agent/models/capability.py`
- `src/amanda_agent/bim/stages/__init__.py`
- `src/amanda_agent/commands/bim.py`
- `state/capabilities.yaml`
- `tests/unit/test_bim_production_contract.py` (leitura do metadado com `utf-8-sig`, o encoding real do arquivo)

## Testes

Comando: `.venv\Scripts\python.exe -X utf8 -m pytest tests -q --ignore=tests/unit/test_topologic_spike.py`

Resultado: 822 testes executados, 822 passaram, 0 falharam. Status: verde.

Focados: `test_bim_production_contract.py`, `test_capability_registry.py`, `test_bim_cli_journal_contract.py` — 31 passed.

## Evidência ao vivo

`bim status --project-root .` agora responde: `semantic crosswalk: loaded`, `capability registry: 11 entries`, `recorded builds: 27.2.0.39`, e dois warnings nomeando as lacunas reais: `revit.create_grid` e `revit.create_roof`.

## Problemas encontrados

- O diretório `%TEMP%\pytest-of-slvma` ficou com ACL de dono antigo e não é removível sem administrador. Contornado rodando com `--basetemp` dentro do projeto. Não afeta o projeto.
- Um teste (`test_circuit_breaker.py::test_failed_half_open_probe_reopens_breaker`) é flaky por contenção de arquivo; passa isolado e na suíte com basetemp local.

## Pendências

- As lacunas `revit.create_grid` e `revit.create_roof` continuam recusando até terem entrada registrada com evidência — agora de forma nomeada.
- P06-T14 (ensaio de entrega) e P08-T08/T09 (concept finalistas) seguem abertos; dependem do escritor do Revit e das chamadas de escrita que o revisor automático vem recusando por erro interno do provedor dele.
- GitHub: `.git` com ACL que nega escrita no momento, então este bloco ainda não foi commitado.

## Instruções de retomada

1. Reverificar: `.venv\Scripts\python.exe -X utf8 -m pytest tests -q --ignore=tests/unit/test_topologic_spike.py` deve continuar 822 verdes.
2. Retomar P06-T14 pela ponte viva do Horizun (a rota stdio segue bloqueada por ACL do arquivo de discovery) ou seguir P08-T08/T09, que são independentes do provider.

