import json
from card_pdf_parser.parser.extract import extract_lines_lr_order

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Procurando todas as ocorrências de ESPORTE CLUBE PINHEIRO 10,80 ===\n")

for i, line in enumerate(lines):
    if "ESPORTE CLUBE PINHEIRO" in line.upper() and "10,80" in line:
        print(f"Linha {i}: {line}")
        # Verificar contexto
        if i > 0:
            print(f"  Anterior: {lines[i-1][:80]}")
        if i < len(lines) - 1:
            print(f"  Próxima: {lines[i+1][:80]}")
        print()


