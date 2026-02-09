import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value

pdf_path = 'fatura_cartao_2.pdf'
lines = extract_lines_lr_order(pdf_path)

# Processar e verificar transações problemáticas
invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)

# Verificar transações específicas
print("=== Transações problemáticas ===")

# 1. UNICEF*UNICEF BRASIL em 2025-10-05
print("\n1. UNICEF*UNICEF BRASIL em 2025-10-05:")
unicef_items = [item for item in items if "UNICEF" in item.description.upper() and item.date == "2025-10-05"]
for item in unicef_items:
    print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# 2. RAPPI*Rappi Brasil Int em 2025-10-23
print("\n2. RAPPI*Rappi Brasil Int em 2025-10-23:")
rappi_items = [item for item in items if "RAPPI" in item.description.upper() and item.date == "2025-10-23"]
for item in rappi_items:
    print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# 3. SEG CARTAO PROTEGIDO em 2025-10-16
print("\n3. SEG CARTAO PROTEGIDO em 2025-10-16:")
seg_items = [item for item in items if "SEG CARTAO" in item.description.upper() and item.date == "2025-10-16"]
for item in seg_items:
    print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# Verificar linhas ao redor dessas transações
print("\n=== Procurando linhas com essas transações ===")
for i, line in enumerate(lines):
    if "UNICEF" in line.upper() and "2025-10-05" not in str(i):  # Verificar se não é a data já processada
        marker = detect_card_marker(line)
        date = extract_date(line, 2025)
        value = extract_value(line)
        if date == "2025-10-05" or "05/10" in line:
            print(f"Linha {i}: {line[:100]}")
            print(f"  Marcador: {marker}, Data: {date}, Valor: {value}")


