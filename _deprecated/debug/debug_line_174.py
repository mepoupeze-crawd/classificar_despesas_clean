import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier, split_concatenated_line
from card_pdf_parser.parser.rules import extract_date, extract_value, extract_description

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Analisando linha 174 ===\n")

line_174 = lines[174]
print(f"Linha 174 completa: {line_174}")

# Separar
separated = split_concatenated_line(line_174)
print(f"\nSeparadas: {len(separated)}")
for trans in separated:
    print(f"  - {trans}")
    date = extract_date(trans)
    value = extract_value(trans)
    if date and value:
        desc = extract_description(trans, date, value)
        print(f"    Data: {date}, Valor: {value}, Descrição: '{desc}'")

# Verificar contexto
print("\n=== Contexto da linha 174 ===\n")
if 174 > 0:
    print(f"Linha 173: {lines[173][:80]}...")
print(f"Linha 174: {line_174}")
if 174 < len(lines) - 1:
    print(f"Linha 175: {lines[175][:80]}...")


