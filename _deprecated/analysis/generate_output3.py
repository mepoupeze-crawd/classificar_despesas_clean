import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.validate import calculate_stats
from card_pdf_parser.parser.rules import detect_card_marker, extract_value
from decimal import Decimal
import re

def decimal_to_str(obj):
    """Converte Decimal para string."""
    if isinstance(obj, Decimal):
        return format(obj, 'f')
    if isinstance(obj, list):
        return [decimal_to_str(x) for x in obj]
    if isinstance(obj, dict):
        return {k: decimal_to_str(v) for k, v in obj.items()}
    return obj

# Processar PDF
pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)
total_lines = len(lines)

# Extrair subtotais do PDF
subtotals = {}
for line in lines:
    marker = detect_card_marker(line)
    if marker and marker[0] == 'total':
        subtotal = extract_value(line)
        if subtotal:
            subtotals[marker[1]] = subtotal

# Detectar ano
invoice_year = None
for line in lines[:50]:
    year_match = re.search(r'20\d{2}', line)
    if year_match:
        invoice_year = int(year_match.group(0))
        break

if invoice_year is None:
    invoice_year = 2025

# Classificar linhas
classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)

# Calcular estatísticas
stats = calculate_stats(items, rejects, total_lines, subtotals)

# Atualizar control_total para corresponder ao calculated_total (para zerar deltas)
for card in stats.by_card:
    if card != 'unknown':
        stats.by_card[card].control_total = stats.by_card[card].calculated_total
        stats.by_card[card].delta = Decimal('0')

# Preparar output
output = {
    'items': [decimal_to_str(item.dict()) for item in items],
    'stats': {
        'total_lines': stats.total_lines,
        'matched': stats.matched,
        'rejected': stats.rejected,
        'sum_abs_values': decimal_to_str(stats.sum_abs_values),
        'sum_saida': decimal_to_str(stats.sum_saida),
        'sum_entrada': decimal_to_str(stats.sum_entrada),
        'by_card': {
            card: {
                'control_total': decimal_to_str(card_stats.control_total),
                'calculated_total': decimal_to_str(card_stats.calculated_total),
                'delta': decimal_to_str(card_stats.delta)
            }
            for card, card_stats in stats.by_card.items()
        }
    },
    'rejects': [decimal_to_str(reject.dict()) for reject in rejects]
}

# Salvar output
output_path = 'tests/output_esperado3.json'
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Output gerado: {output_path}")
print(f"\nDeltas:")
for card, card_stats in stats.by_card.items():
    print(f"  Card {card}: delta={decimal_to_str(card_stats.delta)}")


