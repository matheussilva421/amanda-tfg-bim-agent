# R04 — Pacote final para orientação (2026-09-28)

## Objetivo da entrega

Entregar de forma autocontida o estudo de implantação e partido arquitetônico do RUN-003 (etapa R04) para apresentação à orientadora, sem depender de R05 e sem alterar a geometria canônica aceita em P6. O pacote reúne prancha, vistas, imagens, modelos Revit, relatórios, manifesto e evidências de verificação.

## Base autorizada e hashes

- RUN: `AMANDA-RUN-003-PAVILION-CANONICAL-4B1275558A6C`.
- Checkpoint de origem (P6, não editado): `revit/production/evidence/AMANDA-RUN-003-R04/P6-T01-CANON-011-RECONCILED-20260926.rvt`, SHA-256 `8d8166b8da9d572c445619457e302f868ca2c7bac1cfce83b1b6114d02559326`, 4.960.256 bytes.
- Derivado de apresentação salvo: `AMANDA-RUN-003-R04-PRESENTATION-20260928.rvt`, SHA-256 `bf5f05050679191a0bf2ce4b731441aa20306dd36cfe426a3f2f37c33c42121a`, 5.013.504 bytes.
- Checkpoint final da apresentação: `AMANDA-RUN-003-R04-PRESENTATION-FINAL-ORIENTADORA.rvt` — cópia byte a byte do derivado salvo, mesmo SHA-256.

## Verificação de geometria (SAVE → CLOSE → REOPEN)

- Antes das alterações de apresentação: leitura tipada dos 25 elementos espaciais — 7 massas, 14 pisos, 4 coberturas; fingerprint `1aac5d79b05b159a`.
- Depois de salvar, fechar e reabrir com auditoria (Revit 2027, sem upgrade): leitura tipada dos mesmos 25 elementos, mesmo fingerprint `1aac5d79b05b159a`.
- Comparação campo a campo (ElementId, UniqueId, categoria, nome e caixas delimitadoras mín./máx. com tolerância de 1e-8 m): **25/25 presentes, GEOMETRY_DIFFERENCES = 0**.
- Evidências: `06_EVIDENCIAS/geometry-readback/pre-baseline-25-elements.json`, `06_EVIDENCIAS/geometry-readback/post-readback-after-reopen.json` e `06_EVIDENCIAS/geometry-readback/geometry-comparison.json`.

## Vistas geradas

| Arquivo | ViewId | Conteúdo |
| --- | --- | --- |
| R04-VIEW-01-IMPLANTACAO-GERAL.pdf | 331218 | Planta de implantação com setores A–M coloridos e identificados |
| R04-VIEW-02-ISOMETRICA-GERAL.pdf | 331230 | Isométrica geral com rótulos discretos: administrativo, infantil, residencial, serviços/capacitação |
| R04-VIEW-03-RESIDENCIAL.pdf | 331241 | Quatro pavilhões identificados (A, B, C e D — pavilhão comunitário) |
| R04-VIEW-04-ADMINISTRATIVO.pdf | 331252 | Volume administrativo com rótulo “2 pavimentos (térreo + superior)” |
| R04-VIEW-05-SERVICOS-CAPACITACAO.pdf | 331283 | Composição curva em torno do pátio |
| R04-VIEW-06-INFANTIL-PLAYGROUND.pdf | 331571 | Massa infantil e playground na mesma vista, com rótulos |
| R04-VIEW-07-ADMIN-SECAO.pdf | 331581 | Corte do administrativo com “Nível 1 (térreo)” e “Nível 2 (superior)” (vista complementar) |

As seis vistas exigidas estão em 01–06; a 07 é a vista complementar de corte prevista no escopo do administrativo. Cada vista também foi exportada em PNG (`03_IMAGENS_PNG/`), além da prancha.

## Prancha

