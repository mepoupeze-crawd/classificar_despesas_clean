import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_installments, extract_value
import re

pdf_path = 'fatura_cartao.pdf'
lines = extract_lines_lr_order(pdf_path)

# Encontrar linhas específicas que têm problemas
problematic_descriptions = [
    "MP *JOAOTAXISP",
    "APPLE.COM/BILL",
    "SmartBreak",
    "EC PINHEIROS",
    "UBER* TRIP",
]

print("=== Testando linhas problemáticas ===\n")

for i, line in enumerate(lines):
    line_clean = line.strip()
    if not line_clean:
        continue
    
    # Verificar se contém alguma das descrições problemáticas
    for desc in problematic_descriptions:
        if desc in line_clean:
            # Verificar todos os padrões XX/YY na linha
            all_patterns = list(re.finditer(r'(\d{1,2})/(\d{1,2})', line_clean))
            
            print(f"Linha {i+1}: '{line_clean}'")
            print(f"  Tamanho: {len(line_clean)}")
            
            if all_patterns:
                print(f"  Todos os padrões XX/YY encontrados:")
                for match in all_patterns:
                    print(f"    Posição {match.start()}-{match.end()}: '{match.group()}' -> {match.group(1)}/{match.group(2)}")
            
            value = extract_value(line_clean)
            if value:
                value_start = line_clean.find(str(value).replace('.', ','))
                if value_start == -1:
                    # Tentar encontrar o valor de outra forma
                    value_str = str(value).replace('.', ',')
                    # Procurar padrão de valor monetário
                    value_match = re.search(r'\d+[.,]\d{2}', line_clean)
                    if value_match:
                        value_start = value_match.start()
                
                print(f"  Valor encontrado: {value} (posição aproximada: {value_start})")
                
                # Simular a lógica de extract_installments
                search_start = max(0, value_start - 50)
                text_before_value = line_clean[search_start:value_start]
                print(f"  Texto antes do valor (posição {search_start}-{value_start}): '{text_before_value}'")
                
                installment_matches = list(re.finditer(r'(\d{1,2})/(\d{1,2})', text_before_value))
                if installment_matches:
                    installment_match = installment_matches[-1]
                    pattern_start_in_line = search_start + installment_match.start()
                    line_length = len(line_clean)
                    pattern_position_ratio = pattern_start_in_line / line_length if line_length > 0 else 1.0
                    
                    numero_parcela = int(installment_match.group(1))
                    parcelas = int(installment_match.group(2))
                    
                    print(f"  Padrão encontrado: {numero_parcela}/{parcelas}")
                    print(f"  pattern_start_in_line: {pattern_start_in_line}")
                    print(f"  pattern_position_ratio: {pattern_position_ratio:.2%}")
                    print(f"  Validação 1-12/1-31: {1 <= numero_parcela <= 12 and 1 <= parcelas <= 31}")
                    print(f"  Validação < 10: {pattern_start_in_line < 10}")
                    print(f"  Validação < 15%: {pattern_position_ratio < 0.15}")
            
            numero_parcela, parcelas = extract_installments(line_clean, value)
            print(f"  Resultado extract_installments: {numero_parcela}/{parcelas}")
            print(f"  Esperado: None/None")
            print(f"  Status: {'CORRETO' if numero_parcela is None else 'ERRADO'}\n")
            break

