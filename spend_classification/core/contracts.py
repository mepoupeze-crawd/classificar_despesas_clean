"""
Contratos e Interfaces Base

Define as interfaces e contratos que devem ser implementados
pelos componentes do sistema de classificação de despesas.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .schemas import ExpenseTransaction, ClassificationResult


class ClassifierInterface(ABC):
    """
    Interface para classificadores de despesas.
    
    Define o contrato que todos os classificadores devem implementar,
    seja baseado em ML, regras ou IA.
    """
    
    @abstractmethod
    def classify(self, transaction: ExpenseTransaction) -> ClassificationResult:
        """
        Classifica uma transação de despesa.
        
        Args:
            transaction: Transação a ser classificada
            
        Returns:
            Resultado da classificação com categoria e confiança
        """
        pass
    
    @abstractmethod
    def batch_classify(self, transactions: List[ExpenseTransaction]) -> List[ClassificationResult]:
        """
        Classifica múltiplas transações em lote.
        
        Args:
            transactions: Lista de transações a serem classificadas
            
        Returns:
            Lista de resultados de classificação
        """
        pass
    
    @abstractmethod
    def get_confidence_threshold(self) -> float:
        """
        Retorna o threshold de confiança do classificador.
        
        Returns:
            Valor entre 0.0 e 1.0
        """
        pass


class ModelInterface(ABC):
    """
    Interface para modelos de machine learning.
    
    Define o contrato para modelos ML que podem ser carregados,
    treinados e usados para predição.
    """
    
    @abstractmethod
    def load(self, model_path: str) -> None:
        """
        Carrega um modelo salvo do disco.
        
        Args:
            model_path: Caminho para o arquivo do modelo
        """
        pass
    
    @abstractmethod
    def predict(self, data: List[str]) -> List[str]:
        """
        Realiza predições usando o modelo carregado.
        
        Args:
            data: Lista de textos para classificar
            
        Returns:
            Lista de categorias preditas
        """
        pass
    
    @abstractmethod
    def predict_proba(self, data: List[str]) -> List[List[float]]:
        """
        Realiza predições com probabilidades.
        
        Args:
            data: Lista de textos para classificar
            
        Returns:
            Lista de probabilidades para cada categoria
        """
        pass
    
    @abstractmethod
    def get_feature_names(self) -> List[str]:
        """
        Retorna os nomes das features do modelo.
        
        Returns:
            Lista de nomes das features
        """
        pass


class PipelineInterface(ABC):
    """
    Interface para pipelines de processamento.
    
    Define o contrato para pipelines que processam transações
    através de múltiplas etapas de classificação.
    """
    
    @abstractmethod
    def process(self, transactions: List[ExpenseTransaction]) -> List[ClassificationResult]:
        """
        Processa uma lista de transações através do pipeline.
        
        Args:
            transactions: Lista de transações a serem processadas
            
        Returns:
            Lista de resultados processados
        """
        pass
    
    @abstractmethod
    def add_stage(self, stage_name: str, classifier: ClassifierInterface) -> None:
        """
        Adiciona uma nova etapa ao pipeline.
        
        Args:
            stage_name: Nome da etapa
            classifier: Classificador a ser usado na etapa
        """
        pass
    
    @abstractmethod
    def get_stages(self) -> Dict[str, ClassifierInterface]:
        """
        Retorna as etapas configuradas no pipeline.
        
        Returns:
            Dicionário com nome da etapa e classificador
        """
        pass


class FeedbackInterface(ABC):
    """
    Interface para sistemas de feedback.
    
    Define o contrato para sistemas que coletam e processam
    feedback dos usuários para melhorar os modelos.
    """
    
    @abstractmethod
    def collect_feedback(self, result: ClassificationResult, correct_category: str) -> None:
        """
        Coleta feedback de uma classificação.
        
        Args:
            result: Resultado da classificação original
            correct_category: Categoria correta fornecida pelo usuário
        """
        pass
    
    @abstractmethod
    def get_feedback_data(self) -> List[Dict[str, Any]]:
        """
        Retorna os dados de feedback coletados.
        
        Returns:
            Lista de dados de feedback
        """
        pass
    
    @abstractmethod
    def clear_feedback(self) -> None:
        """
        Limpa todos os dados de feedback coletados.
        """
        pass
