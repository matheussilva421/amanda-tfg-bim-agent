# IFC e DWG para intercâmbio

Estes arquivos foram exportados do Revit 2027 para permitir intercâmbio com Revit 2026 e AutoCAD. Eles não são arquivos RVT salvos nativamente no formato 2026.

## Arquivos

- `AMANDA-RUN-003-R04-PRESENTATION-20260928.ifc` — modelo completo, IFC2x3 Coordination View 2.0.
- `AMANDA-RUN-003-R04-PRESENTATION-20260928-ISOMETRIA.dwg` — vista 3D `R04-02-ISOMETRICA-GERAL`, DWG 2013.
- `AMANDA-RUN-003-R04-PRESENTATION-FINAL-ORIENTADORA-20260928.ifc` — cópia byte a byte do IFC de apresentação; os RVTs de origem têm o mesmo SHA-256.
- `AMANDA-RUN-003-R04-PRESENTATION-FINAL-ORIENTADORA-20260928-ISOMETRIA.dwg` — cópia byte a byte do DWG de apresentação.
- `P6-T01-CANON-011-RECONCILED-20260926.ifc` — modelo completo, IFC2x3 Coordination View 2.0.
- `P6-T01-CANON-011-RECONCILED-20260926-ISOMETRIA.dwg` — vista 3D `P6-R04-RUN003-CANONICAL-ISOMETRIC`, DWG 2013.

Os arquivos `.pcp` são sidecars de plotagem gerados pelo Revit junto aos DWGs. O manifesto registra hashes, tamanhos, fontes e verificações.

## Integridade e validação

O Revit/Horizun confirmou os seis arquivos exportados. Os IFCs têm cabeçalho `IFC2X3`, 1.503 registros de entidades e marcador final STEP. Os DWGs têm assinatura `AC1027` (formato DWG 2013). Os três RVTs foram fechados sem salvar; o Revit confirmou zero alterações pendentes e bytes em disco inalterados.

A abertura/importação final no Revit 2026 e no AutoCAD não foi testada neste computador. IFC/DWG são formatos de intercâmbio e não preservam toda a edição paramétrica do RVT.