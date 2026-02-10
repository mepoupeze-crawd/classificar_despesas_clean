"""
Engines Module - Regras, Similaridade, Modelo e Pipeline

Este módulo contém os engines de classificação que implementam
diferentes estratégias para classificar despesas.

Componentes:
- preloaded_processor: Processador de dados pré-carregados
- classifier: Classificador principal com fallback para IA
- ml_model: Modelo de machine learning baseado em scikit-learn
- rules_engine: Engine de regras baseadas em padrões
- similarity_engine: Engine de similaridade para matching
- pipeline: Pipeline de processamento completo
- ai_fallback: Fallback para IA (ChatGPT + SerpApi)
"""

from .rules_engine import *
from .similarity import *
from .pipeline import *
from .rules import *
from .model_adapter import *
from .ai_fallback import *
from .preloaded_processor import *

__all__ = [
    # Engines
    "RulesEngine",
    
    # Model Adapter
    "ModelAdapter",
    "create_model_adapter",
    
    # Similarity Module
    "SimilarityClassifier",
    "create_similarity_classifier",
    
    # AI Fallback
    "AIFallbackEngine",
    "create_ai_fallback_engine",
    
    # Preloaded Data Processor
    "PreloadedDataProcessor",
    
    # Pipeline
    "ClassificationPipeline",
    "create_classification_pipeline",
    
    # Pure Rules Functions
    "infer_tipo_from_card",
    "infer_comp_from_card",
    "parse_parcelas_from_desc",
    "infer_titular_from_card",
    "infer_final_cartao_from_card",
    "apply_comp_rules_by_titular",
    "clean_transaction_description",
    "extract_establishment_name",
    "validate_parcelas_consistency",
    "get_rule_confidence"
]
