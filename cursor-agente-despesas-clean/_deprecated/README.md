# Arquivos Deprecated

Esta pasta contém arquivos que foram movidos do repositório principal por não serem mais necessários para as funcionalidades core do sistema.

## Estrutura

- `debug/` - Scripts de debug temporários
- `tests/` - Testes temporários ou experimentais (não parte da suíte oficial)
- `analysis/` - Scripts de análise e verificação pontuais
- `outputs/` - Arquivos JSON de saída temporários
- `scripts/` - Scripts utilitários não usados em produção

## Funcionalidades Core (NÃO afetadas)

As seguintes funcionalidades continuam 100% funcionais:

1. **Extrato de conta corrente** (xls, csv, xlsx, pdf)
2. **Fatura do cartão de crédito** (xls, csv, xlsx, pdf)
3. **Classificação de despesas** e categorização
4. **APIs** ativas e **Swagger** acessível
5. **Cenários de teste** oficiais em `tests/` e `spend_classification/tests/`

## Como restaurar

Para restaurar um arquivo movido:

```bash
git mv _deprecated/<categoria>/<arquivo> <caminho_original>
```

## Evidência de não uso

Cada categoria possui um arquivo `MOVED.md` documentando:
- Motivo da realocação
- Evidência de não uso (grep, import graph)
- Data da movimentação


