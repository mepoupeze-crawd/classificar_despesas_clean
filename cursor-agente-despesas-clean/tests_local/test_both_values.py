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

# Calcular total somando TODOS os valores (esquerda + direita) das linhas concatenadas
invoice_year = 2025
total_all = Decimal('0')

for i in range(start_idx, end_idx + 1):
    line = lines[i]
    marker = detect_card_marker(line)
    
    # Pular marcadores
    if marker:
        continue
    
    date_matches = list(re.finditer(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', line))
    value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
    
    if len(date_matches) >= 2 and len(value_matches) >= 2:
        # Linha concatenada - somar AMBOS os valores
        for match in value_matches:
            val_str = match.group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
            try:
                val = Decimal(val_str)
                if match.group(0).strip().startswith('-'):
                    total_all -= val
                else:
                    total_all += val
            except:
                pass
    elif len(value_matches) == 1:
        # Linha não concatenada - somar o valor
        val_str = value_matches[0].group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
        try:
            val = Decimal(val_str)
            if value_matches[0].group(0).strip().startswith('-'):
                total_all -= val
            else:
                total_all += val
        except:
            pass

print(f"Total somando TODOS os valores: {total_all}")
print(f"Subtotal do PDF: 9139.39")
print(f"Diferença: {abs(total_all - Decimal('9139.39'))}")

# Se ainda não bater, verificar se há valores que não estão sendo contabilizados
if abs(total_all - Decimal('9139.39')) > 1:
    print("\n*** Ainda falta algo. Verificando valores específicos... ***")
    
    # Verificar se há valores que aparecem múltiplas vezes ou que não estão sendo contabilizados
    # Talvez o problema seja que alguns valores estão sendo contados duas vezes ou não estão sendo contados
    
    # Vou verificar linha por linha para entender melhor
    print("\n=== Analisando linhas concatenadas específicas ===")
    concatenated_lines = []
    for i in range(start_idx, end_idx + 1):
        line = lines[i]
        date_matches = list(re.finditer(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', line))
        value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
        
        if len(date_matches) >= 2 and len(value_matches) >= 2:
            first_val_str = value_matches[0].group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
            last_val_str = value_matches[-1].group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
            try:
                first_val = Decimal(first_val_str)
                last_val = Decimal(last_val_str)
                if value_matches[0].group(0).strip().startswith('-'):
                    first_val = -first_val
                if value_matches[-1].group(0).strip().startswith('-'):
                    last_val = -last_val
                
                concatenated_lines.append({
                    'line_num': i,
                    'line': line[:70],
                    'left': abs(first_val),
                    'right': abs(last_val),
                    'sum': abs(first_val) + abs(last_val)
                })
            except:
                pass
    
    total_concatenated = sum(cl['sum'] for cl in concatenated_lines)
    print(f"Soma de todas as linhas concatenadas (esquerda + direita): {total_concatenated}")
    
    # Verificar linhas não concatenadas
    non_concatenated_values = []
    for i in range(start_idx, end_idx + 1):
        line = lines[i]
        date_matches = list(re.finditer(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', line))
        value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
        
        if len(date_matches) == 1 and len(value_matches) == 1:
            val_str = value_matches[0].group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
            try:
                val = Decimal(val_str)
                if not value_matches[0].group(0).strip().startswith('-'):
                    non_concatenated_values.append(abs(val))
            except:
                pass
    
    total_non_concatenated = sum(non_concatenated_values)
    print(f"Soma de linhas não concatenadas: {total_non_concatenated}")
    print(f"Total geral: {total_concatenated + total_non_concatenated}")
    print(f"Subtotal do PDF: 9139.39")
    print(f"Diferença: {abs((total_concatenated + total_non_concatenated) - Decimal('9139.39'))}")

