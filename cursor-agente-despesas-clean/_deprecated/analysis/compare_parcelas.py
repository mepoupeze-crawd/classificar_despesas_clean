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
    
    # Comparar parcelas e numero_parcela
    if item['parcelas'] != expected_item['parcelas'] or item['numero_parcela'] != expected_item['numero_parcela']:
        problems.append({
            'index': i,
            'description': item['description'],
            'date': item['date'],
            'expected_parcelas': expected_item['parcelas'],
            'actual_parcelas': item['parcelas'],
            'expected_numero': expected_item['numero_parcela'],
            'actual_numero': item['numero_parcela']
        })

if problems:
    print(f"Encontradas {len(problems)} diferencas em parcelas:\n")
    for p in problems:
        print(f"Linha {p['index']}: {p['description']} ({p['date']})")
        print(f"  Esperado: parcelas={p['expected_parcelas']}, numero_parcela={p['expected_numero']}")
        print(f"  Atual:    parcelas={p['actual_parcelas']}, numero_parcela={p['actual_numero']}\n")
else:
    print("Nenhuma diferenca encontrada em parcelas!")

