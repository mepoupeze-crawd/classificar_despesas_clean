"""
Testes para os engines de classificação

Testa todos os engines: ML, Rules, Similarity, AI Fallback e Pipeline.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from ..core.schemas import ExpenseTransaction, ClassificationResult
from ..engines.classifier import ExpenseClassifier
from ..engines.ml_model import MLModel, MLClassifier
from ..engines.rules_engine import RulesEngine
from ..engines.similarity_engine import SimilarityEngine
from ..engines.ai_fallback import AIFallbackEngine
from ..engines.pipeline import ClassificationPipeline


class TestExpenseClassifier:
    """Testa o classificador principal."""
    
    def test_classifier_initialization(self):
        """Testa inicialização do classificador."""
        classifier = ExpenseClassifier()
        
        assert classifier.confidence_threshold == 0.7
        assert classifier.ml_model is None
        assert classifier.rules_engine is None
    
    def test_classifier_with_components(self):
        """Testa classificador com componentes."""
        ml_model = Mock()
        rules_engine = Mock()
        
        classifier = ExpenseClassifier(
            ml_model=ml_model,
            rules_engine=rules_engine,
            confidence_threshold=0.8
        )
        
        assert classifier.ml_model == ml_model
        assert classifier.rules_engine == rules_engine
        assert classifier.confidence_threshold == 0.8
    
    def test_classify_with_high_confidence_ml(self):
        """Testa classificação com ML de alta confiança."""
        # Mock do ML model
        ml_model = Mock()
        ml_result = ClassificationResult(
            category="Farmácia",
            confidence=0.9,
            classifier_used="ml_model"
        )
        ml_model.classify.return_value = ml_result
        
        # Mock do rules engine
        rules_engine = Mock()
        
        classifier = ExpenseClassifier(
            ml_model=ml_model,
            rules_engine=rules_engine
        )
        
        transaction = ExpenseTransaction(
            description="Drogasil",
            amount=25.50,
            date=datetime.now()
        )
        
        result = classifier.classify(transaction)
        
        assert result.category == "Farmácia"
        assert result.confidence == 0.9
        assert result.classifier_used == "ml_model"
        ml_model.classify.assert_called_once_with(transaction)
    
    def test_classify_fallback_to_rules(self):
        """Testa fallback para regras quando ML tem baixa confiança."""
        # Mock do ML model com baixa confiança
        ml_model = Mock()
        ml_result = ClassificationResult(
            category="Farmácia",
            confidence=0.5,  # Baixa confiança
            classifier_used="ml_model"
        )
        ml_model.classify.return_value = ml_result
        
        # Mock do rules engine com alta confiança
        rules_engine = Mock()
        rules_result = ClassificationResult(
            category="Farmácia",
            confidence=0.9,
            classifier_used="rules_engine"
        )
        rules_engine.classify.return_value = rules_result
        
        classifier = ExpenseClassifier(
            ml_model=ml_model,
            rules_engine=rules_engine
        )
        
        transaction = ExpenseTransaction(
            description="Drogasil",
            amount=25.50,
            date=datetime.now()
        )
        
        result = classifier.classify(transaction)
        
        assert result.category == "Farmácia"
        assert result.confidence == 0.9
        assert result.classifier_used == "rules_engine"


class TestMLModel:
    """Testa o modelo de ML."""
    
    def test_ml_model_initialization(self):
        """Testa inicialização do modelo ML."""
        model = MLModel()
        
        assert model.pipeline is None
        assert model.classes_ is None
        assert model.feature_names_ is None
    
    @patch('joblib.load')
    def test_load_model(self, mock_load):
        """Testa carregamento de modelo."""
        # Mock do pipeline
        mock_pipeline = Mock()
        mock_pipeline.classes_ = ["Farmácia", "Supermercado"]
        mock_tfidf = Mock()
        mock_tfidf.get_feature_names_out.return_value = ["feature1", "feature2"]
        mock_pipeline.named_steps = {"tfidf": mock_tfidf}
        mock_load.return_value = mock_pipeline
        
        model = MLModel()
        model.load("test_model.pkl")
        
        assert model.pipeline == mock_pipeline
        assert model.classes_ == ["Farmácia", "Supermercado"]
        mock_load.assert_called_once_with("test_model.pkl")
    
    def test_predict_without_model(self):
        """Testa predição sem modelo carregado."""
        model = MLModel()
        
        with pytest.raises(ValueError, match="Model not loaded"):
            model.predict(["test"])
    
    @patch('joblib.load')
    def test_predict_with_model(self, mock_load):
        """Testa predição com modelo carregado."""
        # Mock do pipeline
        mock_pipeline = Mock()
        mock_pipeline.predict.return_value = ["Farmácia"]
        mock_pipeline.classes_ = ["Farmácia", "Supermercado"]
        mock_tfidf = Mock()
        mock_tfidf.get_feature_names_out.return_value = ["feature1"]
        mock_pipeline.named_steps = {"tfidf": mock_tfidf}
        mock_load.return_value = mock_pipeline
        
        model = MLModel()
        model.load("test_model.pkl")
        
        result = model.predict(["Drogasil"])
        
        assert result == ["Farmácia"]
        mock_pipeline.predict.assert_called_once_with(["Drogasil"])


class TestRulesEngine:
    """Testa o engine de regras."""
    
    def test_rules_engine_initialization(self):
        """Testa inicialização do engine de regras."""
        engine = RulesEngine()
        
        assert len(engine.rules) > 0  # Deve ter regras padrão
        assert engine.get_confidence_threshold() == 0.8
    
    def test_add_rule(self):
        """Testa adição de nova regra."""
        engine = RulesEngine()
        initial_count = len(engine.rules)
        
        new_rule = {
            "name": "test_rule",
            "pattern": "test_pattern",
            "category": "Farmácia",
            "confidence": 0.9
        }
        
        engine.add_rule(new_rule)
        
        assert len(engine.rules) == initial_count + 1
        assert engine.rules[-1]["name"] == "test_rule"
    
    def test_add_invalid_rule(self):
        """Testa adição de regra inválida."""
        engine = RulesEngine()
        
        invalid_rule = {
            "name": "test_rule",
            "pattern": "test_pattern"
            # Faltam category e confidence
        }
        
        with pytest.raises(ValueError, match="Rule must have field: category"):
            engine.add_rule(invalid_rule)
    
    def test_classify_with_matching_rule(self):
        """Testa classificação com regra correspondente."""
        engine = RulesEngine()
        
        transaction = ExpenseTransaction(
            description="Netflix Com",
            amount=44.90,
            date=datetime.now()
        )
        
        result = engine.classify(transaction)
        
        # Deve encontrar a regra do Netflix
        assert result.category == "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)"
        assert result.confidence >= 0.9
        assert result.classifier_used == "rules_engine"
    
    def test_classify_without_matching_rule(self):
        """Testa classificação sem regra correspondente."""
        engine = RulesEngine()
        
        transaction = ExpenseTransaction(
            description="Unknown Store XYZ",
            amount=10.00,
            date=datetime.now()
        )
        
        result = engine.classify(transaction)
        
        # Deve retornar categoria padrão
        assert result.category == "Gastos pessoais"
        assert result.confidence == 0.3
        assert result.classifier_used == "rules_engine"


class TestSimilarityEngine:
    """Testa o engine de similaridade."""
    
    def test_similarity_engine_initialization(self):
        """Testa inicialização do engine de similaridade."""
        engine = SimilarityEngine()
        
        assert len(engine.examples) > 0  # Deve ter exemplos padrão
        assert engine.similarity_threshold == 0.8
    
    def test_add_example(self):
        """Testa adição de novo exemplo."""
        engine = SimilarityEngine()
        initial_count = len(engine.examples)
        
        engine.add_example({
            "text": "Test Store",
            "category": "Farmácia"
        })
        
        assert len(engine.examples) == initial_count + 1
        assert engine.examples[-1]["text"] == "Test Store"
    
    def test_classify_with_similar_example(self):
        """Testa classificação com exemplo similar."""
        engine = SimilarityEngine()
        
        transaction = ExpenseTransaction(
            description="Netflix",
            amount=44.90,
            date=datetime.now()
        )
        
        result = engine.classify(transaction)
        
        # Deve encontrar exemplo similar
        assert result.category == "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)"
        assert result.confidence > 0.8
        assert result.classifier_used == "similarity_engine"
    
    def test_find_similar_examples(self):
        """Testa busca por exemplos similares."""
        engine = SimilarityEngine()
        
        similar = engine.find_similar_examples("Netflix", limit=3)
        
        assert len(similar) <= 3
        assert all("similarity" in item for item in similar)
        assert all(item["similarity"] >= 0.0 for item in similar)


class TestAIFallbackEngine:
    """Testa o engine de fallback para IA."""
    
    def test_ai_fallback_initialization(self):
        """Testa inicialização do engine de IA."""
        engine = AIFallbackEngine()
        
        assert engine.openai_client is None  # Sem API key
        assert engine.serpapi_key is None  # Sem API key
    
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'})
    @patch('openai.OpenAI')
    def test_ai_fallback_with_api_key(self, mock_openai):
        """Testa inicialização com API key."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        engine = AIFallbackEngine()
        
        assert engine.openai_client == mock_client
    
    def test_extract_establishment(self):
        """Testa extração de estabelecimento."""
        engine = AIFallbackEngine()
        
        description = "PIX CARREFOUR 12345"
        establishment = engine._extract_establishment(description)
        
        assert "CARREFOUR" in establishment
        assert "PIX" not in establishment
    
    def test_classify_without_openai(self):
        """Testa classificação sem OpenAI."""
        engine = AIFallbackEngine()  # Sem API key
        
        transaction = ExpenseTransaction(
            description="Test Store",
            amount=10.00,
            date=datetime.now()
        )
        
        result = engine.classify(transaction)
        
        assert result.category == "Gastos pessoais"
        assert result.confidence == 0.0
        assert result.classifier_used == "ai_fallback"


