"""
Testes unitários para o módulo spend_classification.engines.model_adapter.
"""

import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from spend_classification.engines.model_adapter import ModelAdapter, create_model_adapter, limpar_texto


class MockVectorizer:
    """Mock do vectorizer para testes."""
    
    def __init__(self):
        self.feature_names_ = ["word1", "word2", "word3"]
    
    def transform(self, texts):
        """Simula transformação de textos em vetores."""
        # Retorna matriz com número de textos x número de features
        return np.random.random((len(texts), len(self.feature_names_)))


class MockClassifier:
    """Mock do classifier para testes."""

    def __init__(
        self,
        supports_proba=True,
        supports_decision=False,
        fixed_probs=None,
        fixed_predictions=None,
        class_count=None,
    ):
        self.supports_proba = supports_proba
        self.supports_decision = supports_decision
        self.classes_ = ["categoria1", "categoria2", "categoria3"]
        self.fixed_probs = fixed_probs
        self.fixed_predictions = fixed_predictions
        if class_count is not None:
            self.class_count_ = np.array(class_count)

    def predict(self, X):
        """Simula predições."""
        if self.fixed_predictions is not None:
            return np.array(self.fixed_predictions)
        return np.random.choice(self.classes_, size=X.shape[0])

    def predict_proba(self, X):
        """Simula probabilidades (se suportado)."""
        if not self.supports_proba:
            raise AttributeError("predict_proba not supported")

        if self.fixed_probs is not None:
            return np.array(self.fixed_probs)

        probs = np.random.random((X.shape[0], len(self.classes_)))
        return probs / probs.sum(axis=1, keepdims=True)

    def decision_function(self, X):
        """Simula decision function (se suportado)."""
        if self.supports_decision:
            if self.fixed_predictions is not None:
                return np.array(self.fixed_predictions, dtype=float)
            return np.random.random(X.shape[0]) * 2 - 1  # Scores entre -1 e 1
        raise AttributeError("decision_function not supported")


