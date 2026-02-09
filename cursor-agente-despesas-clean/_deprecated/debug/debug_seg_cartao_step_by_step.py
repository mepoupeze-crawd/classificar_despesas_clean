import sys
import importlib

# Forçar reload dos módulos
if 'card_pdf_parser.parser.classify' in sys.modules:
    importlib.reload(sys.modules['card_pdf_parser.parser.classify'])
if 'card_pdf_parser.parser.rules' in sys.modules:
    importlib.reload(sys.modules['card_pdf_parser.parser.rules'])

from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_date, extract_value, extract_description, detect_card_marker
from card_pdf_parser.parser.classify import LineClassifier

pdf_path = 'fatura_cartao_2.pdf'
lines = extract_lines_lr_order(pdf_path)

# Encontrar a linha específica
target_line = None
target_idx = None
for i, line in enumerate(lines):
    if "seg" in line.lower() and "cartao" in line.lower() and "10,19" in line:
        target_line = line.strip()
        target_idx = i
        break

print(f"=== Processando linha específica ===\n")
print(f"Índice: {target_idx}")
print(f"Linha: '{target_line}'\n")

# Processar com classificador completo
classifier = LineClassifier()

# Processar todas as linhas até a linha alvo
print("=== Processando linhas até a linha alvo ===\n")
for i in range(target_idx + 1):
    line = lines[i].strip()
    if not line:
        continue
    
    # Verificar marcador de cartão
    marker = detect_card_marker(line)
    if marker:
        marker_type, marker_card = marker
        if marker_type == "start":
            classifier.current_card = marker_card
            print(f"Linha {i}: Marcador de cartão START: {marker_card}")
    
    # Extrair data e valor
    card_key = classifier.current_card if classifier.current_card is not None else ""
    inferred_year = classifier._infer_year_from_date(None, card_key)
    date = extract_date(line, default_year=inferred_year)
    value = extract_value(line)
    
    if date and value:
        card_key = classifier.current_card or "unknown"
        last_date_for_card = classifier.last_date_by_card.get(card_key)
        
        if i == target_idx:
            print(f"\n=== PROCESSANDO LINHA ALVO (índice {i}) ===")
            print(f"Cartão: {card_key}")
            print(f"Última data: {last_date_for_card}")
            print(f"Data atual: {date}")
            print(f"Valor: {value}")
            
            if last_date_for_card and date < last_date_for_card:
                from datetime import datetime
                last_date_obj = datetime.strptime(last_date_for_card, "%Y-%m-%d")
                current_date_obj = datetime.strptime(date, "%Y-%m-%d")
                days_diff = (last_date_obj - current_date_obj).days
                print(f"Diferença de dias: {days_diff}")
                if days_diff > 60:
                    print("  [REJEITADA] Diferença > 60 dias")
                else:
                    print("  [ACEITA] Diferença <= 60 dias")
            
            description = extract_description(line, date, value)
            desc_clean = description.strip()
            print(f"\nDescrição extraída: '{description}'")
            print(f"Descrição limpa: '{desc_clean}'")
            print(f"Tamanho: {len(desc_clean)}")
            
            if not desc_clean or len(desc_clean) < 3:
                print("  [REJEITADA] Descrição muito curta")
            elif __import__('re').match(r'^[\d\s\.\,\-\/]+$', desc_clean):
                print("  [REJEITADA] Descrição contém apenas números/símbolos")
            else:
                print("  [ACEITA] Descrição válida")
                print(f"\n  Transação seria adicionada aos itens!")
        
        # Processar normalmente (simular o classificador)
        if last_date_for_card and date < last_date_for_card:
            from datetime import datetime
            last_date_obj = datetime.strptime(last_date_for_card, "%Y-%m-%d")
            current_date_obj = datetime.strptime(date, "%Y-%m-%d")
            days_diff = (last_date_obj - current_date_obj).days
            if days_diff > 60:
                continue
        
        description = extract_description(line, date, value)
        desc_clean = description.strip()
        if not desc_clean or len(desc_clean) < 3:
            continue
        if __import__('re').match(r'^[\d\s\.\,\-\/]+$', desc_clean):
            continue
        
        # Aceitar transação
        if not (last_date_for_card and date < last_date_for_card and days_diff > 60):
            # Atualizar última data apenas se não for muito anterior
            if not last_date_for_card or date >= last_date_for_card:
                classifier.last_date_by_card[card_key] = date

# Agora processar completo
print(f"\n=== Processando PDF completo ===\n")
classifier2 = LineClassifier()
items, rejects = classifier2.classify_lines(lines)

print(f"Total de itens: {len(items)}")
print(f"Total de rejeições: {len(rejects)}\n")

# Procurar especificamente
found = False
for item in items:
    if "seg" in item.description.lower() and "cartao" in item.description.lower():
        found = True
        print(f"ENCONTRADO: {item.date} - {item.description} - {item.amount}")

if not found:
    print("NÃO ENCONTRADO nos itens")
    for reject in rejects:
        if "seg" in reject.line.lower() and "cartao" in reject.line.lower():
            print(f"REJEITADA: {reject.reason}")

