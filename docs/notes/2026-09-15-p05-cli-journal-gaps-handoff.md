# Handoff P05 — CLI BIM e journal de execução

Data: 2026-09-15 (America/Fortaleza). Worker: LUNA, implementação P05.

## Resumo

Foi fechado o subconjunto solicitado da auditoria de P05-T22/P05-T23:

- `bim plan --solution PATH` lê um plano serializado e materializa
  `BIM_PLAN.json` e `BIM_PLAN.md` no diretório do plano, sem abrir ou escrever
  Revit;
- `bim claim --plan PATH` reclama atomicamente a primeira operação READY e
  grava um evento `CLAIMED` em journal JSONL durável;
- `bim record-result --operation-id ID --evidence PATH` exige uma evidência
  regular, existente e não vazia, valida a integridade do plano reclamado e
  acrescenta um evento `VERIFIED` com `result_status=PASS` e hash da evidência;
- claims duplicados, resultados sem claim, resultado duplicado e caminhos de
  evidência inválidos são recusados;
- o relatório `tool-lab/reports/bim-compiler-e2e.md` está rotulado como E2E
  sintético e declara explicitamente que nenhuma execução real em Revit ocorreu.

O journal é append-only: cada transição acrescenta uma linha, usa flush/fsync e
um lock de arquivo para que a seleção do próximo READY e o append sejam uma
operação protegida. O ID de operação é o `task_id` estável do plano.

## Arquivos deste write set

Criados:

- `src/amanda_agent/bim/journal.py`
- `tests/unit/test_bim_cli_journal_contract.py`
- `tool-lab/reports/bim-compiler-e2e.md`
- este handoff

Alterado:

- `src/amanda_agent/commands/bim.py`

Não foi necessário alterar `src/amanda_agent/cli.py`: o `bim_app` já estava
registrado na aplicação raiz e os comandos novos ficam disponíveis por essa
mesma instância Typer.

## Contrato persistido

O evento de claim registra `operation_id`, `task_id`, `logical_id`,
`plan_path`, `plan_sha256`, `input_hashes`, `checkpoint_hash`, `document_hash`,
`lease_token`, `provider_version`, `schema_version`, `tool_schema_hash`,
`provider_schema_versions`, `dependencies`, `intended_delta` e `verifier`.

O evento de resultado preserva esses campos, acrescenta `evidence_path`,
`evidence_sha256`, `evidence_bytes`, `independent_evidence=true` e transiciona
o estado para `VERIFIED`/`PASS`. A localização padrão é
`BIM_EXECUTION_JOURNAL.jsonl` ao lado do `BIM_PLAN.json`; `record-result`
procura esse journal no diretório da evidência e no diretório de invocação.

## TDD e validação

RED confirmado antes de implementar:

```text
./.venv/Scripts/python.exe -m pytest tests/unit/test_bim_cli_journal_contract.py -q --basetemp=.tmp-luna-p05-journal-red -p no:cacheprovider
6 executados; 0 passaram; 6 falharam pelo motivo esperado: markdown/journal/comandos/relatório ausentes.
```

GREEN focado após a implementação:

```text
./.venv/Scripts/python.exe -m pytest tests/unit/test_bim_cli_journal_contract.py -q --basetemp=.tmp-luna-p05-journal-green2 -p no:cacheprovider
6 executados; 6 passaram; 0 falharam.
```

Gate dos testes BIM diretamente impactados:

```text
./.venv/Scripts/python.exe -m pytest tests/unit/test_bim_cli_journal_contract.py tests/unit/test_bim_cli.py tests/unit/test_bim_plan.py -q --basetemp=.tmp-luna-p05-journal-focused2 -p no:cacheprovider
20 executados; 20 passaram; 0 falharam.
```

Checagem estática:

```text
./.venv/Scripts/python.exe -m ruff check src/amanda_agent/commands/bim.py src/amanda_agent/bim/journal.py tests/unit/test_bim_cli_journal_contract.py
exit 0 — All checks passed.
```

Verificações manuais read-only:

- `./.venv/Scripts/python.exe -m amanda_agent.cli bim --help` mostrou `plan`,
  `verify-plan`, `status`, `claim`, `record-result` e `execute`;
- `./.venv/Scripts/python.exe -m amanda_agent.cli bim claim --help` mostrou a
  opção obrigatória `--plan`;
- `git diff --check -- src/amanda_agent/commands/bim.py` terminou com exit 0.

Não houve Revit, instalação de dependência, serviço pago, suíte ampla, nem
alteração em `scripts/**`, `state/**`, `PROJECT_STATE.yaml`,
`tests/unit/test_bim_release_drill.py` ou
`tests/unit/test_bim_lab_drill_preflight.py`.

## Pendências deliberadas

O plano P05 exige escopo maior que o subconjunto autorizado. Permanecem
pendentes e não devem ser inferidos como PASS:

- seleção detalhada/delegada, invalidação de hash de inputs e rejeição explícita
  de alvos GOLDEN/source, em
  `docs/superpowers/plans/05-bim-compiler.md:385-388`;
- casos de resultado para modelo/hash errado, ordem inválida, interrupção,
  transação host pendente, lease expirado e reconciliação `IN_DOUBT`, em
  `docs/superpowers/plans/05-bim-compiler.md:390-391`;
- execução sintética completa R01→R13, fallback realmente injetado,
  save/close/restart/reopen, requery e QA, em
  `docs/superpowers/plans/05-bim-compiler.md:396-409`.

O código implementado cobre a persistência/hash do plano, lease, ordenação,
idempotência básica e integridade do artefato de evidência. Não transforma um
JSON em chamada MCP e não declara prova física do Revit.

## Git e retomada

O worker foi instruído a não executar `git add`, `git commit` ou `git push`,
portanto não há commit SHA novo. O branch observado é `main`; existem várias
alterações e arquivos de outros workers no working tree e todos foram
preservados.

Para retomar, ler este handoff, confirmar o write set, revisar o contrato ainda
pendente nas linhas acima e só então ampliar testes/implementação com uma nova
autorização de escopo. O próximo passo seguro é uma revisão do journal contra
os casos de stale plan/lease e `IN_DOUBT`, seguida de teste isolado; a execução
Revit continua fora deste worker.
