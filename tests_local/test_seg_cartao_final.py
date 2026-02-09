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
from card_pdf_parser.parser.classify import LineClassifier

pdf_path = 'fatura_cartao_2.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Processando fatura_cartao_2.pdf (cache limpo) ===\n")

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
    seg_rejects = []
    for reject in rejects:
        if "seg" in reject.line.lower() and "cartao" in reject.line.lower():
            seg_rejects.append(reject)
    
    if seg_rejects:
        for reject in seg_rejects:
            print(f"  Linha: '{reject.line[:80]}...'")
            print(f"  Motivo: {reject.reason}\n")
    else:
        print("  Nenhuma rejeição encontrada com 'seg' e 'cartao'")
    
    # Verificar todas as transações de outubro de 2025
    print("\n=== Transações de outubro de 2025 ===")
    oct_items = [item for item in items if item.date.startswith("2025-10")]
    for item in sorted(oct_items, key=lambda x: x.date):
        print(f"  {item.date} - {item.description[:50]}... - {item.amount}")

