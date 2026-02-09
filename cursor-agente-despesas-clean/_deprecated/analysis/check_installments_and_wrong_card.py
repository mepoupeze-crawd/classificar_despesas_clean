from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value, extract_installments
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

# Verificar se há valores de parcelas que não estão sendo contabilizados
invoice_year = 2025
total_with_installments = Decimal('0')

for i in range(start_idx, end_idx + 1):
    line = lines[i]
    marker = detect_card_marker(line)
    
    if marker:
        continue
    
    date = extract_date(line, default_year=invoice_year)
    value = extract_value(line, prefer_last=False)
    value_last = extract_value(line, prefer_last=True)
    
    if date and value:
        # Verificar se há parcelas
        numero_parcela, parcelas = extract_installments(line, value)
        
        if numero_parcela and parcelas:
            # Esta transação tem parcelas
            # Verificar se o valor da parcela está sendo contabilizado corretamente
            # O valor total da compra pode ser diferente do valor da parcela
            print(f"Linha {i}: {line[:70]}")
            print(f"  -> date={date}, value={value}, parcelas={numero_parcela}/{parcelas}")
            
            # Se há parcelas, o valor pode ser apenas a parcela atual
            # Mas o subtotal do PDF pode incluir o valor total da compra
            # Vou verificar se há um padrão aqui
        
        total_with_installments += abs(value) if value > 0 else -abs(value)

print(f"\nTotal somando valores extraídos: {total_with_installments}")
print(f"Subtotal do PDF: 9139.39")
print(f"Diferença: {abs(total_with_installments - Decimal('9139.39'))}")

# Talvez o problema seja que o subtotal do PDF inclui valores de parcelas futuras
# ou valores totais de compras parceladas, não apenas as parcelas atuais
# Nesse caso, precisamos ajustar o control_total para corresponder ao calculated_total
# OU extrair mais transações do PDF

# Mas o usuário quer que o control_total seja 9139.39 (o valor do PDF)
# Então precisamos extrair mais transações ou contar valores adicionais

# Vou verificar se há transações que estão sendo atribuídas ao cartão errado
print("\n=== Verificando se há transações atribuídas ao cartão errado ===")
from card_pdf_parser.parser.classify import LineClassifier
classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)

# Verificar transações do 7430 que têm datas anteriores ao marcador "total" do 9826
card_7430_items = [i for i in items if i.last4 and '7430' in i.last4]
transition_date = "2025-08-12"

transactions_before_transition = [i for i in card_7430_items if i.date <= transition_date]
print(f"Transações do 7430 com data <= {transition_date}: {len(transactions_before_transition)}")
total_before = sum(i.amount if i.flux != 'Entrada' else -i.amount for i in transactions_before_transition)
print(f"Total dessas transações: {total_before}")

# Verificar se essas transações deveriam ser do 9826
# Olhando para o output esperado, vejo que algumas transações do 7430 têm datas anteriores
# Mas elas podem estar corretas se o cartão 7430 começou antes

# Talvez o problema seja que precisamos contar valores de parcelas futuras também
# Ou que há transações que não estão sendo extraídas

# Vou verificar se há uma diferença sistemática que indica que precisamos contar valores adicionais

