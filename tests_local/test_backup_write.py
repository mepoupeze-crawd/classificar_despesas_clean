#!/usr/bin/env python3
"""
Testes unitários para write_merged_dataset() e funcionalidades de backup
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import tempfile
import shutil
from pathlib import Path
from app.services.feedback_ingestion import FeedbackIngestionService


def test_write_merged_dataset():
    """Testa escrita de dataset com backup automático"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir, base_csv="test_base.csv")
        
        # Criar dataset base inicial
        base_data = {
            "Aonde Gastou": ["Supermercado"],
            "Natureza do Gasto": ["Alimentação"],
            "Valor Total": [150.0],
            "Parcelas": [1],
            "No da Parcela": [""],
            "Valor Unitário": [150.0],
            "tipo": ["débito"],
            "Comp": [""],
            "Data": ["2024-01-10T00:00:00Z"],
            "cartao": ["Final 1234"],
            "transactionId": ["base_001"],
            "modelVersion": ["v1.0.0"],
            "createdAt": ["2024-01-10T12:00:00Z"],
            "flux": [""]
        }
        
        base_df = pd.DataFrame(base_data)
        base_csv_path = Path(temp_dir) / "test_base.csv"
        base_df.to_csv(base_csv_path, index=False)
        
        # Criar dataset mesclado
        merged_data = {
            "Aonde Gastou": ["Supermercado", "Netflix Com"],
            "Natureza do Gasto": ["Alimentação", "Entretenimento"],
            "Valor Total": [150.0, 44.9],
            "Parcelas": [1, 1],
            "No da Parcela": ["", ""],
            "Valor Unitário": [150.0, 44.9],
            "tipo": ["débito", "crédito"],
            "Comp": ["", ""],
            "Data": ["2024-01-10T00:00:00Z", "2024-01-15T00:00:00Z"],
            "cartao": ["Final 1234", "Final 8073"],
            "transactionId": ["base_001", "fb_001"],
            "modelVersion": ["v1.0.0", "v1.2.0"],
            "createdAt": ["2024-01-10T12:00:00Z", "2024-01-15T12:00:00Z"],
            "flux": ["", ""]
        }
        
        merged_df = pd.DataFrame(merged_data)
        
        # Testar escrita
        output_path = service.write_merged_dataset(merged_df, out_csv=str(base_csv_path))
        
        # Verificações
        assert output_path == str(base_csv_path)
        assert os.path.exists(base_csv_path)
        
        # Verificar se backup foi criado
        backup_files = service.get_backup_files(str(base_csv_path))
        assert len(backup_files) == 1
        assert '.backup_' in backup_files[0]
        
        # Verificar conteúdo do arquivo escrito
        written_df = pd.read_csv(base_csv_path)
        assert len(written_df) == 2
        assert list(written_df['transactionId']) == ["base_001", "fb_001"]
        
        print("OK - Teste escrita com backup passou")


def test_write_merged_dataset_no_backup():
    """Testa escrita de dataset sem arquivo existente (sem backup)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir, base_csv="test_new.csv")
        
        # Criar dataset para escrita
        data = {
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
            "transactionId": ["fb_001"],
            "modelVersion": ["v1.2.0"],
            "createdAt": ["2024-01-15T12:00:00Z"],
            "flux": [""]
        }
        
        df = pd.DataFrame(data)
        output_path = Path(temp_dir) / "test_new.csv"
        
        # Testar escrita
        result_path = service.write_merged_dataset(df, out_csv=str(output_path))
        
        # Verificações
        assert result_path == str(output_path)
        assert os.path.exists(output_path)
        
        # Verificar se não há backups (arquivo não existia)
        backup_files = service.get_backup_files(str(output_path))
        assert len(backup_files) == 0
        
        # Verificar conteúdo
        written_df = pd.read_csv(output_path)
        assert len(written_df) == 1
        assert written_df['transactionId'].iloc[0] == "fb_001"
        
        print("OK - Teste escrita sem backup passou")


def test_validate_written_file():
    """Testa validação de arquivo escrito"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService()
        
        # Criar arquivo válido
        data = {
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
            "transactionId": ["fb_001"],
            "modelVersion": ["v1.2.0"],
            "createdAt": ["2024-01-15T12:00:00Z"],
            "flux": [""]
        }
        
        df = pd.DataFrame(data)
        file_path = Path(temp_dir) / "test_file.csv"
        df.to_csv(file_path, index=False)
        
        # Testar validação
        result = service.validate_written_file(str(file_path))
        
        # Verificações
        assert result['success'] == True
        assert result['final_rows'] == 1
        assert result['file_size'] > 0
        
        print("OK - Teste validacao de arquivo escrito passou")


def test_validate_written_file_invalid():
    """Testa validação de arquivo inválido"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService()
        
        # Criar arquivo inválido (estrutura errada)
        invalid_data = {
            "wrong_column": ["value1"],
            "another_wrong": ["value2"]
        }
        
        df = pd.DataFrame(invalid_data)
        file_path = Path(temp_dir) / "test_invalid.csv"
        df.to_csv(file_path, index=False)
        
        # Testar validação
        result = service.validate_written_file(str(file_path))
        
        # Verificações
        assert result['success'] == False
        assert "Estrutura de colunas incorreta" in result['error']
        
        print("OK - Teste validacao de arquivo invalido passou")


def test_backup_management():
    """Testa gerenciamento de backups"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir, base_csv="test_base.csv")
        
        # Criar arquivo base
        base_path = Path(temp_dir) / "test_base.csv"
        base_data = {"test": ["data"]}
        pd.DataFrame(base_data).to_csv(base_path, index=False)
        
        # Criar vários backups simulados
        for i in range(7):
            backup_path = Path(temp_dir) / f"test_base.csv.backup_202401{i:02d}_120000"
            shutil.copy2(base_path, backup_path)
        
        # Testar listagem de backups
        backup_files = service.get_backup_files(str(base_path))
        assert len(backup_files) == 7
        
        # Testar limpeza de backups
        service.cleanup_old_backups(str(base_path), keep_count=3)
        
        # Verificar se apenas 3 backups restaram
        remaining_backups = service.get_backup_files(str(base_path))
        assert len(remaining_backups) == 3
        
        print("OK - Teste gerenciamento de backups passou")


if __name__ == "__main__":
    print("Executando testes unitarios para backup e escrita...")
    
    test_write_merged_dataset()
    test_write_merged_dataset_no_backup()
    test_validate_written_file()
    test_validate_written_file_invalid()
    test_backup_management()
    
    print("\nTodos os testes passaram!")
