#!/usr/bin/env python3
"""Script de debug para analisar o PDF de novembro"""

import re
from services.pdf.itau_cartao_parser import parse_itau_fatura, normalize_text
from card_pdf_parser.parser.extract import extract_lines_lr_order

pdf_path = 'aline-fatura-novembro-c2cfc522-7e3c-4c2f-b9c2-d5ee4b22c063.pdf'

print("=" * 80)
print("DEBUG: Análise do PDF de Novembro")
print("=" * 80)
print()

# 1. Extrair linhas
print("1. Extraindo linhas do PDF...")
lines = extract_lines_lr_order(pdf_path)
print(f"   Total de linhas extraídas: {len(lines)}\n")

# 2. Padrões
TRANSACTION_PATTERN = re.compile(r"(\d{2}/\d{2})(.*?)(-?\d{1,3}(?:\.\d{3})*,\d{2})")
CARD_HEADER_PATTERN = re.compile(r"aline i de sousa\s*\(final\s*(\d{4})\)", re.IGNORECASE)
SUMMARY_PATTERN = re.compile(r"lancamentos no cartao\s*\(final\s*(\d{4})\)\s+(\d{1,3}(?:\.\d{3})*,\d{2})", re.IGNORECASE)

# 3. Analisar linhas
print("2. Analisando detecção de seções e cartões...\n")
current_section = None
current_card = None
transactions_found = []

for i, line in enumerate(lines):
    line_stripped = line.strip()
    if not line_stripped:
        continue
    
    normalized_lower = normalize_text(line_stripped).lower()
    
    # Verificar seção
    if normalized_lower.startswith("lancamentos: compras e saques"):
        current_section = "compras"
        print(f"Linha {i}: ✓ SEÇÃO DETECTADA: 'compras'")
        print(f"   Texto: {line_stripped[:100]}\n")
    
    if normalized_lower.startswith("lancamentos: produtos e servicos"):
        current_section = "produtos"
        print(f"Linha {i}: ✓ SEÇÃO DETECTADA: 'produtos'")
        print(f"   Texto: {line_stripped[:100]}\n")
    
    # Verificar cabeçalho do cartão
    header_match = CARD_HEADER_PATTERN.search(normalized_lower)
    if header_match:
        current_card = header_match.group(1)
        print(f"Linha {i}: ✓ CARTÃO DETECTADO: final {current_card}")
        print(f"   Texto: {line_stripped[:100]}\n")
    
    # Verificar transações
    if current_section in {"compras", "produtos"}:
        if TRANSACTION_PATTERN.search(line_stripped):
            match = TRANSACTION_PATTERN.search(line_stripped)
            if match:
                date = match.group(1)
                desc = match.group(2).strip()[:50]
                value = match.group(3)
                transactions_found.append({
                    'line': i,
                    'date': date,
                    'desc': desc,
                    'value': value,
                    'section': current_section,
                    'card': current_card
                })
                print(f"Linha {i}: ✓ TRANSAÇÃO ENCONTRADA")
                print(f"   Data: {date}, Valor: {value}")
                print(f"   Descrição: {desc}")
                print(f"   Seção: {current_section}, Cartão: {current_card}")
                print(f"   Texto completo: {line_stripped[:120]}\n")

print(f"\n3. Resumo:")
print(f"   Total de transações encontradas: {len(transactions_found)}")
print(f"   Esperado: 23 transações\n")

# 4. Tentar parse completo
print("4. Tentando parse completo...\n")
try:
    result = parse_itau_fatura(pdf_path)
    items = result.get('items', [])
    print(f"   Itens extraídos pelo parser: {len(items)}")
    print(f"   Esperado: 23\n")
    
    if items:
        print("   Primeiros 5 itens:")
        for item in items[:5]:
            print(f"     - {item.get('date')} | {item.get('description')[:40]} | {item.get('amount')}")
    else:
        print("   ⚠️  NENHUM ITEM EXTRAÍDO!")
        print("\n   Verificando estatísticas:")
        stats = result.get('stats', {})
        print(f"     - Total de linhas: {stats.get('total_lines', 0)}")
        print(f"     - Matched: {stats.get('matched', 0)}")
        print(f"     - By card: {stats.get('by_card', {})}")
        
except Exception as e:
    print(f"   ❌ ERRO: {e}")
    import traceback
    traceback.print_exc()

