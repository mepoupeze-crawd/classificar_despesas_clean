import json

with open('parse_output.json', 'r', encoding='utf-8') as f:
    actual = json.load(f)

with open('tests/output_esperado.json', 'r', encoding='utf-8') as f:
    expected = json.load(f)

problems = []
for i, item in enumerate(actual['items']):
    if i >= len(expected['items']):
        break
    expected_item = expected['items'][i]
    
    # Comparar todos os campos
    fields_to_check = ['date', 'description', 'amount', 'last4', 'flux', 'source', 'parcelas', 'numero_parcela']
    for field in fields_to_check:
        if item.get(field) != expected_item.get(field):
            problems.append({
                'index': i,
                'field': field,
                'description': item.get('description', 'N/A'),
                'date': item.get('date', 'N/A'),
                'expected': expected_item.get(field),
                'actual': item.get(field)
            })
            break  # Reportar apenas o primeiro campo diferente por item

if problems:
    print(f"Encontradas {len(problems)} diferencas:\n")
    for p in problems[:30]:
        print(f"Linha {p['index']}: {p['description']} ({p['date']})")
        print(f"  Campo: {p['field']}")
        print(f"  Esperado: {p['expected']}")
        print(f"  Atual:    {p['actual']}\n")
else:
    print("Nenhuma diferenca encontrada! Arquivos sao identicos em todos os campos.")

