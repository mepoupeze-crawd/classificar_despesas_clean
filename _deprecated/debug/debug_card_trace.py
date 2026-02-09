import json
from decimal import Decimal
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.rules import detect_card_marker, extract_value, extract_date

pdf_path = 'fatura_cartao_3.pdf'
lines = extract_lines_lr_order(pdf_path)

# Verificar marcadores entre linha 48 e 174
print("=== Marcadores entre linha 48 e 174 ===")
for i in range(48, 175):
    line = lines[i]
    marker = detect_card_marker(line)
    if marker:
        print(f"Linha {i}: {marker} - {line[:80]}")

# Simular processamento completo
print("\n=== Simulando processamento completo ===")
invoice_year = 2025
classifier = LineClassifier(invoice_year=invoice_year)

# Adicionar debug ao classifier
original_classify = classifier.classify_lines
def debug_classify_lines(lines):
    items = []
    rejects = []
    current_card_trace = []
    
    for line_idx, line in enumerate(lines):
        line = classifier.__class__.__dict__['clean_line'](line) if hasattr(classifier.__class__, 'clean_line') else line
        
        if not line:
            continue
        
        # Verificar marcador
        from card_pdf_parser.parser.rules import detect_card_marker
        marker = detect_card_marker(line)
        if marker:
            kind, card = marker
            if kind == "start":
                classifier.current_card = card
                current_card_trace.append((line_idx, "START", card))
            elif kind == "total":
                current_card_trace.append((line_idx, "TOTAL", card, classifier.current_card))
                classifier.current_card = None
    
    return current_card_trace

# Usar o classifier real
items, rejects = classifier.classify_lines(lines)

# Verificar trace do cartão 9826
print("\n=== Trace do cartão 9826 ===")
for i in range(48, 175):
    line = lines[i]
    marker = detect_card_marker(line)
    if marker:
        kind, card = marker
        if card == '9826':
            print(f"Linha {i} [{kind}]: {line[:80]}")

# Verificar estado do classifier após processar
print("\n=== Estado final do classifier ===")
print(f"current_card: {classifier.current_card}")
print(f"last_date_by_card: {classifier.last_date_by_card}")

