# Canonical Pavilion Migration — Design Specification

**Status:** USER-APPROVED DIRECTION — pranchas de 2026-09-22 são canônicas.

## Goal

Migrar o Amanda TFG BIM Agent da solução linear R12 para um novo run BIM cuja implantação, setorização e volumetria correspondam materialmente às três pranchas canônicas, preservando toda a infraestrutura/testes/providers já válidos.

## Source hierarchy

1. instrução atual do usuário;
2. `CANONICAL_PARTIDO_OVERRIDE_2026-09-22.md` + três pranchas canônicas;
3. `programa_necessidades.pdf` para números/programa;
4. TFG e fontes verificadas de terreno/norma;
5. estado live do repositório;
6. decisões antigas apenas como histórico.

## Architecture

- Arquivar a geometria linear, não reaproveitá-la como base final.
- Manter providers, BIM compiler, families, parameters, QA, export, persistence e recovery.
- Criar um novo `CanonicalPavilionLayout`/run com quatro pavilhões residenciais, administrativo/acolhimento de dois pavimentos, bloco de serviços/capacitação, setor infantil e paisagismo estruturante.
- A geometria das pranchas é normalizada e escalada pelo programa oficial; não confiar em mapa/norte/área anotados nas imagens quando não verificados.
- O approval hash da nova seleção deve incluir hashes das três imagens canônicas + programa + geometria gerada.

## Error handling

- Se o partido canônico não couber em um dado ainda não verificado, permaneça em STUDY e registre a premissa.
- Se o intervalo estimado de área fechada/coberta conflitar com o partido, não voltar à barra; otimizar a solução pavilionizada e registrar desvio se necessário.
- Nenhuma `CANONICAL_DEVIATION` crítica pode ficar implícita.

## Testing

- TDD para novo layout e seleção.
- Regressão dos exports e BIM compiler existentes.
- Canonical QA antes de R05 e em R14.
- Visual gate obrigatório em R04, R08, R12 e R13.
- Cold reopen antes do GOLDEN.
