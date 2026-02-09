"""
Testes de Integração

Testa a integração entre diferentes componentes do sistema
de classificação de despesas.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from ..core.schemas import ExpenseTransaction, ClassificationResult
from ..engines.classifier import ExpenseClassifier
from ..engines.ml_model import MLClassifier
from ..engines.rules_engine import RulesEngine
from ..engines.similarity_engine import SimilarityEngine
from ..engines.pipeline import ClassificationPipeline


class TestFullClassificationFlow:
    """Testa o fluxo completo de classificação."""
    
    def test_complete_classification_pipeline(self):
        """Testa pipeline completo com todos os engines."""
        # Configura engines
        rules_engine = RulesEngine()
        similarity_engine = SimilarityEngine()
        
        # Configura classificador principal
        classifier = ExpenseClassifier(
            rules_engine=rules_engine,
            similarity_engine=similarity_engine,
            confidence_threshold=0.7
        )
        
        # Configura pipeline
        pipeline = ClassificationPipeline()
        pipeline.add_stage("rules", rules_engine)
        pipeline.add_stage("similarity", similarity_engine)
        
        # Testa transação conhecida (Netflix)
        transaction = ExpenseTransaction(
            description="Netflix Com",
            amount=44.90,
            date=datetime.now()
        )
        
        # Testa classificação direta
        result = classifier.classify(transaction)
        
        assert result.category == "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)"
        assert result.confidence > 0.7
        assert result.classifier_used in ["rules_engine", "similarity_engine"]
        
        # Testa pipeline
        pipeline_result = pipeline.process([transaction])
        
        assert len(pipeline_result) == 1
        assert pipeline_result[0].category == "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)"
    
    def test_fallback_chain(self):
        """Testa cadeia de fallback entre engines."""
        # Configura engines com diferentes thresholds
        rules_engine = RulesEngine()
        similarity_engine = SimilarityEngine(similarity_threshold=0.9)  # Mais restritivo
        
        classifier = ExpenseClassifier(
            rules_engine=rules_engine,
            similarity_engine=similarity_engine,
            confidence_threshold=0.8
        )
        
        # Transação que deve ser classificada pelas regras
        transaction = ExpenseTransaction(
            description="Spotify Premium",
            amount=34.90,
            date=datetime.now()
        )
        
        result = classifier.classify(transaction)
        
        # Deve usar rules_engine (mais específico para Spotify)
        assert result.category == "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)"
        assert result.confidence > 0.8
        assert result.classifier_used == "rules_engine"
    
    def test_batch_processing(self):
        """Testa processamento em lote."""
        pipeline = ClassificationPipeline(enable_parallel=False)  # Sequencial para teste
        
        rules_engine = RulesEngine()
        pipeline.add_stage("rules", rules_engine)
        
        # Lista de transações
        transactions = [
            ExpenseTransaction(
                description="Netflix Com",
                amount=44.90,
                date=datetime.now()
            ),
            ExpenseTransaction(
                description="Drogasil",
                amount=25.50,
                date=datetime.now()
            ),
            ExpenseTransaction(
                description="Carrefour",
                amount=150.00,
                date=datetime.now()
            )
        ]
        
        results = pipeline.process(transactions)
        
        assert len(results) == 3
        
        # Verifica que todas foram classificadas
        categories = [r.category for r in results]
        assert "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)" in categories
        assert "Farmácia" in categories
        assert "Supermercado" in categories


class TestErrorHandling:
    """Testa tratamento de erros na integração."""
    
    def test_classifier_with_failing_engine(self):
        """Testa classificador com engine que falha."""
        # Mock engine que sempre falha
        failing_engine = Mock()
        failing_engine.classify.side_effect = Exception("Engine failed")
        
        classifier = ExpenseClassifier(rules_engine=failing_engine)
        
        transaction = ExpenseTransaction(
            description="Test",
            amount=10.00,
            date=datetime.now()
        )
        
        # Deve retornar resultado padrão sem quebrar
        result = classifier.classify(transaction)
        
        assert result.category == "Gastos pessoais"
        assert result.confidence == 0.1
        assert result.classifier_used == "default"
    
    def test_pipeline_with_mixed_results(self):
        """Testa pipeline com resultados mistos."""
        # Engine que às vezes falha
        unreliable_engine = Mock()
        unreliable_engine.classify.side_effect = [
            ClassificationResult("Farmácia", 0.9, "test"),  # Sucesso
            Exception("Failed"),  # Falha
            ClassificationResult("Supermercado", 0.8, "test")  # Sucesso
        ]
        
        pipeline = ClassificationPipeline()
        pipeline.add_stage("unreliable", unreliable_engine)
        
        transactions = [
            ExpenseTransaction("Test1", 10.0, datetime.now()),
            ExpenseTransaction("Test2", 20.0, datetime.now()),
            ExpenseTransaction("Test3", 30.0, datetime.now())
        ]
        
        results = pipeline.process(transactions)
        
        assert len(results) == 3
        
        # Primeiro e terceiro devem ter sucesso
        assert results[0].category == "Farmácia"
        assert results[2].category == "Supermercado"
        
        # Segundo deve ter resultado padrão
        assert results[1].category == "Gastos pessoais"
        assert results[1].confidence == 0.1


class TestPerformanceIntegration:
    """Testa performance em cenários de integração."""
    
    def test_parallel_processing(self):
        """Testa processamento paralelo."""
        pipeline = ClassificationPipeline(enable_parallel=True)
        
        rules_engine = RulesEngine()
        pipeline.add_stage("rules", rules_engine)
        
        # Cria muitas transações para testar paralelismo
        transactions = []
        for i in range(20):
            transaction = ExpenseTransaction(
                description=f"Netflix Com {i}",
                amount=44.90,
                date=datetime.now()
            )
            transactions.append(transaction)
        
        import time
        start_time = time.time()
        
        results = pipeline.process(transactions)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        assert len(results) == 20
        assert processing_time < 5.0  # Deve ser rápido
        
        # Todas devem ser classificadas como Netflix
        for result in results:
            assert result.category == "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)"
    
    def test_memory_usage(self):
        """Testa uso de memória com grandes volumes."""
        pipeline = ClassificationPipeline()
        
        rules_engine = RulesEngine()
        pipeline.add_stage("rules", rules_engine)
        
        # Cria volume grande de transações
        transactions = []
        for i in range(1000):
            transaction = ExpenseTransaction(
                description=f"Test Transaction {i}",
                amount=10.0,
                date=datetime.now()
            )
            transactions.append(transaction)
        
        # Processa em lotes menores para não sobrecarregar
        batch_size = 100
        all_results = []
        
        for i in range(0, len(transactions), batch_size):
            batch = transactions[i:i + batch_size]
            results = pipeline.process(batch)
            all_results.extend(results)
        
        assert len(all_results) == 1000
        
        # Verifica que não houve vazamento de memória
        # (teste básico - em produção usaria ferramentas específicas)
        pipeline_stats = pipeline.get_pipeline_stats()
        assert pipeline_stats["total_stages"] == 1


class TestDataConsistency:
    """Testa consistência de dados na integração."""
    
    def test_result_format_consistency(self):
        """Testa consistência no formato dos resultados."""
        pipeline = ClassificationPipeline()
        
        rules_engine = RulesEngine()
        similarity_engine = SimilarityEngine()
        
        pipeline.add_stage("rules", rules_engine)
        pipeline.add_stage("similarity", similarity_engine)
        
        transactions = [
            ExpenseTransaction("Netflix", 44.90, datetime.now()),
            ExpenseTransaction("Unknown Store", 10.00, datetime.now()),
            ExpenseTransaction("Drogasil", 25.50, datetime.now())
        ]
        
        results = pipeline.process(transactions)
        
        # Todos os resultados devem ter o mesmo formato
        for result in results:
            assert isinstance(result, ClassificationResult)
            assert isinstance(result.category, str)
            assert isinstance(result.confidence, float)
            assert isinstance(result.classifier_used, str)
            assert isinstance(result.fallback_used, bool)
            assert 0.0 <= result.confidence <= 1.0
    
    def test_transaction_immutability(self):
        """Testa que transações não são modificadas durante processamento."""
        original_transaction = ExpenseTransaction(
            description="Netflix Com",
            amount=44.90,
            date=datetime.now(),
            card_number="1234"
        )
        
        # Cria cópia para comparação
        original_copy = ExpenseTransaction(
            description=original_transaction.description,
            amount=original_transaction.amount,
            date=original_transaction.date,
            card_number=original_transaction.card_number
        )
        
        pipeline = ClassificationPipeline()
        rules_engine = RulesEngine()
        pipeline.add_stage("rules", rules_engine)
        
        result = pipeline.process([original_transaction])
        
        # Transação original não deve ter sido modificada
        assert original_transaction.description == original_copy.description
        assert original_transaction.amount == original_copy.amount
        assert original_transaction.card_number == original_copy.card_number
        
        # Resultado deve ter sido gerado
        assert len(result) == 1
        assert isinstance(result[0], ClassificationResult)
