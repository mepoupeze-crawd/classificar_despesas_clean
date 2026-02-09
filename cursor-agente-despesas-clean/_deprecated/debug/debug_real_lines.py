import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_installments, extract_value, extract_date
from card_pdf_parser.parser.classify import LineClassifier
from decimal import Decimal

pdf_path = 'fatura_cartao.pdf'
lines = extract_lines_lr_order(pdf_path)

# Procurar linhas que contêm as transações problemáticas
problematic_descriptions = [
    "MP *JOAOTAXISP",
    "APPLE.COM/BILL",
    "SmartBreak",
    "EC PINHEIROS",
    "UBER* TRIP",
]

print("=== Linhas reais do PDF que contêm transações problemáticas ===\n")

for i, line in enumerate(lines):
    line_clean = line.strip()
    if not line_clean:
        continue
    
    # Verificar se contém alguma das descrições problemáticas
    for desc in problematic_descriptions:
        if desc in line_clean:
            # Extrair dados como o classificador faz
            date = extract_date(line_clean)
            value = extract_value(line_clean)
            
            if date and value:
                numero_parcela, parcelas = extract_installments(line_clean, value)
                
                print(f"Linha {i}: {line_clean}")
                print(f"  Data: {date}")
                print(f"  Valor: {value}")
                print(f"  Parcelas: {numero_parcela}/{parcelas}")
                print(f"  Descrição esperada: {desc}")
                print()

