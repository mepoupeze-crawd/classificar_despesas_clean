from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import detect_card_marker
import re
from decimal import Decimal

lines = extract_lines_lr_order('fatura_cartao_3.pdf')

# Encontrar seção do 9826
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    marker = detect_card_marker(line)
    if marker:
        if marker[0] == 'start' and marker[1] == '9826':
            start_idx = i
            print(f"START 9826 na linha {i}: {line[:80]}")
        elif marker[0] == 'total' and marker[1] == '9826':
            end_idx = i
            print(f"TOTAL 9826 na linha {i}: {line[:80]}")
            break

print(f"\nSeção do cartão 9826: linhas {start_idx} a {end_idx}\n")

# Verificar se há linhas ANTES do start que podem ser do 9826
print("=== Verificando linhas ANTES do start ===")
for i in range(max(0, start_idx - 10), start_idx):
    print(f"Linha {i}: {lines[i][:80]}")

# Verificar se há linhas DEPOIS do total que podem ser do 9826
print("\n=== Verificando linhas DEPOIS do total ===")
for i in range(end_idx + 1, min(len(lines), end_idx + 10)):
    marker = detect_card_marker(lines[i])
    marker_str = f" [MARCADOR: {marker[0]} -> {marker[1]}]" if marker else ""
    print(f"Linha {i}: {lines[i][:80]}{marker_str}")

# Verificar se o problema é que a linha do total tem uma transação que não está sendo extraída
print("\n=== Verificando linha do total ===")
total_line = lines[end_idx]
print(f"Linha {end_idx}: {total_line}")

# Extrair data e valor da linha do total
from card_pdf_parser.parser.rules import extract_date, extract_value
invoice_year = 2025
date_in_total = extract_date(total_line, default_year=invoice_year)
value_in_total = extract_value(total_line, prefer_last=False)
value_last_in_total = extract_value(total_line, prefer_last=True)

print(f"Data na linha total: {date_in_total}")
print(f"Valor (prefer_last=False): {value_in_total}")
print(f"Valor (prefer_last=True): {value_last_in_total}")

# Verificar se há uma transação na linha do total que não está sendo extraída
if date_in_total and value_in_total and value_in_total != Decimal('9139.39'):
    print(f"\n*** POSSÍVEL PROBLEMA: A linha do total tem uma transação com valor {value_in_total} que não está sendo extraída! ***")

