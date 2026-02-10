import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_installments, extract_value, extract_date

pdf_path = 'fatura_cartao.pdf'
lines = extract_lines_lr_order(pdf_path)

# Procurar linhas específicas que têm problemas
problematic_lines = [
    ("01/09 MP *JOAOTAXISP 36,65", "MP *JOAOTAXISP"),
    ("01/09 APPLE.COM/BILL 39,90", "APPLE.COM/BILL"),
    ("02/09 UBER* TRIP 33,45", "UBER* TRIP"),
]

print("=== Testando linhas problemáticas ===\n")

for line_text, expected_desc in problematic_lines:
    print(f"Linha: {line_text}")
    value = extract_value(line_text)
    numero_parcela, parcelas = extract_installments(line_text, value)
    print(f"  Valor: {value}")
    print(f"  Parcelas extraídas: {numero_parcela}/{parcelas}")
    print(f"  Esperado: None/None")
    print(f"  Resultado: {'CORRETO' if numero_parcela is None else 'ERRADO'}\n")

# Agora testar com as linhas reais do PDF
print("\n=== Testando linhas reais do PDF ===\n")
for i, line in enumerate(lines):
    line_clean = line.strip()
    if not line_clean:
        continue
    
    if "MP *JOAOTAXISP" in line_clean or "APPLE.COM/BILL" in line_clean or ("UBER* TRIP" in line_clean and "01/09" in line_clean or "02/09" in line_clean):
        date = extract_date(line_clean)
        value = extract_value(line_clean)
        if date and value:
            numero_parcela, parcelas = extract_installments(line_clean, value)
            print(f"Linha {i}: {line_clean[:60]}")
            print(f"  Parcelas: {numero_parcela}/{parcelas}")
            print(f"  Esperado: None/None")
            print(f"  Resultado: {'CORRETO' if numero_parcela is None else 'ERRADO'}\n")

