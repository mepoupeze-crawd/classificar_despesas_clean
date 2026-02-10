import sys
import importlib

# Limpar cache completamente
modules_to_reload = [
    'card_pdf_parser.parser.classify',
    'card_pdf_parser.parser.rules',
    'card_pdf_parser.parser.extract'
]

for mod_name in modules_to_reload:
    if mod_name in sys.modules:
        del sys.modules[mod_name]

from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_date, extract_value, detect_card_marker
from card_pdf_parser.parser.classify import LineClassifier

pdf_path = 'fatura_cartao_2.pdf'
lines = extract_lines_lr_order(pdf_path)

# Encontrar índice da linha
target_idx = None
for i, line in enumerate(lines):
    if "seg" in line.lower() and "cartao" in line.lower() and "10,19" in line:
        target_idx = i
        break

print(f"=== Rastreando linha {target_idx} ===\n")
print(f"Linha: '{lines[target_idx].strip()}'\n")

# Criar classificador e processar linha por linha com logs
classifier = LineClassifier()
items = []
rejects = []

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
    
    if i == target_idx:
        print(f"=== PROCESSANDO LINHA {i} (ALVO) ===")
        print(f"Cartão atual: {classifier.current_card}")
        print(f"Data extraída: {date}")
        print(f"Valor extraído: {value}")
        print(f"Última data para cartão: {classifier.last_date_by_card.get(card_key, 'N/A')}")
    
    if date and value:
        card_key = classifier.current_card or "unknown"
        last_date_for_card = classifier.last_date_by_card.get(card_key)
        
        if i == target_idx:
            print(f"\nEntrou no bloco 'if date and value'")
            print(f"last_date_for_card: {last_date_for_card}")
            print(f"date < last_date_for_card: {date < last_date_for_card if last_date_for_card else False}")
        
        if last_date_for_card and date < last_date_for_card:
            from datetime import datetime
            last_date_obj = datetime.strptime(last_date_for_card, "%Y-%m-%d")
            current_date_obj = datetime.strptime(date, "%Y-%m-%d")
            days_diff = (last_date_obj - current_date_obj).days
            
            if i == target_idx:
                print(f"\nData é anterior. Diferença: {days_diff} dias")
            
            if days_diff > 60:
                if i == target_idx:
                    print(f"REJEITADA: diferença > 60 dias")
                rejects.append(type('RejectedLine', (), {
                    'line': line_clean,
                    'reason': f"Data {date} é anterior à data anterior {last_date_for_card} (cartão {card_key}, diferença de {days_diff} dias)"
                })())
                continue
            
            if i == target_idx:
                print(f"ACEITA: diferença <= 60 dias, continuando processamento")
        
        from card_pdf_parser.parser.rules import extract_description
        description = extract_description(line_clean, date, value)
        desc_clean = description.strip()
        
        if i == target_idx:
            print(f"\nDescrição extraída: '{description}'")
            print(f"Descrição limpa: '{desc_clean}'")
            print(f"Tamanho: {len(desc_clean)}")
        
        if not desc_clean or len(desc_clean) < 3:
            if i == target_idx:
                print(f"REJEITADA: descrição muito curta")
            rejects.append(type('RejectedLine', (), {
                'line': line_clean,
                'reason': "Descrição muito curta ou vazia após extração"
            })())
            continue
        
        import re
        if re.match(r'^[\d\s\.\,\-\/]+$', desc_clean):
            if i == target_idx:
                print(f"REJEITADA: descrição contém apenas números/símbolos")
            rejects.append(type('RejectedLine', (), {
                'line': line_clean,
                'reason': "Descrição contém apenas números/símbolos"
            })())
            continue
        
        if i == target_idx:
            print(f"\n[OK] Descrição válida, adicionando aos itens!")
        
        from card_pdf_parser.parser.rules import extract_installments
        numero_parcela, parcelas = extract_installments(line_clean, value)
        
        flux = "Entrada" if value < 0 else "Saida"
        
        last4_formatted = ""
        if classifier.current_card:
            last4_formatted = f"Final {classifier.current_card} - ALINE I DE SOUSA"
        else:
            last4_formatted = None
        
        from card_pdf_parser.parser.model import ParsedItem
        item = ParsedItem(
            date=date,
            description=description,
            amount=abs(value),
            last4=last4_formatted,
            flux=flux,
            source="Cartão de Crédito",
            parcelas=parcelas,
            numero_parcela=numero_parcela
        )
        
        if i == target_idx:
            print(f"\nItem criado:")
            print(f"  date: {item.date}")
            print(f"  description: {item.description}")
            print(f"  amount: {item.amount}")
        
        items.append(item)
        
        if not last_date_for_card or date >= last_date_for_card:
            classifier.last_date = date
            classifier.last_date_by_card[card_key] = date
            if i == target_idx:
                print(f"\nAtualizada last_date_by_card para: {date}")

# Verificar se foi adicionada
print(f"\n=== Verificação final ===")
print(f"Total de itens: {len(items)}")
found = False
for item in items:
    if "seg" in item.description.lower() and "cartao" in item.description.lower():
        found = True
        print(f"\nENCONTRADO: {item.date} - {item.description} - {item.amount}")

if not found:
    print("NÃO ENCONTRADO nos itens!")

