"""
Spend Classification Module

Este módulo é responsável por classificar a Natureza do Gasto de transações bancárias,
utilizando uma combinação de modelos de machine learning e inteligência artificial.

Principais funcionalidades:
- Classificação automática de despesas usando modelos ML treinados
- Fallback para IA (ChatGPT + SerpApi) quando confiança é baixa
- Sistema de feedback para melhoria contínua
- Pipeline de processamento completo

Estrutura:
- core/: Contratos, schemas e constantes
- engines/: Regras, similaridade, modelo e pipeline
- tests/: Testes unitários
"""

__version__ = "1.0.0"
__author__ = "Agente Despesas"

# Imports principais do módulo
from .core.contracts import *
from .core.schemas import *
from .core.constants import *
from .engines.pipeline import *

__all__ = [
    "ClassificationPipeline", 
    "ExpenseTransaction",
    "ClassificationResult",
    "CATEGORIES",
    "CONFIDENCE_THRESHOLD"
]
