# P02-T18 — drill de crash/recovery

Data: 2026-09-15

## Veredito

`PASS_WITH_WARNINGS`: a mutação interrompida não foi salva nem marcada como
PASS, e uma instância própria nova recuperou o último checkpoint PASS e fez
health/read smoke. O aviso é operacional: o checkpoint já continha a parede
328658, portanto a tentativa interrompida criou uma parede sobreposta e o
Revit exibiu o diálogo de paredes sobrepostas; o diálogo foi aceito somente
na janela do PID próprio. O runner de recovery também registrou tentativas de
probe durante o aquecimento antes de obter `healthy`.

## Checkpoint e pré-condições

O checkpoint foi criado a partir de `revit/lab/custom-api/LAB_CUSTOM_WALL.rvt`
aprovado pelo T16, com `CheckpointManager`, estado `STABLE`, fonte estável e
reopen verification:

- `revit/lab/custom-api/T18_LAST_PASS.rvt`
- SHA-256: `8CCAB171E89FA4AC414F9CA3C57B5C4161CD7EE6DD61F45F86529703EE281CB2`
- tamanho: `4.370.432` bytes
- manifest:
  `revit/lab/custom-api/T18_LAST_PASS.rvt.manifest.json`
- manifest SHA-256:
  `A0A5AB6931A57C98B34614B1763DB2686BEC320396D4CF578BE5F3A68E9DE707`

O baseline `revit/lab/baseline/LAB_R00_EMPTY.rvt` permaneceu com SHA-256
`15E0F70DF13A9AD0635A7651B3FEDFF59E76DCFE582C25A7EA759A4B0698299D` antes e
depois.

## Crash controlado

O runner `.tmp-t18-crash-run.ps1` iniciou o Revit 2027 em
`T18_CRASH_WORK.rvt`, uma cópia do checkpoint, com o host isolado na pasta de
add-ins do usuário. O job foi escrito depois de iniciar o processo e contém o
mesmo token herdado por `AMANDA_LAB_HOST_TOKEN`.

- PID próprio: `16556`
- StartTime: `2026-09-15T15:56:48.5563207-03:00`
- `job.ExpectedPid`: `16556`
- SHA-256 do token registrado: `937F3A566F46B20F23DAD1B5779EBA1A6EB4DDF8E8EA4D2D10BDC82B3DCA8514`
- `work_rvt` ativo: caminho exato de `T18_CRASH_WORK.rvt`
- marcador de mutação: `step invoke-external-command: PASS`
- marcador de save: ausente
- resultado de host após o crash: ausente

O host alcançou `verify-geometry-in-session` e o journal registra uma
transação bem-sucedida em memória com `ElementId.Value=328659`, comprimento de
5 m e altura de 3 m. Isso é evidência da mutação interrompida, não evidência
de persistência. O PID só foi parado depois de provar igualdade entre o
`StartTime` observado e o StartTime capturado pelo runner.

Antes e depois do crash, o arquivo de trabalho permaneceu igual ao checkpoint:

```text
checkpoint = 8CCAB171E89FA4AC414F9CA3C57B5C4161CD7EE6DD61F45F86529703EE281CB2
work antes = 8CCAB171E89FA4AC414F9CA3C57B5C4161CD7EE6DD61F45F86529703EE281CB2
work depois = 8CCAB171E89FA4AC414F9CA3C57B5C4161CD7EE6DD61F45F86529703EE281CB2
```

## Recovery

O runner `.tmp-t18-recovery.ps1` iniciou uma segunda instância própria com o
checkpoint `T18_LAST_PASS.rvt`:

- novo PID: `28172`
- StartTime: `2026-09-15T16:02:44.8062098-03:00`
- Revit: `2027`, build `27.2.0.39`
- health: `healthy`
- perfil: `full_write`
- `mcp_paused`: `false`
- documento ativo: caminho exato de `T18_LAST_PASS.rvt`
- read smoke: `horizun_query_model` leu `ElementId=328658`
- cobertura: `matched=1`, `returned=1`, completa, `unreadable=0`
- resultado da mutação interrompida: continua ausente

