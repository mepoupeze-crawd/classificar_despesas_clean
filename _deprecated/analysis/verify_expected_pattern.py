import json

# Carregar output esperado
with open('tests/output_esperado3.json', 'r', encoding='utf-8') as f:
    expected = json.load(f)

card_9826_expected = [i for i in expected['items'] if i['last4'] and '9826' in i['last4']]

# Verificar transações específicas de linhas concatenadas
print("=== Verificando transações de linhas concatenadas no esperado ===\n")

# Linha concatenada: "03/08 IFD*RECANTO DOS BOLOS 51,79 13/08 JOAOTAXISP 40,25"
# Esperado: uma transação com valor 40.25
found_recanto = [item for item in card_9826_expected if 'RECANTO DOS BOLOS' in item['description']]
print(f"IFD*RECANTO DOS BOLOS: {len(found_recanto)} transações")
for item in found_recanto:
    print(f"  -> {item['date']} | {item['description'][:60]} | {item['amount']}")

# Linha concatenada: "03/08 IFD*ALBIS AM COMERCIO 53,79 13/08 SPAZIO CAPELLI 44,00"
found_albis = [item for item in card_9826_expected if 'ALBIS AM COMERCIO' in item['description']]
print(f"\nIFD*ALBIS AM COMERCIO: {len(found_albis)} transações")
for item in found_albis:
    print(f"  -> {item['date']} | {item['description'][:60]} | {item['amount']}")

# Verificar se há transações com valores da esquerda (51.79, 53.79, etc.)
values_left = [51.79, 53.79, 313.22, 39.90, 330.00, 7.90, 159.99, 195.15, 7.10, 95.48, 39.60, 16.60, 22.80, 24.86, 28.05, 16.99, 22.80, 24.80, 158.30, 389.00, 22.00, 58.80, 25.80, 39.90, 45.60, 21.80, 10.80]

print(f"\n=== Verificando se valores da esquerda aparecem no esperado ===")
for val in values_left:
    found = [item for item in card_9826_expected if abs(float(item['amount']) - val) < 0.01]
    if found:
        print(f"Valor {val}: ENCONTRADO - {found[0]['description'][:50]}")

# Verificar o total esperado
total_expected = sum(float(i['amount']) if i['flux'] == 'Saida' else -float(i['amount']) for i in card_9826_expected)
print(f"\nTotal esperado: {total_expected}")
print(f"Subtotal do PDF: 9139.39")
print(f"Diferença: {abs(total_expected - 9139.39)}")

# O problema é que o output esperado tem apenas transações com valores da direita
# Mas o PDF tem subtotal maior. Isso significa que:
# 1. O PDF está contando valores adicionais (parcelas futuras, valores totais, etc.)
# 2. OU há transações que não estão sendo extraídas
# 3. OU precisamos contar ambos os valores das linhas concatenadas

# Vou verificar se há uma diferença sistemática que indica que precisamos contar valores adicionais

