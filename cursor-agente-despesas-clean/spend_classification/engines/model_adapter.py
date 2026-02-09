"""
Model Adapter

Adaptador para carregar e usar modelos de Machine Learning salvos em pickle.
Suporta tanto pipeline completo (modelo_natureza_do_gasto.pkl) quanto componentes separados (vectorizer.pkl + classifier.pkl).
"""

import os
import logging
import unicodedata
from typing import List, Tuple, Optional, Dict, Any
from joblib import load
import numpy as np
from dotenv import load_dotenv
from spend_classification.core.text_normalization import normalize_description

# Função de limpeza centralizada usando a normalização compartilhada
def limpar_texto(texto: Any) -> str:
    """Normaliza texto para predição de forma consistente com o treinamento.

    A função utiliza ``normalize_description`` (compartilhada por treinamento e
    similarity) e remove acentuação para reduzir sparsidade nos vetores.

    Args:
        texto: Texto bruto da transação.

    Returns:
        Texto normalizado e sem acentos.
    """

    normalized = normalize_description(texto)

    # Remover acentos para reduzir variação indesejada em tokens
    normalized = unicodedata.normalize("NFD", normalized)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")

    return normalized.strip()

# Carregar variáveis de ambiente
load_dotenv()

logger = logging.getLogger(__name__)


