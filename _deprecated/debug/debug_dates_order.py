import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_value, extract_date, detect_card_marker
from card_pdf_parser.parser.classify import LineClassifier

pdf_path = 'fatura_cartao_2.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Todas as transações do cartão 1899 em ordem ===\n")

classifier = LineClassifier()
items = []
dates_by_card = {}

for i, line in enumerate(lines):
    line_clean = line.strip()
    if not line_clean:
        continue
    
    # Verificar marcador de cartão
    marker = detect_card_marker(line_clean)
    if marker:
        marker_type, marker_card = marker
        if marker_type == "start":
            classifier.current_card = marker_card
    
    # Extrair data e valor
    card_key = classifier.current_card if classifier.current_card is not None else ""
    inferred_year = classifier._infer_year_from_date(None, card_key)
    date = extract_date(line_clean, default_year=inferred_year)
    value = extract_value(line_clean)
    
    if date and value:
        card_key = classifier.current_card or "unknown"
        
        if card_key == "1899":
            print(f"Linha {i}: {date} - {line_clean[:60]}...")
            print(f"  Valor: {value}")
            
            if card_key not in dates_by_card:
                dates_by_card[card_key] = []
            dates_by_card[card_key].append((date, i, line_clean[:60]))

print(f"\n=== Resumo das datas do cartão 1899 ===")
if "1899" in dates_by_card:
    dates_sorted = sorted(dates_by_card["1899"], key=lambda x: x[0])
    print(f"Total de transações encontradas: {len(dates_sorted)}")
    print(f"\nDatas em ordem cronológica:")
    for date, idx, line_preview in dates_sorted:
        print(f"  {date} (linha {idx}): {line_preview}...")
        
        # Verificar se "SEG CARTAO" está nesta linha
        if "seg" in line_preview.lower() and "cartao" in line_preview.lower():
            print(f"    *** ESTA É A LINHA 'SEG CARTAO PROTEGIDO' ***")

