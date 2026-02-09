#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para validar o parsing de fatura_cartao_3.pdf
"""

import json
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
workspace = Path(__file__).parent
sys.path.insert(0, str(workspace))

from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.validate import calculate_stats
from card_pdf_parser.parser.rules import detect_card_marker, extract_value
from decimal import Decimal
import re

def main():
    print("=" * 80)
    print("  Cenario de Teste: fatura_cartao_3.pdf vs output_esperado3.json")
    print("=" * 80)
    print()
    
    # Caminhos dos arquivos
    pdf_path = workspace / "fatura_cartao_3.pdf"
    expected_path = workspace / "tests" / "output_esperado3.json"
    output_path = workspace / "parse_output3.json"
    
    # [1/3] Carregar output esperado
    print("[1/3] Carregando output esperado...")
    try:
        with open(expected_path, 'r', encoding='utf-8') as f:
            expected_data = json.load(f)
        expected_items = expected_data.get('items', [])
        print(f"   [OK] {len(expected_items)} itens esperados")
    except Exception as e:
        print(f"   [ERRO] Falha ao carregar output esperado: {e}")
        return 1
    
    # [2/3] Processar PDF
    print("[2/3] Processando PDF...")
    try:
        lines = extract_lines_lr_order(str(pdf_path))
        total_lines = len(lines)
        
        # Extrair subtotais do PDF associados aos cartões
        subtotals = {}
        current_card_for_subtotal = None
        
        for line in lines:
            marker = detect_card_marker(line)
            if marker:
                marker_type, marker_card = marker
                if marker_type == "start":
                    current_card_for_subtotal = marker_card
                elif marker_type == "total":
                    subtotal = extract_value(line)
                    if subtotal:
                        subtotals[marker_card] = subtotal
                    current_card_for_subtotal = None
        
        # Detectar ano da fatura
        invoice_year = None
        for line in lines[:50]:
            year_match = re.search(r'20\d{2}', line)
            if year_match:
                invoice_year = int(year_match.group(0))
                break
        
        # Classificar linhas
        classifier = LineClassifier(invoice_year=invoice_year)
        items, rejects = classifier.classify_lines(lines)
        
        # Calcular estatísticas
        stats = calculate_stats(items, rejects, total_lines, subtotals)
        
        parsed_items = items
        print(f"   [OK] {len(parsed_items)} itens extraidos")
    except Exception as e:
        print(f"   [ERRO] Falha ao processar PDF: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Salvar output gerado
    output_data = {
        'items': [
            {
                'date': item.date,
                'description': item.description,
                'amount': str(item.amount),
                'last4': item.last4,
                'flux': item.flux,
                'source': item.source,
                'parcelas': item.parcelas,
                'numero_parcela': item.numero_parcela
            }
            for item in parsed_items
        ],
        'stats': {
            'total_lines': stats.total_lines,
            'matched': stats.matched,
            'rejected': stats.rejected,
            'sum_abs_values': str(stats.sum_abs_values),
            'sum_saida': str(stats.sum_saida),
            'sum_entrada': str(stats.sum_entrada),
            'by_card': {k: {
                'control_total': str(v.control_total),
                'calculated_total': str(v.calculated_total),
                'delta': str(v.delta)
            } for k, v in stats.by_card.items()}
        },
        'rejects': [{'line': r.line, 'reason': r.reason} for r in rejects]
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    print(f"   [OK] Output salvo em: {output_path}")
    
    # [3/3] Comparar outputs
    print("[3/3] Comparando outputs...")
    
    if len(parsed_items) != len(expected_items):
        print(f"   [DIFERENCA] Numero de itens diferente: {len(parsed_items)} vs {len(expected_items)}")
    
    differences = []
    max_items = max(len(parsed_items), len(expected_items))
    
    for i in range(max_items):
        if i >= len(parsed_items):
            differences.append(f"Item {i+1}: FALTANDO no output gerado - {expected_items[i]}")
            continue
        if i >= len(expected_items):
            differences.append(f"Item {i+1}: EXTRA no output gerado - {parsed_items[i].__dict__}")
            continue
        
        parsed = parsed_items[i]
        expected = expected_items[i]
        
        # Comparar todos os campos
        fields_to_check = ['date', 'description', 'amount', 'last4', 'flux', 'source', 'parcelas', 'numero_parcela']
        item_diff = []
        
        for field in fields_to_check:
            parsed_value = getattr(parsed, field, None)
            expected_value = expected.get(field)
            
            # Normalizar valores
            if field == 'amount':
                parsed_value = str(parsed_value) if parsed_value is not None else None
                expected_value = str(expected_value) if expected_value is not None else None
            elif parsed_value is not None and expected_value is not None:
                parsed_value = str(parsed_value)
                expected_value = str(expected_value)
            
            if parsed_value != expected_value:
                item_diff.append(f"{field}: '{parsed_value}' != '{expected_value}'")
        
        if item_diff:
            differences.append(f"Item {i+1} ({parsed.date} - {parsed.description}): " + ", ".join(item_diff))
    
    if differences:
        print(f"   [ERRO] {len(differences)} diferencas encontradas:")
        for diff in differences[:20]:  # Mostrar apenas as primeiras 20
            print(f"      - {diff}")
        if len(differences) > 20:
            print(f"      ... e mais {len(differences) - 20} diferencas")
        print()
        print("=" * 80)
        print("  RESULTADO: FALHA")
        print("=" * 80)
        return 1
    else:
        print("   [OK] Nenhuma diferenca encontrada!")
        print()
        print("=" * 80)
        print("  RESULTADO: SUCESSO")
        print("=" * 80)
        return 0

if __name__ == '__main__':
    sys.exit(main())

