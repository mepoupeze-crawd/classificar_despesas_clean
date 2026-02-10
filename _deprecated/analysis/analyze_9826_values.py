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

print(f"Seção do cartão 9826: linhas {start_idx} a {end_idx}\n")

# Extrair transações
invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)

card_9826_items = [i for i in items if i.last4 and '9826' in i.last4]
total_extracted = sum(i.amount if i.flux != 'Entrada' else -i.amount for i in card_9826_items)

print(f"Total extraído: {total_extracted}")
print(f"Subtotal do PDF: 9139.39")
print(f"Diferença: {abs(total_extracted - Decimal('9139.39'))}\n")

# Analisar TODAS as linhas na seção do 9826 e somar TODOS os valores
print("=== Analisando TODAS as linhas na seção 9826 ===\n")
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
    
    # Extrair todos os valores monetários da linha
    value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
    date_matches = list(re.finditer(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', line))
    
    for match in value_matches:
        val_str = match.group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
        try:
            val = Decimal(val_str)
            if match.group(0).strip().startswith('-'):
                val = -val
            # Ignorar valores muito grandes (provavelmente subtotais)
            if val < 10000:
                is_concatenated = len(date_matches) >= 2 and len(value_matches) >= 2
                all_values.append({
                    'line_num': i,
                    'value': abs(val),
                    'is_negative': val < 0,
                    'is_concatenated': is_concatenated,
                    'line_preview': line[:60]
                })
        except:
            pass

# Separar valores de linhas concatenadas vs não concatenadas
concatenated_left = []
concatenated_right = []
non_concatenated = []

for i in range(start_idx, end_idx + 1):
    line = lines[i]
    date_matches = list(re.finditer(r'\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b', line))
    value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
    
    if len(date_matches) >= 2 and len(value_matches) >= 2:
        # Linha concatenada
        first_val_str = value_matches[0].group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
        last_val_str = value_matches[-1].group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
        try:
            first_val = Decimal(first_val_str)
            last_val = Decimal(last_val_str)
            if value_matches[0].group(0).strip().startswith('-'):
                first_val = -first_val
            if value_matches[-1].group(0).strip().startswith('-'):
                last_val = -last_val
            
            concatenated_left.append(abs(first_val))
            concatenated_right.append(abs(last_val))
        except:
            pass
    elif len(value_matches) == 1:
        # Linha não concatenada
        val_str = value_matches[0].group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
        try:
            val = Decimal(val_str)
            if value_matches[0].group(0).strip().startswith('-'):
                val = -val
            non_concatenated.append(abs(val))
        except:
            pass

total_left = sum(concatenated_left)
total_right = sum(concatenated_right)
total_non_concatenated = sum(non_concatenated)

print(f"Soma valores esquerda (linhas concatenadas): {total_left}")
print(f"Soma valores direita (linhas concatenadas): {total_right}")
print(f"Soma valores não concatenados: {total_non_concatenated}")
print(f"\nTotal se usar apenas direita: {total_right + total_non_concatenated}")
print(f"Total se usar ambos (esquerda + direita): {total_left + total_right + total_non_concatenated}")
print(f"Subtotal do PDF: 9139.39")
print(f"\nDiferença se usar apenas direita: {abs((total_right + total_non_concatenated) - Decimal('9139.39'))}")
print(f"Diferença se usar ambos: {abs((total_left + total_right + total_non_concatenated) - Decimal('9139.39'))}")

# Verificar se precisamos somar ambos os valores das linhas concatenadas
if abs((total_left + total_right + total_non_concatenated) - Decimal('9139.39')) < 1:
    print("\n*** SOLUÇÃO: Precisamos somar AMBOS os valores das linhas concatenadas! ***")

