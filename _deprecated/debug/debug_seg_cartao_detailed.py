import json
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.rules import extract_value, extract_date, extract_description
from card_pdf_parser.parser.classify import LineClassifier
import re

pdf_path = 'fatura_cartao_2.pdf'
lines = extract_lines_lr_order(pdf_path)

print("=== Debug detalhado da linha 'SEG CARTAO PROTEGIDO' ===\n")

# Encontrar a linha específica
target_line = None
for i, line in enumerate(lines):
    if "seg" in line.lower() and "cartao" in line.lower():
        target_line = line.strip()
        print(f"Linha encontrada (índice {i}): '{target_line}'\n")
        break

if not target_line:
    print("Linha não encontrada!")
    exit(1)

# Simular o processo de classificação passo a passo
print("=== Simulando processo de classificação ===\n")

# 1. Extrair data
date = extract_date(target_line)
print(f"1. Data extraída: {date}")

# 2. Extrair valor
value = extract_value(target_line)
print(f"2. Valor extraído: {value}")

if not date or not value:
    print("\nERRO: Falta data ou valor - linha seria rejeitada")
    exit(1)

# 3. Extrair descrição
description = extract_description(target_line, date, value)
print(f"3. Descrição extraída: '{description}'")
print(f"   Tamanho: {len(description)}")

# 4. Validar descrição
desc_clean = description.strip()
print(f"\n4. Validações de descrição:")
print(f"   Descrição limpa: '{desc_clean}'")
print(f"   Tamanho após strip: {len(desc_clean)}")

if not desc_clean or len(desc_clean) < 3:
    print("   [REJEITADA] Descrição muito curta ou vazia")
else:
    print("   [OK] Descrição tem tamanho suficiente")

# Verificar se é só números/símbolos
if re.match(r'^[\d\s\.\,\-\/]+$', desc_clean):
    print("   [REJEITADA] Descrição contém apenas números/símbolos")
else:
    print("   [OK] Descrição contém caracteres alfabéticos")

# 5. Verificar se seria rejeitada por ordem de datas
print(f"\n5. Verificação de ordem de datas:")
print(f"   (Esta verificação depende do contexto - precisa do classificador completo)")

# Processar com o classificador real
print(f"\n=== Processando com classificador real ===\n")
classifier = LineClassifier()
items, rejects = classifier.classify_lines(lines)

# Procurar especificamente essa linha
found_in_items = False
found_in_rejects = False

for item in items:
    if "seg" in item.description.lower() and "cartao" in item.description.lower():
        found_in_items = True
        print(f"ENCONTRADO NOS ITENS:")
        print(f"  Descrição: {item.description}")
        print(f"  Data: {item.date}")
        print(f"  Valor: {item.amount}")
        print(f"  last4: {item.last4}")
        print(f"  parcelas: {item.parcelas}")
        print(f"  numero_parcela: {item.numero_parcela}")

for reject in rejects:
    if target_line in reject.line or ("seg" in reject.line.lower() and "cartao" in reject.line.lower()):
        found_in_rejects = True
        print(f"\nENCONTRADO NAS REJEIÇÕES:")
        print(f"  Linha: '{reject.line}'")
        print(f"  Motivo: {reject.reason}")

if not found_in_items and not found_in_rejects:
    print("ERRO: Linha não encontrada nem nos itens nem nas rejeições!")
    print("Isso pode indicar que a linha foi ignorada ou processada de forma diferente.")

