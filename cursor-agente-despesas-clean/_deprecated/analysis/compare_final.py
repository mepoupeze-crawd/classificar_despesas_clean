import json

# Ler JSON atual
with open('fatura_cartao_3_output.json', encoding='utf-8') as f:
    atual = json.load(f)

# Itens esperados (primeiros 30)
esperado = [
    {"date": "2025-04-30", "description": "CLINICA ADRIANA VI", "amount": "2048.50", "parcelas": 10, "numero_parcela": 4},
    {"date": "2025-05-16", "description": "FRATEX INDUSTRIA E", "amount": "111.96", "parcelas": 5, "numero_parcela": 4},
    {"date": "2025-05-21", "description": "ZARA BRASIL LTDA", "amount": "143.50", "parcelas": 5, "numero_parcela": 4},
    {"date": "2025-05-30", "description": "CLINICA ADRIANA VI", "amount": "513.34", "parcelas": 3, "numero_parcela": 3},
    {"date": "2025-06-03", "description": "PASSARO AZUL COMER", "amount": "266.35", "parcelas": 6, "numero_parcela": 3},
    {"date": "2025-06-03", "description": "GALLERIST COM IMP", "amount": "125.82", "parcelas": 5, "numero_parcela": 3},
    {"date": "2025-06-03", "description": "ZARA BRASIL LTDA", "amount": "135.50", "parcelas": 5, "numero_parcela": 3},
    {"date": "2025-06-12", "description": "SEPHORA CIDJARDIN", "amount": "83.00", "parcelas": 5, "numero_parcela": 3},
    {"date": "2025-06-17", "description": "MTKS JOIAS", "amount": "107.50", "parcelas": 4, "numero_parcela": 3},
    {"date": "2025-07-01", "description": "BRUNA CUTAIT", "amount": "487.74", "parcelas": 7, "numero_parcela": 2},
    {"date": "2025-07-01", "description": "BRUNA CUTAIT", "amount": "0.18", "parcelas": None, "numero_parcela": None},
    {"date": "2025-07-11", "description": "LIVRARIA DA TRAVESSA", "amount": "439.50", "parcelas": 2, "numero_parcela": 2},
    {"date": "2025-07-23", "description": "DROGASIL", "amount": "160.10", "parcelas": 3, "numero_parcela": 2},
    {"date": "2025-07-23", "description": "TIAGO TAXI", "amount": "32.40", "parcelas": None, "numero_parcela": None},
    {"date": "2025-07-30", "description": "ESPORTE CLUBE PINHEIRO", "amount": "10.80", "parcelas": None, "numero_parcela": None},
    {"date": "2025-07-30", "description": "EC PINHEIROS", "amount": "3.00", "parcelas": None, "numero_parcela": None},
    {"date": "2025-07-30", "description": "Quiosque SHOP CIDADE J", "amount": "37.90", "parcelas": None, "numero_parcela": None},
    {"date": "2025-07-30", "description": "OLEA CA RESTAURANTE LT", "amount": "113.56", "parcelas": None, "numero_parcela": None},
    {"date": "2025-07-30", "description": "SPAZIO CAPELLI", "amount": "44.00", "parcelas": None, "numero_parcela": None},
    {"date": "2025-07-31", "description": "IFD*PAPILA RESTAURANTE", "amount": "58.89", "parcelas": None, "numero_parcela": None},
    {"date": "2025-07-31", "description": "KOPENHAGEN SHOPPING CI", "amount": "25.83", "parcelas": None, "numero_parcela": None},
    {"date": "2025-07-31", "description": "MP *JOAOTAXISP", "amount": "39.00", "parcelas": None, "numero_parcela": None},
    {"date": "2025-07-31", "description": "IFD*TENDA ORGANICA LTD", "amount": "80.99", "parcelas": None, "numero_parcela": None},
    {"date": "2025-07-31", "description": "FIT FOOD GF4 BEAR E LAN", "amount": "88.81", "parcelas": None, "numero_parcela": None},
    {"date": "2025-08-01", "description": "CINEMARK CIDADE JARDIM", "amount": "56.00", "parcelas": None, "numero_parcela": None},
    {"date": "2025-08-01", "description": "ESPORTE CLUBE PINHEIRO", "amount": "16.60", "parcelas": None, "numero_parcela": None},
    {"date": "2025-08-03", "description": "D1 DOCES E BOLOS L", "amount": "134.99", "parcelas": None, "numero_parcela": None},
    {"date": "2025-08-03", "description": "IFD*PAPILA RESTAURANTE", "amount": "56.89", "parcelas": None, "numero_parcela": None},
    {"date": "2025-08-03", "description": "ESPORTE CLUBE PINHEIRO", "amount": "5.80", "parcelas": None, "numero_parcela": None},
    {"date": "2025-08-03", "description": "PAO MARIO FERRAZ", "amount": "96.03", "parcelas": None, "numero_parcela": None},
]

print("Comparando primeiros 30 itens:")
print(f"Esperado: {len(esperado)} itens")
print(f"Atual: {len(atual['items'])} itens\n")

erros = []
for i, exp in enumerate(esperado):
    if i < len(atual['items']):
        item = atual['items'][i]
        ok = True
        erros_item = []
        if item['date'] != exp['date']:
            erros_item.append(f"Data: esperado {exp['date']}, atual {item['date']}")
            ok = False
        if item['description'] != exp['description']:
            erros_item.append(f"Desc: esperado '{exp['description']}', atual '{item['description']}'")
            ok = False
        if item['amount'] != exp['amount']:
            erros_item.append(f"Valor: esperado {exp['amount']}, atual {item['amount']}")
            ok = False
        if item.get('parcelas') != exp['parcelas']:
            erros_item.append(f"Parcelas: esperado {exp['parcelas']}, atual {item.get('parcelas')}")
            ok = False
        if item.get('numero_parcela') != exp['numero_parcela']:
            erros_item.append(f"Num parcela: esperado {exp['numero_parcela']}, atual {item.get('numero_parcela')}")
            ok = False
        if not ok:
            erros.append((i+1, exp, item, erros_item))
            print(f"Item {i+1}: ERRO")
            for e in erros_item:
                print(f"  - {e}")
        else:
            print(f"Item {i+1}: OK")
    else:
        erros.append((i+1, exp, None, ["FALTANDO"]))
        print(f"Item {i+1}: FALTANDO - {exp['date']} {exp['description']} {exp['amount']}")

print(f"\nTotal de erros: {len(erros)}")

