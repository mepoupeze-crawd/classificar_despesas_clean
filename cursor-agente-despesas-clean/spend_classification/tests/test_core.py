"""
Testes para o módulo core

Testa schemas, constants e contracts do sistema de classificação.
"""

import pytest
from datetime import datetime
from ..core.schemas import (
    ExpenseTransaction,
    ClassificationResult,
    ModelMetrics,
    FeedbackData,
    ProcessingStats,
    TransactionType,
    ExpenseCategory
)
from ..core.constants import CATEGORIES, CONFIDENCE_THRESHOLD, MODEL_PATHS


class TestExpenseTransaction:
    """Testa o schema ExpenseTransaction."""
    
    def test_valid_transaction(self):
        """Testa criação de transação válida."""
        transaction = ExpenseTransaction(
            description="Netflix Com",
            amount=44.90,
            date=datetime.now()
        )
        
        assert transaction.description == "Netflix Com"
        assert transaction.amount == 44.90
        assert transaction.date is not None
    
    def test_invalid_description(self):
        """Testa validação de descrição inválida."""
        with pytest.raises(ValueError, match="Description cannot be empty"):
            ExpenseTransaction(
                description="",
                amount=44.90,
                date=datetime.now()
            )
    
    def test_invalid_amount(self):
        """Testa validação de valor inválido."""
        with pytest.raises(ValueError, match="Amount must be positive"):
            ExpenseTransaction(
                description="Test",
                amount=-10.0,
                date=datetime.now()
            )
    
    def test_optional_fields(self):
        """Testa campos opcionais."""
        transaction = ExpenseTransaction(
            description="Test",
            amount=10.0,
            date=datetime.now(),
            card_number="1234",
            card_holder="João",
            installments=3,
            installment_number=1
        )
        
        assert transaction.card_number == "1234"
        assert transaction.card_holder == "João"
        assert transaction.installments == 3
        assert transaction.installment_number == 1


class TestClassificationResult:
    """Testa o schema ClassificationResult."""
    
    def test_valid_result(self):
        """Testa criação de resultado válido."""
        result = ClassificationResult(
            category="Farmácia",
            confidence=0.85,
            classifier_used="ml_model"
        )
        
        assert result.category == "Farmácia"
        assert result.confidence == 0.85
        assert result.classifier_used == "ml_model"
        assert not result.fallback_used
    
    def test_invalid_confidence(self):
        """Testa validação de confiança inválida."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ClassificationResult(
                category="Test",
                confidence=1.5,
                classifier_used="test"
            )
    
    def test_fallback_result(self):
        """Testa resultado com fallback."""
        result = ClassificationResult(
            category="Supermercado",
            confidence=0.75,
            classifier_used="ai_fallback",
            fallback_used=True,
            ai_context="Contexto da IA"
        )
        
        assert result.fallback_used
        assert result.ai_context == "Contexto da IA"


class TestModelMetrics:
    """Testa o schema ModelMetrics."""
    
    def test_valid_metrics(self):
        """Testa criação de métricas válidas."""
        metrics = ModelMetrics(
            accuracy=0.85,
            precision=0.82,
            recall=0.88,
            f1_score=0.85,
            training_samples=1000,
            test_samples=200,
            training_date=datetime.now()
        )
        
        assert metrics.accuracy == 0.85
        assert metrics.precision == 0.82
        assert metrics.recall == 0.88
        assert metrics.f1_score == 0.85
        assert metrics.training_samples == 1000
        assert metrics.test_samples == 200


class TestFeedbackData:
    """Testa o schema FeedbackData."""
    
    def test_valid_feedback(self):
        """Testa criação de feedback válido."""
        original_result = ClassificationResult(
            category="Farmácia",
            confidence=0.6,
            classifier_used="ml_model"
        )
        
        transaction = ExpenseTransaction(
            description="Drogasil",
            amount=25.50,
            date=datetime.now()
        )
        
        feedback = FeedbackData(
            original_result=original_result,
            transaction=transaction,
            correct_category="Farmácia"
        )
        
        assert feedback.correct_category == "Farmácia"
        assert feedback.original_result.category == "Farmácia"
        assert feedback.transaction.description == "Drogasil"


class TestProcessingStats:
    """Testa o schema ProcessingStats."""
    
    def test_valid_stats(self):
        """Testa criação de estatísticas válidas."""
        stats = ProcessingStats(
            total_transactions=100,
            successful_classifications=95,
            fallback_used_count=5,
            total_processing_time=10.5,
            average_processing_time=0.105,
            category_distribution={"Farmácia": 20, "Supermercado": 30},
            average_confidence=0.82,
            low_confidence_count=3
        )
        
        assert stats.total_transactions == 100
        assert stats.successful_classifications == 95
        assert stats.fallback_used_count == 5
        assert stats.average_confidence == 0.82


class TestEnums:
    """Testa os enums definidos."""
    
    def test_transaction_type_enum(self):
        """Testa enum TransactionType."""
        assert TransactionType.CREDIT == "crédito"
        assert TransactionType.DEBIT == "débito"
    
    def test_expense_category_enum(self):
        """Testa enum ExpenseCategory."""
        assert ExpenseCategory.PHARMACY == "Farmácia"
        assert ExpenseCategory.GROCERY == "Supermercado"


class TestConstants:
    """Testa as constantes definidas."""
    
    def test_categories_list(self):
        """Testa lista de categorias."""
        assert isinstance(CATEGORIES, list)
        assert len(CATEGORIES) > 0
        assert "Farmácia" in CATEGORIES
        assert "Supermercado" in CATEGORIES
    
    def test_confidence_threshold(self):
        """Testa threshold de confiança."""
        assert isinstance(CONFIDENCE_THRESHOLD, float)
        assert 0.0 <= CONFIDENCE_THRESHOLD <= 1.0
    
    def test_model_paths(self):
        """Testa caminhos dos modelos."""
        assert isinstance(MODEL_PATHS, dict)
        assert "natureza_do_gasto" in MODEL_PATHS
        assert MODEL_PATHS["natureza_do_gasto"].endswith(".pkl")
