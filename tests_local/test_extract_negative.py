from card_pdf_parser.parser.rules import extract_value
from decimal import Decimal

# Testar extração de valor negativo
test_lines = [
    "29/07 TRELA*Pedido Trela - 0,01",
    "29/07 TRELA*Pedido Trela- 0,01",
    "29/07 TRELA*Pedido Trela -0,01",
    "29/07 TRELA*Pedido Trela 0,01",
]

for line in test_lines:
    print(f"\nLinha: {line}")
    value = extract_value(line)
    print(f"Valor extraído: {value}")


