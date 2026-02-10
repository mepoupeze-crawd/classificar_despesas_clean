#!/usr/bin/env python3
"""Debug: verificar ordem das linhas extraídas"""

from card_pdf_parser.parser.extract import extract_lines_lr_order_block_based
from card_pdf_parser.parser.rules import extract_card_header_with_holder, CARD_SECTION_TOTAL_PATTERN, TRANSACTION_BLOCK_HEADER_PATTERN

lines = extract_lines_lr_order_block_based("fatura_cartao_3.pdf")

print("=== LINHAS EXTRAÍDAS ===")
print(f"Total: {len(lines)}\n")

# Procurar seção de transações
in_section = False
left_start = None
right_start = None

for i, line in enumerate(lines, 1):
    if "LANÇAMENTOS: COMPRAS E SAQUES" in line.upper():
        in_section = True
        print(f"Linha {i}: SEÇÃO ENCONTRADA: {line}")
        continue
    
    if not in_section:
        continue
    
    # Verificar header de cartão
    header = extract_card_header_with_holder(line)
    if header:
        holder, last4 = header
        if left_start is None:
            left_start = i
            print(f"\n=== COLUNA ESQUERDA INICIA (linha {i}) ===")
            print(f"Header: {holder} (final {last4})")
        else:
            right_start = i
            print(f"\n=== COLUNA DIREITA INICIA (linha {i}) ===")
            print(f"Header: {holder} (final {last4})")
        continue
    
    # Verificar subtotal
    subtotal = CARD_SECTION_TOTAL_PATTERN.match(line.strip())
    if subtotal:
        print(f"\nLinha {i}: SUBTOTAL: {line[:80]}")
        continue
    
    # Verificar transação
    trans = TRANSACTION_BLOCK_HEADER_PATTERN.match(line.strip())
    if trans and i < 150:  # Mostrar primeiras transações
        data = trans.group('data')
        rest = trans.group('rest')[:50]
        valor = trans.group('valor')
        col = "ESQUERDA" if left_start and (right_start is None or i < right_start) else "DIREITA"
        print(f"Linha {i} [{col}]: {data} {rest}... {valor}")

