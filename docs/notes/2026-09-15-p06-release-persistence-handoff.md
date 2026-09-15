# Handoff P06 release, persistence e visual QA

Data: 2026-09-15
Agente: Tyrion
Status: implementação local concluída; P06-T14 não executada.

## Escopo concluído

P06-T10: coordenador de persistência tipado com dez passos obrigatórios,
ordem verificável, estados por passo, persistência JSON determinística,
redaction de evidência, hash de arquivo fechado e obrigação de revalidação
quando um save posterior altera bytes.

P06-T11: manifesto de release com perfil STUDY ou FINAL, checks obrigatórios e
opcionais, artefatos, hashes, exports, proveniência, mapa source-to-export e
verificação real de tamanho/hash sem auto-hash recursivo do manifesto.

P06-T12: promotor GOLDEN fail-closed. QA, checks mandatory, persistência,
exports, reports, hashes, perfil e marker são verificados antes de publicar.
Staging usa diretório novo e os.rename sem overwrite; staging interrompido
permanece fora do namespace GOLDEN.

P06-T13: grupos Typer qa, export e release registrados no CLI preservando bim.
qa escreve JSON e Markdown e relata módulos QA ausentes como BLOCKED; export
plan é somente leitura; export verify e release verify retornam código de
falha quando a verificação falha.

P06-T15: coleta determinística de PNGs, saneamento raster para página vazia,
sinal de densidade de borda, classificação VISUAL_REVIEW e fila humana com os
caminhos exatos quando a inspeção de imagem não está disponível.

## Arquivos criados ou alterados por este write set

- src/amanda_agent/release/__init__.py
- src/amanda_agent/release/manifest.py
- src/amanda_agent/release/promote.py
- src/amanda_agent/qa/persistence.py
- src/amanda_agent/qa/visual.py
- src/amanda_agent/commands/qa.py
- src/amanda_agent/commands/export.py
- src/amanda_agent/commands/release.py
- src/amanda_agent/cli.py
- tests/unit/test_persistence_plan.py
- tests/unit/test_release_manifest.py
- tests/unit/test_release_promotion.py
- tests/unit/test_release_cli.py
- tests/unit/test_visual_qa.py

Não foram editados qa/models.py, qa/program.py, qa/model.py, qa/warnings.py,
qa/architecture.py, qa/accessibility.py, qa/ifc.py, qa/pdf.py ou qa/dwg.py,
nem os testes correspondentes do outro agente. state/task-graph.yaml e
PROJECT_STATE.yaml também não foram alterados por este write set.

## TDD e validação

RED inicial:

- comando: pytest nos cinco arquivos P06
- resultado: 23 falharam pelas interfaces ausentes e grupos CLI não registrados;
  falha observada pelo motivo esperado antes da implementação.

GREEN focado:

- comando: pytest nos cinco arquivos P06
- resultado final: 23 passaram, 0 falharam.

Gates adicionais:

- pytest test_persistence_plan.py e test_release_manifest.py: 8 passaram.
- pytest test_release_promotion.py: 8 passaram.
- pytest test_release_cli.py: 4 passaram.
- pytest test_visual_qa.py: 3 passaram.
- pytest test_cli.py e test_bim_cli.py: 8 passaram.
- ruff check nos arquivos deste write set: passou.
- mypy nas 7 unidades de produção novas: passou sem issues.
- compileall das unidades novas e cli.py: exit 0.

Gate completo obrigatório:

- comando: pytest tests/unit tests/solver -q -p no:cacheprovider
  --basetemp=.tmp-pytest-tyrion-all-final2
- resultado: 607 passaram, 0 falharam.

Após alinhar a descoberta de releases com os namespaces GOLDEN aninhados,
repetição final:

- comando: pytest tests/unit tests/solver -q -p no:cacheprovider
  --basetemp=.tmp-pytest-tyrion-all-final3
- resultado: 607 passaram, 0 falharam.

Validação final no estado compartilhado atual:

- comando: pytest tests/unit/test_persistence_plan.py
  tests/unit/test_release_manifest.py tests/unit/test_release_promotion.py
  tests/unit/test_release_cli.py tests/unit/test_visual_qa.py -q
  -p no:cacheprovider --basetemp=.tmp-pytest-tyrion-q6-final
- resultado: 23 passaram, 0 falharam.
- comando: pytest tests/unit tests/solver -q -p no:cacheprovider
  --basetemp=.tmp-pytest-tyrion-all-final
- resultado: 607 passaram, 0 falharam.

CLI:

- python -m amanda_agent --help lista bim, qa, export e release.
- python -m amanda_agent export plan --release-id RC01 terminou com exit 0,
  imprimiu o plano e o manifesto planejado sem criar arquivos.

Um primeiro gate completo teve 606 pass e uma falha em
test_open_scope_is_persisted_and_reloaded_without_a_bom durante os.replace do
arquivo temporário do próprio circuit breaker. O mesmo teste isolado passou
1/1 e a repetição completa passou 607/607; classificado como contensão ou
permissão ambiental preexistente, fora do write set.

## GitHub e integridade

Branch observada: main. No fechamento, HEAD e origin/main estão em a15518f;
esse avanço pertence ao estado compartilhado e não foi produzido por este
write set. Nenhum git add, commit, push, avanço de tarefa ou alteração de state
foi feito por Tyrion, conforme instrução do dono. O checkout continua com
alterações/untracked de outros agentes, inclusive PROJECT_STATE.yaml,
state/task-graph.yaml e módulos QA fora deste write set; eles foram
preservados e não foram incluídos neste trabalho.
Não foram adicionados segredos, credenciais, APS/Forge ou dependências pagas.

## Limitações e retomada

- Não houve execução Revit real, cold reopen físico, provider health real,
  export IFC/PDF/DWG real ou promoção de um GOLDEN do projeto.
- P06-T14 foi explicitamente deixada para o agente principal.
- A CLI QA não inventa evidência: manifestos sem checks explícitos permanecem
  BLOCKED mesmo com os módulos QA presentes.
- A revisão visual é saneamento de máquina e fila humana; não é prova
  normativa ou aceite arquitetônico.

Para retomar, verificar primeiro git status e este handoff, depois executar o
drill P06-T14 em ambiente sintético coordenado pelo agente principal. Não
alterar os arquivos do outro agente; qualquer correção posterior deve gerar
novo release e repetir hashes, exports, reports e verificação de persistência.
