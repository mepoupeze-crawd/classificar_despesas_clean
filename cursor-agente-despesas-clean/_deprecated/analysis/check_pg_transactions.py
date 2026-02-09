import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_date, extract_value, extract_description

pdf_path = 'fatura_cartao.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Procurando linhas com PG *SHOPGEORGIA e PG *AMARO ===\n")

for i, line in enumerate(lines):
    if "PG *SHOPGEORGIA" in line.upper() and "159" in line:
        print(f"Linha {i}: {line}")
        date = extract_date(line)
        value = extract_value(line)
        desc = extract_description(line, date, value)
        print(f"  Data: {date}, Valor: {value}, Descrição: '{desc}'")
        print()
    if "PG *AMARO" in line.upper() and "209" in line:
        print(f"Linha {i}: {line}")
        date = extract_date(line)
        value = extract_value(line)
        desc = extract_description(line, date, value)
        print(f"  Data: {date}, Valor: {value}, Descrição: '{desc}'")
        print()