class TestModelAdapter:
    """Testa a classe ModelAdapter."""
    
    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_initialization_with_existing_models(self, mock_exists, mock_load):
        """Testa inicialização com modelos existentes."""
        # Setup mocks
        mock_exists.return_value = True
        mock_vectorizer = MockVectorizer()
        mock_classifier = MockClassifier()
        mock_load.side_effect = [mock_vectorizer, mock_classifier]
        
        # Criar adapter
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        
        # Verificações
        assert adapter.is_loaded is True
        assert adapter.vectorizer is mock_vectorizer
        assert adapter.classifier is mock_classifier
        assert adapter.model_info["vectorizer_type"] == "MockVectorizer"
        assert adapter.model_info["classifier_type"] == "MockClassifier"
        assert adapter.model_info["classes"] == mock_classifier.classes_
        assert adapter.classes_ == mock_classifier.classes_
        assert mock_load.call_count == 2
    
    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_initialization_without_vectorizer(self, mock_exists, mock_load):
        """Testa inicialização quando vectorizer.pkl não existe."""
        # Setup mocks - vectorizer não existe
        def exists_side_effect(path):
            if "vectorizer.pkl" in path:
                return False
            return True
        
        mock_exists.side_effect = exists_side_effect
        
        # Criar adapter
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        
        # Verificações
        assert adapter.is_loaded is False
        assert adapter.vectorizer is None
        assert adapter.classifier is None
        assert mock_load.call_count == 0
    
    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_initialization_without_classifier(self, mock_exists, mock_load):
        """Testa inicialização quando classifier.pkl não existe."""
        # Setup mocks - classifier não existe
        def exists_side_effect(path):
            if "classifier.pkl" in path:
                return False
            return True
        
        mock_exists.side_effect = exists_side_effect
        
        # Criar adapter
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        
        # Verificações
        assert adapter.is_loaded is False
        assert adapter.vectorizer is None
        assert adapter.classifier is None
        assert mock_load.call_count == 0
    
    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_initialization_with_load_error(self, mock_exists, mock_load):
        """Testa inicialização com erro no carregamento."""
        # Setup mocks
        mock_exists.return_value = True
        mock_load.side_effect = Exception("Erro ao carregar modelo")
        
        # Criar adapter
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        
        # Verificações
        assert adapter.is_loaded is False
        assert adapter.vectorizer is None
        assert adapter.classifier is None
    
    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_predict_batch_with_proba_support(self, mock_exists, mock_load):
        """Testa predição em lote com suporte a probabilidades."""
        # Setup mocks
        mock_exists.return_value = True
        mock_vectorizer = MockVectorizer()
        mock_classifier = MockClassifier(supports_proba=True)
        mock_load.side_effect = [mock_vectorizer, mock_classifier]
        
        # Criar adapter
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        
        # Testar predição
        texts = ["texto 1", "texto 2", "texto 3"]
        labels, confidences = adapter.predict_batch(texts)
        
        # Verificações
        assert len(labels) == 3
        assert len(confidences) == 3
        assert all(isinstance(label, str) for label in labels)
        assert all(isinstance(conf, float) for conf in confidences)
        assert all(0 <= conf <= 1 for conf in confidences)
    
    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_predict_batch_with_decision_function(self, mock_exists, mock_load):
        """Testa predição em lote com decision function."""
        # Setup mocks
        mock_exists.return_value = True
        mock_vectorizer = MockVectorizer()
        mock_classifier = MockClassifier(supports_proba=False, supports_decision=True)
        mock_load.side_effect = [mock_vectorizer, mock_classifier]
        
        # Criar adapter
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        
        # Testar predição
        texts = ["texto 1", "texto 2"]
        labels, confidences = adapter.predict_batch(texts)
        
        # Verificações
        assert len(labels) == 2
        assert len(confidences) == 2
        assert all(isinstance(label, str) for label in labels)
        assert all(isinstance(conf, float) for conf in confidences)
        assert all(0 <= conf <= 1 for conf in confidences)
    
    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_predict_batch_without_confidence_support(self, mock_exists, mock_load):
        """Testa predição em lote sem suporte a confiança."""
        # Setup mocks
        mock_exists.return_value = True
        mock_vectorizer = MockVectorizer()
        mock_classifier = MockClassifier(supports_proba=False, supports_decision=False)
        mock_load.side_effect = [mock_vectorizer, mock_classifier]
        
        # Criar adapter
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        
        # Testar predição
        texts = ["texto 1", "texto 2"]
        labels, confidences = adapter.predict_batch(texts)
        
        # Verificações
        assert len(labels) == 2
        assert len(confidences) == 2
        assert all(isinstance(label, str) for label in labels)
        assert all(isinstance(conf, float) for conf in confidences)
        assert all(conf == 0.5 for conf in confidences)  # Confiança padrão
    
    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_predict_batch_not_loaded(self, mock_exists, mock_load):
        """Testa predição em lote quando modelos não estão carregados."""
        # Setup mocks - modelos não carregados
        mock_exists.return_value = False
        
        # Criar adapter
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        
        # Testar predição - deve falhar
        texts = ["texto 1", "texto 2"]
        
        with pytest.raises(RuntimeError) as exc_info:
            adapter.predict_batch(texts)
        
        assert "Modelos não estão carregados" in str(exc_info.value)
    
    def test_predict_batch_empty_list(self):
        """Testa predição em lote com lista vazia."""
        # Criar adapter sem carregar modelos
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        adapter.is_loaded = True  # Simular que está carregado
        
        # Testar predição com lista vazia
        with pytest.raises(ValueError) as exc_info:
            adapter.predict_batch([])
        
        assert "Lista de textos não pode estar vazia" in str(exc_info.value)
    
    def test_predict_batch_invalid_input(self):
        """Testa predição em lote com entrada inválida."""
        # Criar adapter sem carregar modelos
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        adapter.is_loaded = True  # Simular que está carregado
        
        # Testar predição com entrada inválida
        with pytest.raises(ValueError) as exc_info:
            adapter.predict_batch("não é uma lista")
        
        assert "texts deve ser uma lista de strings" in str(exc_info.value)
    
    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_predict_single(self, mock_exists, mock_load):
        """Testa predição para um único texto."""
        # Setup mocks
        mock_exists.return_value = True
        mock_vectorizer = MockVectorizer()
        mock_classifier = MockClassifier()
        mock_load.side_effect = [mock_vectorizer, mock_classifier]
        
        # Criar adapter
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        
        # Testar predição única
        text = "texto único"
        label, confidence = adapter.predict_single(text)
        
        # Verificações
        assert isinstance(label, str)
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
    
    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_get_model_info(self, mock_exists, mock_load):
        """Testa obtenção de informações dos modelos."""
        # Setup mocks
        mock_exists.return_value = True
        mock_vectorizer = MockVectorizer()
        mock_classifier = MockClassifier()
        mock_load.side_effect = [mock_vectorizer, mock_classifier]
        
        # Criar adapter
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        
        # Obter informações
        info = adapter.get_model_info()

        # Verificações
        assert info["is_loaded"] is True
        assert info["models_dir"] == "test_models/"
        assert info["model_info"]["vectorizer_type"] == "MockVectorizer"
        assert info["model_info"]["classifier_type"] == "MockClassifier"
        assert info["classes"] == mock_classifier.classes_
        assert info["decision_threshold"] == 0.0
    
    def test_get_model_info_not_loaded(self):
        """Testa obtenção de informações quando modelos não estão carregados."""
        # Criar adapter sem carregar modelos
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)

        # Obter informações
        info = adapter.get_model_info()

        # Verificações
        assert info["is_loaded"] is False
        assert info["models_dir"] == "test_models/"
        assert info["model_info"] == {}
        assert info["classes"] == []

    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_threshold_and_topk_details(self, mock_exists, mock_load):
        """Garante que o threshold local descarta predições fracas e retorna top-k."""

        mock_exists.return_value = True
        mock_vectorizer = MockVectorizer()
        fixed_probs = [
            [0.4, 0.35, 0.25],  # abaixo do threshold 0.9
            [0.95, 0.03, 0.02],
        ]
        mock_classifier = MockClassifier(
            fixed_probs=fixed_probs,
            fixed_predictions=["categoria1", "categoria1"],
        )
        mock_load.side_effect = [mock_vectorizer, mock_classifier]

        adapter = ModelAdapter("test_models/", decision_threshold=0.9, top_k=2)

        labels, confidences, top_k = adapter.predict_batch(["t1", "t2"], return_top_k=True)

        assert labels[0] is None  # abaixo do limiar
        assert labels[1] == "categoria1"
        assert len(top_k[1]) == 2
        assert top_k[1][0][0] == "categoria1"
        assert confidences[1] == pytest.approx(0.95, rel=1e-6)

    def test_limpar_texto_usa_normalizacao_compartilhada(self):
        """Garante que limpar_texto remove acentos após normalização compartilhada."""
        text = "Café DO João (02/12)"

        cleaned = limpar_texto(text)

        assert cleaned == "cafe do joao"
    
    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_reload_models(self, mock_exists, mock_load):
        """Testa recarregamento dos modelos."""
        # Setup mocks
        mock_exists.return_value = True
        mock_vectorizer = MockVectorizer()
        mock_classifier = MockClassifier()
        # Resetar side_effect para cada chamada
        mock_load.side_effect = lambda path: mock_vectorizer if "vectorizer" in path else mock_classifier
        
        # Criar adapter
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        
        # Verificar que está carregado
        assert adapter.is_loaded is True
        
        # Recarregar modelos
        adapter.reload_models()
        
        # Verificar que ainda está carregado
        assert adapter.is_loaded is True
        assert mock_load.call_count == 4  # 2 carregamentos iniciais + 2 recarregamentos

    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_training_metadata_exposed(self, mock_exists, mock_load):
        """Garante que distribuição de classes e pesos são expostos no model_info."""

        mock_exists.return_value = True
        mock_vectorizer = MockVectorizer()
        mock_classifier = MockClassifier(class_count=[10, 5, 1])
        mock_classifier.class_weight_ = [1.0, 2.0, 3.0]
        mock_load.side_effect = [mock_vectorizer, mock_classifier]

        adapter = ModelAdapter("test_models/", decision_threshold=0.0)

        info = adapter.get_model_info()

        assert info["training_class_distribution"] == {
            "categoria1": 10,
            "categoria2": 5,
            "categoria3": 1,
        }
        assert info["training_class_weights"] == {
            "categoria1": 1.0,
            "categoria2": 2.0,
            "categoria3": 3.0,
        }