O segundo PID também só foi parado após a prova de StartTime. O checkpoint
terminou com o mesmo SHA-256 e o baseline terminou intacto.

## Reconciliação e recuperação no código

O drill encontrou as proteções e o caminho de reconciliação no código:

- `src/amanda_agent/bim/checkpoints.py` cria cópia imutável, manifest e
  verifica identidade, caminho e hash antes de rollback/recovery.
- `src/amanda_agent/session/end.py` impede encerrar tarefa `RUNNING` sem
  suspensão/bloqueio e exige checkpoint para mutação BIM.
- `src/amanda_agent/maintenance/policy.py` exige regressão completa do
  provider antes de aceitar atualização.
- `src/amanda_agent/bim/diff.py` calcula diff determinístico entre estado
  desejado e atual.
- `src/amanda_agent/bim/plan.py` produz plano compensatório e regras de
  verificação.
- `src/amanda_agent/tools/circuit_breaker.py` persiste o estado de falha e
  exige probe independente para recuperação.

Os três primeiros arquivos são gates de checkpoint/sessão/manutenção; o diff
determinístico e o plano compensatório ficam nos módulos BIM adjacentes. Esses
arquivos foram somente lidos neste drill.

## Evidências e hashes

- `t18-drill-summary.json`: resumo estruturado; veredito `PASS_WITH_WARNINGS`.
- `t18-crash-run-log.txt`: 3.412 bytes,
  SHA-256 `DA781F2C6016206803281041AA72A858C0D2F392E7A3FCF8C6410C044B112AF6`.
- `t18-host-status.log`: 597 bytes,
  SHA-256 `0D831E0E5891079C09EB060D55B921511D92D29DFE212C1966C23A535DC654A3`.
- `t18-crash-host-revit-journal.txt`: 476.804 bytes,
  SHA-256 `8823E1CAFE13FDF1058D98F7713CDAC6FFD77FABBEC7CF2E0307DA914B1D6BD7`.
- `t18-recovery-run-log.txt`: 17.459 bytes,
  SHA-256 `230A7EFFAD22243399CB83A22F4CBAEA9E0310071C2AD65DDF7ED3D6D33B011C`.
- `t18-recovery-health.json`: 16.758 bytes,
  SHA-256 `F7662117A59198ECCBC2856D89A58724F5AF6C1E2AE06CE911F767E709D79073`.
- `t18-recovery-read.json`: 5.498 bytes,
  SHA-256 `EF222356CAFBAA9F888A7D7B5C553AA357FD5BFAAE65DFD158749D315627062D`.

Os add-ins compartilhados foram retirados durante cada execução e restaurados
com hash conferido. O baseline e o checkpoint também foram conferidos depois
da restauração. Não foi necessário login, UAC ou clique do dono.

## Comandos e validação

- `python .tmp-t18-checkpoint.py` → checkpoint criado e verificado.
- `& .\.tmp-t18-crash-run.ps1` → exit 0; crash controlado e invariantes PASS.
- `& .\.tmp-t18-recovery.ps1` → exit 0; recovery, health e read smoke PASS.
- `python -m pytest tool-lab/custom-api/test_custom_api_contract.py -q -p no:cacheprovider --basetemp=.tmp-pytest-t18-custom` → 3 passed, 0 failed.
- `PYTHONPATH=src python -m pytest tests/unit/test_checkpoints.py tests/unit/test_maintenance_policy.py tests/unit/test_session_end.py tests/unit/test_session_start.py -q -p no:cacheprovider --basetemp=.tmp-pytest-t18-core` → 32 passed, 0 failed.
- builds Release dos dois projetos → exit 0, 0 erros; somente avisos conhecidos `MSB3277`.
- parse dos runners PowerShell → PASS.

O provider usado foi o fallback local do Tool Lab; nenhuma licença ou
dependência assinada foi introduzida.
