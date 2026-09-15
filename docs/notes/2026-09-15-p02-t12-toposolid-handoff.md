# Handoff — P02-T12 Horizun Toposolid/site test (+ toolmap proof wiring)

Data: 2026-09-15. Escopo: `docs/superpowers/plans/02-revit-tool-lab-providers.md` task 12. Estado: **PASS registrado no grafo**, commit preparado nesta linha de trabalho.

## O que foi feito

O plano pedia, para o site/toposolid: cópia fresca do baseline, invocar a capability mapeada **se disponível**, verificar bounding/extents/elevação por uma leitura independente, salvar/reabrir, e marcar PASS/DEGRADED/FAIL sem assumir suporte de produção a Toposolid.

A capability tipada não existe: `site_toposolid` é `NOT_AVAILABLE` no toolmap, porque nenhuma tool do contrato instalado cria superfície topográfica do zero. As 26 variantes de `horizun_create_elements` não têm kind de toposolid, e as três tools do contrato que mencionam toposolid (`horizun_embed_floors_in_toposolid`, `horizun_grade_toposolid_around_floors`, `horizun_execute_plan`) todas exigem um sólido que já existe. A condição «if available» do plano é falsa nesta máquina, e a ausência ficou documentada em vez de contornada por improviso.

Foi usada a **alternativa verificada já registrada**: `horizun_execute_python` chamando `Toposolid.Create(doc, IList[XYZ], ElementId typeId, ElementId levelId)`. O ensaio com `tx.RollBack()` provou a técnica antes de qualquer commit e não deixou nada atrás. A aplicação real commitou o elemento.

## Fixture e geometria

| Item | Valor |
| --- | --- |
| Fixture | `revit/lab/horizun/LAB_HORIZUN_TOPO.rvt` |
| Origem | cópia do GOLDEN `revit/lab/baseline/LAB_R00_EMPTY.rvt` |
| sha256 na cópia | `15e0f70df13a9ad0635a7651b3fedff59e76dcfe582c25a7ea759a4b0698299d` |
| bytes na cópia | 4366336 |
| Pontos sintéticos (m) | `[0,0,0.0] [20,0,0.5] [20,20,1.0] [0,20,0.5]` |

## Execução e verificação

- **Ensaio**: `rehearsal_created_id` 328666, `count_inside_tx` 1, `rollback_ok` true, `after_rollback_count` 0, `after_rollback_ids` [], `rollback_absent` true.
- **Aplicação commitada**: elemento **id 328673**, tipo 319144 «Genérico – 1000 mm», nível 311 «Nível 1», categoria «Sólido topográfico», **9/9 `verified_checks` ok**, `doc_is_modifiable_after` false, `before_count` 0.
- **Leitura independente tipada** (`horizun_query_model`, `cache_mode=bypass`, `coordinate_units=m`): 1 linha, `unique_id acc9a74d-20e8-4759-a946-2be18b798733-000503e1`, bbox min `[0, ~0, -1.0]` max `[20, 20, 1.0]` m — o ±1 m é a espessura de 1000 mm do tipo genérico, e os Z pedidos (0.0/0.5/1.0 m) caem dentro dele.
- **Segunda e terceira leituras**, nenhuma por id: `by_category` `matched_total` 1; `list_elements` `total` 1.
- **Persistência**: `save` `saved` true com mtime movido e bytes 4366336 → 4370432; sha256 `15e0f70d...299d` → `5a66bfa4c79036232503ada4842b60c53f45ad4b3aa23b0141013e843b2021a6`; `close` com `activate_other=true` fechou por identidade de objeto; `open` `opened_now` true, `upgraded` false; após reabrir o elemento 328673 volta com o mesmo `unique_id` e a mesma bbox.
- `result_set_fingerprint f19e5d8efdc2bb1a` igual antes e depois do ciclo; `warnings_total` 0 em todas as etapas; `transaction_left_open` false.

## Dois defeitos reais encontrados e corrigidos nesta task

