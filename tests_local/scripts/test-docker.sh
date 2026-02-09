#!/bin/bash
# Script de teste para Docker
# Valida se o build e execução do container funcionam corretamente

set -e

echo "🐳 Testando Docker build e execução..."

# 1. Build da imagem
echo "📦 Fazendo build da imagem..."
docker build -t ml-service:local .

# 2. Verificar se a imagem foi criada
echo "✅ Verificando se a imagem foi criada..."
docker images | grep ml-service:local

# 3. Executar container em background
echo "🚀 Executando container..."
docker run -d --name ml-service-test -p 8080:8080 ml-service:local

# 4. Aguardar container inicializar
echo "⏳ Aguardando container inicializar..."
sleep 10

# 5. Testar health check
echo "🏥 Testando health check..."
curl -f http://localhost:8080/healthz || {
    echo "❌ Health check falhou!"
    docker logs ml-service-test
    docker stop ml-service-test
    docker rm ml-service-test
    exit 1
}

# 6. Testar classificação
echo "🎯 Testando classificação..."
response=$(curl -s -X POST "http://localhost:8080/v1/classify" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "description": "Netflix Com",
      "amount": 44.90,
      "date": "2024-01-01"
    }
  ]')

echo "📊 Resposta da classificação:"
echo "$response" | jq '.'

# 7. Verificar se a resposta tem os campos esperados
echo "🔍 Verificando campos da resposta..."
label=$(echo "$response" | jq -r '.predictions[0].label')
confidence=$(echo "$response" | jq -r '.predictions[0].confidence')

if [ "$label" != "null" ] && [ "$label" != "" ]; then
    echo "✅ Label encontrado: $label"
else
    echo "❌ Label não encontrado!"
    docker logs ml-service-test
    docker stop ml-service-test
    docker rm ml-service-test
    exit 1
fi

if [ "$confidence" != "null" ] && [ "$confidence" != "" ]; then
    # Verificar se confidence está entre 0 e 1
    if (( $(echo "$confidence >= 0 && $confidence <= 1" | bc -l) )); then
        echo "✅ Confidence válido: $confidence"
    else
        echo "❌ Confidence fora do range [0,1]: $confidence"
        docker logs ml-service-test
        docker stop ml-service-test
        docker rm ml-service-test
        exit 1
    fi
else
    echo "❌ Confidence não encontrado!"
    docker logs ml-service-test
    docker stop ml-service-test
    docker rm ml-service-test
    exit 1
fi

# 8. Limpar container
echo "🧹 Limpando container..."
docker stop ml-service-test
docker rm ml-service-test

echo "✅ Todos os testes passaram!"
echo "🎉 Container está funcionando corretamente!"