class TestClassificationPipeline:
    """Testa o pipeline de classificação."""
    
    def test_pipeline_initialization(self):
        """Testa inicialização do pipeline."""
        pipeline = ClassificationPipeline()
        
        assert len(pipeline.stages) == 0
        assert pipeline.enable_parallel == True
    
    def test_add_stage(self):
        """Testa adição de etapa ao pipeline."""
        pipeline = ClassificationPipeline()
        
        mock_classifier = Mock()
        pipeline.add_stage("test_stage", mock_classifier)
        
        assert "test_stage" in pipeline.stages
        assert pipeline.stages["test_stage"].classifier == mock_classifier
        assert pipeline.stages["test_stage"].enabled == True
    
    def test_process_empty_transactions(self):
        """Testa processamento de lista vazia."""
        pipeline = ClassificationPipeline()
        
        result = pipeline.process([])
        
        assert result == []
    
    def test_process_single_transaction(self):
        """Testa processamento de uma transação."""
        pipeline = ClassificationPipeline()
        
        # Mock classifier
        mock_classifier = Mock()
        mock_result = ClassificationResult(
            category="Farmácia",
            confidence=0.9,
            classifier_used="test_stage"
        )
        mock_classifier.classify.return_value = mock_result
        mock_classifier.get_confidence_threshold.return_value = 0.7
        
        pipeline.add_stage("test_stage", mock_classifier)
        
        transaction = ExpenseTransaction(
            description="Drogasil",
            amount=25.50,
            date=datetime.now()
        )
        
        result = pipeline.process([transaction])
        
        assert len(result) == 1
        assert result[0].category == "Farmácia"
        assert result[0].confidence == 0.9


