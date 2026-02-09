# Outputs Temporários Movidos

**Data:** 2025-11-15  
**Categoria:** Arquivos JSON de Saída Temporários  
**Total de arquivos:** 12+

## Motivo da Realocação

Arquivos JSON gerados durante testes e desenvolvimento que não são necessários para o funcionamento do sistema.

## Evidência de Não Uso

- **Não referenciados em código:** Nenhum código importa ou lê estes arquivos
- **Gerados dinamicamente:** Podem ser regenerados a qualquer momento
- **Nomes indicam natureza temporária:** out*.json, parse_output*.json, etc.

## Arquivos Movidos

- out*.json (out.json, out1.json, out2.json, out3.json, out_cart_3.json, out_fatura2.json)
- parse_output*.json (parse_output.json, parse_output2.json, parse_output3.json, parse_output_fatura3.json)
- *_output.json (fatura_cartao_3_output.json, curl_parse_output.json)

## Como Restaurar

`ash
git mv _deprecated/outputs/<arquivo>.json ./<arquivo>.json
`

## Impacto

**Nenhum impacto funcional.** Estes são apenas outputs de testes e podem ser regenerados.
