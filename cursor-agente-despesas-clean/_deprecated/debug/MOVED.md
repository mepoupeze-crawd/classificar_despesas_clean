# Arquivos de Debug Movidos

**Data:** 2025-11-15  
**Categoria:** Scripts de Debug Temporários  
**Total de arquivos:** 40

## Motivo da Realocação

Estes arquivos são scripts de debug criados durante o desenvolvimento do parser de fatura Itaú. Eles foram usados para investigar problemas específicos e não fazem parte do código de produção.

## Evidência de Não Uso

- **Nenhum import em código de produção:** Verificado via `grep -r "from.*debug_|import.*debug_" app/ services/ card_pdf_parser/`
- **Não referenciados em testes oficiais:** Testes oficiais estão em `tests/` e `spend_classification/tests/`
- **Não usados em CI/CD:** Nenhum script de build/test referencia estes arquivos
- **Nomes indicam propósito temporário:** Todos começam com `debug_` indicando natureza de investigação

## Arquivos Movidos

Todos os arquivos `debug_*.py` da raiz do repositório foram movidos para `_deprecated/debug/`.

## Como Restaurar

```bash
git mv _deprecated/debug/debug_<nome>.py ./debug_<nome>.py
```

## Impacto

**Nenhum impacto funcional.** Estes arquivos eram apenas para investigação e não são necessários para:
- Parsing de extrato ou fatura
- Classificação de despesas
- APIs ou Swagger
- Testes oficiais


