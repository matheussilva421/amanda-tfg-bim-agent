# BIM compiler E2E — E2E sintético

Status: `PASS_FIXTURE` para o contrato local do compilador BIM.

Este documento é um exemplo de E2E sintético, produzido com dados de fixture e
sem abertura ou escrita em Revit. A execução real em Revit não foi realizada
neste relatório e não é declarada como concluída.

## Escopo

- Fixture: `synthetic-courtyard`.
- Sequência: R01 → R13, em ordem determinística.
- Persistência: journal JSONL local com eventos `CLAIMED` e `VERIFIED`.
- Evidência: artefato independente sintético com hash SHA-256.

## Providers, fallbacks e avisos

| Operação | Provider preferido | Fallback | Resultado |
| --- | --- | --- | --- |
| `revit.create_element` | `synthetic-provider` | `synthetic-fallback` | `PASS_FIXTURE` |

O fallback acima é uma escolha de fixture para demonstrar o formato do
relatório. Nenhuma falha de provider foi injetada neste exemplo e nenhum
provider real foi chamado.

## Duração

| Trecho | Duração |
| --- | ---: |
| Geração do plano | 0 ms (valor sintético) |
| Claim e record-result | 0 ms (valor sintético) |
| E2E total | 0 ms (valor sintético) |

## Limite de evidência

Este relatório valida o contrato offline do plano, do journal e da evidência
de resultado. Ele não prova licença, saúde do host, transação, save/close,
reopen, estado de documento ou qualquer escrita física no Revit.
