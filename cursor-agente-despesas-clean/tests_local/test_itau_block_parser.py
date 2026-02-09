#!/usr/bin/env python3
"""
Test script for Itaú PDF block-based parser
"""

import json
import sys
from decimal import Decimal
from typing import Dict, Any

from card_pdf_parser.parser.extract import extract_lines_lr_order_block_based
from card_pdf_parser.parser.classify import LineClassifier
from card_pdf_parser.parser.validate import calculate_stats
from card_pdf_parser.parser.rules import detect_card_marker, extract_subtotal, extract_value
from card_pdf_parser.parser.model import ParseResponse
import re


def convert_decimals(obj):
    """Converte Decimal para string recursivamente."""
    if isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_decimals(item) for item in obj]
    return obj


def process_pdf(pdf_path: str) -> Dict[str, Any]:
    """Processa PDF e retorna resultado como dicionário."""
    # Extrair linhas
    lines = extract_lines_lr_order_block_based(pdf_path)
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
                subtotal = extract_subtotal(line)
                if subtotal:
                    subtotals[marker_card] = subtotal
                current_card_for_subtotal = None
    
    # Tentar detectar ano da fatura
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
    
    # Preparar resposta
    response = ParseResponse(
        items=items,
        stats=stats,
        rejects=rejects
    )
    
    # Converter para dicionário e serializar Decimal para string
    result = response.model_dump()
    return convert_decimals(result)


def main():
    """Função principal."""
    pdf_path = "fatura_cartao_3.pdf"
    output_path = "fatura_cartao_3_output.json"
    
    print(f"Processando {pdf_path}...")
    result = process_pdf(pdf_path)
    
    print(f"Salvando resultado em {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Processado: {len(result['items'])} transacoes")
    print(f"Rejeitadas: {len(result['rejects'])} linhas")
    print(f"Estatisticas: {len(result['stats']['by_card'])} cartoes")
    print(f"\nResultado salvo em: {output_path}")


if __name__ == "__main__":
    main()

