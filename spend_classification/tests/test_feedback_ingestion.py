#!/usr/bin/env python3
"""
Testes unitários para FeedbackIngestionService.collect_feedbacks()
"""

import pytest
import pandas as pd
import tempfile
import shutil
from pathlib import Path
from app.services.feedback_ingestion import FeedbackIngestionService


class TestCollectFeedbacks:
    """Testes para a função collect_feedbacks()"""
    
    @pytest.fixture
    def temp_feedback_dir(self):
        """Cria diretório temporário para testes"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def service(self, temp_feedback_dir):
        """Cria instância do serviço com diretório temporário"""
        return FeedbackIngestionService(feedback_dir=temp_feedback_dir)
    
    def test_collect_feedbacks_empty_directory(self, service):
        """Testa coleta em diretório vazio"""
        feedbacks = service.collect_feedbacks()
        assert feedbacks == []
    
    def test_collect_feedbacks_nonexistent_directory(self):
        """Testa coleta em diretório inexistente"""
        service = FeedbackIngestionService(feedback_dir="nonexistent_dir")
        feedbacks = service.collect_feedbacks()
        assert feedbacks == []
    
    def test_collect_feedbacks_single_valid_file(self, service, temp_feedback_dir):
        """Testa coleta de arquivo único válido"""
        # Criar arquivo de feedback válido
        feedback_data = {
            "Aonde Gastou": ["Netflix Com", "Spotify Premium"],
            "Natureza do Gasto": ["Entretenimento", "Entretenimento"],
            "Valor Total": [44.9, 19.9],
            "Parcelas": [1, 1],
            "No da Parcela": ["", ""],
            "Valor Unitário": [44.9, 19.9],
            "tipo": ["crédito", "crédito"],
            "Comp": ["", ""],
            "Data": ["2024-01-15T00:00:00Z", "2024-01-16T00:00:00Z"],
            "cartao": ["Final 8073", "Final 8073"],
            "transactionId": ["tx_001", "tx_002"],
            "modelVersion": ["v1.2.0", "v1.2.0"],
            "createdAt": ["2024-01-15T12:00:00Z", "2024-01-16T12:00:00Z"],
            "flux": ["", ""]
        }
        
        df = pd.DataFrame(feedback_data)
        df.to_csv(Path(temp_feedback_dir) / "feedback_2024-01-15.csv", index=False)
        
        # Coletar feedbacks
        feedbacks = service.collect_feedbacks()
        
        # Verificações
        assert len(feedbacks) == 1
        assert len(feedbacks[0]) == 2
        assert list(feedbacks[0]['transactionId']) == ["tx_001", "tx_002"]
    
    def test_collect_feedbacks_multiple_files(self, service, temp_feedback_dir):
        """Testa coleta de múltiplos arquivos"""
        # Criar primeiro arquivo
        feedback_data_1 = {
            "Aonde Gastou": ["Netflix Com"],
            "Natureza do Gasto": ["Entretenimento"],
            "Valor Total": [44.9],
            "Parcelas": [1],
            "No da Parcela": [""],
            "Valor Unitário": [44.9],
            "tipo": ["crédito"],
            "Comp": [""],
            "Data": ["2024-01-15T00:00:00Z"],
            "cartao": ["Final 8073"],
            "transactionId": ["tx_001"],
            "modelVersion": ["v1.2.0"],
            "createdAt": ["2024-01-15T12:00:00Z"],
            "flux": [""]
        }
        
        df1 = pd.DataFrame(feedback_data_1)
        df1.to_csv(Path(temp_feedback_dir) / "feedback_2024-01-15.csv", index=False)
        
        # Criar segundo arquivo
        feedback_data_2 = {
            "Aonde Gastou": ["Spotify Premium"],
            "Natureza do Gasto": ["Entretenimento"],
            "Valor Total": [19.9],
            "Parcelas": [1],
            "No da Parcela": [""],
            "Valor Unitário": [19.9],
            "tipo": ["crédito"],
            "Comp": [""],
            "Data": ["2024-01-16T00:00:00Z"],
            "cartao": ["Final 8073"],
            "transactionId": ["tx_002"],
            "modelVersion": ["v1.2.0"],
            "createdAt": ["2024-01-16T12:00:00Z"],
            "flux": [""]
        }
        
        df2 = pd.DataFrame(feedback_data_2)
        df2.to_csv(Path(temp_feedback_dir) / "feedback_2024-01-16.csv", index=False)
        
        # Coletar feedbacks
        feedbacks = service.collect_feedbacks()
        
        # Verificações
        assert len(feedbacks) == 2
        assert len(feedbacks[0]) == 1  # Primeiro arquivo
        assert len(feedbacks[1]) == 1  # Segundo arquivo
        assert feedbacks[0]['transactionId'].iloc[0] == "tx_001"
        assert feedbacks[1]['transactionId'].iloc[0] == "tx_002"
    
    def test_collect_feedbacks_duplicate_transaction_ids(self, service, temp_feedback_dir):
        """Testa remoção de duplicatas por transactionId"""
        # Criar arquivo com duplicatas internas
        feedback_data = {
            "Aonde Gastou": ["Netflix Com", "Netflix Com", "Spotify Premium"],
            "Natureza do Gasto": ["Entretenimento", "Entretenimento", "Entretenimento"],
            "Valor Total": [44.9, 44.9, 19.9],
            "Parcelas": [1, 1, 1],
            "No da Parcela": ["", "", ""],
            "Valor Unitário": [44.9, 44.9, 19.9],
            "tipo": ["crédito", "crédito", "crédito"],
            "Comp": ["", "", ""],
            "Data": ["2024-01-15T00:00:00Z", "2024-01-15T00:00:00Z", "2024-01-16T00:00:00Z"],
            "cartao": ["Final 8073", "Final 8073", "Final 8073"],
            "transactionId": ["tx_001", "tx_001", "tx_002"],  # tx_001 duplicado
            "modelVersion": ["v1.2.0", "v1.2.0", "v1.2.0"],
            "createdAt": ["2024-01-15T12:00:00Z", "2024-01-15T12:00:00Z", "2024-01-16T12:00:00Z"],
            "flux": ["", "", ""]
        }
        
        df = pd.DataFrame(feedback_data)
        df.to_csv(Path(temp_feedback_dir) / "feedback_2024-01-15.csv", index=False)
        
        # Coletar feedbacks
        feedbacks = service.collect_feedbacks()
        
        # Verificações
        assert len(feedbacks) == 1
        assert len(feedbacks[0]) == 2  # Duplicata removida
        assert list(feedbacks[0]['transactionId']) == ["tx_001", "tx_002"]
    
    def test_collect_feedbacks_duplicate_across_files(self, service, temp_feedback_dir):
        """Testa remoção de duplicatas entre arquivos"""
        # Criar primeiro arquivo
        feedback_data_1 = {
            "Aonde Gastou": ["Netflix Com"],
            "Natureza do Gasto": ["Entretenimento"],
            "Valor Total": [44.9],
            "Parcelas": [1],
            "No da Parcela": [""],
            "Valor Unitário": [44.9],
            "tipo": ["crédito"],
            "Comp": [""],
            "Data": ["2024-01-15T00:00:00Z"],
            "cartao": ["Final 8073"],
            "transactionId": ["tx_001"],
            "modelVersion": ["v1.2.0"],
            "createdAt": ["2024-01-15T12:00:00Z"],
            "flux": [""]
        }
        
        df1 = pd.DataFrame(feedback_data_1)
        df1.to_csv(Path(temp_feedback_dir) / "feedback_2024-01-15.csv", index=False)
        
        # Criar segundo arquivo com transactionId duplicado
        feedback_data_2 = {
            "Aonde Gastou": ["Netflix Com", "Spotify Premium"],
            "Natureza do Gasto": ["Entretenimento", "Entretenimento"],
            "Valor Total": [44.9, 19.9],
            "Parcelas": [1, 1],
            "No da Parcela": ["", ""],
            "Valor Unitário": [44.9, 19.9],
            "tipo": ["crédito", "crédito"],
            "Comp": ["", ""],
            "Data": ["2024-01-15T00:00:00Z", "2024-01-16T00:00:00Z"],
            "cartao": ["Final 8073", "Final 8073"],
            "transactionId": ["tx_001", "tx_002"],  # tx_001 duplicado do primeiro arquivo
            "modelVersion": ["v1.2.0", "v1.2.0"],
            "createdAt": ["2024-01-15T12:00:00Z", "2024-01-16T12:00:00Z"],
            "flux": ["", ""]
        }
        
        df2 = pd.DataFrame(feedback_data_2)
        df2.to_csv(Path(temp_feedback_dir) / "feedback_2024-01-16.csv", index=False)
        
        # Coletar feedbacks
        feedbacks = service.collect_feedbacks()
        
        # Verificações
        assert len(feedbacks) == 2
        assert len(feedbacks[0]) == 1  # Primeiro arquivo
        assert len(feedbacks[1]) == 1  # Segundo arquivo (duplicata removida)
        assert feedbacks[0]['transactionId'].iloc[0] == "tx_001"
        assert feedbacks[1]['transactionId'].iloc[0] == "tx_002"
    
    def test_collect_feedbacks_invalid_structure(self, service, temp_feedback_dir):
        """Testa arquivo com estrutura inválida"""
        # Criar arquivo com estrutura inválida (colunas erradas)
        invalid_data = {
            "wrong_column": ["value1", "value2"],
            "another_wrong": ["value3", "value4"]
        }
        
        df = pd.DataFrame(invalid_data)
        df.to_csv(Path(temp_feedback_dir) / "feedback_2024-01-15.csv", index=False)
        
        # Coletar feedbacks
        feedbacks = service.collect_feedbacks()
        
        # Verificações
        assert feedbacks == []  # Arquivo inválido ignorado
    
    def test_collect_feedbacks_empty_file(self, service, temp_feedback_dir):
        """Testa arquivo vazio"""
        # Criar arquivo vazio
        df = pd.DataFrame()
        df.to_csv(Path(temp_feedback_dir) / "feedback_2024-01-15.csv", index=False)
        
        # Coletar feedbacks
        feedbacks = service.collect_feedbacks()
        
        # Verificações
        assert feedbacks == []  # Arquivo vazio ignorado
    
    def test_collect_feedbacks_file_read_error(self, service, temp_feedback_dir):
        """Testa erro ao ler arquivo"""
        # Criar arquivo corrompido (não é CSV válido)
        with open(Path(temp_feedback_dir) / "feedback_2024-01-15.csv", 'w') as f:
            f.write("not a valid csv file content")
        
        # Coletar feedbacks
        feedbacks = service.collect_feedbacks()
        
        # Verificações
        assert feedbacks == []  # Arquivo com erro ignorado
