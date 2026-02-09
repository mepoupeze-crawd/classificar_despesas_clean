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

# Verificar transações do cartão 9826
card_9826_items = [item for item in items if item.last4 and "9826" in item.last4]
print(f"Total de transações do cartão 9826: {len(card_9826_items)}")
print(f"Soma calculada: {sum(item.amount for item in card_9826_items)}")
print(f"Subtotal esperado: {subtotals.get('9826', 'N/A')}")

# Verificar se há transações duplicadas
print("\n=== Verificando duplicatas ===")
seen = {}
duplicates = []
for item in card_9826_items:
    key = (item.date, item.description[:50], item.amount)
    if key in seen:
        duplicates.append((key, seen[key], item))
    else:
        seen[key] = item

if duplicates:
    print(f"Encontradas {len(duplicates)} duplicatas:")
    for dup in duplicates[:5]:
        print(f"  {dup[0]}")
else:
    print("Nenhuma duplicata encontrada")

# Verificar transações do cartão 7430
card_7430_items = [item for item in items if item.last4 and "7430" in item.last4]
print(f"\nTotal de transações do cartão 7430: {len(card_7430_items)}")
print(f"Soma calculada: {sum(item.amount for item in card_7430_items)}")
print(f"Subtotal esperado: {subtotals.get('7430', 'N/A')}")

# Verificar se há transações do cartão 9826 que deveriam ser do cartão 7430
# (transações após linha 174)
print("\n=== Verificando transações após linha 174 ===")
# Encontrar a transação da linha 174
line174_item = None
for item in card_9826_items:
    if item.description and "ESPORTE CLUBE PINHEIRO" in item.description.upper() and item.date == "2025-08-12" and abs(item.amount - Decimal('10.80')) < 0.01:
        line174_item = item
        break

if line174_item:
    # Encontrar o índice dessa transação
    line174_idx = items.index(line174_item)
    print(f"Transação da linha 174 encontrada no índice {line174_idx}")
    print(f"Próximas 20 transações:")
    for i in range(line174_idx + 1, min(line174_idx + 21, len(items))):
        item = items[i]
        print(f"  {i}. {item.date} | {item.description[:50]} | {item.amount} | {item.last4}")

