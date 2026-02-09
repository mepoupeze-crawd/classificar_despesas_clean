"""
Testes unitários para o módulo spend_classification.engines.pipeline.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from spend_classification.engines.pipeline import ClassificationPipeline, create_classification_pipeline
from spend_classification.core.schemas import ExpenseTransaction, Prediction


class MockRulesEngine:
    """Mock do RulesEngine para testes."""
    
    def __init__(self, should_return_result=True, category="test_category", confidence=0.8):
        self.should_return_result = should_return_result
        self.category = category
        self.confidence = confidence
        self.rules = [{"name": "test_rule", "pattern": "test"}]
    
    def classify(self, transaction):
        if self.should_return_result:
            return Mock(
                category=self.category,
                confidence=self.confidence,
                classifier_used="rules_engine",
                raw_prediction={"rule": "test"}
            )
        else:
            return Mock(category="", confidence=0.0, classifier_used="rules_engine")
    
    def get_rules(self):
        return self.rules


class MockSimilarityEngine:
    """Mock do SimilarityClassifier para testes."""
    
    def __init__(self, should_return_result=True, label="test_label", score=0.8):
        self.is_loaded = True
        self.should_return_result = should_return_result
        self.label = label
        self.score = score
        self.threshold = 0.7
    
    def query(self, text):
        if self.should_return_result and self.score >= self.threshold:
            return (self.label, self.score)
        return None
    
    def get_stats(self):
        return {"loaded": True, "records": 100}


class MockModelAdapter:
    """Mock do ModelAdapter para testes."""
    
    def __init__(self, should_return_result=True, label="test_label", confidence=0.8):
        self.is_loaded = True
        self.should_return_result = should_return_result
        self.label = label
        self.confidence = confidence
    
    def predict_single(self, text):
        if self.should_return_result and self.confidence >= 0.7:
            return (self.label, self.confidence)
        return ("low_confidence", 0.3)
    
    def get_model_info(self):
        return {"is_loaded": True, "models_dir": "test_models/"}


class TestClassificationPipeline:
    """Testa a classe ClassificationPipeline."""
    
    def test_initialization(self):
        """Testa inicialização do pipeline."""
        pipeline = ClassificationPipeline(
            similarity_threshold=0.8,
            model_adapter_threshold=0.9
        )

        assert pipeline.similarity_threshold == 0.8
        assert pipeline.model_adapter_threshold == 0.9
        # Rules engine pode ser None se ENABLE_DETERMINISTIC_RULES=false
        assert pipeline.enable_deterministic_rules == False or pipeline.rules_engine is not None
        # Similarity engine pode ser None se ENABLE_TFIDF_SIMILARITY=false
        assert pipeline.enable_tfidf_similarity == False or pipeline.similarity_engine is not None
        assert pipeline.model_adapter is not None
    
    def test_predict_batch_empty_list(self):
        """Testa predição em lote com lista vazia."""
        pipeline = ClassificationPipeline()
        predictions, elapsed_ms = pipeline.predict_batch([])
        
        assert predictions == []
        assert elapsed_ms == 0.0
    
    def test_predict_batch_rules_engine_success(self):
        """Testa predição quando rules engine tem sucesso."""
        # Setup mocks
        with patch('spend_classification.engines.pipeline.RulesEngine') as mock_rules, \
             patch('spend_classification.engines.pipeline.SimilarityClassifier') as mock_similarity, \
             patch('spend_classification.engines.pipeline.ModelAdapter') as mock_adapter:
            
            mock_rules.return_value = MockRulesEngine(should_return_result=True, category="test_label", confidence=0.9)
            mock_similarity.return_value = MockSimilarityEngine()
            mock_adapter.return_value = MockModelAdapter()
            
            pipeline = ClassificationPipeline()
            
            # Criar transação de teste
            transaction = ExpenseTransaction(
                description="test_label Com",
                amount=44.90,
                date="2024-01-01"
            )
            
            predictions, elapsed_ms = pipeline.predict_batch([transaction])
            
            # Verificações
            assert len(predictions) == 1
            assert predictions[0].label == "test_label"
            # Se rules engine estiver desabilitado, deve usar model adapter
            if pipeline.enable_deterministic_rules:
                assert predictions[0].confidence == 0.9
                assert predictions[0].method_used == "rules_engine"
            else:
                assert predictions[0].confidence == 0.8
                assert predictions[0].method_used == "model_adapter"
            assert predictions[0].elapsed_ms > 0
            assert elapsed_ms > 0
    
    def test_predict_batch_similarity_engine_success(self):
        """Testa predição quando similarity engine tem sucesso."""
        with patch('spend_classification.engines.pipeline.RulesEngine') as mock_rules, \
             patch('spend_classification.engines.pipeline.SimilarityClassifier') as mock_similarity, \
             patch('spend_classification.engines.pipeline.ModelAdapter') as mock_adapter:
            
            mock_rules.return_value = MockRulesEngine(should_return_result=False)
            mock_similarity.return_value = MockSimilarityEngine(should_return_result=True, label="test_label", score=0.8)
            mock_adapter.return_value = MockModelAdapter()
            
            pipeline = ClassificationPipeline()
            
            transaction = ExpenseTransaction(
                description="test_label Viagem",
                amount=25.50,
                date="2024-01-01"
            )
            
            predictions, elapsed_ms = pipeline.predict_batch([transaction])
            
            assert len(predictions) == 1
            assert predictions[0].label == "test_label"
            assert predictions[0].confidence == 0.8
            # Se similarity engine estiver desabilitado, deve usar model adapter
            if pipeline.enable_tfidf_similarity:
                assert predictions[0].method_used == "similarity_engine"
            else:
                assert predictions[0].method_used == "model_adapter"
    
    def test_predict_batch_model_adapter_success(self):
        """Testa predição quando model adapter tem sucesso."""
        with patch('spend_classification.engines.pipeline.RulesEngine') as mock_rules, \
             patch('spend_classification.engines.pipeline.SimilarityClassifier') as mock_similarity, \
             patch('spend_classification.engines.pipeline.ModelAdapter') as mock_adapter:
            
            mock_rules.return_value = MockRulesEngine(should_return_result=False)
            mock_similarity.return_value = MockSimilarityEngine(should_return_result=False)
            mock_adapter.return_value = MockModelAdapter(should_return_result=True, label="test_label", confidence=0.8)
            
            pipeline = ClassificationPipeline()
            
            transaction = ExpenseTransaction(
                description="test_label Farmacia",
                amount=15.75,
                date="2024-01-01"
            )
            
            predictions, elapsed_ms = pipeline.predict_batch([transaction])
            
            assert len(predictions) == 1
            assert predictions[0].label == "test_label"
            assert predictions[0].confidence == 0.8
            assert predictions[0].method_used == "model_adapter"
    
    def test_predict_batch_fallback_to_doubt(self):
        """Testa fallback para 'duvida' quando nenhum método tem sucesso."""
        with patch('spend_classification.engines.pipeline.RulesEngine') as mock_rules, \
             patch('spend_classification.engines.pipeline.SimilarityClassifier') as mock_similarity, \
             patch('spend_classification.engines.pipeline.ModelAdapter') as mock_adapter:
            
            mock_rules.return_value = MockRulesEngine(should_return_result=False)
            mock_similarity.return_value = MockSimilarityEngine(should_return_result=False)
            mock_adapter.return_value = MockModelAdapter(should_return_result=False)
            
            pipeline = ClassificationPipeline()
            
            transaction = ExpenseTransaction(
                description="Transacao Desconhecida",
                amount=100.0,
                date="2024-01-01"
            )
            
            predictions, elapsed_ms = pipeline.predict_batch([transaction])
            
            assert len(predictions) == 1
            assert predictions[0].label == "duvida"
            assert predictions[0].confidence == 0.3  # Confidence padrão do fallback
            assert predictions[0].method_used == "fallback"
            assert predictions[0].needs_keys == True  # AI fallback habilitado mas sem keys
    
    def test_predict_batch_similarity_below_threshold(self):
        """Testa quando similarity engine retorna score abaixo do threshold."""
        with patch('spend_classification.engines.pipeline.RulesEngine') as mock_rules, \
             patch('spend_classification.engines.pipeline.SimilarityClassifier') as mock_similarity, \
             patch('spend_classification.engines.pipeline.ModelAdapter') as mock_adapter:
            
            mock_rules.return_value = MockRulesEngine(should_return_result=False)
            mock_similarity.return_value = MockSimilarityEngine(should_return_result=True, label="test_label", score=0.5)  # Abaixo do threshold
            mock_adapter.return_value = MockModelAdapter(should_return_result=True, label="test_label", confidence=0.8)
            
            pipeline = ClassificationPipeline(similarity_threshold=0.7)
            
            transaction = ExpenseTransaction(
                description="test_label Viagem",
                amount=25.50,
                date="2024-01-01"
            )
            
            predictions, elapsed_ms = pipeline.predict_batch([transaction])
            
            # Deve usar model adapter, não similarity
            assert predictions[0].method_used == "model_adapter"
            assert predictions[0].label == "test_label"
    
    def test_predict_batch_model_adapter_below_threshold(self):
        """Testa quando model adapter retorna confidence abaixo do threshold."""
        with patch('spend_classification.engines.pipeline.RulesEngine') as mock_rules, \
             patch('spend_classification.engines.pipeline.SimilarityClassifier') as mock_similarity, \
             patch('spend_classification.engines.pipeline.ModelAdapter') as mock_adapter:
            
            mock_rules.return_value = MockRulesEngine(should_return_result=False)
            mock_similarity.return_value = MockSimilarityEngine(should_return_result=False)
            mock_adapter.return_value = MockModelAdapter(should_return_result=True, label="test_label", confidence=0.5)  # Abaixo do threshold
            
            pipeline = ClassificationPipeline(model_adapter_threshold=0.7)
            
            transaction = ExpenseTransaction(
                description="test_label Farmacia",
                amount=15.75,
                date="2024-01-01"
            )
            
            predictions, elapsed_ms = pipeline.predict_batch([transaction])
            
            # Deve usar fallback
            assert predictions[0].method_used == "fallback"
            assert predictions[0].label == "duvida"
            assert predictions[0].needs_keys == True  # AI fallback habilitado mas sem keys
    
    def test_predict_batch_multiple_transactions(self):
        """Testa predição em lote com múltiplas transações."""
        with patch('spend_classification.engines.pipeline.RulesEngine') as mock_rules, \
             patch('spend_classification.engines.pipeline.SimilarityClassifier') as mock_similarity, \
             patch('spend_classification.engines.pipeline.ModelAdapter') as mock_adapter:
            
            mock_rules.return_value = MockRulesEngine(should_return_result=True, category="test_label", confidence=0.9)
            mock_similarity.return_value = MockSimilarityEngine()
            mock_adapter.return_value = MockModelAdapter()
            
            pipeline = ClassificationPipeline()
            
            transactions = [
                ExpenseTransaction(description="test_label Com", amount=44.90, date="2024-01-01"),
                ExpenseTransaction(description="test_label Viagem", amount=25.50, date="2024-01-01"),
                ExpenseTransaction(description="test_label", amount=15.75, date="2024-01-01")
            ]
            
            predictions, elapsed_ms = pipeline.predict_batch(transactions)
            
            assert len(predictions) == 3
            assert all(isinstance(p, Prediction) for p in predictions)
            assert elapsed_ms > 0
    
    def test_predict_batch_error_handling(self):
        """Testa tratamento de erros durante predição."""
        with patch('spend_classification.engines.pipeline.RulesEngine') as mock_rules, \
             patch('spend_classification.engines.pipeline.SimilarityClassifier') as mock_similarity, \
             patch('spend_classification.engines.pipeline.ModelAdapter') as mock_adapter:
            
            # Mock que gera erro em todos os engines
            mock_rules_instance = Mock()
            mock_rules_instance.classify.side_effect = Exception("Rules engine error")
            mock_rules_instance.get_rules.return_value = []
            mock_rules.return_value = mock_rules_instance
            
            mock_similarity_instance = Mock()
            mock_similarity_instance.is_loaded = True
            mock_similarity_instance.query.side_effect = Exception("Similarity engine error")
            mock_similarity_instance.threshold = 0.7
            mock_similarity.return_value = mock_similarity_instance
            
            mock_adapter_instance = Mock()
            mock_adapter_instance.is_loaded = True
            mock_adapter_instance.predict_single.side_effect = Exception("Model adapter error")
            mock_adapter.return_value = mock_adapter_instance
            
            pipeline = ClassificationPipeline()
            
            transaction = ExpenseTransaction(
                description="Test Transaction",
                amount=100.0,
                date="2024-01-01"
            )
            
            predictions, elapsed_ms = pipeline.predict_batch([transaction])
            
            # Deve retornar predição de fallback (não de erro, pois o erro é tratado internamente)
            assert len(predictions) == 1
            assert predictions[0].label == "duvida"
            assert predictions[0].method_used == "fallback"
            assert predictions[0].confidence == 0.3
    
    def test_get_engine_status(self):
        """Testa obtenção do status dos engines."""
        with patch('spend_classification.engines.pipeline.RulesEngine') as mock_rules, \
             patch('spend_classification.engines.pipeline.SimilarityClassifier') as mock_similarity, \
             patch('spend_classification.engines.pipeline.ModelAdapter') as mock_adapter:
            
            mock_rules.return_value = MockRulesEngine()
            mock_similarity.return_value = MockSimilarityEngine()
            mock_adapter.return_value = MockModelAdapter()
            
            pipeline = ClassificationPipeline()
            status = pipeline.get_engine_status()
            
            assert "rules_engine" in status
            assert "similarity_engine" in status
            assert "model_adapter" in status
            
            assert status["rules_engine"]["status"] in ["enabled", "disabled"]
            assert status["similarity_engine"]["status"] in ["enabled", "disabled"]
            assert status["model_adapter"]["status"] in ["loaded", "not_loaded"]
            assert "ai_fallback" in status
    
    def test_update_thresholds(self):
        """Testa atualização de thresholds."""
        with patch('spend_classification.engines.pipeline.RulesEngine') as mock_rules, \
             patch('spend_classification.engines.pipeline.SimilarityClassifier') as mock_similarity, \
             patch('spend_classification.engines.pipeline.ModelAdapter') as mock_adapter:
            
            mock_rules.return_value = MockRulesEngine()
            mock_similarity.return_value = MockSimilarityEngine()
            mock_adapter.return_value = MockModelAdapter()
            
            pipeline = ClassificationPipeline()
            
            pipeline.update_thresholds(similarity_threshold=0.8, model_adapter_threshold=0.9)

            assert pipeline.similarity_threshold == 0.8
            assert pipeline.model_adapter_threshold == 0.9
            # Só verifica threshold se similarity_engine não for None
            if pipeline.similarity_engine is not None:
                assert pipeline.similarity_engine.threshold == 0.8


class TestCreateClassificationPipeline:
    """Testa a função de fábrica create_classification_pipeline."""
    
    def test_create_pipeline_default(self):
        """Testa criação de pipeline com parâmetros padrão."""
        with patch('spend_classification.engines.pipeline.RulesEngine'), \
             patch('spend_classification.engines.pipeline.SimilarityClassifier'), \
             patch('spend_classification.engines.pipeline.ModelAdapter'):
            
            pipeline = create_classification_pipeline()
            
            assert isinstance(pipeline, ClassificationPipeline)
            assert pipeline.similarity_threshold == 0.7
            assert pipeline.model_adapter_threshold == 0.7
    
    def test_create_pipeline_custom_params(self):
        """Testa criação de pipeline com parâmetros customizados."""
        with patch('spend_classification.engines.pipeline.RulesEngine'), \
             patch('spend_classification.engines.pipeline.SimilarityClassifier'), \
             patch('spend_classification.engines.pipeline.ModelAdapter'):
            
            pipeline = create_classification_pipeline(
                similarity_threshold=0.8,
                model_adapter_threshold=0.9,
                similarity_model_path="custom_similarity.csv",
                model_adapter_path="custom_models/"
            )
            
            assert isinstance(pipeline, ClassificationPipeline)
            assert pipeline.similarity_threshold == 0.8
            assert pipeline.model_adapter_threshold == 0.9


class TestPipelineIntegration:
    """Testes de integração para o pipeline."""
    
    def test_full_pipeline_workflow(self):
        """Testa workflow completo do pipeline."""
        with patch('spend_classification.engines.pipeline.RulesEngine') as mock_rules, \
             patch('spend_classification.engines.pipeline.SimilarityClassifier') as mock_similarity, \
             patch('spend_classification.engines.pipeline.ModelAdapter') as mock_adapter:
            
            mock_rules.return_value = MockRulesEngine(should_return_result=True, category="test_label", confidence=0.9)
            mock_similarity.return_value = MockSimilarityEngine()
            mock_adapter.return_value = MockModelAdapter()
            
            pipeline = create_classification_pipeline()
            
            # Testar múltiplas transações
            transactions = [
                ExpenseTransaction(description="test_label Com", amount=44.90, date="2024-01-01"),
                ExpenseTransaction(description="test_label Viagem", amount=25.50, date="2024-01-01"),
                ExpenseTransaction(description="test_label", amount=15.75, date="2024-01-01")
            ]
            
            predictions, elapsed_ms = pipeline.predict_batch(transactions)
            
            # Verificações
            assert len(predictions) == 3
            assert elapsed_ms > 0
            
            # Verificar que todas as predições são válidas
            for i, prediction in enumerate(predictions):
                assert isinstance(prediction, Prediction)
                assert prediction.transaction_id == str(i)
                assert prediction.elapsed_ms > 0
                assert prediction.confidence >= 0.0
                assert prediction.confidence <= 1.0
            
            # Verificar status dos engines
            status = pipeline.get_engine_status()
            assert all(engine in status for engine in ["rules_engine", "similarity_engine", "model_adapter"])
    
    def test_pipeline_with_different_decision_paths(self):
        """Testa pipeline com diferentes caminhos de decisão."""
        with patch('spend_classification.engines.pipeline.RulesEngine') as mock_rules, \
             patch('spend_classification.engines.pipeline.SimilarityClassifier') as mock_similarity, \
             patch('spend_classification.engines.pipeline.ModelAdapter') as mock_adapter:
            
            # Configurar mocks para diferentes cenários
            mock_rules.return_value = MockRulesEngine()
            mock_similarity.return_value = MockSimilarityEngine()
            mock_adapter.return_value = MockModelAdapter()
            
            pipeline = ClassificationPipeline()
            
            # Cenário 1: Rules engine sucesso (se habilitado)
            if pipeline.enable_deterministic_rules:
                mock_rules.return_value.should_return_result = True
                mock_rules.return_value.category = "test_label"
                mock_rules.return_value.confidence = 0.9

                transaction1 = ExpenseTransaction(description="test_label Com", amount=44.90, date="2024-01-01")       
                predictions1, _ = pipeline.predict_batch([transaction1])
                assert predictions1[0].method_used == "rules_engine"
            else:
                # Se rules engine estiver desabilitado, deve usar model adapter
                mock_adapter.return_value.should_return_result = True
                mock_adapter.return_value.label = "test_label"
                mock_adapter.return_value.confidence = 0.9

                transaction1 = ExpenseTransaction(description="test_label Com", amount=44.90, date="2024-01-01")       
                predictions1, _ = pipeline.predict_batch([transaction1])
                assert predictions1[0].method_used == "model_adapter"
            
            # Cenário 2: Similarity engine sucesso (se habilitado)
            mock_rules.return_value.should_return_result = False
            if pipeline.enable_tfidf_similarity:
                mock_similarity.return_value.should_return_result = True
                mock_similarity.return_value.label = "test_label"
                mock_similarity.return_value.score = 0.8
                
                transaction2 = ExpenseTransaction(description="test_label Viagem", amount=25.50, date="2024-01-01")
                predictions2, _ = pipeline.predict_batch([transaction2])
                assert predictions2[0].method_used == "similarity_engine"
            else:
                # Se similarity engine estiver desabilitado, deve usar model adapter
                mock_adapter.return_value.should_return_result = True
                mock_adapter.return_value.label = "test_label"
                mock_adapter.return_value.confidence = 0.8
                
                transaction2 = ExpenseTransaction(description="test_label Viagem", amount=25.50, date="2024-01-01")
                predictions2, _ = pipeline.predict_batch([transaction2])
                assert predictions2[0].method_used == "model_adapter"
            
            # Cenário 3: Model adapter sucesso
            mock_similarity.return_value.should_return_result = False
            mock_adapter.return_value.should_return_result = True
            mock_adapter.return_value.label = "test_label"
            mock_adapter.return_value.confidence = 0.8
            
            transaction3 = ExpenseTransaction(description="test_label", amount=15.75, date="2024-01-01")
            predictions3, _ = pipeline.predict_batch([transaction3])
            assert predictions3[0].method_used == "model_adapter"
            
            # Cenário 4: Fallback
            mock_adapter.return_value.should_return_result = False
            
            transaction4 = ExpenseTransaction(description="Unknown", amount=100.0, date="2024-01-01")
            predictions4, _ = pipeline.predict_batch([transaction4])
            assert predictions4[0].method_used == "fallback"
            assert predictions4[0].label == "duvida"
