#!/usr/bin/env python3
"""
Testes unitários para integração com treinar_modelo.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pandas as pd
import tempfile
import shutil
from pathlib import Path
from app.services.feedback_ingestion import FeedbackIngestionService


def test_get_model_timestamps():
    """Testa obtenção de timestamps dos modelos"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService()
        
        # Criar diretório de modelos
        models_dir = Path(temp_dir) / "modelos"
        models_dir.mkdir()
        
        # Criar arquivos de modelo simulados
        model_files = ["modelo_natureza_do_gasto.pkl", "modelo_comp.pkl", "modelo_parcelas.pkl"]
        for model_file in model_files:
            (models_dir / model_file).touch()
        
        # Testar obtenção de timestamps
        timestamps = service.get_model_timestamps(str(models_dir))
        
        # Verificações
        assert len(timestamps) == 3
        assert "modelo_natureza_do_gasto.pkl" in timestamps
        assert "modelo_comp.pkl" in timestamps
        assert "modelo_parcelas.pkl" in timestamps
        
        # Verificar se timestamps são válidos
        for model_name, timestamp in timestamps.items():
            assert timestamp > 0
        
        print("OK - Teste obtencao de timestamps passou")


def test_get_model_timestamps_empty_dir():
    """Testa obtenção de timestamps em diretório vazio"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService()
        
        # Testar diretório vazio
        timestamps = service.get_model_timestamps(temp_dir)
        
        # Verificações
        assert len(timestamps) == 0
        
        print("OK - Teste timestamps diretorio vazio passou")


def test_get_model_timestamps_nonexistent_dir():
    """Testa obtenção de timestamps em diretório inexistente"""
    service = FeedbackIngestionService()
    
    # Testar diretório inexistente
    timestamps = service.get_model_timestamps("nonexistent_dir")
    
    # Verificações
    assert len(timestamps) == 0
    
    print("OK - Teste timestamps diretorio inexistente passou")


def test_validate_model_quality():
    """Testa validação de qualidade do modelo"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService()
        
        # Criar arquivo de modelo simulado (não é um modelo real, mas testa a estrutura)
        model_path = Path(temp_dir) / "test_model.pkl"
        
        # Criar arquivo vazio para teste
        model_path.touch()
        
        # Testar validação
        result = service.validate_model_quality(str(model_path))
        
        # Verificações
        assert 'success' in result
        assert 'error' in result or 'validations' in result
        
        # Como o arquivo é vazio, deve falhar na validação
        assert result['success'] == False
        
        print("OK - Teste validacao de qualidade passou")


def test_get_test_data_for_model():
    """Testa criação de dados de teste"""
    service = FeedbackIngestionService()
    
    # Testar criação de dados de teste
    test_data = service.get_test_data_for_model()
    
    # Verificações
    assert test_data is not None
    assert 'X' in test_data
    assert len(test_data['X']) == 5
    assert "NETFLIX COM" in test_data['X']
    assert "SUPERMERCADO ABC" in test_data['X']
    
    print("OK - Teste criacao de dados de teste passou")


def test_run_complete_pipeline_no_feedbacks():
    """Testa pipeline completo sem feedbacks"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir)
        
        # Testar pipeline sem feedbacks
        result = service.run_complete_pipeline()
        
        # Verificações
        assert result['success'] == False
        assert 'collect_feedbacks' in result['steps_completed']
        assert len(result['errors']) > 0
        assert 'Nenhum feedback encontrado' in result['errors'][0]
        
        print("OK - Teste pipeline sem feedbacks passou")


def test_run_complete_pipeline_with_feedbacks():
    """Testa pipeline completo com feedbacks"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService(feedback_dir=temp_dir, base_csv="test_base.csv")
        
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
        base_csv_path = Path(temp_dir) / "test_base.csv"
        base_df.to_csv(base_csv_path, index=False)
        
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
            "transactionId": ["fb_001"],
            "modelVersion": ["v1.2.0"],
            "createdAt": ["2024-01-15T12:00:00Z"],
            "flux": [""]
        }
        
        feedback_df = pd.DataFrame(feedback_data)
        feedback_df.to_csv(Path(temp_dir) / "feedback_2024-01-15.csv", index=False)
        
        # Testar pipeline completo
        result = service.run_complete_pipeline(base_csv=str(base_csv_path))
        
        # Verificações
        assert 'collect_feedbacks' in result['steps_completed']
        assert 'merge_dataset' in result['steps_completed']
        assert 'write_dataset' in result['steps_completed']
        assert 'retrain_models' in result['steps_completed']
        
        # O retreino pode falhar se treinar_modelo.py não estiver configurado corretamente
        # mas os passos anteriores devem ter funcionado
        assert result['metrics']['feedbacks_collected'] == 1
        assert result['metrics']['total_feedback_records'] == 1
        assert result['metrics']['merged_records'] == 2
        
        print("OK - Teste pipeline com feedbacks passou")


def test_trigger_model_retraining_mock():
    """Testa disparo de retreino (simulado)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FeedbackIngestionService()
        
        # Criar dataset de teste
        test_data = {"test": ["data"]}
        test_csv = Path(temp_dir) / "test_dataset.csv"
        pd.DataFrame(test_data).to_csv(test_csv, index=False)
        
        # Criar diretório de modelos
        models_dir = Path(temp_dir) / "modelos"
        models_dir.mkdir()
        
        # Testar disparo de retreino
        # Nota: Este teste pode falhar se treinar_modelo.py não estiver configurado
        # mas testa a estrutura da função
        result = service.trigger_model_retraining(str(test_csv), str(models_dir))
        
        # Verificações básicas
        assert 'success' in result
        assert 'error' in result or 'updated_models' in result
        
        print("OK - Teste disparo de retreino passou")


if __name__ == "__main__":
    print("Executando testes unitarios para integracao com treinar_modelo.py...")
    
    test_get_model_timestamps()
    test_get_model_timestamps_empty_dir()
    test_get_model_timestamps_nonexistent_dir()
    test_validate_model_quality()
    test_get_test_data_for_model()
    test_run_complete_pipeline_no_feedbacks()
    test_run_complete_pipeline_with_feedbacks()
    test_trigger_model_retraining_mock()
    
    print("\nTodos os testes passaram!")
