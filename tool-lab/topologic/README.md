# Spike TopologicPy — P04-T20

Status observado: **PASS** para o recorte executado, com dependência de runtime adicional. O spike é opcional e permanece fora do caminho de importação do solver em `src/amanda_agent`.

## Execução reproduzível

O ambiente isolado foi criado sem modificar `.venv`:

```powershell
$env:PYTHONIOENCODING='utf-8'
& './.venv/Scripts/python.exe' -m venv '.venv-topologic'
& './.venv-topologic/Scripts/python.exe' -m pip install 'topologicpy==0.9.70'
& './.venv-topologic/Scripts/python.exe' -m pip install 'topologic_core==8.0.4'
```

Disponibilidade medida antes das instalações:

```text
$env:PYTHONIOENCODING='utf-8'; & './.venv/Scripts/python.exe' -m pip index versions topologicpy
exit 0; topologicpy (0.9.70); Available versions included 0.9.70, 0.9.69, 0.9.68, ...
```

O backend necessário foi consultado antes de sua instalação:

```text
$env:PYTHONIOENCODING='utf-8'; & './.venv-topologic/Scripts/python.exe' -m pip index versions topologic_core
exit 0; topologic_core (8.0.4); Available versions: 8.0.4, 8.0.3, 8.0.1, 8.0.0, 7.0.1, 7.0.0
```

O primeiro teste de geometria, antes de instalar `topologic_core`, falhou com `ModuleNotFoundError` para `topologic_core` e também não encontrou `pythonocc-core`. Após instalar `topologic_core==8.0.4`, os construtores passaram. Isso é uma limitação de empacotamento/runtime: `topologicpy==0.9.70` não declarou `topologic_core` em `pip show Requires`.

O lock completo da instalação está em [requirements-lock.txt](requirements-lock.txt). A verificação final do ambiente retornou `pip check` com `No broken requirements found.`. A licença reportada pelo metadata de TopologicPy é **GNU Lesser General Public License v3**; o metadata de `topologic_core` não forneceu licença.

Execute o spike com:

```powershell
$env:PYTHONIOENCODING='utf-8'
& './.venv-topologic/Scripts/python.exe' 'tool-lab/topologic/spike.py'
```

## O que foi executado

`spike.py` constrói um compartimento retangular a partir do contorno 2D em metros `[(0,0), (6,0), (6,4), (0,4)]`. Ele cria `Wire`, `Face` e uma `Cell` entre o wire inferior e o superior a 3 m; mede a face com `Face.Area` e o sólido com `Cell.Volume`. Também cria um grafo TopologicPy de adjacência do contorno com quatro vértices e quatro arestas.

Na execução registrada em [topologic-spike.json](results/topologic-spike.json), a área foi **24.0 m²**, o volume **72.0 m³**, o wire foi fechado, a célula teve **12 vértices, 30 arestas e 20 faces**, e o grafo formou um ciclo de **4 vértices/4 arestas**. O exportador OBJ produziu vértices e faces reais; o exportador de JSON TopologicPy também produziu um arquivo válido:

- [space.obj](results/space.obj)
- [space.mtl](results/space.mtl) (sidecar criado pelo exportador)
- [space.topology.json](results/space.topology.json)

O arquivo OBJ contém geometria válida (12 registros de vértice e 20 de face), mas o exportador escreveu `space.mtl` e deixou `mtllib example.mtl` no OBJ; `example.mtl` não existe no diretório. Por isso o relatório marca o export geométrico como `PASS` e o vínculo do material como `PARTIAL`. Não foi criado um arquivo manual para encobrir essa falha do exportador.

IFC ficou `NOT_ATTEMPTED`. A API encontrada no release é `Topology.ExportToBIM`, documentada para `.bim`/dotBIM, e não foi usada como evidência de IFC.

## Veredito e comparação

TopologicPy faz bem a construção de uma célula 3D nativa a partir de um contorno, a medição de área/volume e a exportação de uma malha OBJ. Isso demonstra capacidade 3D que não está presente na combinação atual de Shapely para verdade geométrica 2D e NetworkX para grafos do solver. O grafo TopologicPy também foi executado, mas este recorte não mede desempenho nem traz uma vantagem comprovada sobre NetworkX para rotas.

O custo é relevante: a instalação isolada trouxe NumPy, SciPy, Pandas, Plotly, Jupyter/nbformat, Requests e outros pacotes, além do backend binário separado `topologic_core`. A integração inicial falhou até que o backend fosse instalado manualmente. O recorte só cobre um retângulo; não comprova booleans, contornos côncavos, precisão em geometrias reais, semântica de ambientes ou IFC.

A rota existente em `C:\Users\slvma\Downloads\Github\Planta` resolve outra parte do problema: fonte PDF/JSON, cena editável no Blender, materiais/mobiliário, exportação GLB e viewer web no Chrome. Ela tem um fluxo visual e de navegador que este spike não fornece. TopologicPy pode complementar a preparação/validação 3D, enquanto Blender/GLB continua sendo a rota adequada para apresentação e walkthrough.

**Recomendação: ADOTAR_COM_LIMITES.** Manter TopologicPy como adaptador opcional, isolado e pinado, para casos que precisem de célula 3D, volume ou OBJ. Manter o solver principal em Shapely/NetworkX, sem adicionar a dependência ao core. A decisão de agenda permanece `DEFERRED_OPTIONAL`; o engine core continua `GO`.
