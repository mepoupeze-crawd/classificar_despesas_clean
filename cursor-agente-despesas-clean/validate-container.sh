# Comandos de Validação para Container
# Execute estes comandos para validar que a aplicação está funcionando corretamente

# 1. Iniciar servidor local
echo "🚀 Iniciando servidor local..."
uvicorn app.main:app --reload --port 8080

# 2. Testar health check
echo "🏥 Testando health check..."
curl http://127.0.0.1:8080/healthz

# 3. Testar classificação com transação única
echo "🎯 Testando classificação..."
curl -X POST "http://127.0.0.1:8080/v1/classify" \
  -H "Content-Type: application/json" \
  -d @app/samples/tx_single.json

# 4. Testar com porta personalizada
echo "🔧 Testando com porta personalizada..."
PORT=9000 uvicorn app.main:app --reload --port 9000 &
sleep 5
curl http://127.0.0.1:9000/healthz
kill %1

# 5. Testar com variáveis de ambiente personalizadas
echo "⚙️  Testando com variáveis personalizadas..."
SIMILARITY_THRESHOLD=0.80 MODEL_THRESHOLD=0.80 uvicorn app.main:app --reload --port 8080 &
sleep 5
curl http://127.0.0.1:8080/v1/status
kill %1

echo "✅ Todos os testes concluídos!"
