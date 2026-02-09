import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import detect_card_marker, extract_value, extract_subtotal

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Verificar como os subtotais estão sendo extraídos
print("=== Extração de subtotais ===")
subtotals = {}
current_card_for_subtotal = None

for i, line in enumerate(lines):
    marker = detect_card_marker(line)
    if marker:
        marker_type, marker_card = marker
        if marker_type == "start":
            current_card_for_subtotal = marker_card
            print(f"Linha {i}: START card {marker_card}")
        elif marker_type == "total":
            print(f"\nLinha {i}: TOTAL card {marker_card}")
            print(f"  Linha: {line[:100]}")
            subtotal_extracted = extract_value(line)
            subtotal_pattern = extract_subtotal(line)
            print(f"  extract_value(): {subtotal_extracted}")
            print(f"  extract_subtotal(): {subtotal_pattern}")
            if subtotal_extracted:
                subtotals[marker_card] = subtotal_extracted
                print(f"  Subtotal armazenado: {subtotal_extracted}")
            current_card_for_subtotal = None

print("\n=== Subtotais extraídos ===")
for card, subtotal in subtotals.items():
    print(f"Card {card}: {subtotal}")

