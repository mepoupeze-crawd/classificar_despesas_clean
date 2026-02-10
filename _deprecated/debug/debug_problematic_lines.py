import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier, split_concatenated_line
from card_pdf_parser.parser.rules import extract_date, extract_value, extract_description

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Analisando linhas problemáticas ===\n")

problematic_lines = [
    (178, "12/08 EC PINHEIROS 3,00 13/03 PURA VIDA 06/06 69,52"),
    (188, "13/08 SmartBreak 11,99 17/05 CABANA CRAFTS 04/04 211,36"),
    (136, "05/08 ORGANICO OSCAR FREIRE 95,48 20/08 RC CAFE LTDA 21,80"),
    (70, "01/07 BRUNA CUTAIT - 0,18"),
    (78, "30/07 ESPORTE CLUBE PINHEIRO 10,80"),
]

for idx, line_text in problematic_lines:
    print(f"Linha {idx}: {line_text}")
    
    # Verificar se está sendo separada
    separated = split_concatenated_line(line_text)
    print(f"  Separadas: {len(separated)}")
    for trans in separated:
        print(f"    - {trans}")
        date = extract_date(trans)
        value = extract_value(trans)
        if date and value:
            desc = extract_description(trans, date, value)
            print(f"      Data: {date}, Valor: {value}, Descrição: '{desc}'")
    print()

# Verificar linha específica do ESPORTE CLUBE PINHEIRO
print("\n=== Verificando ESPORTE CLUBE PINHEIRO 10,80 ===\n")
for i, line in enumerate(lines):
    if "ESPORTE CLUBE PINHEIRO" in line.upper() and "10,80" in line:
        print(f"Linha {i}: {line}")
        # Verificar contexto (linhas antes e depois)
        if i > 0:
            print(f"  Anterior: {lines[i-1][:80]}")
        if i < len(lines) - 1:
            print(f"  Próxima: {lines[i+1][:80]}")
        break


