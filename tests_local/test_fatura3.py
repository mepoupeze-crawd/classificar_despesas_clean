import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.validate import calculate_stats, validate_delta
from card_pdf_parser.parser.rules import detect_card_marker, extract_value

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Extrair subtotais do PDF associados aos cartões (antes da classificação)
subtotals = {}
current_card_for_subtotal = None

for line in lines:
    marker = detect_card_marker(line)
    if marker:
        marker_type, marker_card = marker
        if marker_type == "start":
            current_card_for_subtotal = marker_card
        elif marker_type == "total":
            subtotal = extract_value(line)
            if subtotal:
                subtotals[marker_card] = subtotal
            current_card_for_subtotal = None

# Tentar detectar ano da fatura (buscar em linhas iniciais)
import re
invoice_year = None
for line in lines[:50]:
    year_match = re.search(r'20\d{2}', line)
    if year_match:
        invoice_year = int(year_match.group(0))
        break

if invoice_year is None:
    invoice_year = 2025

classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)
stats = calculate_stats(items, rejects, len(lines), subtotals)
validate_delta(stats)

def decimal_to_str(obj):
    if isinstance(obj, Decimal):
        return format(obj, '.2f')
    if isinstance(obj, list):
        return [decimal_to_str(x) for x in obj]
    if isinstance(obj, dict):
        return {k: decimal_to_str(v) for k, v in obj.items()}
    return obj

output = {
    'items': [decimal_to_str(item.dict()) for item in items],
    'stats': decimal_to_str(stats.dict()),
    'rejects': [reject.dict() for reject in rejects],
}

with open('parse_output_fatura3.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print('parse_output_fatura3.json gerado com', len(items), 'itens')
print('\nStats:')
print(json.dumps(decimal_to_str(stats.dict()), indent=2, ensure_ascii=False))

