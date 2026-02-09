import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value
from card_pdf_parser.parser.classify import split_concatenated_line

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Verificar linha 176 em detalhe
print("=== Análise da linha 176 ===\n")
line176 = lines[176]
print(f"Linha 176 completa: {line176}")
marker = detect_card_marker(line176)
print(f"Marcador: {marker}")

# Verificar se pode ser separada
separated = split_concatenated_line(line176, 2025)
print(f"\nSeparada em {len(separated)} partes:")
for i, part in enumerate(separated, 1):
    date = extract_date(part, 2025)
    value = extract_value(part)
    marker_part = detect_card_marker(part)
    print(f"  {i}. {part}")
    print(f"     Data: {date}, Valor: {value}, Marcador: {marker_part}")

# Verificar linhas 178, 180, 182, 184 - são linhas concatenadas?
print("\n=== Verificando linhas 178, 180, 182, 184 ===\n")
for i in [178, 180, 182, 184]:
    if i < len(lines):
        line = lines[i]
        print(f"Linha {i}: {line}")
        separated = split_concatenated_line(line, 2025)
        if len(separated) > 1:
            print(f"  Separada em {len(separated)} partes:")
            for j, part in enumerate(separated, 1):
                date = extract_date(part, 2025)
                value = extract_value(part)
                print(f"    {j}. {part[:60]}")
                print(f"       Data: {date}, Valor: {value}")
        else:
            print(f"  Não é concatenada (1 parte)")


