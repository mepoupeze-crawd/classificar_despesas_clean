# Ajuste: Ignorar Seção "Compras parceladas - próximas faturas"

## Problema

A seção "Compras parceladas - próximas faturas" contém transações que serão cobradas em faturas futuras e **não devem ser incluídas** na fatura atual. O parser já tinha lógica para ignorar essa seção, mas a detecção era muito restritiva.

## Solução Implementada

### Antes (linha 118):
```python
if normalized_lower.startswith("compras parceladas - proximas faturas"):
    current_section = "ignore"
    current_card = None
    continue
```

### Depois (linha 119):
```python
# Detecção flexível de seções a ignorar (permite prefixos, variações)
if "compras" in normalized_lower and "parceladas" in normalized_lower and "proximas" in normalized_lower and "faturas" in normalized_lower:
    current_section = "ignore"
    current_card = None
    continue
```

## Benefícios

1. **Detecção mais robusta**: Funciona mesmo com prefixos markdown (##, ###), espaços extras ou outras variações de formatação
2. **Consistência**: Usa a mesma abordagem flexível aplicada às outras seções
3. **Ignora corretamente**: Quando `current_section = "ignore"`, todas as linhas subsequentes são ignoradas até que uma nova seção seja detectada

## Como Funciona

1. Quando a linha contém as palavras-chave "compras", "parceladas", "proximas" e "faturas", o parser define `current_section = "ignore"`
2. Na linha 212, há uma verificação: `if current_section not in {"compras", "produtos"}: continue`
3. Isso significa que todas as linhas com `current_section = "ignore"` são puladas (não processadas)
4. A seção continua sendo ignorada até que uma nova seção válida seja detectada (como "Lançamentos: compras e saques")

## Seções Ignoradas

O parser também ignora as seguintes seções usando a mesma lógica flexível:
- "Encargos cobrados nesta fatura"
- "Limites de crédito"

Todas agora usam detecção flexível baseada em palavras-chave, garantindo funcionamento mesmo com variações de formatação.

