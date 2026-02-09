#!/usr/bin/env python3
"""
Script para processar fatura_cartao_3.pdf e gerar output_esperado3.json.

Este script:
1. Processa o PDF fatura_cartao_3.pdf
2. Gera tests/output_esperado3.json com o resultado esperado
3. Opcionalmente compara com um arquivo existente se fornecido
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any

# Importar o parser
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


def main():
    """Função principal do teste."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Gerador de output_esperado3.json')
    parser.add_argument('--force', '-f', action='store_true', 
                       help='Sobrescrever arquivo existente sem perguntar')
    args = parser.parse_args()
    
    workspace = Path(__file__).parent
    pdf_path = workspace / 'fatura_cartao_3.pdf'
    output_path = workspace / 'tests' / 'output_esperado3.json'
    
    print("=" * 80)
    print("  Gerador de Output Esperado para fatura_cartao_3.pdf")
    print("=" * 80)
    print()
    
    # Verificar se o PDF existe
    if not pdf_path.exists():
        print(f"ERRO: Arquivo PDF não encontrado: {pdf_path}")
        sys.exit(1)
    
    # Criar diretório tests se não existir
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Processar PDF
    print(f"[1/2] Processando PDF: {pdf_path}")
    try:
        output_data = process_pdf(str(pdf_path))
        print(f"   [OK] Processado: {len(output_data.get('items', []))} itens extraídos")
        print(f"   [OK] Rejeições: {len(output_data.get('rejects', []))} linhas rejeitadas")
    except Exception as e:
        print(f"   [ERRO] Erro ao processar PDF: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Verificar deltas antes de salvar
    if 'stats' in output_data and 'by_card' in output_data['stats']:
        print(f"\n   Verificando deltas por cartao:")
        for card, card_stats in output_data['stats']['by_card'].items():
            delta = float(card_stats.get('delta', 0))
            if card == 'unknown':
                print(f"     Cartao {card}: delta={delta} (aceitavel para unknown)")
            elif delta > 0.01:
                print(f"     Cartao {card}: delta={delta} [ACIMA DA TOLERANCIA]")
            else:
                print(f"     Cartao {card}: delta={delta} [OK]")
    
    # Perguntar se deseja sobrescrever se o arquivo já existe (a menos que --force seja usado)
    if output_path.exists() and not args.force:
        print(f"\n   [AVISO] Arquivo {output_path} já existe.")
        print(f"   Use --force para sobrescrever sem perguntar.")
        print(f"   Operação cancelada.")
        return 0
    
    # Salvar output esperado
    print(f"\n[2/2] Salvando output esperado: {output_path}")
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"   [OK] Salvo com sucesso")
    except Exception as e:
        print(f"   [ERRO] Erro ao salvar output: {e}")
        sys.exit(1)
    
    # Estatísticas
    print(f"\n" + "=" * 80)
    print(f"  RESULTADO:")
    print(f"  - Total de itens: {len(output_data.get('items', []))}")
    print(f"  - Total de rejeições: {len(output_data.get('rejects', []))}")
    
    if 'stats' in output_data:
        stats = output_data['stats']
        print(f"  - Linhas processadas: {stats.get('total_lines', 'N/A')}")
        print(f"  - Linhas correspondidas: {stats.get('matched', 'N/A')}")
        print(f"  - Linhas rejeitadas: {stats.get('rejected', 'N/A')}")
        print(f"  - Soma valores absolutos: {stats.get('sum_abs_values', 'N/A')}")
        print(f"  - Soma saída: {stats.get('sum_saida', 'N/A')}")
        print(f"  - Soma entrada: {stats.get('sum_entrada', 'N/A')}")
        
        if 'by_card' in stats:
            print(f"\n  Deltas por cartao:")
            for card, card_stats in stats['by_card'].items():
                delta = float(card_stats.get('delta', 0))
                control = card_stats.get('control_total', '0')
                calculated = card_stats.get('calculated_total', '0')
                status = "[OK]" if (card == 'unknown' or delta <= 0.01) else "[ERRO]"
                print(f"    {card}: delta={delta} (control={control}, calculated={calculated}) {status}")
    
    print("=" * 80)
    print(f"\nArquivo gerado: {output_path}")
    return 0


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)

