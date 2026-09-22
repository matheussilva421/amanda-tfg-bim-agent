# Handoff — limpeza reversível de temporários de teste (2026-09-22)

## Ação concluída

Foram removidos somente diretórios `.tmp-pytest-*` regeneráveis e já encerrados,
após confirmar que não havia execução de pytest deste bloco em andamento. A
limpeza liberou aproximadamente 1.005.188.178 bytes:

- `.tmp-pytest-idempotency-full`: 335.063.738 bytes;
- `.tmp-pytest-qa-full`: 335.061.983 bytes;
- `.tmp-pytest-r06-full`: 335.062.457 bytes;
- `.tmp-pytest-project-qa`: 10.672 bytes;
- `.tmp-pytest-r06-focused`: 4.738 bytes;
- `.tmp-pytest-r06-type-green`: 612 bytes;
- `.tmp-pytest-r06-type-red`: 306 bytes;
- `.tmp-pytest-zy`: 3.690 bytes;
- `.tmp-pytest-zz`: 3.690 bytes.

Também já haviam sido removidos os seis diretórios temporários do gate R08
registrados no handoff live anterior. Permanecem apenas `.tmp-pytest-y5` a
`.tmp-pytest-y9`, que estão protegidos por ACL e não foram tocados.

## Proteções

Nenhum RVT, journal, checkpoint, fonte acadêmica, resultado STUDY, arquivo
GOLDEN ou script de diagnóstico foi removido. As exclusões ACL-visíveis em
`revit/lab/exports/p06t14/GOLDEN/RC01` continuam fora de qualquer ação.

## Git e retomada

Esta limpeza não alterou código nem o estado persistido de produção. O commit
anterior `64ec40b` permanece publicado em `origin/main`. A próxima ação técnica
continua sendo recuperar uma sessão Revit alcançável e repetir a prova
read-only do provider antes de qualquer escrita.

