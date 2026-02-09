#!/usr/bin/env python3
"""
Testes unitários simples para FeedbackIngestionService.collect_feedbacks()
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import tempfile
import shutil
from pathlib import Path
from app.services.feedback_ingestion import FeedbackIngestionService


def test_collect_feedbacks_empty_directory():
    """Testa coleta em diretório vazio"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir)
        feedbacks = service.collect_feedbacks()
        assert feedbacks == []
        print("OK - Teste diretorio vazio passou")


def test_collect_feedbacks_single_valid_file():
    """Testa coleta de arquivo único válido"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir)
        
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
        df.to_csv(Path(temp_dir) / "feedback_2024-01-15.csv", index=False)
        
        # Coletar feedbacks
        feedbacks = service.collect_feedbacks()
        
        # Verificações
        assert len(feedbacks) == 1
        assert len(feedbacks[0]) == 2
        assert list(feedbacks[0]['transactionId']) == ["tx_001", "tx_002"]
        print("OK - Teste arquivo unico valido passou")


def test_collect_feedbacks_duplicate_transaction_ids():
    """Testa remoção de duplicatas por transactionId"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir)
        
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
        df.to_csv(Path(temp_dir) / "feedback_2024-01-15.csv", index=False)
        
        # Coletar feedbacks
        feedbacks = service.collect_feedbacks()
        
        # Verificações
        assert len(feedbacks) == 1
        assert len(feedbacks[0]) == 2  # Duplicata removida
        assert list(feedbacks[0]['transactionId']) == ["tx_001", "tx_002"]
        print("OK - Teste remocao de duplicatas passou")


def test_collect_feedbacks_invalid_structure():
    """Testa arquivo com estrutura inválida"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir)
        
        # Criar arquivo com estrutura inválida (colunas erradas)
        invalid_data = {
            "wrong_column": ["value1", "value2"],
            "another_wrong": ["value3", "value4"]
        }
        
        df = pd.DataFrame(invalid_data)
        df.to_csv(Path(temp_dir) / "feedback_2024-01-15.csv", index=False)
        
        # Coletar feedbacks
        feedbacks = service.collect_feedbacks()
        
        # Verificações
        assert feedbacks == []  # Arquivo inválido ignorado
        print("OK - Teste estrutura invalida passou")


if __name__ == "__main__":
    print("Executando testes unitarios para collect_feedbacks()...")
    
    test_collect_feedbacks_empty_directory()
    test_collect_feedbacks_single_valid_file()
    test_collect_feedbacks_duplicate_transaction_ids()
    test_collect_feedbacks_invalid_structure()
    
    print("\nTodos os testes passaram!")
