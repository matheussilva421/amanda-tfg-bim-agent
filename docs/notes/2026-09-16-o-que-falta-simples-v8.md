# O que falta — versão simples (v8)

Data: 2026-09-16
Autor: subagente LUNA XHIGH "Einstein" (análise somente leitura), revisado pelo agente principal.
Público: Amanda / Matheus (não precisa saber programar).
Pergunta respondida: "analisar os planos e dizer de forma simples o que falta".

## Situação em uma linha

**85,5% pronto.** 159 tarefas no total: **136 concluídas**, 2 concluídas com ressalva,
**13 pendentes**, **8 suspensas de propósito** (opcionais), 0 falhadas.
Próxima tarefa: **P06-T14**.

Fonte: `state/task-graph.yaml` (contagem por `status:`), `state/status.md:9`, `PROJECT_STATE.yaml:8`.

## O que já está pronto

- Fases 00 a 05: **96 de 96** — base do programa, conexão com as ferramentas, leitura das fontes,
  motor que monta o projeto e o compilador que transforma o projeto em instruções para o Revit.
- Fase 06: **14 de 15** — só falta o ensaio completo de entrega.
- Fase 07A: **11 de 11** — regras de segurança e controle do que pode ser alterado.
- Fase 08 (a obra no Revit): **7 de 19**. Já foram testadas **144 tentativas de projeto**; restaram
  **2 opções válidas** (F01 e F02), já comparadas.
- Revit reconhecido: versão **2027, build 27.2.0.39**; add-in Horizun e RevitCortex saudáveis.
- Programa fixado: **20 pessoas**, **626 m² internos**, **260 m² externos**.

## O que falta, em 6 blocos

| Bloco | O que falta | Tarefas | Depende de |
|---|---|---:|---|
| 1. Ensaio de entrega | Testar salvar → fechar → reabrir → exportar → guardar cópia | 1 | Revit (ação da máquina) |
| 2. Continuidade | Confirmar que o trabalho volta certo numa sessão nova e após reiniciar | 2 | sessão nova do Codex (humano) |
| 3. Massas e arquivo de trabalho | Desenhar as 2 opções no Revit, escolher uma e criar o arquivo de trabalho | 3 | Revit |
| 4. Modelagem e documentação | Fazer R01 a R13: paredes, pisos, ambientes, acessibilidade, materiais e pranchas | 4 | arquivo de trabalho escolhido |
| 5. Qualidade e pacote final | Conferência geral, reabertura a frio, IFC/PDF/DWG, relatórios, pacote GOLDEN | 5 | modelo completo + exportações válidas |
| 6. Render e nuvem | Blender e APS (nuvem) — opcionais, suspensos de propósito | 6 | só se você pedir render/nuvem |

Observação importante: a preparação da Fase 08 foi feita em modo **STUDY** (estudo) e o próprio
pré-teste registrou **PRODUCTION NO-GO** — ou seja, o modo de produção ainda não está liberado
porque falta comprovar capacidades em uso real, falta teste de runtime marcado e o repositório
tem alterações não commitadas.

## O que ainda atrapalha (não é tarefa, é dado faltando)

- **Topografia, limite oficial do terreno e ocupação atual**: impedem a validação final; o projeto
  segue como cenário de estudo com premissa provisória.
- **Número de frentes e norte verdadeiro**: reduzem a confiança, mas não impedem o estudo.

## Lista exata das tarefas não concluídas

Pendentes (13): P06-T14, P08-T08, P08-T09, P08-T10, P08-T11, P08-T12, P08-T13, P08-T14, P08-T15,
P08-T16, P08-T17, P08-T18, P08-T19.

Suspensas de propósito (8): P07-T17, P07-T19, P09-T03, P09-T04, P09-T05, P09-T07, P09-T08, P09-T09.

- P06-T14 — ensaio de entrega. Destrava com o Revit.
- P07-T17 — retomada em sessão nova. Destrava com você abrindo uma sessão nova do Codex.
- P07-T19 — procedimento de reinício. Destrava com você, depois de reiniciar.
- P08-T08 — massas das opções no Revit. Destrava com o Revit.
- P08-T09 — escolher a solução. Destrava com o próprio agente (Amanda revisa depois).
- P08-T10 — criar o RVT de trabalho. Destrava com o Revit.
- P08-T11 — R01 a R04 no Revit. Destrava com o Revit.
- P08-T12 — R05 a R08 no Revit. Destrava com o Revit.
- P08-T13 — R09 a R12 no Revit. Destrava com o Revit.
- P08-T14 — R13 (pranchas e tabelas). Destrava com o Revit.
- P08-T15 — conferência geral (QA). Destrava com código local + modelo pronto.
- P08-T16 — candidato R15. Destrava com o Revit.
- P08-T17 — exportações IFC/PDF/DWG e validação. Destrava com o Revit.
- P08-T18 — virar GOLDEN (versão oficial). Destrava com código local, depois das provas acima.
- P08-T19 — pacote final. Destrava com código local, depois das exportações.
- P09-T03/T04/T05 — Blender. Só se você pedir renderização.
- P09-T07/T08/T09 — APS/nuvem. Só com autorização e necessidade concreta; **nada pago**.

## Porcentagem

**85,5%** = 136 tarefas PASS ÷ 159 tarefas. As 2 `PASS_WITH_WARNINGS` não foram contadas como PASS.

## Próximos 3 passos mais úteis

1. Rodar **P06-T14** (ensaio completo de entrega) — hoje está livre, não depende de ninguém.
2. Fechar **P07-T17 e P07-T19** numa sessão nova, com evidência real de retomada.
3. Refazer o pré-teste de produção em ambiente limpo e começar **P08-T08**, mantendo tudo como
   estudo até conseguirmos os dados do terreno.

## Nota de honestidade

Nada foi gasto ou comprado: nenhuma etapa paga (APS/nuvem) foi executada, todas estão suspensas.
A análise acima foi somente leitura; nenhum arquivo do projeto foi alterado por ela.

