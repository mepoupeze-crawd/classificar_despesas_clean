from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value
import re
from decimal import Decimal

lines = extract_lines_lr_order('fatura_cartao_3.pdf')

# Encontrar seção do 9826
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    marker = detect_card_marker(line)
    if marker:
        if marker[0] == 'start' and marker[1] == '9826':
            start_idx = i
        elif marker[0] == 'total' and marker[1] == '9826':
            end_idx = i
            break

print(f"Seção do cartão 9826: linhas {start_idx} a {end_idx}\n")

# Extrair transações
invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)

card_9826_items = [i for i in items if i.last4 and '9826' in i.last4]
total_extracted = sum(i.amount if i.flux != 'Entrada' else -i.amount for i in card_9826_items)

print(f"Total extraído: {total_extracted}")
print(f"Subtotal do PDF: 9139.39")
print(f"Diferença: {abs(total_extracted - Decimal('9139.39'))}")
print(f"Items count: {len(card_9826_items)}")

# Verificar se há transações duplicadas ou valores que não estão sendo contabilizados
print("\n=== Verificando transações duplicadas ===")
seen = {}
duplicates = []
for item in card_9826_items:
    key = (item.date, str(item.amount), item.description[:50])
    if key in seen:
        duplicates.append((seen[key], item))
    else:
        seen[key] = item

if duplicates:
    print(f"Transações duplicadas encontradas: {len(duplicates)}")
    for dup in duplicates[:5]:
        print(f"  -> {dup[0].date} | {dup[0].description[:50]} | {dup[0].amount}")
        print(f"     {dup[1].date} | {dup[1].description[:50]} | {dup[1].amount}")
else:
    print("Nenhuma transação duplicada encontrada")

# Verificar se há valores que não estão sendo contabilizados
print("\n=== Verificando valores faltantes ===")
missing = Decimal('9139.39') - total_extracted
print(f"Valor faltante: {missing}")

# Verificar se há transações que estão sendo atribuídas ao cartão errado
print("\n=== Verificando transações atribuídas ao cartão errado ===")
all_items_by_card = {}
for item in items:
    if item.last4:
        card = item.last4[-4:] if len(item.last4) >= 4 else 'unknown'
    else:
        card = 'unknown'
    
    if card not in all_items_by_card:
        all_items_by_card[card] = []
    all_items_by_card[card].append(item)

for card, card_items in all_items_by_card.items():
    if card != '9826' and card != 'unknown':
        # Verificar se há transações com datas anteriores ao marcador "total" do 9826
        transition_date = "2025-08-12"
        before_transition = [i for i in card_items if i.date <= transition_date]
        if before_transition:
            print(f"Card {card}: {len(before_transition)} transações com data <= {transition_date}")
            total_before = sum(i.amount if i.flux != 'Entrada' else -i.amount for i in before_transition)
            print(f"  Total: {total_before}")

