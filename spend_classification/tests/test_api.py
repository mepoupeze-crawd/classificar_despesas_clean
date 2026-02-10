#!/usr/bin/env python3
"""
Testes de API para o microserviço FastAPI

Testa os endpoints usando TestClient do FastAPI sem necessidade
de servidor externo.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock
from datetime import datetime

# Importa a aplicação FastAPI
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.main import app
from spend_classification.core.schemas import ExpenseTransaction, Prediction

# Cliente de teste
client = TestClient(app)

@pytest.fixture
def sample_transactions():
    """Fixture com transações de exemplo para teste."""
    return [
        {
            "id": "test_1",
            "description": "Netflix Com",
            "amount": 44.90,
            "date": "2024-01-01T00:00:00",
            "card_holder": "CC - Aline Silva"
        },
        {
            "id": "test_2",
            "description": "Uber Viagem",
            "amount": 25.50,
            "date": "2024-01-01T00:00:00",
            "card_holder": "Final 1234 - Joao Santos"
        },
        {
            "id": "test_3",
            "description": "Transacao Desconhecida XYZ",
            "amount": 15.75,
            "date": "2024-01-01T00:00:00",
            "card_holder": "Final 9999 - Aline Silva"
        }
    ]

@pytest.fixture
def mock_predictions():
    """Fixture com predições mock para teste."""
    return [
        Prediction(
            label="débito",
            confidence=0.950,
            method_used="rules_engine",
            elapsed_ms=2.5,
            transaction_id="test_1",
            raw_prediction={"rule_type": "card_tipo"}
        ),
        Prediction(
            label="Combustível/ Passagens/ Uber / Sem Parar",
            confidence=0.900,
            method_used="rules_engine",
            elapsed_ms=1.2,
            transaction_id="test_2",
            raw_prediction={"rule_type": "description"}
        ),
        Prediction(
            label="duvida",
            confidence=0.300,
            method_used="fallback",
            elapsed_ms=0.8,
            transaction_id="test_3",
            raw_prediction={"reason": "no_engine_met_threshold"}
        )
    ]

class TestHealthEndpoint:
    """Testes para o endpoint de health check."""
    
    def test_health_check_success(self):
        """Testa se o health check retorna 200 e status ok."""
        response = client.get("/healthz")
        
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

class TestClassifyEndpoint:
    """Testes para o endpoint de classificação."""
    
    @patch('app.main.pipeline.predict_batch')
    def test_classify_success_with_rules_engine(self, mock_predict_batch, sample_transactions, mock_predictions):
        """Testa classificação bem-sucedida com Rules Engine."""
        # Mock do pipeline
        mock_predict_batch.return_value = (mock_predictions, 5.5)
        
        response = client.post("/v1/classify", json=sample_transactions)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validações básicas
        assert "predictions" in data
        assert "elapsed_ms" in data
        assert "total_transactions" in data
        
        # Validações específicas
        assert len(data["predictions"]) == 3
        assert data["total_transactions"] == 3
        assert data["elapsed_ms"] > 0
        
        # Validações das predições
        for pred in data["predictions"]:
            assert "label" in pred
            assert "confidence" in pred
            assert "method_used" in pred
            assert "elapsed_ms" in pred
            assert "transaction_id" in pred
            assert "raw_prediction" in pred
            
            # Validações de tipos e ranges
            assert isinstance(pred["label"], str)
            assert isinstance(pred["confidence"], (int, float))
            assert isinstance(pred["method_used"], str)
            assert isinstance(pred["elapsed_ms"], (int, float))
            assert isinstance(pred["transaction_id"], str)
            assert isinstance(pred["raw_prediction"], dict)
            
            # Validações de ranges
            assert 0.0 <= pred["confidence"] <= 1.0
            assert pred["elapsed_ms"] > 0
    
    @patch('app.main.pipeline.predict_batch')
    def test_classify_with_similarity_engine(self, mock_predict_batch, sample_transactions):
        """Testa classificação usando Similarity Engine."""
        # Mock para similarity engine
        similarity_predictions = [
            Prediction(
                label="Supermercado",
                confidence=0.85,
                method_used="similarity_engine",
                elapsed_ms=3.2,
                transaction_id="test_1",
                raw_prediction={"score": 0.85}
            ),
            Prediction(
                label="Transporte",
                confidence=0.75,
                method_used="similarity_engine", 
                elapsed_ms=2.1,
                transaction_id="test_2",
                raw_prediction={"score": 0.75}
            ),
            Prediction(
                label="duvida",
                confidence=0.30,
                method_used="fallback",
                elapsed_ms=0.5,
                transaction_id="test_3",
                raw_prediction={"reason": "no_match"}
            )
        ]
        
        mock_predict_batch.return_value = (similarity_predictions, 6.8)
        
        response = client.post("/v1/classify", json=sample_transactions)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica que similarity_engine foi usado
        similarity_count = sum(1 for pred in data["predictions"] if pred["method_used"] == "similarity_engine")
        assert similarity_count >= 1
        
        # Validações de confiança
        for pred in data["predictions"]:
            assert 0.0 <= pred["confidence"] <= 1.0
            if pred["method_used"] == "similarity_engine":
                assert pred["confidence"] >= 0.70  # Threshold padrão
    
    @patch('app.main.pipeline.predict_batch')
    def test_classify_with_model_adapter(self, mock_predict_batch, sample_transactions):
        """Testa classificação usando Model Adapter."""
        # Mock para model adapter
        model_predictions = [
            Prediction(
                label="Gastos com mensalidades",
                confidence=0.92,
                method_used="model_adapter",
                elapsed_ms=15.3,
                transaction_id="test_1",
                raw_prediction={"confidence": 0.92}
            ),
            Prediction(
                label="Combustível/ Passagens/ Uber / Sem Parar",
                confidence=0.88,
                method_used="model_adapter",
                elapsed_ms=12.7,
                transaction_id="test_2", 
                raw_prediction={"confidence": 0.88}
            ),
            Prediction(
                label="duvida",
                confidence=0.30,
                method_used="fallback",
                elapsed_ms=1.2,
                transaction_id="test_3",
                raw_prediction={"reason": "low_confidence"}
            )
        ]
        
        mock_predict_batch.return_value = (model_predictions, 29.2)
        
        response = client.post("/v1/classify", json=sample_transactions)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verifica que model_adapter foi usado
        model_count = sum(1 for pred in data["predictions"] if pred["method_used"] == "model_adapter")
        assert model_count >= 1
        
        # Validações de confiança para model adapter
        for pred in data["predictions"]:
            assert 0.0 <= pred["confidence"] <= 1.0
            if pred["method_used"] == "model_adapter":
                assert pred["confidence"] >= 0.70  # Threshold padrão
    
    def test_classify_empty_list(self):
        """Testa erro com lista vazia de transações."""
        response = client.post("/v1/classify", json=[])
        
        assert response.status_code == 400
        assert "não pode estar vazia" in response.json()["detail"]
    
    def test_classify_invalid_payload(self):
        """Testa erro com payload inválido."""
        invalid_transactions = [
            {
                "description": "Teste",
                "amount": -10.0,  # Valor negativo inválido
                "date": "2024-01-01T00:00:00"
            }
        ]
        
        response = client.post("/v1/classify", json=invalid_transactions)
        
        # Deve retornar erro de validação (422) ou erro interno (500)
        assert response.status_code in [422, 500]
    
    def test_classify_missing_required_fields(self):
        """Testa erro com campos obrigatórios ausentes."""
        invalid_transactions = [
            {
                "description": "Teste",
                # amount ausente
                "date": "2024-01-01T00:00:00"
            }
        ]
        
        response = client.post("/v1/classify", json=invalid_transactions)
        
        assert response.status_code == 422
    
    def test_classify_invalid_date_format(self):
        """Testa erro com formato de data inválido."""
        invalid_transactions = [
            {
                "description": "Teste",
                "amount": 10.0,
                "date": "data-invalida"
            }
        ]
        
        response = client.post("/v1/classify", json=invalid_transactions)
        
        # Deve retornar erro de validação ou erro interno
        assert response.status_code in [422, 500]
    
    @patch('app.main.pipeline.predict_batch')
    def test_classify_pipeline_error(self, mock_predict_batch, sample_transactions):
        """Testa tratamento de erro do pipeline."""
        # Mock que gera erro
        mock_predict_batch.side_effect = Exception("Erro simulado no pipeline")
        
        response = client.post("/v1/classify", json=sample_transactions)
        
        assert response.status_code == 500
        assert "Erro na classificação" in response.json()["detail"]

class TestRootEndpoint:
    """Testes para o endpoint raiz."""
    
    def test_root_endpoint(self):
        """Testa o endpoint raiz com informações do serviço."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Validações básicas
        assert "service" in data
        assert "version" in data
        assert "status" in data
        assert "thresholds" in data
        
        # Validações específicas
        assert data["service"] == "Expense Classification API"
        assert data["version"] == "1.0.0"
        assert data["status"] == "running"
        
        # Validações dos thresholds
        assert "similarity_threshold" in data["thresholds"]
        assert "model_threshold" in data["thresholds"]
        assert isinstance(data["thresholds"]["similarity_threshold"], (int, float))
        assert isinstance(data["thresholds"]["model_threshold"], (int, float))

