#!/usr/bin/env python3
"""
Schemas Pydantic para o endpoint de feedback.

Define os modelos de dados para entrada e saída do endpoint de feedback,
incluindo validações e documentação para Swagger.
"""

from typing import List, Optional, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime


class FeedbackItem(BaseModel):
    """
    Schema para um item de feedback individual.
    
    Representa uma correção do usuário para uma transação classificada.
    """
    
    # Campos obrigatórios
    transactionId: str = Field(
        description="ID único da transação (obrigatório)",
        example="tx_123456789"
    )
    description: str = Field(
        description="Descrição da transação - 'Aonde Gastou' (obrigatório)",
        example="Netflix Com"
    )
    amount: float = Field(
        gt=0.0,
        description="Valor unitário da transação (obrigatório)",
        example=44.90
    )
    date: str = Field(
        description="Data da transação no formato ISO (obrigatório)",
        example="2024-01-01T00:00:00Z"
    )
    
    # Campos opcionais principais
    source: Optional[str] = Field(
        None, 
        description="Tipo/fonte da transação (opcional)",
        example="crédito"
    )
    card: Optional[str] = Field(
        None,
        description="Informações do cartão (opcional)",
        example="Final 0001 - USUARIO EXEMPLO"
    )
    modelVersion: Optional[str] = Field(
        None, 
        description="Versão do modelo usado na classificação (opcional)",
        example="v1.2.0"
    )
    createdAt: Optional[str] = Field(
        None, 
        description="Timestamp de criação do feedback (opcional)",
        example="2024-01-01T12:00:00Z"
    )
    
    # Campos editáveis
    category: Optional[str] = Field(
        None, 
        description="Natureza do Gasto - categoria corrigida (opcional)",
        example="Entretenimento"
    )
    flux: Optional[str] = Field(
        None, 
        description="Entrada/Saída - fluxo da transação (opcional)",
        example="Saída"
    )
    comp: Optional[str] = Field(
        None, 
        description="Comp - informação adicional (opcional)",
        example=""
    )
    parcelas: Optional[int] = Field(
        None, 
        ge=1,
        description="Número total de parcelas (opcional, default 1)",
        example=12
    )
    numero_parcela: Optional[int] = Field(
        None, 
        ge=1,
        description="Número da parcela atual (opcional)",
        example=4
    )
    
    @validator('date')
    def validate_date_format(cls, v):
        """Valida formato da data."""
        try:
            # Tentar parsear como ISO format
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            try:
                # Fallback para formato simples
                datetime.fromisoformat(v)
                return v
            except ValueError:
                raise ValueError("Data deve estar no formato ISO (YYYY-MM-DD ou YYYY-MM-DDTHH:MM:SS)")
    
    @validator('createdAt')
    def validate_created_at(cls, v):
        """Valida formato do createdAt."""
        if v is None:
            return v
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            try:
                datetime.fromisoformat(v)
                return v
            except ValueError:
                raise ValueError("createdAt deve estar no formato ISO")
    
    class Config:
        extra = "ignore"  # Ignorar campos extras em vez de rejeitar
        validate_assignment = True
        arbitrary_types_allowed = True
        validate_by_name = True
        use_enum_values = True
        validate_default = True


class FeedbackRequest(BaseModel):
    """
    Schema para requisição de feedback.
    
    Aceita tanto um item único quanto uma lista de itens.
    """
    
    feedback: Union[FeedbackItem, List[FeedbackItem]] = Field(
        description="Item único ou lista de feedbacks para salvar"
    )
    
    @validator('feedback')
    def validate_feedback(cls, v):
        """Valida se feedback é item único ou lista."""
        if isinstance(v, list):
            if not v:
                raise ValueError("Lista de feedbacks não pode estar vazia")
        return v
    
    class Config:
        extra = "ignore"  # Ignorar campos extras em vez de rejeitar
        validate_assignment = True
        arbitrary_types_allowed = True
        validate_by_name = True
        use_enum_values = True
        validate_default = True


class FeedbackResponse(BaseModel):
    """
    Schema para resposta do endpoint de feedback.
    
    Retorna informações sobre o resultado da operação de salvamento.
    """
    
    saved_rows: int = Field(
        ge=0,
        description="Número de linhas salvas no CSV",
        example=3
    )
    file_path: str = Field(
        description="Caminho do arquivo CSV onde os dados foram salvos",
        example="feedbacks/feedback_2024-01-01.csv"
    )
    columns: List[str] = Field(
        description="Lista das colunas do CSV na ordem",
        example=["Aonde Gastou", "Natureza do Gasto", "Valor Total"]
    )
    
    class Config:
        extra = "ignore"  # Ignorar campos extras em vez de rejeitar
        validate_assignment = True
        arbitrary_types_allowed = True
        validate_by_name = True
        use_enum_values = True
        validate_default = True


class FeedbackFileInfo(BaseModel):
    """
    Schema para informações sobre arquivo de feedback.
    """
    
    filename: str = Field(description="Nome do arquivo")
    file_path: str = Field(description="Caminho completo do arquivo")
    exists: bool = Field(description="Se o arquivo existe")
    columns: List[str] = Field(description="Colunas do CSV")
    size_bytes: Optional[int] = Field(None, description="Tamanho em bytes (se existe)")
    modified: Optional[str] = Field(None, description="Data de modificação (se existe)")
    has_header: Optional[bool] = Field(None, description="Se tem cabeçalho correto (se existe)")
    error: Optional[str] = Field(None, description="Erro ao ler arquivo (se houver)")
    
    class Config:
        extra = "ignore"  # Ignorar campos extras em vez de rejeitar
        validate_assignment = True
        arbitrary_types_allowed = True
        validate_by_name = True
        use_enum_values = True
        validate_default = True
