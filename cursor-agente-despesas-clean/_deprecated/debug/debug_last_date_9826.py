import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Encontrar a última data do cartão 9826 antes do reset
print("=== Procurando última data do cartão 9826 antes do reset ===")

# Procurar linha 174 que tem o marcador "total" do cartão 9826
for i in range(170, 180):
    if i < len(lines):
        marker = detect_card_marker(lines[i])
        date = extract_date(lines[i], 2025)
        value = extract_value(lines[i])
        if marker:
            print(f"Linha {i}: {lines[i][:100]}")
            print(f"  Marcador: {marker}, Data: {date}, Valor: {value}")

# Procurar transações do cartão 9826 antes da linha 174
print("\n=== Transações do cartão 9826 antes do reset ===")
for i in range(150, 175):
    if i < len(lines):
        date = extract_date(lines[i], 2025)
        value = extract_value(lines[i])
        if date and value:
            print(f"Linha {i}: {lines[i][:80]}")
            print(f"  Data: {date}, Valor: {value}")


