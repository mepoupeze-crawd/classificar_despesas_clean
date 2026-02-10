import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier, split_concatenated_line
from card_pdf_parser.parser.rules import detect_card_marker, extract_value, extract_date

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Verificar linha 174 e como ela é processada
line174 = lines[174]
print(f"Linha 174 original: {line174}")
print(f"Marcador: {detect_card_marker(line174)}")

# Verificar se a linha é split
separated = split_concatenated_line(line174, 2025)
print(f"\nLinha split em {len(separated)} partes:")
for i, part in enumerate(separated, 1):
    print(f"  {i}. {part}")
    marker = detect_card_marker(part)
    date = extract_date(part, 2025)
    value = extract_value(part)
    print(f"     Marcador: {marker}, Data: {date}, Valor: {value}")

# Processar e verificar quantas transações são criadas
invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)

# Contar transações do cartão 9826 com data 2025-08-12
card_9826_0812 = [item for item in items if item.last4 and "9826" in item.last4 and item.date == "2025-08-12"]
print(f"\nTransações do cartão 9826 em 2025-08-12: {len(card_9826_0812)}")
for item in card_9826_0812:
    print(f"  {item.description[:50]} | {item.amount}")

# Verificar todas as transações do cartão 9826
card_9826_all = [item for item in items if item.last4 and "9826" in item.last4]
print(f"\nTotal de transações do cartão 9826: {len(card_9826_all)}")
print(f"Soma: {sum(item.amount for item in card_9826_all)}")

# Verificar se há transações com valores muito grandes que podem ser subtotais incorretos
large_items = [item for item in card_9826_all if item.amount > 1000]
print(f"\nTransações do cartão 9826 com valor > 1000: {len(large_items)}")
for item in large_items[:10]:
    print(f"  {item.date} | {item.description[:50]} | {item.amount}")

