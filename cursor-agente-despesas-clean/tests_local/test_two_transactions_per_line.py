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

# Estratégia: extrair DUAS transações de cada linha concatenada
# Uma com o valor da esquerda e outra com o valor da direita
invoice_year = 2025
all_transactions = []

for i in range(start_idx, end_idx + 1):
    line = lines[i]
    marker = detect_card_marker(line)
    
    # Pular apenas marcadores sem transações
    if marker and marker[0] == 'start':
        continue
    
    date_matches = list(re.finditer(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', line))
    value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
    
    if len(date_matches) >= 2 and len(value_matches) >= 2:
        # Linha concatenada - extrair DUAS transações
        # Primeira transação: primeira data + primeiro valor
        first_date_match = date_matches[0]
        first_value_match = value_matches[0]
        
        day1 = int(first_date_match.group(1))
        month1 = int(first_date_match.group(2))
        year1 = int(first_date_match.group(3)) if len(first_date_match.groups()) > 2 and first_date_match.group(3) else invoice_year
        if len(str(year1)) == 2:
            year1 = 2000 + year1
        
        first_val_str = first_value_match.group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
        first_val = Decimal(first_val_str)
        if first_value_match.group(0).strip().startswith('-'):
            first_val = -first_val
        
        first_date = f"{year1}-{month1:02d}-{day1:02d}"
        
        # Segunda transação: segunda data + último valor
        if len(date_matches) > 1:
            second_date_match = date_matches[1]
            second_value_match = value_matches[-1]
            
            day2 = int(second_date_match.group(1))
            month2 = int(second_date_match.group(2))
            year2 = int(second_date_match.group(3)) if len(second_date_match.groups()) > 2 and second_date_match.group(3) else invoice_year
            if len(str(year2)) == 2:
                year2 = 2000 + year2
            
            second_val_str = second_value_match.group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
            second_val = Decimal(second_val_str)
            if second_value_match.group(0).strip().startswith('-'):
                second_val = -second_val
            
            second_date = f"{year2}-{month2:02d}-{day2:02d}"
            
            # Adicionar ambas as transações
            all_transactions.append({
                'date': first_date,
                'value': abs(first_val) if first_val > 0 else -abs(first_val),
                'is_negative': first_val < 0,
                'line': line[:60]
            })
            all_transactions.append({
                'date': second_date,
                'value': abs(second_val) if second_val > 0 else -abs(second_val),
                'is_negative': second_val < 0,
                'line': line[:60]
            })
    elif len(date_matches) == 1 and len(value_matches) == 1:
        # Linha não concatenada - uma transação
        date = extract_date(line, default_year=invoice_year)
        value = extract_value(line, prefer_last=False)
        
        if date and value:
            all_transactions.append({
                'date': date,
                'value': abs(value) if value > 0 else -abs(value),
                'is_negative': value < 0,
                'line': line[:60]
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

if abs(total - Decimal('9139.39')) < 1:
    print("\n*** SOLUÇÃO: Precisamos extrair DUAS transações de cada linha concatenada! ***")

