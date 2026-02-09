import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_installments, extract_value, extract_date
import re

pdf_path = 'fatura_cartao.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Debug detalhado para transações 'niini' ===\n")

for i, line in enumerate(lines):
    line_clean = line.strip()
    if not line_clean:
        continue
    
    if "niini" in line_clean.lower():
        print(f"Linha {i+1}: '{line_clean}'")
        print(f"  Tamanho: {len(line_clean)}")
        
        value = extract_value(line_clean)
        print(f"  Valor extraído: {value}")
        
        # Verificar padrão 03/03
        pattern_match = re.search(r'(\d{1,2})/(\d{1,2})', line_clean)
        if pattern_match:
            pattern_start = pattern_match.start()
            pattern_text = pattern_match.group()
            num1 = int(pattern_match.group(1))
            num2 = int(pattern_match.group(2))
            
            print(f"\n  Padrão encontrado: '{pattern_text}' na posição {pattern_start}")
            print(f"  Números: {num1}/{num2}")
            print(f"  pattern_position_ratio: {pattern_start / len(line_clean):.2%}")
            
            # Verificar contexto antes
            text_before = line_clean[max(0, pattern_start - 15):pattern_start].strip()
            descriptive_chars = len([c for c in text_before if c.isalpha()])
            print(f"  Texto antes (15 chars): '{text_before}'")
            print(f"  Caracteres alfabéticos antes: {descriptive_chars}")
            
            # Chamar função real
            numero_parcela, parcelas = extract_installments(line_clean, value)
            print(f"\n  Resultado: {numero_parcela}/{parcelas}")
            print(f"  Esperado: 3/3")
            print(f"  Status: {'CORRETO' if numero_parcela == 3 and parcelas == 3 else 'ERRADO'}\n")
            print("-" * 80 + "\n")

