"""
Modelo de Machine Learning

Implementa o modelo de ML baseado em scikit-learn para classificação
de despesas usando TF-IDF e Random Forest.
"""

from typing import List, Dict, Any, Optional
import joblib
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import logging
from ..core.contracts import ClassifierInterface, ModelInterface
from ..core.schemas import ExpenseTransaction, ClassificationResult
from ..core.constants import MODEL_PATHS, MESSAGES


class MLModel(ModelInterface):
    """
    Modelo de ML para classificação de despesas.
    
    Implementa um pipeline scikit-learn com TF-IDF e Random Forest
    para classificar descrições de transações.
    """
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Inicializa o modelo ML.
        
        Args:
            model_path: Caminho para o arquivo do modelo
        """
        self.model_path = model_path
        self.pipeline: Optional[Pipeline] = None
        self.classes_: Optional[List[str]] = None
        self.feature_names_: Optional[List[str]] = None
        self.logger = logging.getLogger(__name__)
        
        if model_path:
            self.load(model_path)
    
    def load(self, model_path: str) -> None:
        """
        Carrega um modelo salvo do disco.
        
        Args:
            model_path: Caminho para o arquivo do modelo
        """
        try:
            self.pipeline = joblib.load(model_path)
            self.classes_ = self.pipeline.classes_
            self.feature_names_ = self._get_feature_names()
            self.model_path = model_path
            
            self.logger.info(MESSAGES["model_loaded"].format(model_name=model_path))
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar modelo {model_path}: {e}")
            raise
    
    def predict(self, data: List[str]) -> List[str]:
        """
        Realiza predições usando o modelo carregado.
        
        Args:
            data: Lista de textos para classificar
            
        Returns:
            Lista de categorias preditas
        """
        if not self.pipeline:
            raise ValueError("Model not loaded")
        
        return self.pipeline.predict(data).tolist()
    
    def predict_proba(self, data: List[str]) -> List[List[float]]:
        """
        Realiza predições com probabilidades.
        
        Args:
            data: Lista de textos para classificar
            
        Returns:
            Lista de probabilidades para cada categoria
        """
        if not self.pipeline:
            raise ValueError("Model not loaded")
        
        probabilities = self.pipeline.predict_proba(data)
        return probabilities.tolist()
    
    def get_feature_names(self) -> List[str]:
        """
        Retorna os nomes das features do modelo.
        
        Returns:
            Lista de nomes das features
        """
        return self.feature_names_ or []
    
    def _get_feature_names(self) -> List[str]:
        """Extrai nomes das features do pipeline TF-IDF."""
        if not self.pipeline:
            return []
        
        try:
            # Extrai o vectorizer TF-IDF do pipeline
            tfidf_step = self.pipeline.named_steps.get('tfidf')
            if tfidf_step:
                return tfidf_step.get_feature_names_out().tolist()
        except Exception as e:
            self.logger.warning(f"Não foi possível extrair nomes das features: {e}")
        
        return []
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o modelo carregado.
        
        Returns:
            Dicionário com informações do modelo
        """
        if not self.pipeline:
            return {"loaded": False}
        
        info = {
            "loaded": True,
            "model_path": self.model_path,
            "classes": self.classes_,
            "n_classes": len(self.classes_) if self.classes_ else 0,
            "n_features": len(self.feature_names_) if self.feature_names_ else 0,
            "pipeline_steps": list(self.pipeline.named_steps.keys())
        }
        
        return info


class MLClassifier(ClassifierInterface):
    """
    Classificador baseado em modelo de ML.
    
    Usa o MLModel para classificar transações de despesas.
    """
    
    def __init__(self, model_type: str = "natureza_do_gasto"):
        """
        Inicializa o classificador ML.
        
        Args:
            model_type: Tipo do modelo a ser carregado
        """
        self.model_type = model_type
        self.model: Optional[MLModel] = None
        self.logger = logging.getLogger(__name__)
        
        # Carrega o modelo apropriado
        model_path = MODEL_PATHS.get(model_type)
        if model_path:
            self.model = MLModel(model_path)
    
    def classify(self, transaction: ExpenseTransaction) -> ClassificationResult:
        """
        Classifica uma transação usando o modelo ML.
        
        Args:
            transaction: Transação a ser classificada
            
        Returns:
            Resultado da classificação
        """
        if not self.model or not self.model.pipeline:
            return ClassificationResult(
                category="Gastos pessoais",
                confidence=0.0,
                classifier_used="ml_model",
                fallback_used=False
            )
        
        try:
            # Prepara o texto para classificação
            text = self._prepare_text(transaction)
            
            # Realiza predição
            predictions = self.model.predict([text])
            probabilities = self.model.predict_proba([text])
            
            # Extrai resultado
            predicted_class = predictions[0]
            max_probability = float(np.max(probabilities[0]))
            
            result = ClassificationResult(
                category=predicted_class,
                confidence=max_probability,
                classifier_used="ml_model",
                fallback_used=False,
                raw_prediction={
                    "all_probabilities": probabilities[0].tolist(),
                    "classes": self.model.classes_.tolist()
                }
            )
            
            self.logger.debug(MESSAGES["classification_complete"].format(
                category=predicted_class,
                confidence=max_probability
            ))
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na classificação ML: {e}")
            return ClassificationResult(
                category="Gastos pessoais",
                confidence=0.0,
                classifier_used="ml_model",
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
        if not self.model or not self.model.pipeline:
            return [
                ClassificationResult(
                    category="Gastos pessoais",
                    confidence=0.0,
                    classifier_used="ml_model",
                    fallback_used=False
                )
                for _ in transactions
            ]
        
        try:
            # Prepara textos
            texts = [self._prepare_text(t) for t in transactions]
            
            # Predições em lote
            predictions = self.model.predict(texts)
            probabilities = self.model.predict_proba(texts)
            
            # Monta resultados
            results = []
            for i, (pred, probs) in enumerate(zip(predictions, probabilities)):
                max_prob = float(np.max(probs))
                
                result = ClassificationResult(
                    category=pred,
                    confidence=max_prob,
                    classifier_used="ml_model",
                    fallback_used=False,
                    raw_prediction={
                        "all_probabilities": probs.tolist(),
                        "classes": self.model.classes_.tolist()
                    }
                )
                results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Erro na classificação em lote: {e}")
            # Retorna resultados de erro
            return [
                ClassificationResult(
                    category="Gastos pessoais",
                    confidence=0.0,
                    classifier_used="ml_model",
                    fallback_used=False
                )
                for _ in transactions
            ]
    
    def get_confidence_threshold(self) -> float:
        """Retorna o threshold de confiança padrão."""
        return 0.7
    
    def _prepare_text(self, transaction: ExpenseTransaction) -> str:
        """
        Prepara o texto da transação para classificação.
        
        Args:
            transaction: Transação a ser processada
            
        Returns:
            Texto limpo e preparado
        """
        text = transaction.description
        
        # Adiciona informações do cartão se disponível
        if transaction.card_number:
            text += f" [cartao: {transaction.card_number}]"
        
        # Limpeza básica do texto
        text = text.lower().strip()
        
        return text
    
    def get_model_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do modelo.
        
        Returns:
            Dicionário com estatísticas
        """
        if not self.model:
            return {"model_loaded": False}
        
        stats = self.model.get_model_info()
        stats["model_type"] = self.model_type
        
        return stats
