from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.rules import detect_card_marker, extract_date, extract_value
import re
from decimal import Decimal
import json

lines = extract_lines_lr_order('fatura_cartao_3.pdf')

# Carregar output esperado
with open('tests/output_esperado3.json', 'r', encoding='utf-8') as f:
    expected = json.load(f)

card_9826_expected = [i for i in expected['items'] if i['last4'] and '9826' in i['last4']]
total_expected = sum(float(i['amount']) if i['flux'] == 'Saida' else -float(i['amount']) for i in card_9826_expected)

print(f"Total esperado (output_esperado3.json): {total_expected}")
print(f"Subtotal do PDF: 9139.39")
print(f"Diferença: {abs(Decimal(str(total_expected)) - Decimal('9139.39'))}\n")

# Verificar se o output esperado está correto
# Talvez o problema seja que o output esperado não corresponde ao PDF
print("=== Verificando se o output esperado corresponde ao PDF ===\n")

# Extrair transações do PDF
invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)

card_9826_items = [i for i in items if i.last4 and '9826' in i.last4]
total_extracted = sum(i.amount if i.flux != 'Entrada' else -i.amount for i in card_9826_items)

print(f"Total extraído: {total_extracted}")
print(f"Total esperado: {total_expected}")
print(f"Subtotal do PDF: 9139.39")
print(f"\nDiferença extraído vs esperado: {abs(total_extracted - Decimal(str(total_expected)))}")
print(f"Diferença esperado vs PDF: {abs(Decimal(str(total_expected)) - Decimal('9139.39'))}")
print(f"Diferença extraído vs PDF: {abs(total_extracted - Decimal('9139.39'))}")

# O problema pode ser que o output esperado está incorreto
# Ou que precisamos extrair mais transações do PDF
# Vou verificar se há transações que não estão sendo extraídas

print("\n=== Verificando se há transações faltantes ===")
# Verificar se há valores no PDF que não estão no output esperado
pdf_values = set()
for item in card_9826_items:
    pdf_values.add((item.date, str(item.amount)))

expected_values = set()
for item in card_9826_expected:
    expected_values.add((item['date'], str(item['amount'])))

missing_in_expected = pdf_values - expected_values
extra_in_expected = expected_values - pdf_values

print(f"Valores no PDF mas não no esperado: {len(missing_in_expected)}")
for val in list(missing_in_expected)[:5]:
    print(f"  {val}")

print(f"\nValores no esperado mas não no PDF: {len(extra_in_expected)}")
for val in list(extra_in_expected)[:5]:
    print(f"  {val}")

# Talvez o problema seja que o PDF tem um subtotal que inclui valores adicionais
# que não estão nas transações listadas (como parcelas futuras ou outros valores)
# Nesse caso, precisamos ajustar o control_total para corresponder ao calculated_total
# OU extrair mais transações do PDF

# Vou verificar se há transações que estão sendo rejeitadas mas deveriam ser extraídas
print("\n=== Verificando linhas rejeitadas na seção 9826 ===")
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

rejected_in_section = []
for reject in rejects:
    for i, line in enumerate(lines):
        if start_idx <= i <= end_idx and reject.line.strip() in line:
            date = extract_date(line, default_year=invoice_year)
            value = extract_value(line, prefer_last=False)
            if date and value:
                rejected_in_section.append({
                    'line_num': i,
                    'line': line[:80],
                    'reason': reject.reason,
                    'date': date,
                    'value': value
                })
            break

print(f"Linhas rejeitadas com data e valor: {len(rejected_in_section)}")
for rv in rejected_in_section[:5]:
    print(f"Linha {rv['line_num']}: {rv['line']}")
    print(f"  -> {rv['reason']}, date={rv['date']}, value={rv['value']}")

