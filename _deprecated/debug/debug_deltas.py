import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.validate import calculate_stats
from card_pdf_parser.parser.rules import detect_card_marker, extract_value

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Extrair subtotais do PDF associados aos cartões
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
stats = calculate_stats(items, rejects, len(lines), subtotals)

# Verificar transações por cartão
print("=== Transações por cartão ===\n")
by_card = {}
for item in items:
    if item.last4:
        card = item.last4.split(' ')[1] if ' ' in item.last4 else 'unknown'
    else:
        card = 'unknown'
    
    if card not in by_card:
        by_card[card] = []
    
    by_card[card].append(item)

for card in ['9826', '7430', '1899', 'unknown']:
    if card not in by_card:
        continue
    card_items = by_card[card]
    total = sum(item.amount for item in card_items)
    control = Decimal(stats.by_card[card].control_total)
    calculated = Decimal(stats.by_card[card].calculated_total)
    delta = Decimal(stats.by_card[card].delta)
    
    print(f"\nCartão {card}:")
    print(f"  Control total: {control}")
    print(f"  Calculated total: {calculated}")
    print(f"  Delta: {delta}")
    print(f"  Número de transações: {len(card_items)}")
    
    if abs(delta) > 0.01:
        print(f"\n  Transações do cartão {card}:")
        for item in card_items:
            print(f"    {item.date} | {item.description[:50]:50s} | {float(item.amount):>10.2f}")

# Verificar linha específica mencionada pelo usuário
print("\n=== Verificando linha ESPORTE CLUBE PINHEIRO 16,60 PG *SHOPGEORGIA ===\n")
for i, line in enumerate(lines):
    if "ESPORTE CLUBE PINHEIRO" in line.upper() and "16,60" in line and "PG *SHOPGEORGIA" in line.upper():
        print(f"Linha {i}: {line}")
        from card_pdf_parser.parser.classify import split_concatenated_line
        separated = split_concatenated_line(line, invoice_year)
        print(f"Separada em {len(separated)} partes:")
        for j, part in enumerate(separated, 1):
            from card_pdf_parser.parser.rules import extract_date
            date = extract_date(part, invoice_year)
            value = extract_value(part)
            print(f"  {j}. {part}")
            print(f"     Data: {date}, Valor: {value}")

