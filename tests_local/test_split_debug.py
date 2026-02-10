from card_pdf_parser.parser.classify import split_concatenated_line
from card_pdf_parser.parser.rules import extract_date, extract_value

test_lines = [
    "13/08 ESPORTE CLUBE PINHEIRO 16,60 12/05 PG *SHOPGEORGIA 04/05 356,68",
    "12/08 EC PINHEIROS 3,00 13/03 PURA VIDA 06/06 69,52",
    "03/08 IFD*RECANTO DOS BOLOS 51,79 13/08 JOAOTAXISP 40,25",
]

for line in test_lines:
    print(f"\nLinha: {line}")
    separated = split_concatenated_line(line)
    print(f"Separada em {len(separated)} transações:")
    for i, trans in enumerate(separated, 1):
        date = extract_date(trans)
        value = extract_value(trans)
        print(f"  {i}. {trans}")
        print(f"     Data: {date}, Valor: {value}")


