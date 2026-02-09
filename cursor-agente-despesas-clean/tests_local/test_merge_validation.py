#!/usr/bin/env python3
"""
Testes unitários para merge_into_model_dataset() e validate_dataset_integration()
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import tempfile
import shutil
from pathlib import Path
from app.services.feedback_ingestion import FeedbackIngestionService


def test_merge_into_model_dataset():
    """Testa mesclagem de dataset base com feedbacks"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir, base_csv="test_base.csv")
        
        # Criar dataset base
        base_data = {
            "Aonde Gastou": ["Supermercado", "Farmácia"],
            "Natureza do Gasto": ["Alimentação", "Saúde"],
            "Valor Total": [150.0, 25.0],
            "Parcelas": [1, 1],
            "No da Parcela": ["", ""],
            "Valor Unitário": [150.0, 25.0],
            "tipo": ["débito", "débito"],
            "Comp": ["", ""],
            "Data": ["2024-01-10T00:00:00Z", "2024-01-11T00:00:00Z"],
            "cartao": ["Final 1234", "Final 1234"],
            "transactionId": ["base_001", "base_002"],
            "modelVersion": ["v1.0.0", "v1.0.0"],
            "createdAt": ["2024-01-10T12:00:00Z", "2024-01-11T12:00:00Z"],
            "flux": ["", ""]
        }
        
        base_df = pd.DataFrame(base_data)
        base_csv_path = Path(temp_dir) / "test_base.csv"
        base_df.to_csv(base_csv_path, index=False)
        
        # Criar feedbacks
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
            "transactionId": ["fb_001", "fb_002"],
            "modelVersion": ["v1.2.0", "v1.2.0"],
            "createdAt": ["2024-01-15T12:00:00Z", "2024-01-16T12:00:00Z"],
            "flux": ["", ""]
        }
        
        feedback_df = pd.DataFrame(feedback_data)
        
        # Testar mesclagem
        merged_df = service.merge_into_model_dataset(base_csv=str(base_csv_path), feedbacks_list=[feedback_df])
        
        # Verificações
        assert len(merged_df) == 4  # 2 base + 2 feedback
        assert list(merged_df['transactionId']) == ["base_001", "base_002", "fb_001", "fb_002"]
        assert merged_df['Natureza do Gasto'].iloc[0] == "Alimentação"
        assert merged_df['Natureza do Gasto'].iloc[2] == "Entretenimento"
        
        print("OK - Teste mesclagem de dataset passou")


def test_validate_dataset_integration():
    """Testa validação de integração"""
    service = FeedbackIngestionService()
    
    # Criar dataset base
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
    
    # Criar feedbacks válidos
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
        "transactionId": ["fb_001"],
        "modelVersion": ["v1.2.0"],
        "createdAt": ["2024-01-15T12:00:00Z"],
        "flux": [""]
    }
    
    feedback_df = pd.DataFrame(feedback_data)
    
    # Testar validação
    result = service.validate_dataset_integration(base_df, feedback_df)
    
    # Verificações
    assert result['success'] == True
    assert result['base_rows'] == 1
    assert result['feedback_rows'] == 1
    assert result['duplicates'] == 0
    assert len(result['quality_issues']) == 0
    assert result['balance_metrics']['base_categories'] == 1
    assert result['balance_metrics']['feedback_categories'] == 1
    assert result['balance_metrics']['new_categories'] == 1  # Entretenimento é nova
    
    print("OK - Teste validacao de integracao passou")


def test_validate_dataset_integration_duplicates():
    """Testa validação com duplicatas"""
    service = FeedbackIngestionService()
    
    # Criar dataset base
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
    
    # Criar feedbacks com transactionId duplicado
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
        "transactionId": ["base_001"],  # Duplicado!
        "modelVersion": ["v1.2.0"],
        "createdAt": ["2024-01-15T12:00:00Z"],
        "flux": [""]
    }
    
    feedback_df = pd.DataFrame(feedback_data)
    
    # Testar validação
    result = service.validate_dataset_integration(base_df, feedback_df)
    
    # Verificações
    assert result['success'] == True  # Duplicatas são detectadas mas não impedem integração
    assert result['duplicates'] == 1
    assert "base_001" in result['duplicate_ids']
    
    print("OK - Teste validacao com duplicatas passou")


def test_validate_dataset_integration_quality_issues():
    """Testa validação com problemas de qualidade"""
    service = FeedbackIngestionService()
    
    # Criar dataset base
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
    
    # Criar feedbacks com problemas de qualidade
    feedback_data = {
        "Aonde Gastou": [None],  # Valor nulo
        "Natureza do Gasto": ["Entretenimento"],
        "Valor Total": [-44.9],  # Valor negativo
        "Parcelas": [1],
        "No da Parcela": [""],
        "Valor Unitário": [-44.9],  # Valor negativo
        "tipo": ["crédito"],
        "Comp": [""],
        "Data": ["2024-01-15T00:00:00Z"],
        "cartao": ["Final 8073"],
        "transactionId": ["fb_001"],
        "modelVersion": ["v1.2.0"],
        "createdAt": ["2024-01-15T12:00:00Z"],
        "flux": [""]
    }
    
    feedback_df = pd.DataFrame(feedback_data)
    
    # Testar validação
    result = service.validate_dataset_integration(base_df, feedback_df)
    
    # Verificações
    assert result['success'] == True  # Problemas são detectados mas não impedem integração
    assert len(result['quality_issues']) > 0
    assert any("nulos" in issue for issue in result['quality_issues'])
    assert any("negativos" in issue for issue in result['quality_issues'])
    
    print("OK - Teste validacao com problemas de qualidade passou")


if __name__ == "__main__":
    print("Executando testes unitarios para merge e validacao...")
    
    test_merge_into_model_dataset()
    test_validate_dataset_integration()
    test_validate_dataset_integration_duplicates()
    test_validate_dataset_integration_quality_issues()
    
    print("\nTodos os testes passaram!")
