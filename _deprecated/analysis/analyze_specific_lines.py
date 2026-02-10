import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import split_concatenated_line
from card_pdf_parser.parser.rules import extract_date, extract_value
import re

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Analisando linhas específicas ===\n")

# Linhas problemáticas
problem_lines = [
    (178, "12/08 EC PINHEIROS 3,00 13/03 PURA VIDA 06/06 69,52"),
    (182, "12/08 APPLE.COM/BILL 64,90 29/04 PURA VIDA 04/04 311,02"),
    (184, "13/08 ESPORTE CLUBE PINHEIRO 16,60 12/05 PG *SHOPGEORGIA 04/05 356,68"),
    (188, "13/08 SmartBreak 11,99 17/05 CABANA CRAFTS 04/04 211,36"),
]

for idx, line_text in problem_lines:
    print(f"Linha {idx}: {line_text}")
    
    # Analisar estrutura
    date_pattern = re.compile(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b')
    value_pattern = re.compile(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}')
    
    date_matches = list(date_pattern.finditer(line_text))
    value_matches = list(value_pattern.finditer(line_text))
    
    print(f"  {len(date_matches)} datas, {len(value_matches)} valores")
    for i, dm in enumerate(date_matches):
        print(f"    Data {i+1}: {dm.group(0)} em posição {dm.start()}")
    for i, vm in enumerate(value_matches):
        print(f"    Valor {i+1}: {vm.group(0)} em posição {vm.start()}")
    
    # Separar
    separated = split_concatenated_line(line_text)
    print(f"  Separadas: {len(separated)}")
    for trans in separated:
        print(f"    - {trans}")
        date = extract_date(trans)
        value = extract_value(trans)
        print(f"      Data: {date}, Valor: {value}")
    print()


