import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_date, extract_value, extract_description
from decimal import Decimal

line = "12/08 ESPORTE CLUBE PINHEIRO 10,80 Lançamentos no cartão (final 9826) 9.139,39"

print(f"Linha: {line}\n")

# Encontrar todos os valores
import re
value_pattern = re.compile(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}')
value_matches = list(value_pattern.finditer(line))
print("Valores encontrados:")
for match in value_matches:
    print(f"  {match.start()}-{match.end()}: {match.group(0)}")

date = extract_date(line)
value = extract_value(line)
desc = extract_description(line, date, value)

print(f"\nData extraída: {date}")
print(f"Valor extraído: {value}")
print(f"Descrição extraída: '{desc}'")

# Tentar com prefer_last=False
value_first = extract_value(line, prefer_last=False)
print(f"\nValor extraído (prefer_last=False): {value_first}")


