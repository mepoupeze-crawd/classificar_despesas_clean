"""
Teste de Fumaça

Teste básico que verifica se todos os módulos podem ser importados
corretamente sem erros. Este é o teste mais fundamental do sistema.
"""

import pytest
import sys
import importlib


class TestModuleImports:
    """Testa importação de todos os módulos do sistema."""
    
    def test_core_imports(self):
        """Testa importação do módulo core."""
        try:
            from spend_classification.core import (
                contracts,
                schemas,
                constants
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Falha ao importar módulos core: {e}")
    
    def test_engines_imports(self):
        """Testa importação do módulo engines."""
        try:
            from spend_classification.engines import (
                rules_engine,
                similarity,
                model_adapter,
                pipeline,
                rules
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Falha ao importar módulos engines: {e}")
    
    def test_main_module_import(self):
        """Testa importação do módulo principal."""
        try:
            import spend_classification
            assert hasattr(spend_classification, '__version__')
            assert spend_classification.__version__ == "1.0.0"
        except ImportError as e:
            pytest.fail(f"Falha ao importar módulo principal: {e}")
    
    def test_schemas_import(self):
        """Testa importação de schemas específicos."""
        try:
            from spend_classification.core.schemas import (
                ExpenseTransaction,
                ClassificationResult,
                ModelMetrics,
                FeedbackData,
                ProcessingStats,
                TransactionType,
                ExpenseCategory
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Falha ao importar schemas: {e}")
    
    def test_contracts_import(self):
        """Testa importação de contratos."""
        try:
            from spend_classification.core.contracts import (
                ClassifierInterface,
                ModelInterface,
                PipelineInterface,
                FeedbackInterface
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Falha ao importar contratos: {e}")
    
    def test_constants_import(self):
        """Testa importação de constantes."""
        try:
            from spend_classification.core.constants import (
                CATEGORIES,
                CONFIDENCE_THRESHOLD,
                MODEL_PATHS,
                API_CONFIG
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Falha ao importar constantes: {e}")
    
    def test_engines_import(self):
        """Testa importação de engines específicos."""
        try:
            from spend_classification.engines import (
                RulesEngine,
                SimilarityClassifier,
                ModelAdapter,
                ClassificationPipeline
            )
            assert True
        except ImportError as e:
            pytest.fail(f"Falha ao importar engines: {e}")


class TestBasicInstantiation:
    """Testa instanciação básica dos componentes principais."""
    
    def test_expense_transaction_creation(self):
        """Testa criação básica de ExpenseTransaction."""
        try:
            from spend_classification.core.schemas import ExpenseTransaction
            from datetime import datetime
            
            transaction = ExpenseTransaction(
                description="Test Transaction",
                amount=10.0,
                date=datetime.now()
            )
            
            assert transaction.description == "Test Transaction"
            assert transaction.amount == 10.0
            assert transaction.date is not None
            
        except Exception as e:
            pytest.fail(f"Falha ao criar ExpenseTransaction: {e}")
    
    def test_classification_result_creation(self):
        """Testa criação básica de ClassificationResult."""
        try:
            from spend_classification.core.schemas import ClassificationResult
            
            result = ClassificationResult(
                category="Test Category",
                confidence=0.8,
                classifier_used="test_classifier"
            )
            
            assert result.category == "Test Category"
            assert result.confidence == 0.8
            assert result.classifier_used == "test_classifier"
            
        except Exception as e:
            pytest.fail(f"Falha ao criar ClassificationResult: {e}")
    
    def test_rules_engine_instantiation(self):
        """Testa instanciação básica do RulesEngine."""
        try:
            from spend_classification.engines.rules_engine import RulesEngine
            
            engine = RulesEngine()
            
            assert engine is not None
            assert hasattr(engine, 'rules')
            assert len(engine.rules) > 0  # Deve ter regras padrão
            
        except Exception as e:
            pytest.fail(f"Falha ao instanciar RulesEngine: {e}")
    
    def test_similarity_classifier_instantiation(self):
        """Testa instanciação básica do SimilarityClassifier."""
        try:
            from spend_classification.engines.similarity import SimilarityClassifier
            
            classifier = SimilarityClassifier("modelo_despesas_completo.csv")
            
            assert classifier is not None
            assert hasattr(classifier, 'is_loaded')
            
        except Exception as e:
            pytest.fail(f"Falha ao instanciar SimilarityClassifier: {e}")
    
    def test_pipeline_instantiation(self):
        """Testa instanciação básica do ClassificationPipeline."""
        try:
            from spend_classification.engines.pipeline import ClassificationPipeline
            
            pipeline = ClassificationPipeline()
            
            assert pipeline is not None
            assert hasattr(pipeline, 'rules_engine')
            assert hasattr(pipeline, 'similarity_engine')
            assert hasattr(pipeline, 'model_adapter')
            
        except Exception as e:
            pytest.fail(f"Falha ao instanciar ClassificationPipeline: {e}")
    
    def test_model_adapter_instantiation(self):
        """Testa instanciação básica do ModelAdapter."""
        try:
            from spend_classification.engines.model_adapter import ModelAdapter
            
            adapter = ModelAdapter()
            
            assert adapter is not None
            assert hasattr(adapter, 'is_loaded')
            assert hasattr(adapter, 'predict_batch')
            
        except Exception as e:
            pytest.fail(f"Falha ao instanciar ModelAdapter: {e}")


class TestConstantsValidation:
    """Testa validação das constantes do sistema."""
    
    def test_categories_not_empty(self):
        """Testa que a lista de categorias não está vazia."""
        try:
            from spend_classification.core.constants import CATEGORIES
            
            assert isinstance(CATEGORIES, list)
            assert len(CATEGORIES) > 0
            assert "Farmácia" in CATEGORIES
            assert "Supermercado" in CATEGORIES
            
        except Exception as e:
            pytest.fail(f"Falha ao validar categorias: {e}")
    
    def test_confidence_threshold_valid(self):
        """Testa que o threshold de confiança é válido."""
        try:
            from spend_classification.core.constants import CONFIDENCE_THRESHOLD
            
            assert isinstance(CONFIDENCE_THRESHOLD, float)
            assert 0.0 <= CONFIDENCE_THRESHOLD <= 1.0
            
        except Exception as e:
            pytest.fail(f"Falha ao validar threshold de confiança: {e}")
    
    def test_model_paths_format(self):
        """Testa formato dos caminhos dos modelos."""
        try:
            from spend_classification.core.constants import MODEL_PATHS
            
            assert isinstance(MODEL_PATHS, dict)
            assert "natureza_do_gasto" in MODEL_PATHS
            assert MODEL_PATHS["natureza_do_gasto"].endswith(".pkl")
            
        except Exception as e:
            pytest.fail(f"Falha ao validar caminhos dos modelos: {e}")


class TestBasicFunctionality:
    """Testa funcionalidades básicas do sistema."""
    
    def test_rules_engine_basic_classification(self):
        """Testa classificação básica com RulesEngine."""
        try:
            from spend_classification.engines.rules_engine import RulesEngine
            from spend_classification.core.schemas import ExpenseTransaction
            from datetime import datetime
            
            engine = RulesEngine()
            transaction = ExpenseTransaction(
                description="Netflix Com",
                amount=44.90,
                date=datetime.now()
            )
            
            result = engine.classify(transaction)
            
            assert result is not None
            assert result.category is not None
            assert 0.0 <= result.confidence <= 1.0
            
        except Exception as e:
            pytest.fail(f"Falha na classificação básica: {e}")
    
    def test_similarity_classifier_basic_query(self):
        """Testa query básica com SimilarityClassifier."""
        try:
            from spend_classification.engines.similarity import SimilarityClassifier
            
            classifier = SimilarityClassifier("modelo_despesas_completo.csv")
            
            # Testa query mesmo se não estiver carregado
            result = classifier.query("Netflix")
            
            # Resultado pode ser None se não carregado, mas não deve quebrar
            assert result is None or isinstance(result, tuple)
            
        except Exception as e:
            pytest.fail(f"Falha na query de similaridade: {e}")
    
    def test_pipeline_basic_processing(self):
        """Testa processamento básico com Pipeline."""
        try:
            from spend_classification.engines.pipeline import ClassificationPipeline
            from spend_classification.core.schemas import ExpenseTransaction
            from datetime import datetime
            
            pipeline = ClassificationPipeline()
            
            transaction = ExpenseTransaction(
                description="Netflix Com",
                amount=44.90,
                date=datetime.now()
            )
            
            predictions, elapsed_ms = pipeline.predict_batch([transaction])
            
            assert len(predictions) == 1
            assert predictions[0].label is not None
            assert 0.0 <= predictions[0].confidence <= 1.0
            assert elapsed_ms >= 0
            
        except Exception as e:
            pytest.fail(f"Falha no processamento básico do pipeline: {e}")


class TestDependencies:
    """Testa dependências externas."""
    
    def test_pandas_available(self):
        """Testa se pandas está disponível."""
        try:
            import pandas as pd
            assert True
        except ImportError:
            pytest.fail("pandas não está disponível")
    
    def test_sklearn_available(self):
        """Testa se scikit-learn está disponível."""
        try:
            import sklearn
            assert True
        except ImportError:
            pytest.fail("scikit-learn não está disponível")
    
    def test_pydantic_available(self):
        """Testa se pydantic está disponível."""
        try:
            import pydantic
            assert True
        except ImportError:
            pytest.fail("pydantic não está disponível")
    
    def test_optional_dependencies(self):
        """Testa dependências opcionais."""
        # Testa OpenAI (opcional)
        try:
            import openai
            assert True
        except ImportError:
            # OpenAI é opcional, então não deve falhar o teste
            pass
        
        # Testa requests (deve estar disponível)
        try:
            import requests
            assert True
        except ImportError:
            pytest.fail("requests não está disponível")


def test_system_health():
    """Teste de saúde geral do sistema."""
    try:
        # Importa módulos principais
        import spend_classification
        from spend_classification.core import schemas, constants
        from spend_classification.engines import rules_engine, pipeline
        
        # Testa instanciação básica
        from spend_classification.core.schemas import ExpenseTransaction
        from datetime import datetime
        
        transaction = ExpenseTransaction(
            description="System Health Test",
            amount=1.0,
            date=datetime.now()
        )
        
        # Testa classificação básica
        rules_engine = rules_engine.RulesEngine()
        result = rules_engine.classify(transaction)
        
        # Verifica resultado básico
        assert result is not None
        assert hasattr(result, 'category')
        assert hasattr(result, 'confidence')
        
        print("✅ Sistema de classificação de despesas está funcionando corretamente!")
        
    except Exception as e:
        pytest.fail(f"Sistema não está funcionando corretamente: {e}")
