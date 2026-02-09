#!/usr/bin/env python3
"""
Testes unitários para controle de arquivos processados
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import tempfile
import shutil
from pathlib import Path
from app.services.feedback_ingestion import FeedbackIngestionService


def test_processed_files_control():
    """Testa controle de arquivos processados"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir)
        
        # Criar arquivo de feedback
        feedback_data = {
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
        
        df = pd.DataFrame(feedback_data)
        df.to_csv(Path(temp_dir) / "feedback_2024-01-15.csv", index=False)
        
        # Primeira execução - deve processar o arquivo
        feedbacks1 = service.collect_feedbacks_with_control()
        assert len(feedbacks1) == 1
        assert len(feedbacks1[0]) == 1
        
        # Segunda execução - não deve processar novamente
        feedbacks2 = service.collect_feedbacks_with_control()
        assert len(feedbacks2) == 0
        
        # Verificar se arquivo foi marcado como processado
        processed_files = service.get_processed_files()
        assert "feedback_2024-01-15.csv" in processed_files
        
        print("OK - Teste controle de arquivos processados passou")


def test_processed_files_multiple():
    """Testa controle com múltiplos arquivos"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir)
        
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
        df1.to_csv(Path(temp_dir) / "feedback_2024-01-15.csv", index=False)
        
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
        df2.to_csv(Path(temp_dir) / "feedback_2024-01-16.csv", index=False)
        
        # Primeira execução - deve processar ambos os arquivos
        feedbacks1 = service.collect_feedbacks_with_control()
        assert len(feedbacks1) == 2
        
        # Segunda execução - não deve processar nenhum
        feedbacks2 = service.collect_feedbacks_with_control()
        assert len(feedbacks2) == 0
        
        # Verificar se ambos foram marcados como processados
        processed_files = service.get_processed_files()
        assert "feedback_2024-01-15.csv" in processed_files
        assert "feedback_2024-01-16.csv" in processed_files
        
        print("OK - Teste controle multiplos arquivos passou")


def test_clear_processed_files():
    """Testa limpeza de arquivos processados"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir)
        
        # Criar arquivo de feedback
        feedback_data = {
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
        
        df = pd.DataFrame(feedback_data)
        df.to_csv(Path(temp_dir) / "feedback_2024-01-15.csv", index=False)
        
        # Processar arquivo
        feedbacks1 = service.collect_feedbacks_with_control()
        assert len(feedbacks1) == 1
        
        # Limpar arquivos processados
        service.clear_processed_files()
        
        # Processar novamente - deve processar o arquivo novamente
        feedbacks2 = service.collect_feedbacks_with_control()
        assert len(feedbacks2) == 1
        
        print("OK - Teste limpeza de arquivos processados passou")


if __name__ == "__main__":
    print("Executando testes unitarios para controle de arquivos processados...")
    
    test_processed_files_control()
    test_processed_files_multiple()
    test_clear_processed_files()
    
    print("\nTodos os testes passaram!")
