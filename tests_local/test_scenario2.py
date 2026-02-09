#!/usr/bin/env python3
"""
Cenário de teste: Processa fatura_cartao_2.pdf e compara com output_esperado2.json

Este script:
1. Processa o PDF fatura_cartao_2.pdf
2. Gera um output temporário
3. Compara com tests/output_esperado2.json
4. Reporta diferenças detalhadas
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any

from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.validate import calculate_stats, validate_delta
from card_pdf_parser.parser.rules import detect_card_marker, extract_value
from card_pdf_parser.parser.model import ParseResponse
from decimal import Decimal
import re


def process_pdf(pdf_path: str) -> Dict[str, Any]:
    """Processa o PDF e retorna o resultado como dicionário."""
    # Extrair linhas na ordem L→R
    lines = extract_lines_lr_order(pdf_path)
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
    
    # Validar deltas
    tolerance = Decimal('0.01')
    validate_delta(stats, tolerance)
    
    # Preparar resposta
    response = ParseResponse(
        items=items,
        stats=stats,
        rejects=rejects
    )
    
    # Converter para dicionário e serializar Decimal para string
    result = response.model_dump()
    
    def convert_decimals(obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_decimals(item) for item in obj]
        return obj
    
    return convert_decimals(result)


def compare_items(actual_items: List[Dict], expected_items: List[Dict]) -> List[Dict]:
    """Compara itens e retorna lista de diferenças."""
    differences = []
    max_len = max(len(actual_items), len(expected_items))
    
    for i in range(max_len):
        if i >= len(actual_items):
            differences.append({
                'type': 'missing',
                'index': i,
                'item': expected_items[i],
                'message': f'Item esperado na posição {i} não encontrado: {expected_items[i].get("description", "N/A")} ({expected_items[i].get("date", "N/A")})'
            })
            continue
        
        if i >= len(expected_items):
            differences.append({
                'type': 'extra',
                'index': i,
                'item': actual_items[i],
                'message': f'Item extra na posição {i}: {actual_items[i].get("description", "N/A")} ({actual_items[i].get("date", "N/A")})'
            })
            continue
        
        actual = actual_items[i]
        expected = expected_items[i]
        
        # Comparar cada campo
        fields = ['date', 'description', 'amount', 'last4', 'flux', 'source', 'parcelas', 'numero_parcela']
        
        for field in fields:
            actual_val = actual.get(field)
            expected_val = expected.get(field)
            
            if actual_val != expected_val:
                differences.append({
                    'type': 'mismatch',
                    'index': i,
                    'field': field,
                    'description': actual.get('description', 'N/A'),
                    'date': actual.get('date', 'N/A'),
                    'expected': expected_val,
                    'actual': actual_val,
                    'message': f'Item {i}: {actual.get("description", "N/A")} ({actual.get("date", "N/A")}) - Campo "{field}": esperado "{expected_val}", atual "{actual_val}"'
                })
                break
    
    return differences


def main():
    """Função principal."""
    workspace = Path(__file__).parent
    pdf_path = workspace / 'fatura_cartao_2.pdf'
    expected_path = workspace / 'tests' / 'output_esperado2.json'
    
    print("=" * 80)
    print("  Cenário de Teste: fatura_cartao_2.pdf vs output_esperado2.json")
    print("=" * 80)
    print()
    
    # Verificar arquivos
    if not pdf_path.exists():
        print(f"[ERRO] PDF não encontrado: {pdf_path}")
        return 1
    
    if not expected_path.exists():
        print(f"[ERRO] Arquivo esperado não encontrado: {expected_path}")
        print(f"Execute primeiro: python test_generate_output2.py")
        return 1
    
    # Carregar esperado
    print(f"[1/3] Carregando output esperado...")
    try:
        with open(expected_path, 'r', encoding='utf-8') as f:
            expected = json.load(f)
        print(f"   [OK] {len(expected.get('items', []))} itens esperados")
    except Exception as e:
        print(f"   [ERRO] {e}")
        return 1
    
    # Processar PDF
    print(f"\n[2/3] Processando PDF...")
    try:
        actual = process_pdf(str(pdf_path))
        print(f"   [OK] {len(actual.get('items', []))} itens extraídos")
    except Exception as e:
        print(f"   [ERRO] {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Comparar
    print(f"\n[3/3] Comparando outputs...")
    differences = compare_items(
        actual.get('items', []),
        expected.get('items', [])
    )
    
    if not differences:
        print("   [OK] Nenhuma diferenca encontrada!")
        print("\n" + "=" * 80)
        print("  RESULTADO: SUCESSO")
        print("=" * 80)
        return 0
    else:
        print(f"   [ERRO] {len(differences)} diferença(s) encontrada(s):\n")
        
        # Agrupar por tipo
        by_type = {}
        for diff in differences:
            diff_type = diff['type']
            if diff_type not in by_type:
                by_type[diff_type] = []
            by_type[diff_type].append(diff)
        
        # Reportar
        for diff_type, diffs in by_type.items():
            print(f"  {diff_type.upper()}: {len(diffs)} ocorrência(s)")
            for diff in diffs[:10]:
                print(f"    - {diff['message']}")
            if len(diffs) > 10:
                print(f"    ... e mais {len(diffs) - 10} ocorrência(s)")
            print()
        
        print("=" * 80)
        print("  RESULTADO: FALHA")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    sys.exit(main())

