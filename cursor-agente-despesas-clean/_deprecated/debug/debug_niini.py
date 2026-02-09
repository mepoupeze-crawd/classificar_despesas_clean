import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_installments, extract_value, extract_date
import re

pdf_path = 'fatura_cartao.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Procurando transações 'niini' no PDF ===\n")

for i, line in enumerate(lines):
    line_clean = line.strip()
    if not line_clean:
        continue
    
    if "niini" in line_clean.lower():
        print(f"Linha {i+1}: '{line_clean}'")
        print(f"  Tamanho: {len(line_clean)}")
        
        # Verificar todos os padrões XX/YY na linha
        all_patterns = list(re.finditer(r'(\d{1,2})/(\d{1,2})', line_clean))
        print(f"\n  Todos os padrões XX/YY encontrados:")
        for match in all_patterns:
            num1 = int(match.group(1))
            num2 = int(match.group(2))
            print(f"    Posição {match.start()}-{match.end()}: '{match.group()}' -> {num1}/{num2}")
        
        # Extrair dados como o classificador faz
        date = extract_date(line_clean)
        value = extract_value(line_clean)
        
        if date and value:
            numero_parcela, parcelas = extract_installments(line_clean, value)
            
            print(f"\n  Data extraída: {date}")
            print(f"  Valor extraído: {value}")
            print(f"  Parcelas extraídas: {numero_parcela}/{parcelas}")
            print(f"  Esperado: None/None")
            print(f"  Resultado: {'CORRETO' if numero_parcela is None else 'ERRADO'}\n")
            print("-" * 80 + "\n")

