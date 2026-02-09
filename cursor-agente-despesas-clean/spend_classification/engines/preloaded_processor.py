"""
Processador de Dados Pré-carregados

Este módulo contém a lógica para processar dados pré-carregados (pre_loaded_data)
que já foram classificados por sistemas externos.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from ..core.schemas import ExpenseTransaction, Prediction

logger = logging.getLogger(__name__)


class PreloadedDataProcessor:
    """
    Processador para dados pré-carregados de classificação.
    
    Extrai e processa classificações já existentes em transações que possuem
    dados pré-carregados (pre_loaded_data) de sistemas externos.
    """
    
    @staticmethod
    def has_preloaded_data(transaction: ExpenseTransaction) -> bool:
        """
        Verifica se a transação possui dados pré-carregados.
        
        Args:
            transaction: Transação para verificar
            
        Returns:
            True se possui dados pré-carregados, False caso contrário
        """
        if not transaction.raw_data:
            return False
            
        return (
            'pre_loaded_data' in transaction.raw_data and
            transaction.raw_data['pre_loaded_data'] is not None
        )
    
    @staticmethod
    def extract_preloaded_classification(transaction: ExpenseTransaction) -> Optional[Dict[str, Any]]:
        """
        Extrai dados de classificação pré-carregados de uma transação.
        
        IMPORTANTE: A categoria (natureza do gasto) dos dados pré-carregados 
        é IGNORADA. O pipeline irá usar os engines de classificação para 
        determinar a categoria, mas outros dados como parcelas, fluxo, etc.
        podem ser utilizados.
        
        Args:
            transaction: Transação com dados pré-carregados
            
        Returns:
            None (sempre retorna None para forçar pipeline usar engines de classificação)
        """
        # SEMPRE retornar None para forçar pipeline usar engines de classificação
        # Os dados pré-carregados só contêm metadados, não a categoria final
        logger.debug("Ignorando categoria de dados pré-carregados - usando engines de classificação")
        return None
    
    @staticmethod
    def create_prediction_from_preloaded(
        transaction: ExpenseTransaction, 
        classification_data: Dict[str, Any],
        elapsed_ms: float = 0.0,
        transaction_id: Optional[str] = None
    ) -> Prediction:
        """
        Cria um objeto Prediction a partir de dados pré-carregados.
        
        Args:
            transaction: Transação original
            classification_data: Dados de classificação extraídos
            elapsed_ms: Tempo de processamento em milissegundos
            transaction_id: ID da transação (opcional)
            
        Returns:
            Objeto Prediction com os dados pré-carregados
        """
        return Prediction(
            label=classification_data['category'],
            confidence=classification_data['confidence'],
            method_used=classification_data['method_used'],
            elapsed_ms=elapsed_ms,
            transaction_id=transaction_id,
            needs_keys=False,  # Dados pré-carregados não precisam de API keys
            raw_prediction={
                'source': 'preloaded_data',
                'original_method': classification_data['method_used'],
                'source_model': classification_data['source_model'],
                'model_version': classification_data['model_version'],
                'subcategory': classification_data['subcategory'],
                'preloaded_raw_prediction': classification_data['raw_prediction']
            }
        )
    
    @staticmethod
    def process_preloaded_classification(
        transaction: ExpenseTransaction, 
        elapsed_ms: float = 0.0,
        transaction_id: Optional[str] = None
    ) -> Optional[Prediction]:
        """
        Processa classificação pré-carregada de uma transação.
        
        Args:
            transaction: Transação para processar
            elapsed_ms: Tempo de processamento em milissegundos
            transaction_id: ID da transação (opcional)
            
        Returns:
            Prediction com dados pré-carregados ou None se não disponível
        """
        if not PreloadedDataProcessor.has_preloaded_data(transaction):
            return None
        
        classification_data = PreloadedDataProcessor.extract_preloaded_classification(transaction)
        if not classification_data:
            return None
        
        return PreloadedDataProcessor.create_prediction_from_preloaded(
            transaction, classification_data, elapsed_ms, transaction_id
        )
