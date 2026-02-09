"""
Testes unitários para o módulo spend_classification.engines.similarity.
"""

import pytest
import tempfile
import os
import pandas as pd
from unittest.mock import patch, MagicMock

from spend_classification.engines.similarity import SimilarityClassifier, create_similarity_classifier


class TestSimilarityClassifier:
    """Testa a classe SimilarityClassifier."""
    
    def test_initialization_with_existing_csv(self):
        """Testa inicialização com CSV existente."""
        # Criar CSV temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'aonde gastou': ['Netflix Com', 'Drogasil', 'Spotify'],
                'natureza do gasto': ['Gastos com mensalidades', 'Farmácia', 'Gastos com mensalidades']
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path, threshold=0.8)
            assert classifier.is_loaded is True
            assert classifier.threshold == 0.8
            assert len(classifier.data) == 3
            assert classifier.vectorizer is not None
            assert classifier.tfidf_matrix is not None
        finally:
            os.unlink(csv_path)
    
    def test_initialization_without_csv(self):
        """Testa inicialização quando CSV não existe."""
        classifier = SimilarityClassifier("arquivo_inexistente.csv")
        assert classifier.is_loaded is False
        assert classifier.data is None
        assert classifier.vectorizer is None
        assert classifier.tfidf_matrix is None
    
    def test_initialization_with_invalid_csv(self):
        """Testa inicialização com CSV inválido."""
        # Criar CSV sem as colunas necessárias
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'coluna_errada': ['valor1', 'valor2'],
                'outra_coluna': ['categoria1', 'categoria2']
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path)
            assert classifier.is_loaded is False
        finally:
            os.unlink(csv_path)
    
    def test_query_with_identical_text(self):
        """Testa query com texto idêntico ao existente."""
        # Criar CSV temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'aonde gastou': ['Netflix Com', 'Drogasil', 'Spotify'],
                'natureza do gasto': ['Gastos com mensalidades', 'Farmácia', 'Gastos com mensalidades']
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path, threshold=0.5)
            
            # Testar com texto idêntico
            result = classifier.query("Netflix Com")
            assert result is not None
            category, score = result
            assert category == "Gastos com mensalidades"
            assert score >= 0.9  # Deve ser muito alta para texto idêntico
            
            # Testar com texto similar
            result = classifier.query("netflix")
            assert result is not None
            category, score = result
            assert score >= 0.5  # Deve estar acima do threshold
            
        finally:
            os.unlink(csv_path)
    
    def test_query_with_text_below_threshold(self):
        """Testa query com texto que não atinge o threshold."""
        # Criar CSV temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'aonde gastou': ['Netflix Com', 'Drogasil'],
                'natureza do gasto': ['Gastos com mensalidades', 'Farmácia']
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path, threshold=0.9)  # Threshold alto
            
            # Testar com texto completamente diferente
            result = classifier.query("Texto completamente diferente")
            assert result is None
            
        finally:
            os.unlink(csv_path)
    
    def test_query_with_empty_text(self):
        """Testa query com texto vazio."""
        # Criar CSV temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'aonde gastou': ['Netflix Com'],
                'natureza do gasto': ['Gastos com mensalidades']
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path)
            
            # Testar com texto vazio
            assert classifier.query("") is None
            assert classifier.query("   ") is None
            assert classifier.query(None) is None
            
        finally:
            os.unlink(csv_path)
    
    def test_query_when_not_loaded(self):
        """Testa query quando classificador não foi carregado."""
        classifier = SimilarityClassifier("arquivo_inexistente.csv")
        result = classifier.query("Netflix Com")
        assert result is None
    
    def test_get_stats_when_loaded(self):
        """Testa get_stats quando classificador está carregado."""
        # Criar CSV temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'aonde gastou': ['Netflix Com', 'Drogasil', 'Spotify'],
                'natureza do gasto': ['Gastos com mensalidades', 'Farmácia', 'Gastos com mensalidades']
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path, threshold=0.7)
            stats = classifier.get_stats()
            
            assert stats['loaded'] is True
            assert stats['records'] == 3
            assert stats['features'] > 0
            assert stats['threshold'] == 0.7
            assert stats['csv_path'] == csv_path
            
        finally:
            os.unlink(csv_path)
    
    def test_get_stats_when_not_loaded(self):
        """Testa get_stats quando classificador não foi carregado."""
        classifier = SimilarityClassifier("arquivo_inexistente.csv")
        stats = classifier.get_stats()
        
        assert stats['loaded'] is False
        assert stats['records'] == 0
        assert stats['features'] == 0
        assert stats['threshold'] == 0.7
    
    def test_reload(self):
        """Testa recarregamento do classificador."""
        # Criar CSV inicial
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'aonde gastou': ['Netflix Com'],
                'natureza do gasto': ['Gastos com mensalidades']
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path)
            assert classifier.is_loaded is True
            assert len(classifier.data) == 1
            
            # Atualizar CSV com mais dados
            df = pd.DataFrame({
                'aonde gastou': ['Netflix Com', 'Drogasil', 'Spotify'],
                'natureza do gasto': ['Gastos com mensalidades', 'Farmácia', 'Gastos com mensalidades']
            })
            df.to_csv(csv_path, index=False)
            
            # Recarregar
            success = classifier.reload()
            assert success is True
            assert len(classifier.data) == 3
            
        finally:
            os.unlink(csv_path)
    
    def test_threshold_from_environment(self):
        """Testa configuração de threshold via variável de ambiente."""
        with patch.dict(os.environ, {'SIMILARITY_THRESHOLD': '0.85'}):
            classifier = SimilarityClassifier("arquivo_inexistente.csv")
            assert classifier.threshold == 0.85
    
    def test_case_insensitive_matching(self):
        """Testa que a busca é case-insensitive."""
        # Criar CSV temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'aonde gastou': ['Netflix Com'],
                'natureza do gasto': ['Gastos com mensalidades']
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path, threshold=0.5)
            
            # Testar com diferentes casos
            result1 = classifier.query("netflix com")
            result2 = classifier.query("NETFLIX COM")
            result3 = classifier.query("Netflix Com")
            
            assert result1 is not None
            assert result2 is not None
            assert result3 is not None
            
            # Todos devem ter o mesmo resultado
            assert result1[0] == result2[0] == result3[0]
            
        finally:
            os.unlink(csv_path)


