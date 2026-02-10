import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_installments, extract_value
import re

pdf_path = 'fatura_cartao.pdf'
lines = extract_lines_lr_order(pdf_path)

# Transações problemáticas - buscar por descrição
problematic_descriptions = [
    "MP *JOAOTAXISP",
    "APPLE.COM/BILL",
    "SmartBreak",
    "EC PINHEIROS",
    "UBER* TRIP",
]

print("=== Linhas problemáticas do PDF ===\n")

found_count = 0
for i, line in enumerate(lines):
    line_clean = line.strip()
    if not line_clean:
        continue
    
    for desc in problematic_descriptions:
        if desc in line_clean:
            value = extract_value(line_clean)
            if value:
                numero_parcela, parcelas = extract_installments(line_clean, value)
                
                # Verificar todos os padrões XX/YY na linha
                all_patterns = list(re.finditer(r'(\d{1,2})/(\d{1,2})', line_clean))
                
                print(f"Linha {i+1}: '{line_clean[:100]}...'")
                print(f"  Valor: {value}")
                print(f"  Parcelas extraídas: {numero_parcela}/{parcelas}")
                print(f"  Esperado: None/None")
                if all_patterns:
                    print(f"  Padrões XX/YY encontrados:")
                    for match in all_patterns:
                        num1, num2 = match.groups()
                        print(f"    Posição {match.start()}-{match.end()}: '{match.group()}' -> {num1}/{num2}")
                print()
                found_count += 1
                if found_count >= 10:  # Limitar para não ficar muito longo
                    break
    if found_count >= 10:
        break
