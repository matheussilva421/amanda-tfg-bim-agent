# Handoff P04-T20 — 2026-09-15

## Resumo

Spike TopologicPy executável concluído em ambiente isolado. O contorno retangular de 6 m × 4 m foi convertido em uma célula 3D de 3 m de altura; área, volume, topologia, grafo de adjacência e exports foram medidos no runtime real.

## Arquivos e artefatos

- `.venv-topologic/`: ambiente isolado criado a partir do Python 3.12.14 do projeto.
- `tool-lab/topologic/spike.py`: script executável, fora do caminho de importação do core.
- `tool-lab/topologic/requirements-lock.txt`: 31 distribuições pinadas.
- `tool-lab/topologic/README.md`: instalação, evidências, comparação e veredito.
- `tool-lab/topologic/results/topologic-spike.json`: relatório real; timestamp `2026-09-15T16:51:35Z`.
- `tool-lab/topologic/results/space.obj`: export real, 557 bytes, 12 vértices e 20 faces.
- `tool-lab/topologic/results/space.mtl`: sidecar criado pelo exportador; o OBJ referencia `example.mtl`, que não existe (`PARTIAL`).
- `tool-lab/topologic/results/space.topology.json`: export TopologicPy real, 33.059 bytes.
- `tests/unit/test_topologic_spike.py`: teste focado que executa o script com o interpretador isolado.

## Decisões técnicas

- `topologicpy==0.9.70` foi instalado após disponibilidade observada no índice.
- O primeiro runtime falhou porque `topologic_core` não era dependência declarada/instalada. `topologic_core==8.0.4` foi consultado e instalado separadamente; depois os construtores passaram.
- O spike mede `Face.Area` = `24.0 m²` e `Cell.Volume` = `72.0 m³`, com `base_wire_closed=true`.
- A célula tem 12 vértices, 30 arestas e 20 faces; o grafo do contorno tem 4 vértices e 4 arestas.
- IFC está `NOT_ATTEMPTED`: a API encontrada documenta `.bim`/dotBIM, não uma escrita IFC validada.
- Veredito: `ADOTAR_COM_LIMITES`; manter opcional, pinado e fora do solver Shapely/NetworkX. Agenda: `DEFERRED_OPTIONAL`; core permanece `GO`.

## Validação

- `pytest tests/unit/test_topologic_spike.py -q -p no:cacheprovider --basetemp=".tmp-pytest-t20-final-mtl-0915"`: 1 executado, 1 aprovado, 0 falhas.
- `ruff check tool-lab/topologic/spike.py tests/unit/test_topologic_spike.py`: limpo.
- `pip check` no `.venv-topologic`: `No broken requirements found.`
- Comparação lock/metadata: `LOCK_MATCH True`, 31 entradas.
- Execução do script: `SCRIPT_EXIT=0`, relatório `PASS`.
- SHA-256 final: relatório `53FF65173B73DD3A76FAA6C75B3947EF6AF190CDB41C9634A2D79215D7945D33`; OBJ `073367146B8746DCE1DD5793549645A3CCA23B14AAFE4057FA5B3C7CD39C3FFF`; MTL `B5152B57D33BB9A75F76B85D5EE9F6D4568DADD38B9F60D485B4AA4FD25D15CD`; topology JSON `3B6F7416BB8B203C074F840E58471602DFEE7D67B71160C5ED37FDE9F6598F91`.

## GitHub e pendências

O working tree consultado estava `main...origin/main`; nenhuma operação `add`, `commit`, `push`, `checkout`, `stash` ou `reset` foi executada. O agente principal deve revisar os arquivos autorizados, fazer o commit e o push.

Pendências: atualizar o estado formal P04-T20 e seu handoff na localização canônica do projeto quando o agente principal puder fazê-lo; não foram alterados `state/task-graph.yaml` nem `docs/notes/` por restrição desta tarefa. Qualquer promoção futura deve testar contornos côncavos/reais, booleans, semântica de ambientes, round-trip e necessidade de IFC.

## Retomada

No diretório do projeto, usar o interpretador isolado:

```powershell
$env:PYTHONIOENCODING='utf-8'
& './.venv-topologic/Scripts/python.exe' 'tool-lab/topologic/spike.py'
```

Reexecutar somente o teste focado com um novo sufixo `--basetemp` e comparar o JSON gerado com os artefatos esperados. Não mover a implementação para `src/` nem adicionar TopologicPy às dependências do core sem decisão arquitetural.
