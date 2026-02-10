import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_date, extract_value, extract_description
from decimal import Decimal

line = "01/07 BRUNA CUTAIT - 0,18"
date = extract_date(line)
value = extract_value(line)
desc = extract_description(line, date, value)

print(f"Linha: {line}")
print(f"Data: {date}")
print(f"Valor: {value}")
print(f"Descrição: '{desc}'")


