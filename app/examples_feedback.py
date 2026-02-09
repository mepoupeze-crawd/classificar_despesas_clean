#!/usr/bin/env python3
"""
Exemplos de uso do endpoint de feedback.

Este script demonstra como usar o endpoint POST /v1/feedback
para registrar correções do usuário em transações classificadas.
"""

import requests
import json
from datetime import datetime

# URL base da API
BASE_URL = "http://localhost:8081"

def test_single_feedback():
    """Testa feedback com item único."""
    print("=== Teste: Feedback Único ===")
    
    payload = {
        "feedback": {
            "transactionId": "tx_example_001",
            "description": "Netflix Com",
            "amount": 44.90,
            "date": "2024-01-01T00:00:00Z",
            "source": "crédito",
            "card": "Final 0001 - USUARIO EXEMPLO",
            "category": "Entretenimento",
            "parcelas": 1,
            "modelVersion": "v1.2.0"
        }
    }
    
    response = requests.post(f"{BASE_URL}/v1/feedback", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_batch_feedback():
    """Testa feedback com múltiplos itens."""
    print("=== Teste: Feedback em Lote ===")
    
    payload = {
        "feedback": [
            {
                "transactionId": "tx_example_002",
                "description": "Pao De Acucar-0061",
                "amount": 401.68,
                "date": "2024-01-02T00:00:00Z",
                "source": "crédito",
                "card": "Final 0001 - USUARIO EXEMPLO",
                "category": "Supermercado",
                "parcelas": 1,
                "modelVersion": "v1.2.0"
            },
            {
                "transactionId": "tx_example_003",
                "description": "Anuidade Diferenciada",
                "amount": 0.01,
                "date": "2024-01-03T00:00:00Z",
                "source": "crédito",
                "card": "Final 0001 - USUARIO EXEMPLO",
                "category": "Gastos com mensalidades",
                "parcelas": 12,
                "numero_parcela": 4,
                "modelVersion": "v1.2.0"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/v1/feedback", json=payload)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_file_info():
    """Testa endpoint de informações do arquivo."""
    print("=== Teste: Informações do Arquivo ===")
    
    response = requests.get(f"{BASE_URL}/v1/feedback/file-info")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

def test_file_info_with_date():
    """Testa endpoint de informações do arquivo com data específica."""
    print("=== Teste: Informações do Arquivo (Data Específica) ===")
    
    response = requests.get(f"{BASE_URL}/v1/feedback/file-info?date=2025-10-21")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    print()

if __name__ == "__main__":
    print("🧪 Testando Endpoint de Feedback")
    print("=" * 50)
    
    try:
        test_single_feedback()
        test_batch_feedback()
        test_file_info()
        test_file_info_with_date()
        
        print("✅ Todos os testes executados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")
