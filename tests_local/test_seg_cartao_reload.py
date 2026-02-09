import sys
import importlib

# Forçar reload dos módulos
if 'card_pdf_parser.parser.classify' in sys.modules:
    importlib.reload(sys.modules['card_pdf_parser.parser.classify'])
if 'card_pdf_parser.parser.rules' in sys.modules:
    importlib.reload(sys.modules['card_pdf_parser.parser.rules'])

from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
import json

pdf_path = 'fatura_cartao_2.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Processando fatura_cartao_2.pdf (com reload forçado) ===\n")

classifier = LineClassifier()
items, rejects = classifier.classify_lines(lines)

print(f"Total de itens extraídos: {len(items)}")
print(f"Total de linhas rejeitadas: {len(rejects)}\n")

# Procurar "SEG CARTAO PROTEGIDO"
print("=== Procurando 'SEG CARTAO PROTEGIDO' ===\n")
found = False

for item in items:
    desc_lower = item.description.lower()
    if "seg" in desc_lower and "cartao" in desc_lower:
        found = True
        print("ENCONTRADO NOS ITENS:")
        print(f"  Descrição: {item.description}")
        print(f"  Data: {item.date}")
        print(f"  Valor: {item.amount}")
        print(f"  last4: {item.last4}")
        print(f"  flux: {item.flux}")
        print(f"  source: {item.source}")
        print(f"  parcelas: {item.parcelas}")
        print(f"  numero_parcela: {item.numero_parcela}")
        
        # Comparar com o esperado
        print(f"\nComparação com esperado:")
        print(f"  Esperado: date='2025-10-16', description='SEG CARTAO PROTEGIDO', amount='10.19'")
        print(f"  Atual:    date='{item.date}', description='{item.description}', amount='{item.amount}'")
        
        if item.date == "2025-10-16" and "SEG CARTAO PROTEGIDO" in item.description.upper() and str(item.amount) == "10.19":
            print(f"\n[OK] Transação identificada corretamente!")
        else:
            print(f"\n[ATENÇÃO] Algum campo não corresponde exatamente ao esperado")
        print()

if not found:
    print("NÃO ENCONTRADO nos itens extraídos.")
    print("\nVerificando nas rejeições:")
    for reject in rejects:
        if "seg" in reject.line.lower() and "cartao" in reject.line.lower():
            print(f"  Linha: '{reject.line}'")
            print(f"  Motivo: {reject.reason}")
    
    # Listar todos os itens para debug
    print("\n=== Todos os itens extraídos ===")
    for i, item in enumerate(items):
        print(f"{i+1}. {item.date} - {item.description[:50]}... - {item.amount}")

