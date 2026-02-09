import re
from card_pdf_parser.parser.rules import VALUE_PATTERN, DATE_PATTERN_FULL, DATE_PATTERN_SHORT

line = '14/07 niini 03/03 120,08'
value = 120.08

# Simular exatamente a lógica da função até a validação XX/XX
value_matches = list(VALUE_PATTERN.finditer(line))
value_match = value_matches[-1]
value_start = value_match.start()

search_start = max(0, value_start - 50)
text_before_value = line[search_start:value_start]

installment_matches = list(re.finditer(r'(\d{1,2})/(\d{1,2})', text_before_value))
installment_match = installment_matches[-1]

numero_parcela = int(installment_match.group(1))
parcelas = int(installment_match.group(2))

pattern_start_in_line = search_start + installment_match.start()
line_length = len(line)
pattern_position_ratio = pattern_start_in_line / line_length if line_length > 0 else 1.0
context_before = line[max(0, pattern_start_in_line - 20):pattern_start_in_line].strip().lower()

parcel_keywords = ['parcela', 'parcelas', 'x de', 'de x', 'vezes']
has_parcel_keyword = any(keyword in context_before for keyword in parcel_keywords)

print(f"Padrão: {numero_parcela}/{parcelas}")
print(f"numero_parcela == parcelas: {numero_parcela == parcelas}")
print(f"pattern_position_ratio: {pattern_position_ratio:.2%}")

# Validação XX/XX (linha 382)
if numero_parcela == parcelas:
    text_before = line[max(0, pattern_start_in_line - 15):pattern_start_in_line].strip()
    descriptive_chars_before = len([c for c in text_before if c.isalpha()])
    
    print(f"\nValidação XX/XX:")
    print(f"  text_before: '{text_before}'")
    print(f"  descriptive_chars_before: {descriptive_chars_before}")
    print(f"  pattern_position_ratio > 0.50: {pattern_position_ratio > 0.50}")
    print(f"  has_parcel_keyword: {has_parcel_keyword}")
    
    if pattern_position_ratio > 0.50:
        if descriptive_chars_before >= 3:
            print("  -> ACEITO: pattern_position_ratio > 0.50 e descriptive_chars_before >= 3")
        elif not has_parcel_keyword:
            print("  -> BLOQUEADO: pattern_position_ratio > 0.50 mas descriptive_chars_before < 3 e sem palavra-chave")
            exit()
    elif not has_parcel_keyword and descriptive_chars_before < 8:
        print("  -> BLOQUEADO: pattern_position_ratio <= 0.50 e sem palavra-chave e descriptive_chars_before < 8")
        exit()

print("\nPASSOU validação XX/XX!")

