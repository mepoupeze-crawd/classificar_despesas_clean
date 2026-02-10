import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import split_concatenated_line
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Verificar como as linhas problemáticas estão sendo separadas
print("=== Verificando separação de linhas concatenadas ===")

test_lines = [
    (176, "12/08 ORGANICO OSCAR FREIRE 92,66 ALINE I DE SOUSA (final 7430)"),
    (178, "12/08 EC PINHEIROS 3,00 13/03 PURA VIDA 06/06 69,52"),
    (180, "12/08 CAFE ZINN 69,30 31/03 CLINICA ADRIANA VI05/10 1.252,39"),
    (182, "12/08 APPLE.COM/BILL 64,90 29/04 PURA VIDA 04/04 311,02"),
    (184, "13/08 ESPORTE CLUBE PINHEIRO 16,60 12/05 PG *SHOPGEORGIA 04/05 356,68"),
    (186, "13/08 EC PINHEIROS 3,00 12/05 PG *SHOPGEORGIA - 159,60"),
    (188, "13/08 SmartBreak 11,99 17/05 CABANA CRAFTS 04/04 211,36"),
]

for line_num, line_text in test_lines:
    if line_num < len(lines):
        actual_line = lines[line_num]
        print(f"\nLinha {line_num}: {actual_line}")
        separated = split_concatenated_line(actual_line, 2025)
        print(f"Separada em {len(separated)} partes:")
        for i, part in enumerate(separated, 1):
            marker = detect_card_marker(part)
            date = extract_date(part, 2025)
            value = extract_value(part)
            marker_str = f" [MARCADOR: {marker}]" if marker else ""
            print(f"  {i}. {part[:80]}")
            print(f"     Data: {date}, Valor: {value}{marker_str}")