class TestPipelineStage:
    """Testa uma etapa do pipeline."""
    
    def test_stage_initialization(self):
        """Testa inicialização de etapa."""
        mock_classifier = Mock()
        stage = PipelineStage("test", mock_classifier)
        
        assert stage.name == "test"
        assert stage.classifier == mock_classifier
        assert stage.enabled == True
    
    def test_stage_process_success(self):
        """Testa processamento bem-sucedido de etapa."""
        mock_classifier = Mock()
        mock_result = ClassificationResult(
            category="Farmácia",
            confidence=0.9,
            classifier_used="test"
        )
        mock_classifier.classify.return_value = mock_result
        
        stage = PipelineStage("test", mock_classifier)
        
        transaction = ExpenseTransaction(
            description="Drogasil",
            amount=25.50,
            date=datetime.now()
        )
        
        result = stage.process(transaction)
        
        assert result == mock_result
        assert stage.stats["successful"] == 1
        assert stage.stats["total_processed"] == 1
    
    def test_stage_process_disabled(self):
        """Testa processamento de etapa desabilitada."""
        mock_classifier = Mock()
        stage = PipelineStage("test", mock_classifier, enabled=False)
        
        transaction = ExpenseTransaction(
            description="Test",
            amount=10.00,
            date=datetime.now()
        )
        
        result = stage.process(transaction)
        
        assert result is None
        assert stage.stats["total_processed"] == 0
