import re
from card_pdf_parser.parser.rules import VALUE_PATTERN, DATE_PATTERN_FULL, DATE_PATTERN_SHORT

line = '14/07 niini 03/03 120,08'
value = 120.08

# Simular exatamente a lógica da função
value_matches = list(VALUE_PATTERN.finditer(line))
value_match = value_matches[-1]
value_start = value_match.start()

search_start = max(0, value_start - 50)
text_before_value = line[search_start:value_start]

installment_matches = list(re.finditer(r'(\d{1,2})/(\d{1,2})', text_before_value))
installment_match = installment_matches[-1]  # Pegar o último (03/03)

numero_parcela = int(installment_match.group(1))
parcelas = int(installment_match.group(2))

pattern_start_in_line = search_start + installment_match.start()
line_length = len(line)
pattern_position_ratio = pattern_start_in_line / line_length if line_length > 0 else 1.0
context_before = line[max(0, pattern_start_in_line - 20):pattern_start_in_line].strip().lower()

print(f"Padrão: {numero_parcela}/{parcelas}")
print(f"pattern_start_in_line: {pattern_start_in_line}")
print(f"pattern_position_ratio: {pattern_position_ratio:.2%}")
print(f"context_before: '{context_before}'")
print(f"len(context_before): {len(context_before)}")

# Validação linha 313
if pattern_start_in_line < 10 and 1 <= numero_parcela <= 12 and 1 <= parcelas <= 31:
    print("\nBLOQUEADO na linha 313: pattern_start_in_line < 10")
    exit()

# Validação linha 318-319
if 1 <= numero_parcela <= 12 and 1 <= parcelas <= 31:
    if pattern_position_ratio < 0.15:
        print("\nBLOQUEADO na linha 319: pattern_position_ratio < 0.15")
        exit()
    
    text_around = line[max(0, pattern_start_in_line - 20):min(len(line), pattern_start_in_line + 20)]
    if DATE_PATTERN_FULL.search(text_around):
        print("\nBLOQUEADO na linha 322: DATE_PATTERN_FULL encontrado")
        exit()
    
    parcel_keywords = ['parcela', 'parcelas', 'x de', 'de x', 'vezes']
    has_parcel_keyword = any(keyword in context_before for keyword in parcel_keywords)
    context_descriptive_chars = len([c for c in context_before if c.isalpha()])
    
    print(f"\nhas_parcel_keyword: {has_parcel_keyword}")
    print(f"context_descriptive_chars: {context_descriptive_chars}")
    
    # Validação linha 335-338
    if pattern_position_ratio >= 0.15:
        condition = (pattern_position_ratio > 0.40 and len(context_before) >= 10 and 
                     (has_parcel_keyword or context_descriptive_chars >= 5))
        print(f"\nCondição linha 336: pattern_position_ratio > 0.40: {pattern_position_ratio > 0.40}")
        print(f"  len(context_before) >= 10: {len(context_before) >= 10}")
        print(f"  has_parcel_keyword or context_descriptive_chars >= 5: {has_parcel_keyword or context_descriptive_chars >= 5}")
        print(f"  Resultado da condição: {condition}")
        
        if not condition:
            print("\nBLOQUEADO na linha 337: condição não satisfeita")
            exit()

print("\nPASSOU todas as validações até a linha 338!")

