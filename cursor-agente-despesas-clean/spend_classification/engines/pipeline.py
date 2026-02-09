"""
Pipeline de Classificação

Orquestra diferentes engines de classificação seguindo a lógica:
0. Verificar dados pré-carregados (prioridade máxima)
1. Aplicar regras determinísticas
2. Consultar similarity; se score ≥ 0.70, aceitar
3. Senão, consultar model_adapter; se conf ≥ 0.70, aceitar
4. Se nada bater, label="duvida" e confidence baixa (0.3)
"""

import time
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from ..core.schemas import ExpenseTransaction, Prediction
from .rules_engine import RulesEngine
from .similarity import SimilarityClassifier
from .model_adapter import ModelAdapter
from .ai_fallback import AIFallbackEngine
from .preloaded_processor import PreloadedDataProcessor

# Carregar variáveis de ambiente
# override=False para não sobrescrever variáveis já definidas (ex: Docker)
load_dotenv(override=False)

logger = logging.getLogger(__name__)


class ClassificationPipeline:
    """
    Pipeline de classificação que orquestra diferentes engines.
    
    Segue a lógica:
    0. Dados Pré-carregados (prioridade máxima)
    1. Rules Engine (determinístico)
    2. Similarity Engine (se score ≥ 0.70)
    3. Model Adapter (se conf ≥ 0.70)
    4. Fallback para "duvida" (confidence 0.3)
    """
    
    def __init__(
        self,
        similarity_threshold: float = None,
        model_adapter_threshold: float = None,
        similarity_model_path: str = None,
        model_adapter_path: str = None
    ):
        """
        Inicializa o pipeline de classificação.
        
        Args:
            similarity_threshold: Threshold para aceitar resultado do similarity engine (se None, lê do .env com fallback 0.7)
            model_adapter_threshold: Threshold para aceitar resultado do model adapter (se None, lê do .env com fallback 0.7)
            similarity_model_path: Caminho para o arquivo CSV do similarity engine
            model_adapter_path: Caminho para os modelos do model adapter
        """
        # Se não foi passado, ler do .env com fallback para 0.9
        self.similarity_threshold = similarity_threshold if similarity_threshold is not None else float(os.getenv('SIMILARITY_THRESHOLD', '0.9'))
        self.model_adapter_threshold = model_adapter_threshold if model_adapter_threshold is not None else float(os.getenv('MODEL_THRESHOLD', '0.7'))
        
        # Usar MODEL_DIR se model_adapter_path não for fornecido
        if model_adapter_path is None:
            model_adapter_path = os.getenv('MODEL_DIR', './modelos')
        
        # Feature flags
        self.enable_deterministic_rules = os.getenv('ENABLE_DETERMINISTIC_RULES', 'false').lower() == 'true'
        self.enable_tfidf_similarity = os.getenv('ENABLE_TFIDF_SIMILARITY', 'false').lower() == 'true'
        self.enable_fallback_ai = os.getenv('ENABLE_FALLBACK_AI', 'true').lower() == 'true'
        
        # Inicializar engines
        self.rules_engine = RulesEngine() if self.enable_deterministic_rules else None
        self.similarity_engine = SimilarityClassifier(similarity_model_path, similarity_threshold) if self.enable_tfidf_similarity else None
        self.model_adapter = ModelAdapter(model_adapter_path)
        self.ai_fallback = AIFallbackEngine() if self.enable_fallback_ai else None
        
        logger.info(f"Pipeline inicializado com thresholds: similarity={similarity_threshold}, model_adapter={model_adapter_threshold}")
        logger.info(f"Feature flags: deterministic_rules={self.enable_deterministic_rules}, tfidf_similarity={self.enable_tfidf_similarity}, fallback_ai={self.enable_fallback_ai}")
    
    def predict_batch(self, transactions: List[ExpenseTransaction]) -> Tuple[List[Prediction], float]:
        """
        Processa um lote de transações e retorna predições com tempo total.
        
        Args:
            transactions: Lista de transações para classificar
            
        Returns:
            Tupla com (lista de predições, tempo total em ms)
        """
        if not transactions:
            return [], 0.0
        
        start_time = time.time()
        predictions = []
        
        logger.info(f"Iniciando processamento de {len(transactions)} transações")
        
        for i, transaction in enumerate(transactions):
            try:
                # Tentar extrair ID real da transação dos metadados
                transaction_id = str(i)  # fallback para índice
                if hasattr(transaction, 'raw_data') and transaction.raw_data:
                    # Tentar extrair ID dos metadados
                    if 'pre_loaded_data' in transaction.raw_data:
                        preloaded_id = transaction.raw_data['pre_loaded_data'].get('transactionId')
                        if preloaded_id:
                            transaction_id = preloaded_id
                    # Tentar extrair ID de outros campos dos metadados
                    elif 'id' in transaction.raw_data:
                        transaction_id = transaction.raw_data['id']
                
                prediction = self._predict_single(transaction, transaction_id=transaction_id)
                predictions.append(prediction)
            except Exception as e:
                logger.error(f"Erro ao processar transação {i}: {e}")
                # Criar predição de erro
                needs_keys = self.enable_fallback_ai and self.ai_fallback and not self.ai_fallback.has_valid_keys
                error_prediction = Prediction(
                    label="duvida",
                    confidence=0.3,
                    method_used="error",
                    elapsed_ms=0.0,
                    transaction_id=str(i),
                    needs_keys=needs_keys,
                    raw_prediction={"error": str(e), "needs_keys": needs_keys}
                )
                predictions.append(error_prediction)
        
        elapsed_ms = (time.time() - start_time) * 1000
        
        logger.info(f"Processamento concluído: {len(predictions)} predições em {elapsed_ms:.2f}ms")
        
        return predictions, elapsed_ms
    
    def _predict_single(self, transaction: ExpenseTransaction, transaction_id: Optional[str] = None) -> Prediction:
        """
        Processa uma única transação seguindo a lógica do pipeline.
        
        Args:
            transaction: Transação para classificar
            transaction_id: ID da transação (opcional)
            
        Returns:
            Predição com resultado e metadados
        """
        start_time = time.time()
        
        try:
            # 0. Verificar se há dados pré-carregados (prioridade máxima)
            preloaded_result = self._try_preloaded_data(transaction, transaction_id)
            if preloaded_result:
                elapsed_ms = (time.time() - start_time) * 1000
                return Prediction(
                    label=preloaded_result.label,
                    confidence=preloaded_result.confidence,
                    method_used=preloaded_result.method_used,
                    elapsed_ms=elapsed_ms,
                    transaction_id=transaction_id,
                    needs_keys=preloaded_result.needs_keys,
                    raw_prediction=preloaded_result.raw_prediction
                )
            
            # 1. Aplicar regras determinísticas
            rules_result = self._try_rules_engine(transaction)
            if rules_result:
                elapsed_ms = (time.time() - start_time) * 1000
                # Garantir que confiança está no range válido
                confidence = min(max(rules_result["confidence"], 0.0), 1.0)
                return Prediction(
                    label=rules_result["category"],
                    confidence=confidence,
                    method_used="rules_engine",
                    elapsed_ms=elapsed_ms,
                    transaction_id=transaction_id,
                    raw_prediction=rules_result
                )
            
            # 2. Consultar similarity engine
            similarity_result = self._try_similarity_engine(transaction)
            if similarity_result and similarity_result["score"] >= self.similarity_threshold:
                elapsed_ms = (time.time() - start_time) * 1000
                # Garantir que confiança está no range válido
                confidence = min(max(similarity_result["score"], 0.0), 1.0)
                return Prediction(
                    label=similarity_result["label"],
                    confidence=confidence,
                    method_used="similarity_engine",
                    elapsed_ms=elapsed_ms,
                    transaction_id=transaction_id,
                    raw_prediction=similarity_result
                )
            
            # 3. Consultar model adapter
            model_result = self._try_model_adapter(transaction)
            if model_result:
                if model_result["confidence"] >= self.model_adapter_threshold:
                    # Confiança alta: aceita resultado do Model Adapter
                    elapsed_ms = (time.time() - start_time) * 1000
                    confidence = min(max(model_result["confidence"], 0.0), 1.0)
                    return Prediction(
                        label=model_result["label"],
                        confidence=confidence,
                        method_used="model_adapter",
                        elapsed_ms=elapsed_ms,
                        transaction_id=transaction_id,
                        raw_prediction=model_result
                    )
                else:
                    # Confiança baixa: log para debug e continua para próximo método (AI Fallback)
                    logger.debug(f"Model Adapter retornou confiança baixa ({model_result['confidence']:.3f} < {self.model_adapter_threshold}), tentando próximo método")
                    # model_result será incluído no raw_prediction do fallback final
            
            # 4. Tentar AI Fallback se habilitado
            if self.enable_fallback_ai and self.ai_fallback:
                logger.debug(f"Chamando AI Fallback para transação {transaction_id or 'N/A'}")
                ai_result = self._try_ai_fallback(transaction)
                if ai_result:
                    elapsed_ms = (time.time() - start_time) * 1000
                    # Garantir que confiança está no range válido
                    confidence = min(max(ai_result["confidence"], 0.0), 1.0)
                    logger.info(f"AI Fallback classificou como {ai_result['label']} com confiança {confidence:.3f}")
                    return Prediction(
                        label=ai_result["label"],
                        confidence=confidence,
                        method_used=ai_result["method_used"],
                        elapsed_ms=elapsed_ms,
                        transaction_id=transaction_id,
                        raw_prediction=ai_result
                    )
            else:
                logger.debug(f"AI Fallback não disponível: enabled={self.enable_fallback_ai}, ai_fallback={self.ai_fallback is not None}")
            
            # 5. Fallback para "duvida"
            elapsed_ms = (time.time() - start_time) * 1000
            needs_keys = self.enable_fallback_ai and self.ai_fallback and not self.ai_fallback.has_valid_keys
            return Prediction(
                label="duvida",
                confidence=0.3,
                method_used="fallback",
                elapsed_ms=elapsed_ms,
                transaction_id=transaction_id,
                needs_keys=needs_keys,
                raw_prediction={
                    "reason": "no_method_met_threshold",
                    "needs_keys": needs_keys,
                    "rules_result": rules_result,
                    "similarity_result": similarity_result,
                    "model_result": model_result
                }
            )
            
        except Exception as e:
            # Se houver qualquer erro durante o processamento, retornar fallback com erro
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Erro durante classificação: {e}")
            needs_keys = self.enable_fallback_ai and self.ai_fallback and not self.ai_fallback.has_valid_keys
            return Prediction(
                label="duvida",
                confidence=0.3,
                method_used="error",
                elapsed_ms=elapsed_ms,
                transaction_id=transaction_id,
                needs_keys=needs_keys,
                raw_prediction={
                    "error": str(e),
                    "needs_keys": needs_keys
                }
            )
    
    def _try_preloaded_data(self, transaction: ExpenseTransaction, transaction_id: Optional[str] = None) -> Optional[Prediction]:
        """
        Tenta usar dados pré-carregados para classificação.
        
        Args:
            transaction: Transação para classificar
            transaction_id: ID da transação (opcional)
            
        Returns:
            Prediction com dados pré-carregados ou None se não disponível
        """
        try:
            result = PreloadedDataProcessor.process_preloaded_classification(transaction, transaction_id=transaction_id)
            if result:
                logger.debug(f"Usando dados pré-carregados para transação {transaction_id or 'N/A'}: "
                           f"{result.label} (confiança: {result.confidence})")
            return result
        except Exception as e:
            logger.warning(f"Erro ao processar dados pré-carregados da transação {transaction_id or 'N/A'}: {e}")
            return None
    
    def _try_rules_engine(self, transaction: ExpenseTransaction) -> Optional[Dict[str, Any]]:
        """
        Tenta classificar usando o rules engine.
        
        Args:
            transaction: Transação para classificar
            
        Returns:
            Resultado do rules engine ou None se não aplicável
        """
        # Verificar se regras determinísticas estão habilitadas
        if not self.enable_deterministic_rules or self.rules_engine is None:
            logger.debug("Rules engine desabilitado por feature flag")
            return None
            
        try:
            result = self.rules_engine.classify(transaction)
            
            # Se o rules engine retornou uma categoria não vazia com confiança > 0
            if result.category and result.category.strip() and result.confidence > 0:
                return {
                    "category": result.category,
                    "confidence": result.confidence,
                    "classifier_used": result.classifier_used,
                    "raw_prediction": result.raw_prediction
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Erro no rules engine: {e}")
            return None
    
    def _try_similarity_engine(self, transaction: ExpenseTransaction) -> Optional[Dict[str, Any]]:
        """
        Tenta classificar usando o similarity engine.
        
        Args:
            transaction: Transação para classificar
            
        Returns:
            Resultado do similarity engine ou None se não aplicável
        """
        # Verificar se TF-IDF similarity está habilitado
        if not self.enable_tfidf_similarity or self.similarity_engine is None:
            logger.debug("Similarity engine desabilitado por feature flag")
            return None
            
        try:
            if not self.similarity_engine.is_loaded:
                logger.debug("Similarity engine não está carregado")
                return None
            
            result = self.similarity_engine.query(transaction.description)
            
            if result:
                label, score = result
                return {
                    "label": label,
                    "score": score,
                    "description": transaction.description
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Erro no similarity engine: {e}")
            return None
    
    def _try_model_adapter(self, transaction: ExpenseTransaction) -> Optional[Dict[str, Any]]:
        """
        Tenta classificar usando o model adapter.
        
        Args:
            transaction: Transação para classificar
            
        Returns:
            Resultado do model adapter ou None se não aplicável
        """
        try:
            if not self.model_adapter.is_loaded:
                logger.debug("Model adapter não está carregado")
                return None
            
            label, confidence = self.model_adapter.predict_single(transaction.description)
            
            return {
                "label": label,
                "confidence": confidence,
                "description": transaction.description
            }
            
        except Exception as e:
            logger.warning(f"Erro no model adapter: {e}")
            return None
    
    def _try_ai_fallback(self, transaction: ExpenseTransaction) -> Optional[Dict[str, Any]]:
        """
        Tenta classificar usando AI fallback.
        
        Args:
            transaction: Transação para classificar
            
        Returns:
            Resultado do AI fallback ou None se não aplicável
        """
        if not self.enable_fallback_ai or self.ai_fallback is None:
            logger.debug("AI Fallback desabilitado por feature flag")
            return None
            
        try:
            result = self.ai_fallback.classify(transaction)
            return result
            
        except Exception as e:
            logger.warning(f"Erro no AI fallback: {e}")
            return None
    
    def get_engine_status(self) -> Dict[str, Any]:
        """
        Retorna o status de todos os engines.
        
        Returns:
            Dicionário com status de cada engine
        """
        return {
            "rules_engine": {
                "status": "enabled" if self.enable_deterministic_rules else "disabled",
                "rules_count": len(self.rules_engine.get_rules()) if self.rules_engine else 0
            },
            "similarity_engine": {
                "status": "enabled" if self.enable_tfidf_similarity else "disabled",
                "loaded": self.similarity_engine.is_loaded if self.similarity_engine else False,
                "threshold": self.similarity_threshold,
                "stats": self.similarity_engine.get_stats() if self.similarity_engine and self.similarity_engine.is_loaded else None
            },
            "model_adapter": {
                "status": "loaded" if self.model_adapter.is_loaded else "not_loaded",
                "threshold": self.model_adapter_threshold,
                "info": self.model_adapter.get_model_info()
            },
            "ai_fallback": {
                "status": "enabled" if self.enable_fallback_ai else "disabled",
                "has_valid_keys": self.ai_fallback.has_valid_keys if self.ai_fallback else False,
                "status_info": self.ai_fallback.get_status() if self.ai_fallback else None
            }
        }
    
    def update_thresholds(
        self,
        similarity_threshold: Optional[float] = None,
        model_adapter_threshold: Optional[float] = None
    ) -> None:
        """
        Atualiza os thresholds dos engines.
        
        Args:
            similarity_threshold: Novo threshold para similarity engine
            model_adapter_threshold: Novo threshold para model adapter
        """
        if similarity_threshold is not None:
            self.similarity_threshold = similarity_threshold
            if self.similarity_engine is not None:
                self.similarity_engine.threshold = similarity_threshold
            logger.info(f"Threshold do similarity engine atualizado para {similarity_threshold}")
        
        if model_adapter_threshold is not None:
            self.model_adapter_threshold = model_adapter_threshold
            logger.info(f"Threshold do model adapter atualizado para {model_adapter_threshold}")


def create_classification_pipeline(
    similarity_threshold: float = None,
    model_adapter_threshold: float = None,
    similarity_model_path: str = None,
    model_adapter_path: str = None
) -> ClassificationPipeline:
    """
    Função de fábrica para criar uma instância de ClassificationPipeline.
    
    Args:
        similarity_threshold: Threshold para similarity engine (se None, lê do .env com fallback 0.9)
        model_adapter_threshold: Threshold para model adapter (se None, lê do .env com fallback 0.7)
        similarity_model_path: Caminho para o arquivo CSV do similarity
        model_adapter_path: Caminho para os modelos do model adapter
        
    Returns:
        Instância de ClassificationPipeline configurada
    """
    return ClassificationPipeline(
        similarity_threshold=similarity_threshold,
        model_adapter_threshold=model_adapter_threshold,
        similarity_model_path=similarity_model_path,
        model_adapter_path=model_adapter_path
    )