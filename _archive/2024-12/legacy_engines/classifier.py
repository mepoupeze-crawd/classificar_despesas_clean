"""
Classificador Principal de Despesas

Implementa o classificador principal que combina diferentes estratégias
de classificação com fallback para IA quando necessário.
"""

from typing import List, Dict, Any, Optional
import time
import logging
from ..core.contracts import ClassifierInterface
from ..core.schemas import ExpenseTransaction, ClassificationResult
from ..core.constants import CONFIDENCE_THRESHOLD, MESSAGES


class ExpenseClassifier(ClassifierInterface):
    """
    Classificador principal de despesas.
    
    Combina múltiplas estratégias de classificação:
    1. Modelo de ML treinado
    2. Engine de regras
    3. Engine de similaridade
    4. Fallback para IA (ChatGPT + SerpApi)
    """
    
    def __init__(
        self,
        ml_model: Optional['MLClassifier'] = None,
        rules_engine: Optional['RulesEngine'] = None,
        similarity_engine: Optional['SimilarityEngine'] = None,
        ai_fallback: Optional['AIFallbackEngine'] = None,
        confidence_threshold: float = CONFIDENCE_THRESHOLD
    ):
        """
        Inicializa o classificador principal.
        
        Args:
            ml_model: Classificador baseado em ML
            rules_engine: Engine de regras
            similarity_engine: Engine de similaridade
            ai_fallback: Fallback para IA
            confidence_threshold: Threshold de confiança
        """
        self.ml_model = ml_model
        self.rules_engine = rules_engine
        self.similarity_engine = similarity_engine
        self.ai_fallback = ai_fallback
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(__name__)
    
    def classify(self, transaction: ExpenseTransaction) -> ClassificationResult:
        """
        Classifica uma transação de despesa.
        
        Args:
            transaction: Transação a ser classificada
            
        Returns:
            Resultado da classificação
        """
        start_time = time.time()
        
        try:
            # 1. Tenta classificação com modelo ML
            if self.ml_model:
                result = self._classify_with_ml(transaction)
                if result.confidence >= self.confidence_threshold:
                    return result
            
            # 2. Tenta classificação com regras
            if self.rules_engine:
                result = self._classify_with_rules(transaction)
                if result.confidence >= self.confidence_threshold:
                    return result
            
            # 3. Tenta classificação por similaridade
            if self.similarity_engine:
                result = self._classify_with_similarity(transaction)
                if result.confidence >= self.confidence_threshold:
                    return result
            
            # 4. Fallback para IA
            if self.ai_fallback:
                result = self._classify_with_ai(transaction)
                processing_time = time.time() - start_time
                result.processing_time = processing_time
                return result
            
            # 5. Resultado padrão se nada funcionar
            return ClassificationResult(
                category="Gastos pessoais",
                confidence=0.1,
                classifier_used="default",
                processing_time=time.time() - start_time,
                fallback_used=False
            )
            
        except Exception as e:
            self.logger.error(f"Erro na classificação: {e}")
            return ClassificationResult(
                category="Gastos pessoais",
                confidence=0.0,
                classifier_used="error",
                processing_time=time.time() - start_time,
                fallback_used=False
            )
    
    def batch_classify(self, transactions: List[ExpenseTransaction]) -> List[ClassificationResult]:
        """
        Classifica múltiplas transações em lote.
        
        Args:
            transactions: Lista de transações
            
        Returns:
            Lista de resultados
        """
        results = []
        total_start_time = time.time()
        
        self.logger.info(MESSAGES["processing_start"].format(count=len(transactions)))
        
        for transaction in transactions:
            result = self.classify(transaction)
            results.append(result)
        
        total_time = time.time() - total_start_time
        self.logger.info(f"Processamento concluído em {total_time:.2f}s")
        
        return results
    
    def get_confidence_threshold(self) -> float:
        """Retorna o threshold de confiança."""
        return self.confidence_threshold
    
    def _classify_with_ml(self, transaction: ExpenseTransaction) -> ClassificationResult:
        """Classifica usando modelo de ML."""
        if not self.ml_model:
            raise ValueError("ML model not available")
        
        result = self.ml_model.classify(transaction)
        result.classifier_used = "ml_model"
        return result
    
    def _classify_with_rules(self, transaction: ExpenseTransaction) -> ClassificationResult:
        """Classifica usando engine de regras."""
        if not self.rules_engine:
            raise ValueError("Rules engine not available")
        
        result = self.rules_engine.classify(transaction)
        result.classifier_used = "rules_engine"
        return result
    
    def _classify_with_similarity(self, transaction: ExpenseTransaction) -> ClassificationResult:
        """Classifica usando engine de similaridade."""
        if not self.similarity_engine:
            raise ValueError("Similarity engine not available")
        
        result = self.similarity_engine.classify(transaction)
        result.classifier_used = "similarity_engine"
        return result
    
    def _classify_with_ai(self, transaction: ExpenseTransaction) -> ClassificationResult:
        """Classifica usando fallback de IA."""
        if not self.ai_fallback:
            raise ValueError("AI fallback not available")
        
        self.logger.info(MESSAGES["fallback_triggered"].format(
            description=transaction.description[:50]
        ))
        
        result = self.ai_fallback.classify(transaction)
        result.classifier_used = "ai_fallback"
        result.fallback_used = True
        return result
    
    def add_classifier(self, classifier_type: str, classifier: ClassifierInterface) -> None:
        """
        Adiciona um novo classificador ao sistema.
        
        Args:
            classifier_type: Tipo do classificador
            classifier: Instância do classificador
        """
        if classifier_type == "ml_model":
            self.ml_model = classifier
        elif classifier_type == "rules_engine":
            self.rules_engine = classifier
        elif classifier_type == "similarity_engine":
            self.similarity_engine = classifier
        elif classifier_type == "ai_fallback":
            self.ai_fallback = classifier
        else:
            raise ValueError(f"Unknown classifier type: {classifier_type}")
    
    def get_classifier_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas dos classificadores disponíveis.
        
        Returns:
            Dicionário com estatísticas
        """
        stats = {
            "ml_model_available": self.ml_model is not None,
            "rules_engine_available": self.rules_engine is not None,
            "similarity_engine_available": self.similarity_engine is not None,
            "ai_fallback_available": self.ai_fallback is not None,
            "confidence_threshold": self.confidence_threshold
        }
        
        return stats
