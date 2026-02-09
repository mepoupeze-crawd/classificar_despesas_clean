#!/usr/bin/env python3
"""
Testes para a API de Feedback

Testa os endpoints de feedback usando TestClient do FastAPI sem necessidade
de servidor externo. Inclui testes de criação, append, validação, mapeamento
e concorrência.
"""

import pytest
import tempfile
import os
import csv
from pathlib import Path
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch

# Importa a aplicação FastAPI
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.main import app
from app.services.feedback_store import FeedbackStore


class TestFeedbackAPI:
    """Classe de testes para a API de feedback."""
    
    @pytest.fixture
    def client(self):
        """Fixture para criar cliente de teste."""
        return TestClient(app)
    
    @pytest.fixture
    def temp_dir(self):
        """Fixture para criar diretório temporário para testes."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Limpar diretório após teste
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_feedback_dir(self, temp_dir):
        """Fixture para mockar FEEDBACK_DIR durante os testes."""
        # Usar o diretório padrão 'feedbacks' mas limpar após os testes
        feedback_dir = "feedbacks"
        yield feedback_dir
        
        # Limpar arquivos de teste criados
        import glob
        test_files = glob.glob(os.path.join(feedback_dir, "feedback_*.csv"))
        for file in test_files:
            try:
                os.remove(file)
            except:
                pass
    
    def get_today_filename(self):
        """Obtém nome do arquivo para hoje."""
        return datetime.now().strftime("feedback_%Y-%m-%d.csv")
    
    def get_test_filename(self):
        """Obtém nome do arquivo para testes."""
        return f"feedback_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    def count_csv_rows(self, filepath):
        """Conta linhas em arquivo CSV."""
        if not os.path.exists(filepath):
            return 0
        
        with open(filepath, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            return sum(1 for _ in reader)
    
    def read_csv_content(self, filepath):
        """Lê conteúdo do arquivo CSV."""
        if not os.path.exists(filepath):
            return []
        
        with open(filepath, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f)
            return list(reader)
    
    def test_create_new_file(self, client, mock_feedback_dir):
        """
        Teste 1: Criação de arquivo novo
        
        Dado payload com 1 item válido
        Quando POST /v1/feedback
        Então status 201, saved_rows=1 e arquivo criado com cabeçalho correto e 1 linha
        """
        # Arrange
        payload = {
            "feedback": {
                "transactionId": "tx_test_001",
                "description": "Netflix Com",
                "amount": 44.90,
                "date": "2024-01-01T00:00:00Z",
                "source": "crédito",
                "card": "Final 8073 - JOAO G B CALICE",
                "category": "Entretenimento",
                "parcelas": 1,
                "modelVersion": "v1.2.0"
            }
        }
        
        # Mockar o nome do arquivo para usar um nome único
        test_filename = f"feedback_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        expected_filepath = os.path.join("feedbacks", test_filename)
        
        # Mockar o método que gera o nome do arquivo
        from app.services.feedback_store import FeedbackStore
        with patch.object(FeedbackStore, '_get_today_filename', return_value=test_filename):
            # Act
            response = client.post("/v1/feedback", json=payload)
            
            # Assert
            assert response.status_code == 201
            
            response_data = response.json()
            assert response_data["saved_rows"] == 1
            # Verificar que o caminho contém o arquivo esperado
            assert response_data["file_path"].endswith(expected_filepath.replace("/", os.sep))
            
            # Verificar colunas esperadas
            expected_columns = [
                "Aonde Gastou", "Natureza do Gasto", "Valor Total", "Parcelas",
                "No da Parcela", "Valor Unitário", "tipo", "Comp", "Data",
                "cartao", "transactionId", "modelVersion", "createdAt", "flux"
            ]
            assert response_data["columns"] == expected_columns
            
            # Verificar arquivo criado
            assert os.path.exists(expected_filepath)
            
            # Verificar conteúdo do arquivo
            content = self.read_csv_content(expected_filepath)
            assert len(content) == 2  # Cabeçalho + 1 linha de dados
            
            # Verificar cabeçalho
            assert content[0] == expected_columns
            
            # Verificar dados
            data_row = content[1]
            assert data_row[0] == "Netflix Com"  # Aonde Gastou
            assert data_row[1] == "Entretenimento"  # Natureza do Gasto
            assert data_row[2] == "44.9"  # Valor Total
            assert data_row[3] == "1"  # Parcelas
            assert data_row[4] == ""  # No da Parcela (vazio)
            assert data_row[5] == "44.9"  # Valor Unitário
            assert data_row[6] == "crédito"  # tipo
            assert data_row[7] == ""  # Comp (vazio)
            assert data_row[8] == "2024-01-01T00:00:00Z"  # Data
            assert data_row[9] == "Final 8073 - JOAO G B CALICE"  # cartao
            assert data_row[10] == "tx_test_001"  # transactionId
            assert data_row[11] == "v1.2.0"  # modelVersion
            assert data_row[12] != ""  # createdAt (preenchido automaticamente)
            assert data_row[13] == ""  # flux (vazio)
            
            print(f"✅ Arquivo criado: {expected_filepath}")
    
    def test_append_existing_file(self, client, mock_feedback_dir):
        """
        Teste 2: Append em arquivo existente
        
        Dado payload com 2 itens válidos
        Quando POST /v1/feedback
        Então status 201, saved_rows=2 e arquivo passa a conter +2 linhas
        """
        # Arrange - Primeiro criar arquivo com 1 item
        initial_payload = {
            "feedback": {
                "transactionId": "tx_initial_001",
                "description": "Item Inicial",
                "amount": 10.00,
                "date": "2024-01-01T00:00:00Z"
            }
        }
        
        response1 = client.post("/v1/feedback", json=initial_payload)
        assert response1.status_code == 201
        assert response1.json()["saved_rows"] == 1
        
        expected_filename = self.get_today_filename()
        expected_filepath = os.path.join("feedbacks", expected_filename)
        
        # Verificar contagem inicial
        initial_rows = self.count_csv_rows(expected_filepath)
        assert initial_rows == 2  # Cabeçalho + 1 linha
        
        # Arrange - Payload com 2 itens para append
        append_payload = {
            "feedback": [
                {
                    "transactionId": "tx_append_001",
                    "description": "Item Append 1",
                    "amount": 20.00,
                    "date": "2024-01-02T00:00:00Z",
                    "category": "Categoria 1",
                    "parcelas": 2,
                    "numero_parcela": 1
                },
                {
                    "transactionId": "tx_append_002",
                    "description": "Item Append 2",
                    "amount": 30.00,
                    "date": "2024-01-03T00:00:00Z",
                    "category": "Categoria 2",
                    "parcelas": 3,
                    "numero_parcela": 2
                }
            ]
        }
        
        # Act
        response2 = client.post("/v1/feedback", json=append_payload)
        
        # Assert
        assert response2.status_code == 201
        
        response_data = response2.json()
        assert response_data["saved_rows"] == 2
        assert response_data["file_path"] == expected_filepath
        
        # Verificar contagem final
        final_rows = self.count_csv_rows(expected_filepath)
        assert final_rows == 4  # Cabeçalho + 3 linhas (1 inicial + 2 append)
        
        # Verificar conteúdo das novas linhas
        content = self.read_csv_content(expected_filepath)
        
        # Verificar segunda linha (primeiro item do append)
        append_row_1 = content[2]
        assert append_row_1[0] == "Item Append 1"  # Aonde Gastou
        assert append_row_1[1] == "Categoria 1"  # Natureza do Gasto
        assert append_row_1[2] == "40.0"  # Valor Total (20.00 * 2 parcelas)
        assert append_row_1[3] == "2"  # Parcelas
        assert append_row_1[4] == "1"  # No da Parcela
        
        # Verificar terceira linha (segundo item do append)
        append_row_2 = content[3]
        assert append_row_2[0] == "Item Append 2"  # Aonde Gastou
        assert append_row_2[1] == "Categoria 2"  # Natureza do Gasto
        assert append_row_2[2] == "90.0"  # Valor Total (30.00 * 3 parcelas)
        assert append_row_2[3] == "3"  # Parcelas
        assert append_row_2[4] == "2"  # No da Parcela
        
        print(f"✅ Append realizado: {final_rows} linhas totais no arquivo")
    
    def test_validation_missing_required_fields(self, client, mock_feedback_dir):
        """
        Teste 3a: Validações - Campos obrigatórios ausentes
        
        Ausência de transactionId OU description OU amount OU date → 422
        """
        # Teste sem transactionId
        payload_no_id = {
            "feedback": {
                "description": "Test Description",
                "amount": 10.00,
                "date": "2024-01-01T00:00:00Z"
            }
        }
        response = client.post("/v1/feedback", json=payload_no_id)
        assert response.status_code == 422
        
        # Teste sem description
        payload_no_desc = {
            "feedback": {
                "transactionId": "tx_test",
                "amount": 10.00,
                "date": "2024-01-01T00:00:00Z"
            }
        }
        response = client.post("/v1/feedback", json=payload_no_desc)
        assert response.status_code == 422
        
        # Teste sem amount
        payload_no_amount = {
            "feedback": {
                "transactionId": "tx_test",
                "description": "Test Description",
                "date": "2024-01-01T00:00:00Z"
            }
        }
        response = client.post("/v1/feedback", json=payload_no_amount)
        assert response.status_code == 422
        
        # Teste sem date
        payload_no_date = {
            "feedback": {
                "transactionId": "tx_test",
                "description": "Test Description",
                "amount": 10.00
            }
        }
        response = client.post("/v1/feedback", json=payload_no_date)
        assert response.status_code == 422
        
        print("✅ Validações de campos obrigatórios funcionando")
    
    def test_validation_invalid_amount(self, client, mock_feedback_dir):
        """
        Teste 3b: Validações - Amount inválido
        
        Amount deve ser > 0
        """
        # Teste com amount = 0
        payload_zero = {
            "feedback": {
                "transactionId": "tx_test",
                "description": "Test Description",
                "amount": 0.0,
                "date": "2024-01-01T00:00:00Z"
            }
        }
        response = client.post("/v1/feedback", json=payload_zero)
        assert response.status_code == 422
        
        # Teste com amount negativo
        payload_negative = {
            "feedback": {
                "transactionId": "tx_test",
                "description": "Test Description",
                "amount": -10.0,
                "date": "2024-01-01T00:00:00Z"
            }
        }
        response = client.post("/v1/feedback", json=payload_negative)
        assert response.status_code == 422
        
        print("✅ Validações de amount funcionando")
    
    def test_unknown_fields_ignored(self, client, mock_feedback_dir):
        """
        Teste 3c: Campos desconhecidos são ignorados silenciosamente
        
        Campos desconhecidos no payload → ignorar silenciosamente (não quebrar)
        """
        payload_with_unknown = {
            "feedback": {
                "transactionId": "tx_test",
                "description": "Test Description",
                "amount": 10.00,
                "date": "2024-01-01T00:00:00Z",
                "unknownField1": "valor1",
                "unknownField2": 123,
                "unknownField3": {"nested": "object"}
            }
        }
        
        response = client.post("/v1/feedback", json=payload_with_unknown)
        assert response.status_code == 201
        
        response_data = response.json()
        assert response_data["saved_rows"] == 1
        
        print("✅ Campos desconhecidos ignorados silenciosamente")
    
    def test_mapping_columns_and_values(self, client, mock_feedback_dir):
        """
        Teste 4: Mapeamento de colunas e valores
        
        Validar que as colunas estão presentes e preenchidas conforme mapeamento
        """
        payload = {
            "feedback": {
                "transactionId": "tx_mapping_test",
                "description": "Teste Mapeamento",
                "amount": 100.50,
                "date": "2024-01-01T00:00:00Z",
                "source": "débito",
                "card": "Cartão Teste",
                "category": "Categoria Teste",
                "comp": "Comp Teste",
                "parcelas": 5,
                "numero_parcela": 3,
                "modelVersion": "v2.0.0",
                "flux": "Saída"
            }
        }
        
        response = client.post("/v1/feedback", json=payload)
        assert response.status_code == 201
        
        # Verificar arquivo criado
        expected_filename = self.get_today_filename()
        expected_filepath = os.path.join("feedbacks", expected_filename)
        
        content = self.read_csv_content(expected_filepath)
        data_row = content[1]  # Primeira linha de dados
        
        # Verificar mapeamento específico
        assert data_row[0] == "Teste Mapeamento"  # Aonde Gastou ← description
        assert data_row[1] == "Categoria Teste"  # Natureza do Gasto ← category
        assert data_row[2] == "502.5"  # Valor Total ← amount * parcelas (100.50 * 5)
        assert data_row[3] == "5"  # Parcelas ← parcelas
        assert data_row[4] == "3"  # No da Parcela ← numero_parcela
        assert data_row[5] == "100.5"  # Valor Unitário ← amount
        assert data_row[6] == "débito"  # tipo ← source
        assert data_row[7] == "Comp Teste"  # Comp ← comp
        assert data_row[8] == "2024-01-01T00:00:00Z"  # Data ← date
        assert data_row[9] == "Cartão Teste"  # cartao ← card
        assert data_row[10] == "tx_mapping_test"  # transactionId ← transactionId
        assert data_row[11] == "v2.0.0"  # modelVersion ← modelVersion
        assert data_row[12] != ""  # createdAt (preenchido automaticamente)
        assert data_row[13] == "Saída"  # flux ← flux
        
        print("✅ Mapeamento de colunas e valores correto")
    
    def test_mapping_default_values(self, client, mock_feedback_dir):
        """
        Teste 4b: Mapeamento com valores padrão
        
        Testar valores padrão (parcelas=1, campos vazios)
        """
        payload = {
            "feedback": {
                "transactionId": "tx_default_test",
                "description": "Teste Defaults",
                "amount": 50.00,
                "date": "2024-01-01T00:00:00Z"
                # Sem parcelas, category, source, etc.
            }
        }
        
        response = client.post("/v1/feedback", json=payload)
        assert response.status_code == 201
        
        expected_filename = self.get_today_filename()
        expected_filepath = os.path.join("feedbacks", expected_filename)
        
        content = self.read_csv_content(expected_filepath)
        data_row = content[1]  # Primeira linha de dados
        
        # Verificar valores padrão
        assert data_row[0] == "Teste Defaults"  # Aonde Gastou
        assert data_row[1] == ""  # Natureza do Gasto (vazio)
        assert data_row[2] == "50.0"  # Valor Total (50.00 * 1 parcelas padrão)
        assert data_row[3] == "1"  # Parcelas (padrão 1)
        assert data_row[4] == ""  # No da Parcela (vazio)
        assert data_row[5] == "50.0"  # Valor Unitário
        assert data_row[6] == ""  # tipo (vazio)
        assert data_row[7] == ""  # Comp (vazio)
        assert data_row[8] == "2024-01-01T00:00:00Z"  # Data
        assert data_row[9] == ""  # cartao (vazio)
        assert data_row[10] == "tx_default_test"  # transactionId
        assert data_row[11] == ""  # modelVersion (vazio)
        assert data_row[12] != ""  # createdAt (preenchido automaticamente)
        assert data_row[13] == ""  # flux (vazio)
        
        print("✅ Valores padrão aplicados corretamente")
    
    def test_concurrency_best_effort(self, client, mock_feedback_dir):
        """
        Teste 5: Concorrência best-effort
        
        Simular 2 POST seguidos e verificar que ambas as requisições
        resultam em incremento de linhas (sem perda)
        """
        # Arrange - Criar arquivo inicial
        initial_payload = {
            "feedback": {
                "transactionId": "tx_concurrent_initial",
                "description": "Item Inicial",
                "amount": 10.00,
                "date": "2024-01-01T00:00:00Z"
            }
        }
        
        response1 = client.post("/v1/feedback", json=initial_payload)
        assert response1.status_code == 201
        assert response1.json()["saved_rows"] == 1
        
        expected_filename = self.get_today_filename()
        expected_filepath = os.path.join("feedbacks", expected_filename)
        
        # Verificar contagem inicial
        initial_rows = self.count_csv_rows(expected_filepath)
        assert initial_rows == 2  # Cabeçalho + 1 linha
        
        # Act - Primeiro POST concorrente
        concurrent_payload_1 = {
            "feedback": {
                "transactionId": "tx_concurrent_1",
                "description": "Item Concorrente 1",
                "amount": 20.00,
                "date": "2024-01-02T00:00:00Z"
            }
        }
        
        response2 = client.post("/v1/feedback", json=concurrent_payload_1)
        assert response2.status_code == 201
        assert response2.json()["saved_rows"] == 1
        
        # Act - Segundo POST concorrente
        concurrent_payload_2 = {
            "feedback": {
                "transactionId": "tx_concurrent_2",
                "description": "Item Concorrente 2",
                "amount": 30.00,
                "date": "2024-01-03T00:00:00Z"
            }
        }
        
        response3 = client.post("/v1/feedback", json=concurrent_payload_2)
        assert response3.status_code == 201
        assert response3.json()["saved_rows"] == 1
        
        # Assert - Verificar contagem final
        final_rows = self.count_csv_rows(expected_filepath)
        assert final_rows == 4  # Cabeçalho + 3 linhas (1 inicial + 2 concorrentes)
        
        # Verificar que todos os itens estão presentes
        content = self.read_csv_content(expected_filepath)
        
        # Encontrar linhas por transactionId
        transaction_ids = [row[10] for row in content[1:]]  # transactionId está na coluna 10
        assert "tx_concurrent_initial" in transaction_ids
        assert "tx_concurrent_1" in transaction_ids
        assert "tx_concurrent_2" in transaction_ids
        
        print(f"✅ Concorrência testada: {final_rows} linhas totais, sem perda de dados")
    
    def test_file_info_endpoint(self, client, mock_feedback_dir):
        """
        Teste adicional: Endpoint de informações do arquivo
        """
        # Criar arquivo primeiro
        payload = {
            "feedback": {
                "transactionId": "tx_info_test",
                "description": "Teste Info",
                "amount": 10.00,
                "date": "2024-01-01T00:00:00Z"
            }
        }
        
        response = client.post("/v1/feedback", json=payload)
        assert response.status_code == 201
        
        # Testar endpoint de info
        info_response = client.get("/v1/feedback/file-info")
        assert info_response.status_code == 200
        
        info_data = info_response.json()
        assert info_data["exists"] == True
        assert info_data["has_header"] == True
        assert info_data["size_bytes"] > 0
        assert len(info_data["columns"]) == 14
        
        print("✅ Endpoint de informações do arquivo funcionando")