class TestAPIIntegration:
    """Testes de integração da API."""
    
    @patch('app.main.pipeline.predict_batch')
    def test_full_classification_workflow(self, mock_predict_batch, sample_transactions, mock_predictions):
        """Testa workflow completo de classificação."""
        # Mock do pipeline
        mock_predict_batch.return_value = (mock_predictions, 8.5)
        
        # 1. Health check
        health_response = client.get("/healthz")
        assert health_response.status_code == 200
        
        # 2. Informações do serviço
        info_response = client.get("/")
        assert info_response.status_code == 200
        
        # 3. Classificação
        classify_response = client.post("/v1/classify", json=sample_transactions)
        assert classify_response.status_code == 200
        
        # Verifica que o pipeline foi chamado corretamente
        mock_predict_batch.assert_called_once()
        
        # Verifica que as transações foram convertidas corretamente
        called_transactions = mock_predict_batch.call_args[0][0]
        assert len(called_transactions) == 3
        assert all(isinstance(t, ExpenseTransaction) for t in called_transactions)
    
    @patch('app.main.pipeline.predict_batch')
    def test_performance_metrics(self, mock_predict_batch, sample_transactions, mock_predictions):
        """Testa se as métricas de performance estão corretas."""
        # Mock com tempo específico
        mock_predict_batch.return_value = (mock_predictions, 12.5)
        
        response = client.post("/v1/classify", json=sample_transactions)
        
        assert response.status_code == 200
        data = response.json()
        
        # Validações de performance
        assert data["elapsed_ms"] > 0  # Tempo deve ser positivo
        assert data["total_transactions"] == 3
        
        # Validações individuais
        for pred in data["predictions"]:
            assert pred["elapsed_ms"] > 0
            # Note: elapsed_ms individual pode ser maior que o total devido ao timing

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
