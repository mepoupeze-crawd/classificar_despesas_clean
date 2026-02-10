import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.validate import calculate_stats, validate_delta
from card_pdf_parser.parser.rules import detect_card_marker, extract_value

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Extrair subtotais do PDF associados aos cartões (antes da classificação)
subtotals = {}
current_card_for_subtotal = None

for line in lines:
    marker = detect_card_marker(line)
    if marker:
        marker_type, marker_card = marker
        if marker_type == "start":
            current_card_for_subtotal = marker_card
        elif marker_type == "total":
            subtotal = extract_value(line)
            if subtotal:
                subtotals[marker_card] = subtotal
            current_card_for_subtotal = None

# Tentar detectar ano da fatura
import re
invoice_year = None
for line in lines[:50]:
    year_match = re.search(r'20\d{2}', line)
    if year_match:
        invoice_year = int(year_match.group(0))
        break

if invoice_year is None:
    invoice_year = 2025

classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)

# Verificar itens do cartão 9826
print("=== Itens do cartão 9826 ===")
card_9826_items = [item for item in items if item.last4 and "9826" in item.last4]
print(f"Total de itens: {len(card_9826_items)}")
total_9826 = sum(item.amount for item in card_9826_items)
print(f"Soma calculada: {total_9826}")
print(f"Subtotal esperado: {subtotals.get('9826', 'N/A')}")

# Verificar itens do cartão 7430
print("\n=== Itens do cartão 7430 ===")
card_7430_items = [item for item in items if item.last4 and "7430" in item.last4]
print(f"Total de itens: {len(card_7430_items)}")
total_7430 = sum(item.amount for item in card_7430_items)
print(f"Soma calculada: {total_7430}")
print(f"Subtotal esperado: {subtotals.get('7430', 'N/A')}")

# Verificar transações após linha 174 que deveriam ser do cartão 7430
print("\n=== Verificando transações após linha 174 ===")
# Encontrar onde está a linha 174 no processamento
# Linha 174: "12/08 ESPORTE CLUBE PINHEIRO 10,80 Lançamentos no cartão (final 9826) 9.139,39"
for i, item in enumerate(items):
    if item.description and "ESPORTE CLUBE PINHEIRO" in item.description.upper() and abs(item.amount - Decimal('10.80')) < 0.01:
        print(f"\nEncontrada transação ESPORTE CLUBE PINHEIRO 10,80 no índice {i}")
        print(f"  Data: {item.date}, Valor: {item.amount}, Cartão: {item.last4}")
        # Verificar próximas transações
        print("\nPróximas 10 transações:")
        for j in range(i+1, min(i+11, len(items))):
            print(f"  {j}. {items[j].date} | {items[j].description[:50]} | {items[j].amount} | {items[j].last4}")
        break

