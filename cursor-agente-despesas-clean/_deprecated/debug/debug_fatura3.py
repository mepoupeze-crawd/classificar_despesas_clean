import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.validate import calculate_stats, validate_delta
from card_pdf_parser.parser.rules import detect_card_marker, extract_value, extract_date

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

print("\n=== Primeiros 20 itens do cartão 9826 ===")
for i, item in enumerate(card_9826_items[:20], 1):
    print(f"{i}. {item.date} | {item.description[:60]} | {item.amount}")

# Verificar linhas que contêm "ESPORTE CLUBE PINHEIRO" e "PG *SHOPGEORGIA"
print("\n=== Linhas com ESPORTE CLUBE PINHEIRO ===")
for i, line in enumerate(lines):
    if "ESPORTE CLUBE PINHEIRO" in line.upper() or "PG *SHOPGEORGIA" in line.upper():
        print(f"Linha {i}: {line}")
        date = extract_date(line, invoice_year)
        value = extract_value(line)
        print(f"  Data: {date}, Valor: {value}")
        print()