- Folha `R04-01` (elemento 331392), A1 horizontal (841 × 594 mm), viewport da planta na escala 1:300.
- Layout reorganizado: prancha maior à esquerda, título no topo, programa oficial e ressalvas, e coluna de setores/organização à direita.
- Textos mantidos: “PROGRAMA OFICIAL”, “20 pessoas”, “626 m² internos úteis”, “260 m² externos programados”, as duas ressalvas de estudo e a nota de que o norte verdadeiro não está verificado.
- Setores A–M permanecem identificados na planta; as massas e pisos receberam diferenciação de cor por setor em nível de vista (sem alterar geometria).

## Correção do Pavilhão D

- Antes: “F Residencial D — dormitório comunitário” e “Residencial: 4 pavilhões; 3 dormitórios/família + 1 comunitário.”
- Depois (contrato canônico): “F — Residencial D — pavilhão comunitário: convivência, refeitório e copa” e “Residencial: 3 pavilhões de dormitórios/família + 1 pavilhão comunitário.”
- As descrições dos pavilhões A, B e C também foram alinhadas ao contrato (dormitórios; dormitórios/família; dormitórios acessíveis/mistos). O programa oficial não foi alterado.

## Substituição do carimbo

- O title block genérico Autodesk foi removido da folha (delete tipado verificado, com 9 elementos em cascata), eliminando “Consultor”, “Endereço”, “Fax”, “Proprietário” e campos repetidos vazios.
- Foi desenhado na folha um carimbo acadêmico simples com: TFG, nome do projeto, “Aluno(a): Amanda”, prancha, etapa, data 28/09/2026, escala 1:300 (implantação), número R04-01, moldura A1 e divisórias.
- Não foram inventados instituição, orientadora, matrícula, endereço ou disciplina.

## Limitações atuais

- Estudo volumétrico e de implantação: compartimentação interna, esquadrias, mobiliário, materiais e detalhamento seguem em desenvolvimento.
- Implantação em referência local normalizada: sem levantamento cadastral ou topográfico definitivo e sem norte verdadeiro verificado.
- O pacote não declara: levantamento cadastral validado, topografia validada, norte verdadeiro validado, projeto final, aprovação da orientadora ou R05 concluído.
- Os manifestos brutos do Horizun em `06_EVIDENCIAS/manifests/` registram caminhos absolutos da máquina de autoria (evidência original); os caminhos do pacote (README e manifesto) são relativos e funcionam em qualquer pasta.

## Estado do projeto

- P7-T01/R05: não iniciado nesta entrega; permanece separado e sujeito ao seu próprio gate (bloqueio de transporte do runner registrado no repositório).
- R06: não iniciado.
- RC01: intocado. GeoNatal: não pesquisado. S01/S02/R12: não reutilizados.

## Conteúdo do pacote

```
AMANDA-TFG-R04-ORIENTADORA-20260928/
  LEIA-ME-ORIENTADORA.md
  SHA256SUMS.txt
  RUN003-R04-ORIENTADORA-MANIFEST.json
  01_PRANCHA/R04-01-PRANCHA-A1.pdf
  02_VISTAS_PDF/ (7 PDFs)
  03_IMAGENS_PNG/ (8 PNGs)
  04_REVIT/ (checkpoint P6, derivado editável, checkpoint final)
  05_RELATORIOS/ (este relatório, closeout e handoff)
  06_EVIDENCIAS/ (manifestos, readback de geometria, hashes, notas de construção)
```

## SHA-256 do ZIP

O hash do próprio arquivo ZIP é registrado em `AMANDA-TFG-R04-ORIENTADORA-20260928.zip.sha256`, ao lado do ZIP, e na cópia deste relatório no repositório (`docs/reports/R04-orientadora-final-package-2026-09-28.md`). Um arquivo ZIP não pode conter o hash de si mesmo; por isso o valor não aparece nesta cópia interna.


SHA-256 do ZIP entregue: bcc00f88ea6db7f7b940445e1a2be6afbb60fd8f9e7bd35fe68975732ae2c83a (arquivo AMANDA-TFG-R04-ORIENTADORA-20260928.zip, 16604517 bytes).
