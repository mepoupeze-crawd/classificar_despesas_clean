"""
Validation and statistics calculation

DEPRECATED: Este módulo foi substituído por `services/pdf/itau_cartao_parser.py`.
O novo parser calcula estatísticas internamente via método `_build_stats()`.

Este módulo permanece apenas para referência e pode ser removido no futuro após validação completa.
"""

from typing import List, Dict
from decimal import Decimal

# Usar imports relativos para acessar módulos do diretório pai
from ..model import ParsedItem, ParseStats, CardStats, RejectedLine


def calculate_stats(
    items: List[ParsedItem],
    rejects: List[RejectedLine],
    total_lines: int,
    subtotals: Dict[str, Decimal] = None
) -> ParseStats:
    """
    Calcula estatísticas do parsing.
    
    Args:
        items: Lista de transações extraídas
        rejects: Lista de linhas rejeitadas
        total_lines: Total de linhas processadas
        subtotals: Subtotais por cartão extraídos do PDF (opcional)
        
    Returns:
        Estatísticas do parsing
    """
    matched = len(items)
    rejected = len(rejects)
    
    # Calcular soma dos valores absolutos
    sum_abs_values = sum((item.amount for item in items), Decimal('0'))
    sum_flux_saida = Decimal('0')
    sum_flux_entrada = Decimal('0')

    for item in items:
        if item.flux == "Entrada":
            sum_flux_entrada += item.amount
        else:
            sum_flux_saida += item.amount
    
    # Agrupar por cartão e calcular estatísticas
    by_card: Dict[str, CardStats] = {}
    
    if items:
        # Função para extrair apenas os últimos 4 dígitos do last4
        def extract_last4_digits(last4: str) -> str:
            """Extrai apenas os últimos 4 dígitos do last4 formatado."""
            if not last4:
                return "unknown"
            # Se last4 está no formato "Final XXXX - NOME", extrair apenas XXXX
            import re
            match = re.search(r'(\d{4})', last4)
            if match:
                return match.group(1)
            # Se já for apenas números, retornar como está
            if last4.isdigit() and len(last4) == 4:
                return last4
            return "unknown"
        
        # Agrupar items por last4 (usando apenas os últimos 4 dígitos)
        items_by_card: Dict[str, List[ParsedItem]] = {}
        for item in items:
            # Extrair apenas os últimos 4 dígitos para agrupamento
            card_key = extract_last4_digits(item.last4) if item.last4 else "unknown"
            if card_key == "":
                continue  # Seção sem cartão (ex: produtos e serviços)
            if card_key not in items_by_card:
                items_by_card[card_key] = []
            items_by_card[card_key].append(item)
        
        # Calcular estatísticas por cartão
        for card_key, card_items in items_by_card.items():
            calculated_total = Decimal('0')
            for item in card_items:
                signed_value = item.amount if item.flux != "Entrada" else -item.amount
                calculated_total += signed_value
            
            # Obter control_total do PDF se disponível (usando apenas os últimos 4 dígitos)
            control_total = subtotals.get(card_key, Decimal('0')) if subtotals else Decimal('0')
            
            delta = abs(calculated_total - control_total)
            
            by_card[card_key] = CardStats(
                control_total=control_total,
                calculated_total=calculated_total,
                delta=delta
            )
    
    return ParseStats(
        total_lines=total_lines,
        matched=matched,
        rejected=rejected,
        sum_abs_values=sum_abs_values,
        by_card=by_card,
        sum_saida=sum_flux_saida,
        sum_entrada=sum_flux_entrada
    )


def validate_delta(stats: ParseStats, tolerance: Decimal = Decimal('0.01')) -> bool:
    """
    Valida se os deltas estão dentro da tolerância.
    
    Args:
        stats: Estatísticas do parsing
        tolerance: Tolerância para validação (padrão: R$0.01)
        
    Returns:
        True se todos os deltas estão dentro da tolerância
    """
    for card_stats in stats.by_card.values():
        if card_stats.delta > tolerance:
            return False
    return True

