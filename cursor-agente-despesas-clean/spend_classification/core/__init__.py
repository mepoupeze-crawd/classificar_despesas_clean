"""
Core Module - Contratos, Schemas e Constantes

Este módulo contém os contratos base, schemas de dados e constantes
utilizadas em todo o sistema de classificação de despesas.

Componentes:
- contracts: Interfaces e contratos base
- schemas: Estruturas de dados (Pydantic models)
- constants: Constantes do sistema
"""

from .contracts import *
from .schemas import *
from .constants import *

__all__ = [
    # Contracts
    "ClassifierInterface",
    "ModelInterface",
    "PipelineInterface",
    
    # Schemas
    "ExpenseTransaction",
    "ClassificationResult",
    "ModelMetrics",
    "FeedbackData",
    
    # Constants
    "CATEGORIES",
    "CONFIDENCE_THRESHOLD",
    "MODEL_PATHS",
    "API_CONFIG"
]
