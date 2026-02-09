#!/bin/bash
# Script para testar classificação de transação única
# Executa POST /v1/classify com app/samples/tx_single.json

set -e

echo "🎯 Testando classificação de transação única..."

# Verificar se o arquivo de exemplo existe
if [ ! -f "app/samples/tx_single.json" ]; then
    echo "❌ Arquivo app/samples/tx_single.json não encontrado!"
    exit 1
fi

# Verificar se a API está rodando
echo "🔍 Verificando se a API está rodando..."
if ! curl -s http://localhost:8080/healthz > /dev/null; then
    echo "❌ API não está rodando em http://localhost:8080"
    echo "💡 Execute 'make run-api' ou 'uvicorn app.main:app --reload --port 8080' primeiro"
    exit 1
fi

echo "✅ API está rodando!"

# Executar teste
echo "📤 Enviando requisição de classificação..."
echo "📄 Arquivo: app/samples/tx_single.json"
echo ""

response=$(curl -s -X POST "http://localhost:8080/v1/classify" \
  -H "Content-Type: application/json" \
  -d @app/samples/tx_single.json)

echo "📊 Resposta da API:"
echo "$response" | jq '.' 2>/dev/null || echo "$response"

echo ""
echo "🔍 Verificando campos obrigatórios..."

# Verificar se jq está disponível
if command -v jq > /dev/null; then
    # Extrair campos importantes
    label=$(echo "$response" | jq -r '.predictions[0].label // "null"')
    confidence=$(echo "$response" | jq -r '.predictions[0].confidence // "null"')
    method_used=$(echo "$response" | jq -r '.predictions[0].method_used // "null"')
    elapsed_ms=$(echo "$response" | jq -r '.predictions[0].elapsed_ms // "null"')
    
    echo "  Label: $label"
    echo "  Confidence: $confidence"
    echo "  Method: $method_used"
    echo "  Elapsed: ${elapsed_ms}ms"
    
    # Verificar se confidence está no range [0,1]
    if [ "$confidence" != "null" ] && [ "$confidence" != "" ]; then
        if (( $(echo "$confidence >= 0 && $confidence <= 1" | bc -l) )); then
            echo "  ✅ Confidence válido (0-1)"
        else
            echo "  ❌ Confidence fora do range [0,1]: $confidence"
        fi
    fi
    
    if [ "$label" != "null" ] && [ "$label" != "" ]; then
        echo "  ✅ Label encontrado"
    else
        echo "  ❌ Label não encontrado"
    fi
else
    echo "  ⚠️  jq não está instalado - não é possível verificar campos automaticamente"
fi

echo ""
echo "✅ Teste concluído!"
