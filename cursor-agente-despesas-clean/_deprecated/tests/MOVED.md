# Testes Temporários Movidos

**Data:** 2025-11-15  
**Categoria:** Testes Experimentais e Temporários

## Motivo da Realocação

Testes temporários criados durante desenvolvimento que não fazem parte da suíte oficial de testes.

## Evidência de Não Uso

- **Testes oficiais estão em:**
  - `tests/` (testes de parsing)
  - `spend_classification/tests/` (testes de classificação)
  - `card_pdf_parser/tests/` (testes de parser)
- **Não executados em CI/CD:** Apenas testes oficiais são executados
- **Nomes indicam natureza experimental:** Muitos têm sufixos como `_scenario2`, `_validation2`, etc.

## Arquivos Movidos

Testes temporários da raiz (se houver) foram movidos para `_deprecated/tests/`.

**Nota:** Testes oficiais em `tests/`, `spend_classification/tests/` e `card_pdf_parser/tests/` **NÃO** foram movidos.

## Como Restaurar

```bash
git mv _deprecated/tests/test_<nome>.py ./test_<nome>.py
```

## Impacto

**Nenhum impacto funcional.** Testes oficiais continuam intactos e funcionando.