class ModelAdapter:
    """
    Adaptador para modelos de ML salvos em pickle.
    
    Suporta dois modos:
    1. Pipeline completo (modelo_natureza_do_gasto.pkl) - padrão
    2. Componentes separados (vectorizer.pkl + classifier.pkl) - fallback
    """
    
    def __init__(
        self,
        models_dir: str = None,
        decision_threshold: Optional[float] = None,
        top_k: int = 3,
    ):
        """
        Inicializa o adaptador de modelos.
        
        Args:
            models_dir: Diretório onde estão salvos os modelos (usa MODEL_DIR se None)
        """
        # Usar MODEL_DIR se models_dir não for fornecido
        if models_dir is None:
            models_dir = os.getenv('MODEL_DIR', './modelos')
        
        self.models_dir = models_dir
        self.pipeline = None
        self.vectorizer = None
        self.classifier = None
        self.is_loaded = False
        self.model_info = {}
        self.classes_: List[str] = []
        self.training_distribution: Dict[str, int] = {}
        self.training_class_weights: Optional[Dict[str, float]] = None
        self.top_k = max(1, int(top_k)) if top_k else 0

        # Threshold de decisão local do adapter (mantém padrão 0.9)
        if decision_threshold is None:
            decision_threshold = float(os.getenv('MODEL_THRESHOLD', '0.9'))
        self.decision_threshold = decision_threshold
        env_use_pipeline = os.getenv('USE_PIPELINE_MODEL', 'false').lower() == 'true'
        # Só habilita pipeline automático quando usando diretório padrão para evitar carregar
        # modelos incompatíveis em diretórios de teste ou customizados.
        self.use_pipeline_model = env_use_pipeline and models_dir is None
        
        self._load_models()

    @staticmethod
    def _get_final_estimator(model: Any) -> Any:
        """Retorna o estimador final em um pipeline sklearn, se existir."""

        if hasattr(model, "steps") and model.steps:
            return model.steps[-1][1]
        return model

    @staticmethod
    def _softmax(scores: np.ndarray) -> np.ndarray:
        shifted = scores - np.max(scores, axis=1, keepdims=True)
        exp_scores = np.exp(shifted)
        return exp_scores / np.maximum(exp_scores.sum(axis=1, keepdims=True), 1e-12)

    def _populate_class_metadata(self, model: Any) -> None:
        """Preenche classes, distribuição e pesos do treinamento quando disponíveis."""

        estimator = self._get_final_estimator(model)
        classes = getattr(estimator, "classes_", None)

        if classes is not None:
            self.classes_ = list(classes)
            self.model_info["classes"] = self.classes_

        class_counts = getattr(estimator, "class_count_", None)
        if class_counts is not None and classes is not None:
            self.training_distribution = {
                str(cls): int(count) for cls, count in zip(classes, class_counts)
            }
            self.model_info["training_class_distribution"] = self.training_distribution

        class_weights = getattr(estimator, "class_weight_", None)
        if class_weights is not None and classes is not None:
            try:
                self.training_class_weights = {
                    str(cls): float(weight) for cls, weight in zip(classes, class_weights)
                }
                self.model_info["training_class_weights"] = self.training_class_weights
            except TypeError:
                # class_weight_ pode ser um dicionário ou None
                pass

    def _get_probabilities(self, model: Any, features: Any) -> Optional[np.ndarray]:
        """Retorna probabilidades calibradas quando disponíveis."""

        estimator = self._get_final_estimator(model)

        if hasattr(estimator, 'predict_proba'):
            try:
                return estimator.predict_proba(features)
            except Exception:
                return None

        if hasattr(estimator, 'decision_function'):
            try:
                decision_scores = estimator.decision_function(features)
            except Exception:
                decision_scores = None

            if decision_scores is None:
                return None

            scores = np.array(decision_scores)
            classes = getattr(estimator, 'classes_', None)

            # Binary case: converter para probabilidades via sigmoid
            if scores.ndim == 1:
                prob_pos = 1 / (1 + np.exp(-scores))
                if classes is not None and len(classes) == 2:
                    return np.vstack([1 - prob_pos, prob_pos]).T
                # fallback sem classes conhecidas
                return np.vstack([prob_pos, 1 - prob_pos]).T

            # Multiclasse: aplicar softmax
            return self._softmax(scores)

        return None
    
    def _load_models(self) -> None:
        """
        Carrega os modelos baseado na configuração USE_PIPELINE_MODEL.
        
        Modo pipeline (padrão): carrega modelo_natureza_do_gasto.pkl
        Modo componentes: carrega vectorizer.pkl e classifier.pkl
        """
        pipeline_path = os.path.join(self.models_dir, "modelo_natureza_do_gasto.pkl")
        vectorizer_path = os.path.join(self.models_dir, "vectorizer.pkl")
        classifier_path = os.path.join(self.models_dir, "classifier.pkl")

        # Resetar metadados de treinamento a cada carregamento
        self.training_distribution = {}
        self.training_class_weights = None

        pipeline_exists = os.path.exists(pipeline_path)
        components_exist = os.path.exists(vectorizer_path) and os.path.exists(classifier_path)

        missing_components = not os.path.exists(vectorizer_path) or not os.path.exists(classifier_path)

        if missing_components:
            self.is_loaded = False
            self.vectorizer = None
            self.classifier = None
            self.pipeline = None

            if self.use_pipeline_model and pipeline_exists:
                self._load_pipeline_model(pipeline_path)
                return

            self._handle_loading_error(
                "Arquivos de modelo ausentes: forneça pipeline completo ou vectorizer/classifier separados"
            )
            return

        # Preferir componentes quando ambos estão presentes, mesmo que USE_PIPELINE_MODEL esteja habilitado,
        # para reduzir risco de pipeline desatualizado/incompleto.
        self.use_pipeline_model = False
        self._load_separate_components()
    
    def _load_pipeline_model(self, pipeline_path: str) -> None:
        """
        Carrega o pipeline completo (modelo_natureza_do_gasto.pkl).
        """
        try:
            logger.info(f"Carregando pipeline de: {pipeline_path}")
            self.pipeline = load(pipeline_path)

            if not hasattr(self.pipeline, 'predict'):
                raise ValueError("Pipeline carregado não possui método predict; esperando pipeline sklearn completo")

            # Extrair informações do pipeline
            self.model_info = {
                "model_type": "pipeline",
                "pipeline_path": pipeline_path,
                "steps": [name for name, _ in self.pipeline.steps] if hasattr(self.pipeline, 'steps') else []
            }

            self._populate_class_metadata(self.pipeline)

            self.is_loaded = True
            logger.info(f"Pipeline carregado com sucesso: {self.model_info}")
            
        except (FileNotFoundError, ValueError) as e:
            logger.warning(f"Pipeline indisponível: {e}")
            logger.info("Tentando carregar componentes separados como fallback...")
            self.use_pipeline_model = False
            self._load_separate_components()

        except Exception as e:
            logger.error(f"Erro ao carregar pipeline: {e}")
            self._handle_loading_error(f"Erro ao carregar pipeline: {e}")
    
    def _load_separate_components(self) -> None:
        """
        Carrega os componentes separados (vectorizer.pkl e classifier.pkl).
        """
        try:
            vectorizer_path = os.path.join(self.models_dir, "vectorizer.pkl")
            classifier_path = os.path.join(self.models_dir, "classifier.pkl")
            
            # Verificar se os arquivos existem
            if not os.path.exists(vectorizer_path):
                raise FileNotFoundError(f"Arquivo vectorizer.pkl não encontrado em {vectorizer_path}")
            
            if not os.path.exists(classifier_path):
                raise FileNotFoundError(f"Arquivo classifier.pkl não encontrado em {classifier_path}")
            
            # Carregar modelos
            logger.info(f"Carregando vectorizer de: {vectorizer_path}")
            self.vectorizer = load(vectorizer_path)
            
            logger.info(f"Carregando classifier de: {classifier_path}")
            self.classifier = load(classifier_path)
            
            # Extrair informações dos modelos
            self.model_info = {
                "model_type": "separate_components",
                "vectorizer_type": type(self.vectorizer).__name__,
                "classifier_type": type(self.classifier).__name__,
                "vectorizer_path": vectorizer_path,
                "classifier_path": classifier_path
            }

            self._populate_class_metadata(self.classifier)
            
            # Verificar se os modelos foram carregados corretamente
            if self.vectorizer is None:
                raise ValueError("Vectorizer não foi carregado corretamente")
            
            if self.classifier is None:
                raise ValueError("Classifier não foi carregado corretamente")
            
            self.is_loaded = True
            logger.info(f"Componentes carregados com sucesso: {self.model_info}")
            
        except FileNotFoundError as e:
            logger.error(f"Erro ao carregar componentes: {e}")
            self._handle_loading_error(str(e))
            
        except Exception as e:
            logger.error(f"Erro inesperado ao carregar componentes: {e}")
            self._handle_loading_error(f"Erro inesperado: {e}")
    
    def _handle_loading_error(self, error_message: str) -> None:
        """
        Trata erros de carregamento de forma amigável.
        
        Args:
            error_message: Mensagem de erro
        """
        self.is_loaded = False
        self.vectorizer = None
        self.classifier = None
        
        # Log amigável para o usuário
        logger.warning(f"⚠️  Modelos não puderam ser carregados: {error_message}")
        logger.warning("📁 Verifique se os arquivos vectorizer.pkl e classifier.pkl existem na pasta modelos/")
        logger.warning("🔧 Execute o treinamento dos modelos antes de usar o ModelAdapter")
    
    def predict_batch(self, texts: List[str], return_top_k: bool = False) -> Tuple[List[str], List[float]]:
        """
        Faz predições em lote para uma lista de textos.
        
        Args:
            texts: Lista de textos para classificar
            
        Returns:
            Tupla com (labels, confidences) para cada texto
            
        Raises:
            RuntimeError: Se os modelos não estiverem carregados
            ValueError: Se a lista de textos estiver vazia
        """
        if not self.is_loaded:
            raise RuntimeError(
                "Modelos não estão carregados. Verifique se os arquivos existem na pasta modelos/ "
                "e execute o treinamento dos modelos."
            )
        
        if not texts:
            raise ValueError("Lista de textos não pode estar vazia")
        
        if not isinstance(texts, list):
            raise ValueError("texts deve ser uma lista de strings")
        
        try:
            # LIMPAR textos antes de predizer (igual ao código antigo)
            cleaned_texts = [limpar_texto(text) or "" for text in texts]
            logger.debug(f"Textos limpos: {cleaned_texts[:3] if len(cleaned_texts) >= 3 else cleaned_texts}")
            
            if self.pipeline is not None:
                logger.debug(f"Fazendo predições com pipeline para {len(cleaned_texts)} textos")
                features = cleaned_texts
                model = self.pipeline
            else:
                logger.debug(f"Vetorizando {len(cleaned_texts)} textos")
                features = self.vectorizer.transform(cleaned_texts)
                model = self.classifier

            logger.debug("Fazendo predições")
            predictions = model.predict(features)

            probabilities = self._get_probabilities(model, features)
            confidences = self._extract_confidences_from_model(model, probabilities, predictions, features)

            labels, top_k_details = self._apply_threshold_and_topk(predictions, confidences, probabilities)

            logger.info(f"Predições concluídas: {len(labels)} textos processados")

            if return_top_k:
                return labels, confidences, top_k_details

            return labels, confidences
            
        except Exception as e:
            logger.error(f"Erro durante predição: {e}")
            raise RuntimeError(f"Erro durante predição: {e}")
    
    def predict_single(self, text: str, return_top_k: bool = False) -> Tuple[str, float]:
        """
        Faz predição para um único texto.
        
        Args:
            text: Texto para classificar
            
        Returns:
            Tupla com (label, confidence)
        """
        result = self.predict_batch([text], return_top_k=return_top_k)

        if return_top_k:
            labels, confidences, top_k = result
            return labels[0], confidences[0], top_k[0]

        labels, confidences = result
        return labels[0], confidences[0]

    @staticmethod
    def _extract_confidences_from_model(
        model: Any,
        probabilities: Optional[np.ndarray],
        predictions: List[str],
        features: Any,
    ) -> List[float]:
        """Extrai confiança do modelo com priorização de probabilidades calibradas."""

        if probabilities is not None:
            confidences = np.max(probabilities, axis=1)
            return np.clip(confidences, 0.0, 1.0).tolist()

        estimator = ModelAdapter._get_final_estimator(model)
        if hasattr(estimator, 'decision_function'):
            try:
                scores = estimator.decision_function(features)
            except Exception:
                scores = None

            if scores is not None:
                scores = np.array(scores)
                scores = np.abs(scores)
                if np.max(scores) > np.min(scores):
                    scores = (scores - np.min(scores)) / (np.max(scores) - np.min(scores))
                else:
                    scores = np.ones_like(scores) * 0.5

                return np.clip(scores, 0.0, 1.0).tolist()

        return [0.5] * len(predictions)

    def _apply_threshold_and_topk(
        self,
        predictions: List[Any],
        confidences: List[float],
        probabilities: Optional[np.ndarray],
    ) -> Tuple[List[Optional[str]], List[List[Tuple[str, float]]]]:
        """Aplica threshold local e calcula top-k para depuração."""

        labels: List[Optional[str]] = []
        top_k_details: List[List[Tuple[str, float]]] = []

        classes = self.classes_ or []

        # Preparar top-k se houver probabilidades e classes conhecidas
        if probabilities is not None and classes and probabilities.shape[1] == len(classes):
            for row in probabilities:
                sorted_idx = np.argsort(row)[::-1]
                top_entries = []
                for idx in sorted_idx[: self.top_k]:
                    top_entries.append((str(classes[idx]), float(row[idx])))
                top_k_details.append(top_entries)
        else:
            top_k_details = [[] for _ in predictions]

        for idx, (pred, conf) in enumerate(zip(predictions, confidences)):
            label = str(pred) if pred is not None else None

            # Aplica threshold local para reduzir queda em classe dominante
            if conf < self.decision_threshold:
                logger.debug(
                    "Descartando predição abaixo do threshold local do adapter: "
                    f"pred={label}, conf={conf:.3f}, threshold={self.decision_threshold:.3f}"
                )
                label = None
            else:
                # Se confiança alta mas margem pequena, registrar para depuração
                if probabilities is not None and probabilities.shape[1] > 1 and idx < len(top_k_details):
                    if len(top_k_details[idx]) >= 2:
                        margin = top_k_details[idx][0][1] - top_k_details[idx][1][1]
                        if margin < 0.05:
                            logger.debug(
                                "Predição com margem reduzida entre top-2: %s (Δ=%.3f)",
                                top_k_details[idx],
                                margin,
                            )

            labels.append(label)

        return labels, top_k_details
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre os modelos carregados.
        
        Returns:
            Dicionário com informações dos modelos
        """
        info = {
            "is_loaded": self.is_loaded,
            "models_dir": self.models_dir,
            "use_pipeline_model": self.use_pipeline_model,
            "model_info": self.model_info.copy() if self.model_info else {},
            "classes": list(self.classes_) if self.classes_ else [],
            "decision_threshold": self.decision_threshold,
            "top_k": self.top_k,
            "training_class_distribution": self.training_distribution,
            "training_class_weights": self.training_class_weights,
        }
        
        if self.pipeline is not None:
            info["active_model"] = "pipeline"
        elif self.vectorizer is not None and self.classifier is not None:
            info["active_model"] = "separate_components"
        else:
            info["active_model"] = "none"
            
        return info
    
    def reload_models(self) -> None:
        """
        Recarrega os modelos do disco.
        """
        logger.info("Recarregando modelos...")
        self._load_models()


def create_model_adapter(
    models_dir: str = "modelos/",
    decision_threshold: Optional[float] = None,
    top_k: int = 3,
) -> ModelAdapter:
    """
    Função de fábrica para criar uma instância de ModelAdapter.
    
    Args:
        models_dir: Diretório onde estão salvos os modelos (usa MODEL_DIR se None)
        
    Returns:
        Instância de ModelAdapter
    """
    return ModelAdapter(models_dir, decision_threshold=decision_threshold, top_k=top_k)
