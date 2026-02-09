import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Procurar linhas com PURA VIDA 69,52 e TRELA - 0,01
print("=== Procurando transações faltantes ===")

# PURA VIDA 69,52
print("\n1. PURA VIDA 69,52:")
for i, line in enumerate(lines):
    if "PURA VIDA" in line.upper() and "69" in line and "52" in line:
        print(f"   Linha {i}: {line}")
        date = extract_date(line, 2025)
        value = extract_value(line)
        print(f"   Data: {date}, Valor: {value}")

# TRELA - 0,01
print("\n2. TRELA - 0,01:")
for i, line in enumerate(lines):
    if "TRELA" in line.upper() and "0,01" in line:
        print(f"   Linha {i}: {line}")
        date = extract_date(line, 2025)
        value = extract_value(line)
        print(f"   Data: {date}, Valor: {value}")

# Processar e verificar
invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)

print("\n=== Verificando transações extraídas ===")
# PURA VIDA 69,52
pura_vida_items = [item for item in items if "PURA VIDA" in item.description.upper() and abs(item.amount - Decimal('69.52')) < 0.01]
print(f"\nPURA VIDA 69,52 encontradas: {len(pura_vida_items)}")
for item in pura_vida_items:
    print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# TRELA - 0,01
trela_items = [item for item in items if "TRELA" in item.description.upper() and abs(item.amount - Decimal('0.01')) < 0.01]
print(f"\nTRELA - 0,01 encontradas: {len(trela_items)}")
for item in trela_items:
    print(f"   {item.date} | {item.description} | {item.amount} | {item.last4}")

# Verificar rejeições relacionadas
print("\n=== Verificando rejeições relacionadas ===")
for reject in rejects:
    if "PURA VIDA" in reject.line.upper() or "TRELA" in reject.line.upper():
        print(f"   {reject.line[:80]} - {reject.reason}")


