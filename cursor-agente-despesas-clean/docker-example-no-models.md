# Exemplo de uso do Docker sem modelos
# Demonstra como a aplicação funciona com degradação graciosa

# 1. Build da imagem (sem modelos)
docker build -t ml-service:local .

# 2. Executar sem modelos (degradação graciosa)
docker run --rm -p 8080:8080 \
  -e PORT=8080 \
  -e ENABLE_FALLBACK_AI=true \
  -e SIMILARITY_THRESHOLD=0.70 \
  -e MODEL_THRESHOLD=0.70 \
  -e MODEL_DIR=/models \
  ml-service:local

# 3. Em outro terminal, testar:
curl http://localhost:8080/healthz

# 4. Testar classificação (deve retornar "duvida" por falta de modelos)
curl -X POST "http://localhost:8080/v1/classify" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "description": "Netflix Com",
      "amount": 44.90,
      "date": "2024-01-01"
    }
  ]'

# Resultado esperado:
# {
#   "predictions": [
#     {
#       "label": "duvida",
#       "confidence": 0.3,
#       "method_used": "fallback",
#       "elapsed_ms": 5.2,
#       "transaction_id": null,
#       "needs_keys": null,
#       "raw_prediction": {
#         "reason": "no_method_met_threshold"
#       }
#     }
#   ],
#   "elapsed_ms": 15.2,
#   "total_transactions": 1
# }
