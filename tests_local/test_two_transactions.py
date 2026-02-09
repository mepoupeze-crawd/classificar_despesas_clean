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

# Analisar linha por linha e somar valores corretamente
invoice_year = 2025
total_correct = Decimal('0')
transactions_found = []

for i in range(start_idx, end_idx + 1):
    line = lines[i]
    marker = detect_card_marker(line)
    
    # Pular marcadores (mas não o valor do subtotal)
    if marker and marker[0] == 'total':
        # Esta linha tem o subtotal - não contar valores aqui
        continue
    
    if marker and marker[0] == 'start':
        continue
    
    # Extrair data e valores
    date = extract_date(line, default_year=invoice_year)
    value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
    date_matches = list(re.finditer(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', line))
    
    if not date or not value_matches:
        continue
    
    is_concatenated = len(date_matches) >= 2 and len(value_matches) >= 2
    
    if is_concatenated:
        # Linha concatenada - extrair ambas as transações
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
        
        # Segunda transação: segunda data + segundo valor
        if len(date_matches) > 1 and len(value_matches) > 1:
            second_date_match = date_matches[1]
            second_value_match = value_matches[-1]  # Usar o último valor
            
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
            transactions_found.append({
                'line_num': i,
                'date': first_date,
                'value': abs(first_val) if first_val > 0 else -abs(first_val),
                'is_negative': first_val < 0
            })
            transactions_found.append({
                'line_num': i,
                'date': second_date,
                'value': abs(second_val) if second_val > 0 else -abs(second_val),
                'is_negative': second_val < 0
            })
            
            total_correct += abs(first_val) if first_val > 0 else -abs(first_val)
            total_correct += abs(second_val) if second_val > 0 else -abs(second_val)
    else:
        # Linha não concatenada - uma transação
        val_str = value_matches[0].group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
        val = Decimal(val_str)
        if value_matches[0].group(0).strip().startswith('-'):
            val = -val
        
        transactions_found.append({
            'line_num': i,
            'date': date,
            'value': abs(val) if val > 0 else -abs(val),
            'is_negative': val < 0
        })
        
        total_correct += abs(val) if val > 0 else -abs(val)

print(f"Total de transações encontradas: {len(transactions_found)}")
print(f"Total calculado: {total_correct}")
print(f"Subtotal do PDF: 9139.39")
print(f"Diferença: {abs(total_correct - Decimal('9139.39'))}")

# Verificar se isso corresponde ao que precisamos
if abs(total_correct - Decimal('9139.39')) < 1:
    print("\n*** SOLUÇÃO ENCONTRADA: Precisamos extrair DUAS transações de cada linha concatenada! ***")
    print("Uma com o valor da esquerda e outra com o valor da direita.")

