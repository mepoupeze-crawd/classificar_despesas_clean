import json
from pathlib import Path

expected = json.loads(Path('tests/output_fatura3.json').read_text(encoding='utf-8'))
actual = json.loads(Path('out_cart_3.json').read_text(encoding='utf-8'))

# Criar dicionários indexados por (date, description, amount)
def make_key(item):
    return (item['date'], item['description'], item['amount'])

expected_dict = {make_key(item): item for item in expected['items']}
actual_dict = {make_key(item): item for item in actual['items']}

print("ITENS COM LAST4 INCORRETO (mesma data/desc/amount mas last4 diferente):")
count = 0
for key in sorted(expected_dict.keys()):
    if key in actual_dict:
        exp_item = expected_dict[key]
        act_item = actual_dict[key]
        if exp_item.get('last4') != act_item.get('last4'):
            count += 1
            print(f"  {key[0]} | {key[1]} | {key[2]}")
            print(f"    Esperado: {exp_item.get('last4')}")
            print(f"    Atual:    {act_item.get('last4')}")
            print()

print(f"Total de itens com last4 incorreto: {count}")

