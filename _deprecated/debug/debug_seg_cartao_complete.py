import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_value, extract_date, extract_description, detect_card_marker
from card_pdf_parser.parser.classify import LineClassifier
import re

pdf_path = 'fatura_cartao_2.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Debug completo da linha 'SEG CARTAO PROTEGIDO' ===\n")

# Encontrar índice da linha
target_index = None
target_line = None
for i, line in enumerate(lines):
    if "seg" in line.lower() and "cartao" in line.lower():
        target_index = i
        target_line = line.strip()
        break

if not target_line:
    print("Linha não encontrada!")
    exit(1)

print(f"Linha encontrada no índice {target_index}: '{target_line}'\n")

# Verificar contexto antes dessa linha
print("=== Contexto antes da linha (últimas 5 linhas) ===")
for i in range(max(0, target_index - 5), target_index):
    print(f"  [{i}] {lines[i].strip()}")

print(f"\n  [{target_index}] {target_line} <-- LINHA ALVO")

print(f"\n=== Contexto depois da linha (próximas 5 linhas) ===")
for i in range(target_index + 1, min(len(lines), target_index + 6)):
    print(f"  [{i}] {lines[i].strip()}")

# Processar passo a passo simulando o classificador
print(f"\n=== Simulando classificação passo a passo ===\n")

classifier = LineClassifier()

# Processar linhas até chegar na linha alvo
items_before = []
rejects_before = []
last_date_before = None
current_card_before = None

for i in range(target_index):
    line = lines[i].strip()
    if not line:
        continue
    
    # Verificar marcador de cartão
    marker = detect_card_marker(line)
    if marker:
        marker_type, marker_card = marker
        if marker_type == "start":
            classifier.current_card = marker_card
            current_card_before = marker_card
    
    # Extrair data e valor
    card_key = classifier.current_card if classifier.current_card is not None else ""
    inferred_year = classifier._infer_year_from_date(None, card_key)
    date = extract_date(line, default_year=inferred_year)
    value = extract_value(line)
    
    if date and value:
        card_key = classifier.current_card or "unknown"
        last_date_for_card = classifier.last_date_by_card.get(card_key)
        
        if not (last_date_for_card and date < last_date_for_card):
            # Seria aceita
            classifier.last_date_by_card[card_key] = date
            last_date_before = date
            current_card_before = card_key

print(f"Estado antes da linha alvo:")
print(f"  Cartão atual: {classifier.current_card}")
print(f"  Última data para este cartão: {classifier.last_date_by_card.get(classifier.current_card or 'unknown', 'N/A')}")

# Agora processar a linha alvo
print(f"\n=== Processando linha alvo ===\n")
line = target_line

# Verificar marcador de cartão
marker = detect_card_marker(line)
if marker:
    print(f"Marcador de cartão encontrado: {marker}")

card_key = classifier.current_card if classifier.current_card is not None else ""
inferred_year = classifier._infer_year_from_date(None, card_key)
date = extract_date(line, default_year=inferred_year)
value = extract_value(line)

print(f"Data extraída: {date}")
print(f"Valor extraído: {value}")

if date and value:
    card_key = classifier.current_card or "unknown"
    last_date_for_card = classifier.last_date_by_card.get(card_key)
    
    print(f"\nValidação de ordem de datas:")
    print(f"  Cartão: {card_key}")
    print(f"  Última data para este cartão: {last_date_for_card}")
    print(f"  Data atual: {date}")
    
    if last_date_for_card and date < last_date_for_card:
        # Verificar se está dentro da janela de 60 dias
        from datetime import datetime
        last_date_obj = datetime.strptime(last_date_for_card, "%Y-%m-%d")
        current_date_obj = datetime.strptime(date, "%Y-%m-%d")
        days_diff = (last_date_obj - current_date_obj).days
        
        print(f"  Diferença de dias: {days_diff}")
        if days_diff > 60:
            print(f"  [REJEITADA] Data {date} é anterior à data anterior {last_date_for_card} (diferença de {days_diff} dias > 60)")
        else:
            print(f"  [ACEITA] Data {date} é anterior mas dentro da janela de 60 dias (diferença de {days_diff} dias)")
    else:
        print(f"  [OK] Data válida")
        
        description = extract_description(line, date, value)
        desc_clean = description.strip()
        
        print(f"\nDescrição extraída: '{description}'")
        print(f"Descrição limpa: '{desc_clean}'")
        print(f"Tamanho: {len(desc_clean)}")
        
        if not desc_clean or len(desc_clean) < 3:
            print(f"  [REJEITADA] Descrição muito curta")
        elif re.match(r'^[\d\s\.\,\-\/]+$', desc_clean):
            print(f"  [REJEITADA] Descrição contém apenas números/símbolos")
        else:
            print(f"  [OK] Descrição válida - DEVERIA SER ACEITA")