class TestCreateModelAdapter:
    """Testa a função de fábrica create_model_adapter."""
    
    @patch('spend_classification.engines.model_adapter.ModelAdapter')
    def test_create_model_adapter_default(self, mock_model_adapter):
        """Testa criação de ModelAdapter com parâmetros padrão."""
        # Criar adapter
        adapter = create_model_adapter()

        # Verificar que ModelAdapter foi chamado com parâmetros corretos
        mock_model_adapter.assert_called_once_with("modelos/", decision_threshold=None, top_k=3)

    @patch('spend_classification.engines.model_adapter.ModelAdapter')
    def test_create_model_adapter_custom_dir(self, mock_model_adapter):
        """Testa criação de ModelAdapter com diretório customizado."""
        # Criar adapter
        adapter = create_model_adapter("custom_models/")

        # Verificar que ModelAdapter foi chamado com parâmetros corretos
        mock_model_adapter.assert_called_once_with("custom_models/", decision_threshold=None, top_k=3)


class TestModelAdapterIntegration:
    """Testes de integração para ModelAdapter."""
    
    @patch('spend_classification.engines.model_adapter.load')
    @patch('os.path.exists')
    def test_full_workflow(self, mock_exists, mock_load):
        """Testa workflow completo: carregar -> predizer -> recarregar."""
        # Setup mocks
        mock_exists.return_value = True
        mock_vectorizer = MockVectorizer()
        mock_classifier = MockClassifier()
        # Resetar side_effect para cada chamada
        mock_load.side_effect = lambda path: mock_vectorizer if "vectorizer" in path else mock_classifier
        
        # Criar adapter
        adapter = ModelAdapter("test_models/", decision_threshold=0.0)
        
        # Verificar carregamento
        assert adapter.is_loaded is True
        
        # Fazer predições
        texts = ["texto 1", "texto 2", "texto 3"]
        labels, confidences = adapter.predict_batch(texts)
        
        # Verificar resultados
        assert len(labels) == 3
        assert len(confidences) == 3
        
        # Testar predição única
        label, confidence = adapter.predict_single("texto único")
        assert isinstance(label, str)
        assert isinstance(confidence, float)
        
        # Obter informações
        info = adapter.get_model_info()
        assert info["is_loaded"] is True
        
        # Recarregar modelos
        adapter.reload_models()
        assert adapter.is_loaded is True