class TestCreateSimilarityClassifier:
    """Testa a função de conveniência create_similarity_classifier."""
    
    def test_create_classifier(self):
        """Testa criação de classificador via função de conveniência."""
        classifier = create_similarity_classifier("arquivo_inexistente.csv", 0.8)
        assert isinstance(classifier, SimilarityClassifier)
        assert classifier.threshold == 0.8
        assert classifier.csv_path == "arquivo_inexistente.csv"
    
    def test_default_parameters(self):
        """Testa parâmetros padrão da função de conveniência."""
        classifier = create_similarity_classifier()
        assert classifier.csv_path == "modelo_despesas_completo.csv"
        assert classifier.threshold == 0.70


class TestSimilarityIntegration:
    """Testes de integração para o módulo de similaridade."""
    
    def test_complete_workflow(self):
        """Testa workflow completo com dados realistas."""
        # Criar CSV temporário com dados realistas
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'aonde gastou': [
                    'Netflix Com',
                    'Drogasil',
                    'Spotify',
                    'Carrefour',
                    '99app *99app'
                ],
                'natureza do gasto': [
                    'Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)',
                    'Farmácia',
                    'Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)',
                    'Supermercado',
                    'Combustível/ Passagens/ Uber / Sem Parar'
                ]
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path, threshold=0.6)
            
            # Testar diferentes tipos de queries
            test_cases = [
                ("Netflix Com", "Gastos com mensalidades"),
                ("Drogasil", "Farmácia"),
                ("99app", "Combustível/ Passagens/ Uber / Sem Parar"),
                ("Carrefour", "Supermercado")
            ]
            
            for query_text, expected_category in test_cases:
                result = classifier.query(query_text)
                assert result is not None, f"Query '{query_text}' não retornou resultado"
                category, score = result
                assert expected_category in category, f"Esperado '{expected_category}', obtido '{category}'"
                assert score >= 0.6, f"Score {score} abaixo do threshold"
            
        finally:
            os.unlink(csv_path)
    
    def test_error_handling(self):
        """Testa tratamento de erros."""
        # Criar CSV temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'aonde gastou': ['Netflix Com'],
                'natureza do gasto': ['Gastos com mensalidades']
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path)
            
            # Testar com diferentes tipos de entrada problemática
            assert classifier.query("") is None
            assert classifier.query("   ") is None
            assert classifier.query(None) is None
            
        finally:
            os.unlink(csv_path)


class TestSimilarityEdgeCases:
    """Testa casos extremos e edge cases."""
    
    def test_empty_csv(self):
        """Testa comportamento com CSV vazio."""
        # Criar CSV vazio (apenas cabeçalho)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame(columns=['aonde gastou', 'natureza do gasto'])
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path)
            # Deve falhar ao carregar dados vazios
            assert classifier.is_loaded is False
            
        finally:
            os.unlink(csv_path)
    
    def test_single_record_csv(self):
        """Testa comportamento com CSV de um único registro."""
        # Criar CSV com um registro
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'aonde gastou': ['Netflix Com'],
                'natureza do gasto': ['Gastos com mensalidades']
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path)
            assert classifier.is_loaded is True
            
            # Deve funcionar com um registro
            result = classifier.query("Netflix Com")
            assert result is not None
            category, score = result
            assert category == "Gastos com mensalidades"
            
        finally:
            os.unlink(csv_path)
    
    def test_very_high_threshold(self):
        """Testa comportamento com threshold muito alto."""
        # Criar CSV temporário
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            df = pd.DataFrame({
                'aonde gastou': ['Netflix Com', 'Drogasil'],
                'natureza do gasto': ['Gastos com mensalidades', 'Farmácia']
            })
            df.to_csv(f.name, index=False)
            csv_path = f.name
        
        try:
            classifier = SimilarityClassifier(csv_path, threshold=0.99)  # Threshold muito alto
            
            # Mesmo com texto idêntico, pode não atingir threshold tão alto
            result = classifier.query("Netflix Com")
            if result is not None:
                category, score = result
                assert score >= 0.99
            
        finally:
            os.unlink(csv_path)

