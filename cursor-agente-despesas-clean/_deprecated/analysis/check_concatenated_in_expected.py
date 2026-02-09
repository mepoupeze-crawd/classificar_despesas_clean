from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value
import re
from decimal import Decimal

lines = extract_lines_lr_order('fatura_cartao_3.pdf')

# Verificar linhas concatenadas específicas e como aparecem no output esperado
test_lines = [
    "04/08 SAPATARIA DO FITURO 313,22 14/08 KOPENHAGENSHOPPING CI 19,90",
    "04/08 DM*mondaycom 330,00 15/08 DOLCISSIMO LANCHONETE 14,00",
    "08/08 SPAZIO CAPELLI 389,00 26/08 KOPENHAGENSHOPPING CI 19,90"
]

print("=== Verificando linhas concatenadas específicas ===")
for test_line in test_lines:
    date1 = extract_date(test_line, default_year=2025)
    value1 = extract_value(test_line, prefer_last=False)
    value2 = extract_value(test_line, prefer_last=True)
    
    print(f"\nLinha: {test_line}")
    print(f"  Data: {date1}")
    print(f"  Valor esquerda: {value1}")
    print(f"  Valor direita: {value2}")
    
    # Verificar se ambos os valores aparecem no output esperado
    import json
    with open('tests/output_esperado3.json', 'r', encoding='utf-8') as f:
        expected = json.load(f)
    
    # Procurar transações com esses valores
    found_left = [item for item in expected['items'] if abs(float(item['amount']) - float(value1)) < 0.01]
    found_right = [item for item in expected['items'] if abs(float(item['amount']) - float(value2)) < 0.01]
    
    print(f"  Encontrado no esperado:")
    print(f"    Valor esquerda ({value1}): {len(found_left)} transações")
    if found_left:
        for item in found_left:
            print(f"      -> {item['date']} | {item['description'][:50]} | {item['amount']} | card={item['last4'][-4:] if item['last4'] else 'None'}")
    print(f"    Valor direita ({value2}): {len(found_right)} transações")
    if found_right:
        for item in found_right:
            print(f"      -> {item['date']} | {item['description'][:50]} | {item['amount']} | card={item['last4'][-4:] if item['last4'] else 'None'}")

