#!/usr/bin/env python3
"""Debug: verificar processamento de transações"""

from card_pdf_parser.parser.extract import extract_lines_lr_order_block_based
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.rules import TRANSACTION_BLOCK_HEADER_PATTERN
import re

lines = extract_lines_lr_order_block_based("fatura_cartao_3.pdf")

# Encontrar seção de transações
in_section = False
for i, line in enumerate(lines, 1):
    if "LANÇAMENTOS: COMPRAS E SAQUES" in line.upper():
        in_section = True
        print(f"=== SEÇÃO ENCONTRADA (linha {i}) ===\n")
        break

# Mostrar primeiras 20 transações esperadas
print("PRIMEIRAS TRANSAÇÕES ESPERADAS (coluna esquerda):")
expected_left = [
    ("30/04", "CLINICA ADRIANA VI", "2.048,50", "04/10"),
    ("16/05", "FRATEX INDUSTRIA E", "111,96", "04/05"),
    ("21/05", "ZARA BRASIL LTDA", "143,50", "04/05"),
    ("30/05", "CLINICA ADRIANA VI", "513,34", "03/03"),
    ("03/06", "PASSARO AZUL COMER", "266,35", "03/06"),
    ("03/06", "GALLERIST COM IMP", "125,82", "03/05"),
    ("03/06", "ZARA BRASIL LTDA", "135,50", "03/05"),
    ("12/06", "SEPHORA CIDJARDIN", "83,00", "03/05"),
    ("17/06", "MTKS JOIAS", "107,50", "03/04"),
    ("01/07", "BRUNA CUTAIT", "487,74", "02/07"),
    ("01/07", "BRUNA CUTAIT", "- 0,18", None),  # Negativo
    ("11/07", "LIVRARIA DA TRAVES", "439,50", "02/02"),
    ("23/07", "DROGASIL1255", "160,10", "02/03"),
    ("30/07", "TIAGO TAXI", "32,40", None),
    ("30/07", "ESPORTE CLUBE PINHEIRO", "10,80", None),
]

for date, desc, value, parcelas in expected_left[:5]:
    print(f"  {date} {desc} {value} {parcelas or ''}")

print("\n\nPRIMEIRAS TRANSAÇÕES DA DIREITA (após '30/07 ESPORTE CLUBE PINHEIRO'):")
expected_right = [
    ("30/07", "EC PINHEIROS", "3,00", None),
    ("30/07", "Quiosque SHOP CIDADE J", "37,90", None),
    # ... etc
]

for date, desc, value, parcelas in expected_right[:3]:
    print(f"  {date} {desc} {value} {parcelas or ''}")

print("\n\n=== LINHAS EXTRAÍDAS (primeiras 20 após seção) ===")
count = 0
for i, line in enumerate(lines, 1):
    if not in_section:
        if "LANÇAMENTOS: COMPRAS E SAQUES" in line.upper():
            in_section = True
        continue
    
    if count >= 20:
        break
    
    # Verificar se é transação
    trans = TRANSACTION_BLOCK_HEADER_PATTERN.match(line.strip())
    if trans:
        data = trans.group('data')
        rest = trans.group('rest')[:60]
        valor = trans.group('valor')
        print(f"{i:3}: {data} {rest}... {valor}")
        count += 1

