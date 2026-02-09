#!/bin/bash
# Script para testar a API no Linux/Mac

echo "========================================"
echo " Agente de Despesas - Testar API"
echo "========================================"
echo

# Verificar se curl está disponível
if ! command -v curl &> /dev/null; then
    echo "[ERRO] curl não encontrado!"
    echo "Instale curl primeiro."
    echo
    exit 1
fi

echo "[INFO] Testando API..."
echo

# Testar health check
echo "[TEST] Health Check..."
response=$(curl -s http://localhost:8080/healthz)
if [ $? -ne 0 ]; then
    echo "[ERRO] Falha ao conectar com a API!"
    echo "Certifique-se de que o servidor está rodando em http://localhost:8080"
    echo "Execute 'make run' para iniciar o servidor."
    echo
    exit 1
fi

echo "$response" | jq . 2>/dev/null || echo "$response"
echo
echo

# Testar classificação
echo "[TEST] Classificação de Transações..."
curl -X POST "http://localhost:8080/v1/classify" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "description": "Netflix Com",
      "amount": 44.90,
      "date": "2024-01-01T00:00:00",
      "card_holder": "CC - Aline Silva"
    },
    {
      "description": "Uber Viagem",
      "amount": 25.50,
      "date": "2024-01-01T00:00:00",
      "card_holder": "Final 1234 - Joao Santos"
    }
  ]' | jq . 2>/dev/null || echo "Resposta recebida (jq não disponível)"

echo
echo
echo "[INFO] Testes da API concluídos!"
echo
echo "Para mais testes, acesse:"
echo "  - Swagger UI: http://localhost:8080/docs"
echo "  - ReDoc: http://localhost:8080/redoc"
echo
