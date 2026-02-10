# Scripts Temporários Movidos

**Data:** 2025-11-15  
**Categoria:** Scripts Utilitários Não Usados em Produção

## Motivo da Realocação

Scripts criados para testes pontuais ou experimentos que não são usados em produção ou CI/CD.

## Evidência de Não Uso

- **Não referenciados em:**
  - `Makefile`
  - Scripts de CI/CD
  - `README.md` ou documentação oficial
  - Código de produção
- **Nomes indicam natureza temporária:** `tmp_`, `temp_`, etc.

## Arquivos Movidos

- `tmp_code.py` - Código temporário
- `temp_inspect.py` - Inspeção temporária
- `parse_pdf_direct.py` - Parser direto (substituído por API)
- `send_request.py` - Envio de requisições de teste
- `list_routes.py` - Listagem de rotas (pode ser feito via Swagger)

## Como Restaurar

```bash
git mv _deprecated/scripts/<arquivo>.py ./<arquivo>.py
```

## Impacto

**Nenhum impacto funcional.** Estes scripts eram apenas utilitários temporários.


