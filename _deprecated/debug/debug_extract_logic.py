import re
from card_pdf_parser.parser.rules import VALUE_PATTERN

line = '14/07 niini 03/03 120,08'

# Simular a lógica da função
value_matches = list(VALUE_PATTERN.finditer(line))
if value_matches:
    value_match = value_matches[-1]
    value_start = value_match.start()
    
    print(f"Valor encontrado: '{value_match.group()}' na posição {value_start}")
    
    search_start = max(0, value_start - 50)
    text_before_value = line[search_start:value_start]
    
    print(f"text_before_value: '{text_before_value}'")
    print(f"search_start: {search_start}, value_start: {value_start}")
    
    installment_matches = list(re.finditer(r'(\d{1,2})/(\d{1,2})', text_before_value))
    print(f"\nPadrões encontrados em text_before_value: {len(installment_matches)}")
    
    for i, match in enumerate(installment_matches):
        print(f"  {i}: '{match.group()}' na posição {match.start()} (relativa ao text_before_value)")
        print(f"     Posição absoluta na linha: {search_start + match.start()}")
    
    if installment_matches:
        installment_match = installment_matches[-1]
        print(f"\nÚltimo padrão selecionado: '{installment_match.group()}'")
        print(f"  Posição absoluta: {search_start + installment_match.start()}")

