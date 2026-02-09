#!/usr/bin/env python3
"""Script para testar todos os PDFs e garantir que os ajustes não quebram nada"""

import json
from pathlib import Path
from services.pdf.itau_cartao_parser import parse_itau_fatura

# PDFs para testar
pdfs_to_test = [
    'aline-fatura-novembro-c2cfc522-7e3c-4c2f-b9c2-d5ee4b22c063.pdf',
    'aline-agosto-fatura-Fatura_Itau_20251109-201318.pdf',
    'aline-outubro_Fatura_Itau_20251116-142233.pdf',
]

print("=" * 80)
print("TESTE: Validação de todos os PDFs")
print("=" * 80)
print()

results = {}

for pdf_path in pdfs_to_test:
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        print(f"⚠️  {pdf_path}: ARQUIVO NÃO ENCONTRADO")
        results[pdf_path] = {'status': 'not_found', 'items': 0}
        continue
    
    print(f"Processando: {pdf_path}")
    try:
        result = parse_itau_fatura(str(pdf_file))
        items = result.get('items', [])
        stats = result.get('stats', {})
        
        items_count = len(items)
        matched = stats.get('matched', 0)
        
        print(f"  ✓ Itens extraídos: {items_count}")
        print(f"  ✓ Matched: {matched}")
        print(f"  ✓ Total linhas: {stats.get('total_lines', 0)}")
        
        if items_count > 0:
            print(f"  ✓ Primeiro item: {items[0].get('date')} | {items[0].get('description')[:40]}")
        
        results[pdf_path] = {
            'status': 'success',
            'items': items_count,
            'matched': matched
        }
        
        # Verificar se é o PDF de novembro e se tem 23 transações
        if 'novembro' in pdf_path.lower():
            if items_count == 23:
                print(f"  ✅ PDF DE NOVEMBRO: 23 transações detectadas corretamente!")
            else:
                print(f"  ⚠️  PDF DE NOVEMBRO: Esperado 23, encontrado {items_count}")
        
    except Exception as e:
        print(f"  ❌ ERRO: {e}")
        results[pdf_path] = {'status': 'error', 'error': str(e), 'items': 0}
        import traceback
        traceback.print_exc()
    
    print()

print("=" * 80)
print("RESUMO:")
print("=" * 80)
for pdf_path, result in results.items():
    status = result.get('status', 'unknown')
    items = result.get('items', 0)
    if status == 'success':
        print(f"✓ {Path(pdf_path).name}: {items} itens")
    elif status == 'not_found':
        print(f"⚠️  {Path(pdf_path).name}: Arquivo não encontrado")
    else:
        print(f"❌ {Path(pdf_path).name}: Erro - {result.get('error', 'Desconhecido')}")

