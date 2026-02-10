import json
from pathlib import Path

expected = json.loads(Path('tests/output_fatura3.json').read_text(encoding='utf-8'))
actual = json.loads(Path('out_cart_3.json').read_text(encoding='utf-8'))

# Criar sets para comparação (usando uma chave única)
def make_key(item):
    return (item['date'], item['description'], item['amount'], item.get('last4'))

expected_keys = {make_key(item) for item in expected['items']}
actual_keys = {make_key(item) for item in actual['items']}

missing_keys = expected_keys - actual_keys

print(f"Total esperado: {len(expected['items'])}")
print(f"Total atual: {len(actual['items'])}")
print(f"Faltantes: {len(missing_keys)}")
print("\nITENS FALTANTES:")
for key in sorted(missing_keys):
    print(f"  Date: {key[0]}, Desc: {key[1]}, Amount: {key[2]}, Last4: {key[3]}")

# Também verificar itens que estão no atual mas não no esperado
extra_keys = actual_keys - expected_keys
if extra_keys:
    print("\nITENS EXTRAS (no atual mas não no esperado):")
    for key in sorted(extra_keys):
        print(f"  Date: {key[0]}, Desc: {key[1]}, Amount: {key[2]}, Last4: {key[3]}")

