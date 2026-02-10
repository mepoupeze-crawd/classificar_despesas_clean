import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import detect_card_marker, extract_value, extract_date

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Encontrar onde cada cartão começa e termina
print("=== Marcadores de cartão ===")
card_markers = []
for i, line in enumerate(lines):
    marker = detect_card_marker(line)
    if marker:
        marker_type, marker_card = marker
        card_markers.append((i, marker_type, marker_card, line))
        print(f"Linha {i} [{marker_type}]: {marker_card} - {line[:80]}")

# Verificar linhas problemáticas
print("\n=== Linha 174 (com subtotal) ===")
print(f"Linha 174: {lines[174]}")
print(f"Valor extraído: {extract_value(lines[174])}")

print("\n=== Linha 184 (concatenada) ===")
print(f"Linha 184: {lines[184]}")

# Verificar linhas ao redor do marcador de cartão 9826
print("\n=== Linhas ao redor do marcador de cartão 9826 ===")
for marker in card_markers:
    if marker[2] == '9826':
        idx = marker[0]
        print(f"\nMarcador na linha {idx}: {marker[1]}")
        print("Linhas próximas:")
        for i in range(max(0, idx-3), min(len(lines), idx+10)):
            marker_info = ""
            if i == idx:
                marker_info = " <-- MARCADOR"
            print(f"  {i}: {lines[i][:100]}{marker_info}")

