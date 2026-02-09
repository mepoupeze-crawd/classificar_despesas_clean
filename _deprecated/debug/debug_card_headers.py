from card_pdf_parser.parser.extract import extract_lines_lr_order
import re

lines = extract_lines_lr_order('fatura_cartao_3.pdf')

# Padrão para cabeçalho de cartão
CARD_HEADER_PATTERN = re.compile(r"aline i de sousa\s*\(final\s*(\d{4})\)", re.IGNORECASE)

# Procurar por linhas com transações problemáticas
problem_dates = ['2025-08-12', '2025-08-13']
problem_descriptions = ['APPLE.COM/BILL', 'CAFE ZINN', 'EC PINHEIROS', 'ORGANICO OSCAR FREIRE', 'ESPORTE CLUBE PINHEIRO', 'SmartBreak']

print("Procurando por cabeçalhos de cartão e transações problemáticas...")
print()

# Encontrar índices das linhas problemáticas
for i, line in enumerate(lines):
    normalized = line.lower()
    
    # Verificar se é um cabeçalho de cartão
    header_match = CARD_HEADER_PATTERN.search(normalized)
    if header_match:
        last4 = header_match.group(1)
        print(f"Linha {i}: CABEÇALHO CARTÃO {last4}")
        print(f"  {line[:100]}")
        print()
    
    # Verificar se é uma transação problemática
    for desc in problem_descriptions:
        if desc.lower() in normalized and any(date.replace('-', '/') in line for date in problem_dates):
            print(f"Linha {i}: TRANSAÇÃO PROBLEMÁTICA")
            print(f"  {line[:150]}")
            print()
