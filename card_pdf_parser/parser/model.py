"""
Pydantic models for PDF parsing results
"""

from typing import List, Optional, Dict
from decimal import Decimal
from pydantic import BaseModel, Field


class ParsedItem(BaseModel):
    """Item parsed from PDF."""
    date: str = Field(..., description="Data da transação (YYYY-MM-DD)")
    description: str = Field(..., description="Descrição da transação")
    amount: Decimal = Field(..., description="Valor absoluto da transação")
    last4: Optional[str] = Field(None, description="Últimos 4 dígitos do cartão")
    flux: str = Field("Saida", description="Fluxo da transação (entrada/saída)")
    source: Optional[str] = Field(None, description="Fonte da transação (ex: Cartão de Crédito)")
    parcelas: Optional[int] = Field(None, description="Total de parcelas")
    numero_parcela: Optional[int] = Field(None, description="Número da parcela atual")


class CardStats(BaseModel):
    """Estatísticas por cartão."""
    control_total: Decimal = Field(..., description="Total de controle do PDF")
    calculated_total: Decimal = Field(..., description="Total calculado das transações")
    delta: Decimal = Field(..., description="Diferença entre controle e calculado")


class RejectedLine(BaseModel):
    """Linha rejeitada durante o parsing."""
    line: str = Field(..., description="Conteúdo da linha rejeitada")
    reason: str = Field(..., description="Motivo da rejeição")


class ParseStats(BaseModel):
    """Estatísticas do parsing."""
    total_lines: int = Field(..., description="Total de linhas processadas")
    matched: int = Field(..., description="Número de transações extraídas")
    rejected: int = Field(..., description="Número de linhas rejeitadas")
    sum_abs_values: Decimal = Field(..., description="Soma dos valores absolutos")
    sum_saida: Decimal = Field(..., description="Soma dos valores com flux='Saida'")
    sum_entrada: Decimal = Field(..., description="Soma dos valores com flux='Entrada'")
    by_card: Dict[str, CardStats] = Field(default_factory=dict, description="Estatísticas por cartão")


class ParseResponse(BaseModel):
    """Resposta completa do parsing."""
    items: List[ParsedItem] = Field(..., description="Lista de transações extraídas")
    stats: ParseStats = Field(..., description="Estatísticas do parsing")
    rejects: List[RejectedLine] = Field(default_factory=list, description="Linhas rejeitadas")

