import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier

pdf_path = 'fatura_cartao_2.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Processando fatura_cartao_2.pdf ===\n")

classifier = LineClassifier()
items, rejects = classifier.classify_lines(lines)

print(f"Total de itens extraídos: {len(items)}")
print(f"Total de linhas rejeitadas: {len(rejects)}\n")

# Procurar "SEG CARTAO PROTEGIDO"
print("=== Procurando 'SEG CARTAO PROTEGIDO' ===\n")
found = False

for item in items:
    if "seg" in item.description.lower() and "cartao" in item.description.lower():
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

if not found:
    print("NÃO ENCONTRADO nos itens extraídos.")
    print("\nVerificando nas rejeições:")
    for reject in rejects:
        if "seg" in reject.line.lower() and "cartao" in reject.line.lower():
            print(f"  Linha: '{reject.line}'")
            print(f"  Motivo: {reject.reason}")

