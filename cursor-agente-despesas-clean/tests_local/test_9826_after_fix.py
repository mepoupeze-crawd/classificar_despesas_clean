from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.validate import calculate_stats
from card_pdf_parser.parser.rules import detect_card_marker, extract_value

lines = extract_lines_lr_order('fatura_cartao_3.pdf')
subtotals = {}
for line in lines:
    marker = detect_card_marker(line)
    if marker and marker[0] == 'total':
        subtotal = extract_value(line)
        if subtotal:
            subtotals[marker[1]] = subtotal

invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)
items, rejects = classifier.classify_lines(lines)
stats = calculate_stats(items, rejects, len(lines), subtotals)

card_9826_items = [i for i in items if i.last4 and '9826' in i.last4]
total = sum(i.amount if i.flux != 'Entrada' else -i.amount for i in card_9826_items)

print(f'Card 9826: total={total}, control={subtotals.get("9826", 0)}, delta={abs(total - subtotals.get("9826", 0))}')
print(f'Items count: {len(card_9826_items)}')

