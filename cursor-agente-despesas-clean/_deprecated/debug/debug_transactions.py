import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier, split_concatenated_line
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Processar e verificar o que acontece com as linhas problemáticas
invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)

# Verificar transações específicas
print("=== Verificando transações específicas ===")

# 1. ORGANICO OSCAR FREIRE 92,66 - deveria estar no cartão 9826
print("\n1. ORGANICO OSCAR FREIRE 92,66:")
for item in items:
    if "ORGANICO OSCAR FREIRE" in item.description.upper() and abs(item.amount - Decimal('92.66')) < 0.01:
        print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# 2. EC PINHEIROS 3,00 em 12/08 - deveria estar no cartão 9826
print("\n2. EC PINHEIROS 3,00 em 12/08:")
for item in items:
    if "EC PINHEIROS" in item.description.upper() and item.date == "2025-08-12" and abs(item.amount - Decimal('3.00')) < 0.01:
        print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# 3. CAFE ZINN 69,30 em 12/08 - deveria estar no cartão 9826
print("\n3. CAFE ZINN 69,30 em 12/08:")
for item in items:
    if "CAFE ZINN" in item.description.upper() and item.date == "2025-08-12" and abs(item.amount - Decimal('69.30')) < 0.01:
        print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# 4. APPLE.COM/BILL 64,90 em 12/08 - deveria estar no cartão 9826
print("\n4. APPLE.COM/BILL 64,90 em 12/08:")
for item in items:
    if "APPLE.COM/BILL" in item.description.upper() and item.date == "2025-08-12" and abs(item.amount - Decimal('64.90')) < 0.01:
        print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# 5. ESPORTE CLUBE PINHEIRO 16,60 em 13/08 - deveria estar no cartão 9826
print("\n5. ESPORTE CLUBE PINHEIRO 16,60 em 13/08:")
for item in items:
    if "ESPORTE CLUBE PINHEIRO" in item.description.upper() and item.date == "2025-08-13" and abs(item.amount - Decimal('16.60')) < 0.01:
        print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# 6. EC PINHEIROS 3,00 em 13/08 - deveria estar no cartão 9826
print("\n6. EC PINHEIROS 3,00 em 13/08:")
for item in items:
    if "EC PINHEIROS" in item.description.upper() and item.date == "2025-08-13" and abs(item.amount - Decimal('3.00')) < 0.01:
        print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# 7. SmartBreak 11,99 em 13/08 - deveria estar no cartão 9826
print("\n7. SmartBreak 11,99 em 13/08:")
for item in items:
    if "SmartBreak" in item.description and item.date == "2025-08-13" and abs(item.amount - Decimal('11.99')) < 0.01:
        print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# 8. PURA VIDA 69,52 em 13/03 - deveria estar no cartão 7430
print("\n8. PURA VIDA 69,52 em 13/03:")
for item in items:
    if "PURA VIDA" in item.description.upper() and item.date == "2025-03-13" and abs(item.amount - Decimal('69.52')) < 0.01:
        print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# 9. TRELA - 0,01 em 29/07 - deveria estar no cartão 7430
print("\n9. TRELA - 0,01 em 29/07:")
for item in items:
    if "TRELA" in item.description.upper() and item.date == "2025-07-29" and abs(item.amount - Decimal('0.01')) < 0.01:
        print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")


