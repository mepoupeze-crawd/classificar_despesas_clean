#!/usr/bin/env python3
"""
Script de teste para validar o parsing do fatura_cartao_2.pdf contra o output_esperado2.json.

Este script:
1. Processa o PDF fatura_cartao_2.pdf
2. Gera parse_output2.json
3. Compara com tests/output_esperado2.json
4. Reporta todas as diferenças encontradas
5. Retorna código de saída 0 se idênticos, 1 se houver diferenças
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Importar o parser
from card_pdf_parser.parser.extract import extract_lines_lr_order
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.validate import calculate_stats, validate_delta
from card_pdf_parser.parser.rules import detect_card_marker, extract_card_heading, extract_subtotal, extract_value
from card_pdf_parser.parser.model import ParseResponse
from decimal import Decimal


def process_pdf(pdf_path: str) -> Dict[str, Any]:
    """Processa o PDF e retorna o resultado como dicionário."""
    # Extrair linhas na ordem L→R
    lines = extract_lines_lr_order(pdf_path)
    total_lines = len(lines)
    
    # Extrair subtotais do PDF associados aos cartões (antes da classificação)
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
    
    # Tentar detectar ano da fatura (buscar em linhas iniciais)
    import re
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
    delta_valid = validate_delta(stats, tolerance)
    
    # Preparar resposta
    response = ParseResponse(
        items=items,
        stats=stats,
        rejects=rejects
    )
    
    # Converter para dicionário e serializar Decimal para string
    result = response.model_dump()
    
    # Converter todos os Decimal para string recursivamente
    def convert_decimals(obj):
        if isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: convert_decimals(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_decimals(item) for item in obj]
        return obj
    
    return convert_decimals(result)


def compare_outputs(actual: Dict[str, Any], expected: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Compara dois outputs e retorna lista de diferenças encontradas.
    
    Returns:
        Lista de dicionários com informações sobre cada diferença encontrada
    """
    differences = []
    
    # Comparar items
    actual_items = actual.get('items', [])
    expected_items = expected.get('items', [])
    
    max_items = max(len(actual_items), len(expected_items))
    
    for i in range(max_items):
        if i >= len(actual_items):
            differences.append({
                'type': 'missing_item',
                'index': i,
                'expected': expected_items[i],
                'message': f'Item esperado na posição {i} não encontrado no output atual'
            })
            continue
        
        if i >= len(expected_items):
            differences.append({
                'type': 'extra_item',
                'index': i,
                'actual': actual_items[i],
                'message': f'Item extra na posição {i} no output atual'
            })
            continue
        
        actual_item = actual_items[i]
        expected_item = expected_items[i]
        
        # Comparar cada campo
        fields_to_check = ['date', 'description', 'amount', 'last4', 'flux', 'source', 'parcelas', 'numero_parcela']
        
        for field in fields_to_check:
            actual_value = actual_item.get(field)
            expected_value = expected_item.get(field)
            
            if actual_value != expected_value:
                differences.append({
                    'type': 'field_mismatch',
                    'index': i,
                    'field': field,
                    'description': actual_item.get('description', 'N/A'),
                    'date': actual_item.get('date', 'N/A'),
                    'expected': expected_value,
                    'actual': actual_value,
                    'message': f'Item {i} ({actual_item.get("description", "N/A")} - {actual_item.get("date", "N/A")}): campo "{field}" diferente. Esperado: {expected_value}, Atual: {actual_value}'
                })
                break  # Reportar apenas o primeiro campo diferente por item
    
    # Comparar stats (opcional - apenas reportar, não falhar)
    actual_stats = actual.get('stats', {})
    expected_stats = expected.get('stats', {})
    
    stats_fields = ['total_lines', 'matched', 'rejected', 'sum_abs_values', 'sum_saida', 'sum_entrada']
    for field in stats_fields:
        if actual_stats.get(field) != expected_stats.get(field):
            differences.append({
                'type': 'stats_mismatch',
                'field': field,
                'expected': expected_stats.get(field),
                'actual': actual_stats.get(field),
                'message': f'Estatística "{field}" diferente. Esperado: {expected_stats.get(field)}, Atual: {actual_stats.get(field)}'
            })
    
    return differences


def main():
    """Função principal do teste."""
    workspace = Path(__file__).parent
    pdf_path = workspace / 'fatura_cartao_2.pdf'
    output_path = workspace / 'parse_output2.json'
    expected_path = workspace / 'tests' / 'output_esperado2.json'
    
    print("=" * 80)
    print("  Teste de Validacao do Parser de PDF Itau (fatura_cartao_2.pdf)")
    print("=" * 80)
    print()
    
    # Verificar se os arquivos existem
    if not pdf_path.exists():
        print(f"ERRO: Arquivo PDF nao encontrado: {pdf_path}")
        sys.exit(1)
    
    if not expected_path.exists():
        print(f"ERRO: Arquivo esperado nao encontrado: {expected_path}")
        print(f"Execute primeiro: python test_generate_output2.py")
        sys.exit(1)
    
    # Carregar output esperado
    print(f"[1/3] Carregando output esperado: {expected_path}")
    try:
        with open(expected_path, 'r', encoding='utf-8') as f:
            expected_output = json.load(f)
        print(f"   [OK] Carregado: {len(expected_output.get('items', []))} itens esperados")
    except Exception as e:
        print(f"   [ERRO] Erro ao carregar arquivo esperado: {e}")
        sys.exit(1)
    
    # Processar PDF
    print(f"\n[2/3] Processando PDF: {pdf_path}")
    try:
        actual_output = process_pdf(str(pdf_path))
        print(f"   [OK] Processado: {len(actual_output.get('items', []))} itens extraidos")
    except Exception as e:
        print(f"   [ERRO] Erro ao processar PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Salvar output gerado
    print(f"\n[3/3] Salvando output gerado: {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(actual_output, f, ensure_ascii=False, indent=2)
        print(f"   [OK] Salvo com sucesso")
    except Exception as e:
        print(f"   [ERRO] Erro ao salvar output: {e}")
        sys.exit(1)
    
    # Comparar outputs
    print(f"\n[4/4] Comparando outputs...")
    differences = compare_outputs(actual_output, expected_output)
    
    if not differences:
        print("   [OK] Nenhuma diferenca encontrada!")
        print("\n" + "=" * 80)
        print("  RESULTADO: SUCESSO - Outputs sao identicos!")
        print("=" * 80)
        return 0
    else:
        print(f"   [ERRO] Encontradas {len(differences)} diferenca(s):\n")
        
        # Agrupar por tipo
        by_type = {}
        for diff in differences:
            diff_type = diff['type']
            if diff_type not in by_type:
                by_type[diff_type] = []
            by_type[diff_type].append(diff)
        
        # Reportar diferenças de forma detalhada
        for diff_type, diffs in by_type.items():
            print(f"  {diff_type.upper()}: {len(diffs)} ocorrencia(s)")
            for diff in diffs[:20]:  # Mostrar no máximo 20 de cada tipo
                if diff_type == 'field_mismatch':
                    print(f"    Item {diff['index']}: {diff['description']} ({diff['date']})")
                    print(f"      Campo '{diff['field']}':")
                    print(f"        Esperado: {diff['expected']}")
                    print(f"        Atual:    {diff['actual']}")
                else:
                    print(f"    - {diff['message']}")
            if len(diffs) > 20:
                print(f"    ... e mais {len(diffs) - 20} ocorrencia(s)")
            print()
        
        print("=" * 80)
        print("  RESULTADO: FALHA - Outputs sao diferentes!")
        print("=" * 80)
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)


