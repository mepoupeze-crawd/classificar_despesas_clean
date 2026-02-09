"""
Schemas de Dados

Define as estruturas de dados utilizadas em todo o sistema
de classificação de despesas usando Pydantic para validação.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class TransactionType(str, Enum):
    """Tipos de transação bancária."""
    CREDIT = "crédito"
    DEBIT = "débito"


class ExpenseCategory(str, Enum):
    """Categorias de despesas disponíveis."""
    UTILITIES_LIGHT = "Conta de luz"
    UTILITIES_GAS = "Conta de gás"
    INTERNET_TV = "Internet & TV a cabo"
    HOUSING = "Moradia (Financiamento/ Aluguel/ Condominio)"
    SUBSCRIPTIONS = "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)"
    PHONE_PLANS = "Planos de celular"
    HOUSEKEEPER = "Gastos com Diarista"
    EDUCATION = "Gastos com Educação (Inglês, MBA, Pós)"
    PHARMACY = "Farmácia"
    GROCERY = "Supermercado"
    WEDDING = "Casamento"
    RESTAURANTS = "Restaurantes/ Bares/ Lanchonetes"
    TRAVEL = "Viagens / Férias"
    CAR_MAINTENANCE = "Carro (Manutenção/ IPVA/ Seguro)"
    TRANSPORT = "Combustível/ Passagens/ Uber / Sem Parar"
    PERSONAL_CARE = "Cuidados Pessoais (Nutricionista / Medico / Suplemento)"
    HOUSE_EXPENSES = "Gastos com casa (outros)"
    GIFTS = "Gastos com presentes"
    PERSONAL_EXPENSES = "Gastos pessoais"
    PET_EXPENSES = "Gastos com Cachorro"
    SPORTS = "Futevolei"
    FINANCING = "Financiamento/Condominio"
    HOME_RENOVATION = "Obra casa"
    AI_EXPENSES = "Inteligência Artificial"
    INVESTMENT = "Investimento"
    SALARY = "Salário"
    INTERNAL_TRANSFER = "Transferencia Interna"


class ExpenseTransaction(BaseModel):
    """
    Schema para uma transação de despesa.
    
    Representa uma transação bancária que precisa ser classificada.
    """
    
    # Dados básicos da transação
    description: str = Field(..., description="Descrição da transação")
    amount: float = Field(..., description="Valor da transação")
    date: datetime = Field(..., description="Data da transação")
    
    # Dados do cartão/conta
    card_number: Optional[str] = Field(None, description="Número ou final do cartão")
    card_holder: Optional[str] = Field(None, description="Titular do cartão")
    origin: Optional[str] = Field(None, description="Origem da transação (fatura/extrato)")
    
    # Dados de parcelamento
    installments: Optional[int] = Field(None, description="Total de parcelas")
    installment_number: Optional[int] = Field(None, description="Número da parcela atual")
    
    # Metadados
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Dados brutos da transação")
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if not v or not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be positive')
        return v
    
    model_config = {"use_enum_values": True}


class ClassificationResult(BaseModel):
    """
    Schema para o resultado de uma classificação.
    
    Contém a categoria predita, confiança e metadados da classificação.
    """
    
    # Resultado da classificação
    category: str = Field(..., description="Categoria predita")
    confidence: float = Field(..., ge=0.0, le=1.0001, description="Nível de confiança da predição")
    
    # Metadados
    classifier_used: str = Field(..., description="Nome do classificador utilizado")
    processing_time: Optional[float] = Field(None, description="Tempo de processamento em segundos")
    fallback_used: bool = Field(False, description="Se foi usado fallback (IA)")
    
    # Dados adicionais
    raw_prediction: Optional[Dict[str, Any]] = Field(None, description="Predição bruta do modelo")
    ai_context: Optional[str] = Field(None, description="Contexto usado pela IA")
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0001:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    model_config = {"use_enum_values": True}


class ModelMetrics(BaseModel):
    """
    Schema para métricas de um modelo de ML.
    
    Contém métricas de performance do modelo.
    """
    
    # Métricas básicas
    accuracy: float = Field(..., ge=0.0, le=1.0001, description="Acurácia do modelo")
    precision: float = Field(..., ge=0.0, le=1.0001, description="Precisão média")
    recall: float = Field(..., ge=0.0, le=1.0001, description="Recall médio")
    f1_score: float = Field(..., ge=0.0, le=1.0001, description="F1-Score médio")
    
    # Dados do treinamento
    training_samples: int = Field(..., description="Número de amostras de treino")
    test_samples: int = Field(..., description="Número de amostras de teste")
    training_date: datetime = Field(..., description="Data do treinamento")
    
    # Métricas por categoria
    category_metrics: Optional[Dict[str, Dict[str, float]]] = Field(
        None, description="Métricas detalhadas por categoria"
    )


class FeedbackData(BaseModel):
    """
    Schema para dados de feedback.
    
    Representa feedback do usuário sobre uma classificação.
    """
    
    # Referência à classificação original
    original_result: ClassificationResult = Field(..., description="Resultado original")
    transaction: ExpenseTransaction = Field(..., description="Transação original")
    
    # Feedback do usuário
    correct_category: str = Field(..., description="Categoria correta fornecida pelo usuário")
    feedback_date: datetime = Field(default_factory=datetime.now, description="Data do feedback")
    
    # Metadados
    user_notes: Optional[str] = Field(None, description="Notas adicionais do usuário")
    
    @field_validator('correct_category')
    @classmethod
    def validate_correct_category(cls, v):
        if not v or not v.strip():
            raise ValueError('Correct category cannot be empty')
        return v.strip()


class ProcessingStats(BaseModel):
    """
    Schema para estatísticas de processamento.
    
    Contém estatísticas sobre o processamento de um lote de transações.
    """
    
    # Contadores
    total_transactions: int = Field(..., description="Total de transações processadas")
    successful_classifications: int = Field(..., description="Classificações bem-sucedidas")
    fallback_used_count: int = Field(..., description="Número de vezes que fallback foi usado")
    
    # Tempos
    total_processing_time: float = Field(..., description="Tempo total de processamento")
    average_processing_time: float = Field(..., description="Tempo médio por transação")
    
    # Distribuição de categorias
    category_distribution: Dict[str, int] = Field(..., description="Distribuição das categorias")
    
    # Métricas de confiança
    average_confidence: float = Field(..., ge=0.0, le=1.0001, description="Confiança média das predições")
    low_confidence_count: int = Field(..., description="Número de predições com baixa confiança")


class Prediction(BaseModel):
    """
    Schema para resultado de uma predição do pipeline de classificação.
    
    Representa o resultado final de uma classificação com todos os metadados
    necessários para análise e debugging.
    """
    
    # Resultado da predição
    label: str = Field(..., description="Categoria predita")
    confidence: float = Field(..., ge=0.0, le=1.0001, description="Confiança da predição (0-1)")
    method_used: str = Field(..., description="Método usado para a predição")
    
    # Metadados de processamento
    elapsed_ms: float = Field(..., ge=0.0, description="Tempo de processamento em milissegundos")
    transaction_id: Optional[str] = Field(None, description="ID da transação original")
    
    # Flag para indicar se faltam API keys para fallback IA
    needs_keys: Optional[bool] = Field(None, description="Indica se faltam API keys para fallback IA")
    
    # Dados brutos para debugging
    raw_prediction: Optional[Dict[str, Any]] = Field(None, description="Dados brutos da predição")
    
    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0001:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    @field_validator('label')
    @classmethod
    def validate_label(cls, v):
        if not v or not v.strip():
            raise ValueError('Label cannot be empty')
        return v.strip()
    
    model_config = {"use_enum_values": True}
