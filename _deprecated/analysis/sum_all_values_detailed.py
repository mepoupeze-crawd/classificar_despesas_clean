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

# Verificar TODAS as linhas e somar TODOS os valores monetários
print("=== Somando TODOS os valores monetários na seção 9826 ===\n")
all_values = []
for i in range(start_idx, end_idx + 1):
    line = lines[i]
    marker = detect_card_marker(line)
    
    # Se tem marcador "total", pegar o valor do subtotal
    if marker and marker[0] == 'total':
        subtotal = extract_value(line)
        if subtotal:
            print(f"Linha {i} (TOTAL): {subtotal}")
        continue
    
    # Extrair TODOS os valores monetários da linha
    value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
    for match in value_matches:
        val_str = match.group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
        try:
            val = Decimal(val_str)
            if match.group(0).strip().startswith('-'):
                val = -val
            # Ignorar apenas valores muito grandes (provavelmente subtotais)
            if val < 10000:
                all_values.append({
                    'line_num': i,
                    'value': val,
                    'abs_value': abs(val),
                    'is_negative': val < 0,
                    'line': line[:70]
                })
        except:
            pass

# Calcular total
total_positive = Decimal('0')
total_negative = Decimal('0')
for v in all_values:
    if v['is_negative']:
        total_negative += v['abs_value']
    else:
        total_positive += v['abs_value']

total_all = total_positive - total_negative

print(f"Total valores positivos: {total_positive}")
print(f"Total valores negativos: {total_negative}")
print(f"Total líquido (todos valores): {total_all}")
print(f"Subtotal do PDF: 9139.39")
print(f"Diferença: {abs(total_all - Decimal('9139.39'))}")

# Verificar se há valores específicos que podem estar faltando
print("\n=== Verificando valores específicos ===")
missing = Decimal('9139.39') - total_all
print(f"Valor faltante: {missing}")

# Procurar valores próximos ao faltante
print("\n=== Procurando valores próximos ao faltante ===")
for v in all_values:
    if abs(v['abs_value'] - missing) < 5 or abs(v['abs_value'] - missing/2) < 5:
        print(f"Linha {v['line_num']}: valor {v['value']} em '{v['line']}'")

# Verificar se há valores que aparecem múltiplas vezes
print("\n=== Verificando valores duplicados ===")
value_counts = {}
for v in all_values:
    key = str(v['abs_value'])
    if key not in value_counts:
        value_counts[key] = []
    value_counts[key].append(v)

for val_str, occurrences in value_counts.items():
    if len(occurrences) > 1 and Decimal(val_str) > 100:
        print(f"Valor {val_str} aparece {len(occurrences)} vezes:")
        for occ in occurrences[:3]:
            print(f"  Linha {occ['line_num']}: {occ['line']}")