1. **O emit do toolmap descartava os campos de prova.** `generate_toolmap.py` declarava `proven_alternative` (em `site_toposolid`) e `proven`/`proven_utc` (em `python`), mas `build()` só copiava campos nomeados explicitamente — então o YAML publicado nunca recebia nenhum dos três e `--check` ficava «verde» sobre um artefato incompleto. O teste novo falhou RED com `KeyError: 'proven_alternative'` e só então o emit foi corrigido.
2. **`independent_reads` estava `null` no artefato consolidado.** `.tmp-t12-consolidate.py` chamava `structured()` — que espera **um** envelope JSON-RPC — sobre `.tmp-t12-verify.json`, que guarda **três** envelopes rotulados. O unwrapping errado devolvia `null` silenciosamente, e o arquivo de evidência afirmava «li independentemente» sem conter nenhuma leitura. O unwrapping foi separado por rótulo (`structured_envelope`), as leituras foram refeitas registrando **pedido e resposta** lado a lado, e a bbox 0–20 m agora está no arquivo em vez de só na prosa.

## Arquivos criados/alterados

- `tool-lab/horizun/results/t12-toposolid.json` (novo, 33917 bytes) — `fixture`, `mapped_capability`, `rehearsal`, `apply`, `independent_reads` (com `tool`, `arguments` e `reply` por leitura) e `persistence`.
- `tool-lab/horizun/generate_toolmap.py` — `proven_alternative` em `site_toposolid`; `proven` + `proven_utc` em `python`; **emit corrigido** para os três campos.
- `state/providers/horizun-toolmap.yaml` — regenerado; `--check` imprime «toolmap is up to date».
- `tests/providers/test_toolmaps.py` — dois testes novos (abaixo).
- `state/task-graph.yaml`, `state/task-history.yaml`, `PROJECT_STATE.yaml` — `P02-T12` = `PASS`, próxima `P02-T13`, `state_revision` 79.
- `tool-lab/horizun/resource-dump.json` — **passou a ser rastreado** (ver abaixo).

## Testes executados

```
pytest tests/providers -q -p no:cacheprovider --basetemp=.tmp-pytest-prov-4
→ 11 passed, 0 failed

python tool-lab/horizun/generate_toolmap.py --check
→ toolmap is up to date
```

Os dois testes novos são `test_the_proven_toolmap_entries_record_their_host_evidence` (status NOT_AVAILABLE/PARTIAL, ponteiro para `horizun_execute_python` e `t12-toposolid.json`, e o payload do artefato) e `test_the_toposolid_task_meets_the_plan_geometry_and_independent_read` (os quatro pontos do plano, rollback do ensaio, contagens antes/depois, extents 0–20 m com tolerância, as três leituras independentes, e o ciclo save/reopen com hash e `unique_id` iguais).

## Gap que este trabalho expôs e fechou

**`resource-dump.json` não estava versionado.** Ele é lido por `tests/providers/test_toolmaps.py` (`RESOURCE_DUMP_PATH`) e citado como `contract_resource_capture` na proveniência do toolmap, mas nunca foi commitado. Prova: `git clone` local em `.tmp-clone-check2` → `pytest tests/providers` deu **5 failed, 4 passed** com `FileNotFoundError: .../tool-lab/horizun/resource-dump.json`. Não contém segredo: varredura de `sk-`, `ghp_`, `password`, `api_key`, `Bearer`, `slvma` e `C:\Users` deu 0 ocorrências; os 108 hits de «token» são todos o campo de schema `confirmation_token`.

## O que NÃO ficou provado (e não é afirmado)

- Um único elemento sintético. Sem grading nem embed contra terreno real, e o site data do projeto continua `MISSING`.
- Não existe kind tipado de criação para toposolid no contrato: a rota é Python, não tool tipada.
- Python é sempre `self_reported_verified` no bridge; a verificação de host veio das queries tipadas, nunca do auto-relato do script.
- Não se afirma suporte de produção a Toposolid.

## Próximo passo

`P02-T13` (clone/audit/build/deploy do RevitCortex). O plano exige **fechar o Revit normalmente** antes — o Revit 2027 está aberto com `LAB_HORIZUN_TOPO` e o fixture segue aberto ao fim desta task.

