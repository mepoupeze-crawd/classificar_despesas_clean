import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.rules import detect_card_marker, extract_value, extract_date

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Encontrar linha 174
line174 = lines[174]
print(f"Linha 174: {line174}")
print(f"Marcador: {detect_card_marker(line174)}")
print(f"Data extraída: {extract_date(line174, 2025)}")
print(f"Valor extraído (prefer_last=False): {extract_value(line174, prefer_last=False)}")
print(f"Valor extraído (prefer_last=True): {extract_value(line174, prefer_last=True)}")

# Processar e verificar o que acontece
invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)

# Simular processamento até linha 174
print("\n=== Simulando processamento até linha 174 ===")
current_card = None
for i in range(170, 180):
    line = lines[i]
    marker = detect_card_marker(line)
    if marker:
        kind, card = marker
        if kind == "start":
            current_card = card
            print(f"Linha {i}: START card {card}")
        elif kind == "total":
            print(f"Linha {i}: TOTAL card {card} (current_card antes: {current_card})")
            # Verificar se tem transação
            date = extract_date(line, invoice_year)
            value = extract_value(line, prefer_last=False)
            print(f"  Tem transação? date={date}, value={value}")
            if date and value and current_card:
                print(f"  Transação seria processada com card {current_card}")
            current_card = None
            print(f"  current_card depois: {current_card}")
    else:
        date = extract_date(line, invoice_year)
        value = extract_value(line)
        if date and value:
            print(f"Linha {i}: Transação - date={date}, value={value}, card={current_card}")

# Verificar quantas transações do cartão 9826 existem antes da linha 174
print("\n=== Contando transações do cartão 9826 ===")
items, rejects = classifier.classify_lines(lines)
card_9826_items = [item for item in items if item.last4 and "9826" in item.last4]
print(f"Total de transações do cartão 9826: {len(card_9826_items)}")

# Verificar qual transação corresponde à linha 174
print("\n=== Procurando transação da linha 174 ===")
for item in card_9826_items:
    if "ESPORTE CLUBE PINHEIRO" in item.description.upper() and abs(item.amount - Decimal('10.80')) < 0.01:
        print(f"Encontrada: {item.date} | {item.description} | {item.amount}")

