from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value
import re
from decimal import Decimal

lines = extract_lines_lr_order('fatura_cartao_3.pdf')

# Encontrar seção do 9826
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    marker = detect_card_marker(line)
    if marker:
        if marker[0] == 'start' and marker[1] == '9826':
            start_idx = i
        elif marker[0] == 'total' and marker[1] == '9826':
            end_idx = i
            break

print(f"Seção do cartão 9826: linhas {start_idx} a {end_idx}\n")

# Analisar TODAS as transações na seção do 9826
# Uma transação tem: data + descrição + valor
invoice_year = 2025
all_transactions = []

for i in range(start_idx, end_idx + 1):
    line = lines[i]
    marker = detect_card_marker(line)
    
    # Pular marcadores
    if marker:
        continue
    
    # Extrair data e valores
    date = extract_date(line, default_year=invoice_year)
    value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
    date_matches = list(re.finditer(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', line))
    
    if date and value_matches:
        is_concatenated = len(date_matches) >= 2 and len(value_matches) >= 2
        
        if is_concatenated:
            # Linha concatenada - pode ter duas transações
            # Primeira transação: primeira data + primeiro valor
            # Segunda transação: segunda data + segundo valor
            first_date = extract_date(line, default_year=invoice_year)
            first_value = extract_value(line, prefer_last=False)
            second_date_match = date_matches[1] if len(date_matches) > 1 else None
            second_value = extract_value(line, prefer_last=True)
            
            if first_date and first_value:
                all_transactions.append({
                    'line_num': i,
                    'date': first_date,
                    'value': abs(first_value) if first_value > 0 else -abs(first_value),
                    'is_negative': first_value < 0,
                    'is_left': True,
                    'line': line[:70]
                })
            
            if second_date_match and second_value:
                # Extrair segunda data
                day2 = int(second_date_match.group(1))
                month2 = int(second_date_match.group(2))
                year2 = int(second_date_match.group(3)) if len(second_date_match.groups()) > 2 and second_date_match.group(3) else invoice_year
                if len(str(year2)) == 2:
                    year2 = 2000 + year2
                second_date = f"{year2}-{month2:02d}-{day2:02d}"
                
                all_transactions.append({
                    'line_num': i,
                    'date': second_date,
                    'value': abs(second_value) if second_value > 0 else -abs(second_value),
                    'is_negative': second_value < 0,
                    'is_left': False,
                    'line': line[:70]
                })
        else:
            # Linha não concatenada - uma transação
            value = extract_value(line, prefer_last=False)
            if value:
                all_transactions.append({
                    'line_num': i,
                    'date': date,
                    'value': abs(value) if value > 0 else -abs(value),
                    'is_negative': value < 0,
                    'is_left': False,
                    'line': line[:70]
                })

# Calcular total
total_saida = Decimal('0')
total_entrada = Decimal('0')
for trans in all_transactions:
    if trans['is_negative']:
        total_entrada += trans['value']
    else:
        total_saida += trans['value']

total = total_saida - total_entrada

print(f"Total de transações encontradas: {len(all_transactions)}")
print(f"Total saída: {total_saida}")
print(f"Total entrada: {total_entrada}")
print(f"Total líquido: {total}")
print(f"Subtotal do PDF: 9139.39")
print(f"Diferença: {abs(total - Decimal('9139.39'))}")

# Verificar se precisamos contar apenas valores da direita ou ambos
print("\n=== Verificando estratégias ===")
total_right_only = Decimal('0')
total_both = Decimal('0')

for trans in all_transactions:
    if not trans['is_left']:
        if trans['is_negative']:
            total_right_only -= trans['value']
        else:
            total_right_only += trans['value']
    
    if trans['is_negative']:
        total_both -= trans['value']
    else:
        total_both += trans['value']

print(f"Total apenas valores direita: {total_right_only}")
print(f"Total ambos valores: {total_both}")
print(f"Subtotal do PDF: 9139.39")
print(f"\nDiferença se usar apenas direita: {abs(total_right_only - Decimal('9139.39'))}")
print(f"Diferença se usar ambos: {abs(total_both - Decimal('9139.39'))}")

