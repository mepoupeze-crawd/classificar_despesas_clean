import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value
from card_pdf_parser.parser.classify import split_concatenated_line

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Verificar linhas 178, 180, 182, 184 e ver quais cartões estão sendo atribuídos
print("=== Verificando atribuição de cartões para linhas concatenadas ===\n")

invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)

# Simular processamento até a linha 176
for i in range(174):
    line = lines[i]
    marker = detect_card_marker(line)
    if marker:
        kind, card = marker
        if kind == "start":
            classifier.current_card = card
        elif kind == "total":
            classifier.last_reset_card = card

# Processar linha 174 (total marker para 9826)
line174 = lines[174]
marker174 = detect_card_marker(line174)
print(f"Linha 174: {line174}")
print(f"  Marcador: {marker174}")
print(f"  current_card antes: {classifier.current_card}")
# Processar marcador
if marker174 and marker174[0] == "total":
    classifier.last_reset_card = marker174[1]
    # Não resetar current_card
print(f"  current_card depois: {classifier.current_card}")
print(f"  last_reset_card: {classifier.last_reset_card}")
print(f"  previous_card_before_start: {classifier.previous_card_before_start}")

# Processar linha 176 (start marker para 7430)
line176 = lines[176]
marker176 = detect_card_marker(line176)
print(f"\nLinha 176: {line176}")
print(f"  Marcador: {marker176}")
print(f"  current_card antes: {classifier.current_card}")
# Processar marcador
if marker176 and marker176[0] == "start":
    classifier.previous_card_before_start = classifier.current_card
    classifier.current_card = marker176[1]
print(f"  current_card depois: {classifier.current_card}")
print(f"  previous_card_before_start: {classifier.previous_card_before_start}")

# Verificar última data do cartão 9826
print(f"\n  last_date_by_card['9826']: {classifier.last_date_by_card.get('9826')}")

# Processar linha 178 (primeira parte deve ser 9826)
line178 = lines[178]
print(f"\nLinha 178: {line178}")
separated178 = split_concatenated_line(line178, invoice_year)
print(f"  Separada em {len(separated178)} partes:")
for j, part in enumerate(separated178):
    date = extract_date(part, invoice_year)
    value = extract_value(part)
    print(f"    Parte {j}: {part[:60]}")
    print(f"      Data: {date}, Valor: {value}")
    if date:
        last_prev_date = classifier.last_date_by_card.get('9826')
        if last_prev_date:
            from datetime import datetime
            last_prev_date_obj = datetime.strptime(last_prev_date, "%Y-%m-%d")
            current_date_obj = datetime.strptime(date, "%Y-%m-%d")
            days_diff = abs((current_date_obj - last_prev_date_obj).days)
            print(f"      Diferença de dias com 9826: {days_diff}")
            print(f"      previous_card_before_start: {classifier.previous_card_before_start}")
            print(f"      Deve usar 9826? {days_diff <= 7 and classifier.previous_card_before_start == '9826'}")


