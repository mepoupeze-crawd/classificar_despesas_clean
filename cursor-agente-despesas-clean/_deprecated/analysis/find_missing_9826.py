from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
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

# Extrair transações
invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)

# Verificar se há transações do 7430 que deveriam ser do 9826
print("=== Verificando transações do 7430 que podem ser do 9826 ===")
card_7430_items = [i for i in items if i.last4 and '7430' in i.last4]
for item in card_7430_items:
    if item.date <= "2025-08-12":  # Data do marcador total do 9826
        print(f"{item.date} | {item.description[:60]} | {item.amount}")

# Verificar linhas rejeitadas na seção do 9826 que podem ter valores
print("\n=== Verificando linhas rejeitadas na seção 9826 ===")
rejected_values = []
for reject in rejects:
    for i, line in enumerate(lines):
        if start_idx <= i <= end_idx and reject.line.strip() in line:
            date = extract_date(line, default_year=invoice_year)
            value = extract_value(line, prefer_last=False)
            value_last = extract_value(line, prefer_last=True)
            if value or value_last:
                rejected_values.append({
                    'line_num': i,
                    'line': line[:80],
                    'reason': reject.reason,
                    'date': date,
                    'value': value,
                    'value_last': value_last
                })
            break

for rv in rejected_values[:10]:
    print(f"Linha {rv['line_num']}: {rv['line']}")
    print(f"  -> {rv['reason']}")
    if rv['date']:
        print(f"  -> date={rv['date']}, value={rv['value']}, value_last={rv['value_last']}")

# Verificar se há valores grandes que podem estar faltando
print("\n=== Verificando valores grandes na seção 9826 ===")
large_values = []
for i in range(start_idx, end_idx + 1):
    line = lines[i]
    value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
    for match in value_matches:
        val_str = match.group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
        try:
            val = Decimal(val_str)
            if 200 < val < 3000:  # Valores médios-grandes que podem estar faltando
                # Verificar se foi extraído
                extracted = False
                date = extract_date(line, default_year=invoice_year)
                if date:
                    for item in items:
                        if item.date == date and abs(float(item.amount) - float(val)) < 0.01:
                            extracted = True
                            break
                
                if not extracted:
                    large_values.append({
                        'line_num': i,
                        'value': val,
                        'line': line[:80],
                        'date': date
                    })
        except:
            pass

for lv in large_values:
    print(f"Linha {lv['line_num']}: valor {lv['value']} em '{lv['line']}'")
    if lv['date']:
        print(f"  -> date={lv['date']}")

# Verificar o total se incluirmos valores da esquerda das linhas concatenadas
print("\n=== Calculando total incluindo valores da esquerda ===")
total_with_left = Decimal('0')
for item in items:
    if item.last4 and '9826' in item.last4:
        total_with_left += item.amount if item.flux != 'Entrada' else -item.amount

# Adicionar valores da esquerda das linhas concatenadas
for i in range(start_idx, end_idx + 1):
    line = lines[i]
    date_matches = list(re.finditer(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', line))
    value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
    
    if len(date_matches) >= 2 and len(value_matches) >= 2:
        # Linha concatenada - adicionar valor da esquerda
        first_val_str = value_matches[0].group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
        try:
            first_val = Decimal(first_val_str)
            if not value_matches[0].group(0).strip().startswith('-'):
                total_with_left += first_val
        except:
            pass

print(f"Total incluindo valores da esquerda: {total_with_left}")
print(f"Subtotal do PDF: 9139.39")
print(f"Diferença: {abs(total_with_left - Decimal('9139.39'))}")

