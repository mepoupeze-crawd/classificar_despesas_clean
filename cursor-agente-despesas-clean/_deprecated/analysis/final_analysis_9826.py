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

# Verificar TODAS as transações (não apenas do 9826)
print("=== Verificando TODAS as transações extraídas ===")
all_items_by_card = {}
for item in items:
    if item.last4:
        card = item.last4[-4:] if len(item.last4) >= 4 else 'unknown'
    else:
        card = 'unknown'
    
    if card not in all_items_by_card:
        all_items_by_card[card] = []
    all_items_by_card[card].append(item)

for card, card_items in all_items_by_card.items():
    total = sum(i.amount if i.flux != 'Entrada' else -i.amount for i in card_items)
    print(f"Card {card}: {len(card_items)} transações, total={total}")

# Verificar se há transações do 7430 que deveriam ser do 9826
print("\n=== Verificando transações do 7430 próximas à transição ===")
card_7430_items = [i for i in items if i.last4 and '7430' in i.last4]
transition_date = "2025-08-12"  # Data do marcador total do 9826

for item in card_7430_items:
    if item.date <= transition_date:
        print(f"{item.date} | {item.description[:60]} | {item.amount}")

# Verificar se há transações que estão sendo atribuídas ao cartão errado
# Olhando para o output esperado, vejo que algumas transações do 7430 têm datas anteriores
# Mas elas podem estar corretas se o cartão 7430 começou antes

# O problema pode ser que precisamos contar AMBOS os valores das linhas concatenadas
# Vou verificar se isso resolve o problema
print("\n=== Testando: contar ambos os valores das linhas concatenadas ===")
total_with_both = Decimal('0')
card_9826_items = [i for i in items if i.last4 and '9826' in i.last4]

# Somar transações extraídas
for item in card_9826_items:
    total_with_both += item.amount if item.flux != 'Entrada' else -item.amount

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
                total_with_both += first_val
        except:
            pass

print(f"Total incluindo valores da esquerda: {total_with_both}")
print(f"Subtotal do PDF: 9139.39")
print(f"Diferença: {abs(total_with_both - Decimal('9139.39'))}")

# Se ainda não bater, preciso verificar se há transações faltantes
if abs(total_with_both - Decimal('9139.39')) > 1:
    print("\n*** Ainda falta algo. Verificando transações faltantes... ***")
    # Verificar se há valores grandes que não estão sendo extraídos
    missing_values = []
    for i in range(start_idx, end_idx + 1):
        line = lines[i]
        date = extract_date(line, default_year=invoice_year)
        value_matches = list(re.finditer(r'-?\s*\d{1,3}(?:\.\d{3})*,\d{2}', line))
        
        if date and value_matches:
            for match in value_matches:
                val_str = match.group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
                try:
                    val = Decimal(val_str)
                    if val > 100:  # Valores significativos
                        # Verificar se foi extraído
                        extracted = False
                        for item in items:
                            if item.date == date and abs(float(item.amount) - float(val)) < 0.01:
                                extracted = True
                                break
                        
                        if not extracted:
                            missing_values.append({
                                'line_num': i,
                                'date': date,
                                'value': val,
                                'line': line[:70]
                            })
                except:
                    pass
    
    print(f"Valores não extraídos encontrados: {len(missing_values)}")
    for mv in missing_values[:10]:
        print(f"Linha {mv['line_num']}: {mv['date']} | valor {mv['value']} | {mv['line']}")

