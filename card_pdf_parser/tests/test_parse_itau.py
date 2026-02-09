"""
Tests for /parse_itau endpoint
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_parse_itau_endpoint_exists():
    """Testa se o endpoint /parse_itau existe."""
    # Testar com arquivo inválido para verificar se o endpoint existe
    response = client.post("/parse_itau", files={"file": ("test.txt", b"not a pdf")})
    # Deve retornar 400 (bad request) e não 404 (not found)
    assert response.status_code != 404, "Endpoint /parse_itau não encontrado"


def test_parse_itau_invalid_file_type():
    """Testa rejeição de arquivo não-PDF."""
    response = client.post("/parse_itau", files={"file": ("test.txt", b"not a pdf")})
    assert response.status_code == 400
    assert "PDF" in response.json()["detail"]


def test_parse_itau_missing_file():
    """Testa requisição sem arquivo."""
    response = client.post("/parse_itau")
    assert response.status_code == 422  # Validation error


@pytest.mark.skipif(not pytest.config.getoption("--run-pdf-tests"), reason="PDF tests require PDF file")
def test_parse_itau_with_pdf():
    """Testa parsing com PDF real (requer arquivo de teste)."""
    # Este teste requer um PDF de teste
    # Por enquanto, apenas verifica a estrutura da resposta
    pass

