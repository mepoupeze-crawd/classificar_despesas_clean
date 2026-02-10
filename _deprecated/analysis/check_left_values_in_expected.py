import json

# Carregar output esperado
with open('tests/output_esperado3.json', 'r', encoding='utf-8') as f:
    expected = json.load(f)

card_9826_expected = [i for i in expected['items'] if i['last4'] and '9826' in i['last4']]

# Verificar se há transações com valores da esquerda das linhas concatenadas
values_left = [313.22, 330.00, 159.99, 195.15, 158.30, 389.00]
print("=== Verificando se valores da esquerda aparecem no esperado ===")
for val in values_left:
    found = [item for item in card_9826_expected if abs(float(item['amount']) - val) < 0.01]
    print(f"Valor {val}: {'ENCONTRADO' if found else 'NÃO encontrado'}")
    if found:
        for item in found:
            print(f"  -> {item['date']} | {item['description'][:50]} | {item['amount']}")

# Verificar o total esperado
total_expected = sum(float(i['amount']) if i['flux'] == 'Saida' else -float(i['amount']) for i in card_9826_expected)
print(f"\nTotal esperado: {total_expected}")
print(f"Subtotal do PDF: 9139.39")
print(f"Diferença: {abs(total_expected - 9139.39)}")

# Verificar se há transações que têm valores grandes que podem ser da esquerda
print("\n=== Verificando transações com valores grandes ===")
large_items = [item for item in card_9826_expected if float(item['amount']) > 200]
for item in large_items:
    print(f"{item['date']} | {item['description'][:60]} | {item['amount']}")

