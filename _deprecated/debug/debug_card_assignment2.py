import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.validate import calculate_stats
from card_pdf_parser.parser.rules import detect_card_marker, extract_value

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Extrair subtotais
subtotals = {}
for line in lines:
    marker = detect_card_marker(line)
    if marker and marker[0] == "total":
        subtotal = extract_value(line)
        if subtotal:
            subtotals[marker[1]] = subtotal

invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)

# Verificar transações do cartão 9826 que deveriam estar no 7430
print("=== Transações do cartão 9826 que podem estar erradas ===")
card_9826_items = [item for item in items if item.last4 and "9826" in item.last4]
# Verificar transações em 12/08 e 13/08 que podem estar no cartão errado
for item in card_9826_items:
    if item.date in ["2025-08-12", "2025-08-13"]:
        print(f"  {item.date} | {item.description[:50]} | {item.amount}")

# Verificar transações do cartão 7430
print("\n=== Transações do cartão 7430 ===")
card_7430_items = [item for item in items if item.last4 and "7430" in item.last4]
print(f"Total: {len(card_7430_items)}")
for item in card_7430_items[:20]:
    print(f"  {item.date} | {item.description[:50]} | {item.amount}")

# Verificar se TRELA - 0,01 está no cartão correto
print("\n=== TRELA - 0,01 ===")
trela_items = [item for item in items if "TRELA" in item.description.upper() and abs(item.amount - Decimal('0.01')) < 0.01]
for item in trela_items:
    print(f"  {item.date} | {item.description} | {item.amount} | {item.last4}")


