#!/bin/bash
# Script para testar classificação de lote de transações
# Executa POST /v1/classify com app/samples/tx_batch.json

set -e

echo "🎯 Testando classificação de lote de transações..."

# Verificar se o arquivo de exemplo existe
if [ ! -f "app/samples/tx_batch.json" ]; then
    echo "❌ Arquivo app/samples/tx_batch.json não encontrado!"
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
echo "📤 Enviando requisição de classificação em lote..."
echo "📄 Arquivo: app/samples/tx_batch.json"
echo ""

response=$(curl -s -X POST "http://localhost:8080/v1/classify" \
  -H "Content-Type: application/json" \
  -d @app/samples/tx_batch.json)

echo "📊 Resposta da API:"
echo "$response" | jq '.' 2>/dev/null || echo "$response"

echo ""
echo "🔍 Verificando campos obrigatórios..."

# Verificar se jq está disponível
if command -v jq > /dev/null; then
    # Extrair informações do lote
    total_transactions=$(echo "$response" | jq -r '.total_transactions // "null"')
    total_elapsed_ms=$(echo "$response" | jq -r '.elapsed_ms // "null"')
    predictions_count=$(echo "$response" | jq -r '.predictions | length')
    
    echo "  Total de transações: $total_transactions"
    echo "  Predictions retornadas: $predictions_count"
    echo "  Tempo total: ${total_elapsed_ms}ms"
    
    # Verificar cada predição
    for i in $(seq 0 $((predictions_count - 1))); do
        label=$(echo "$response" | jq -r ".predictions[$i].label // \"null\"")
        confidence=$(echo "$response" | jq -r ".predictions[$i].confidence // \"null\"")
        method_used=$(echo "$response" | jq -r ".predictions[$i].method_used // \"null\"")
        
        echo "  Transação $((i + 1)):"
        echo "    Label: $label"
        echo "    Confidence: $confidence"
        echo "    Method: $method_used"
        
        # Verificar se confidence está no range [0,1]
        if [ "$confidence" != "null" ] && [ "$confidence" != "" ]; then
            if (( $(echo "$confidence >= 0 && $confidence <= 1" | bc -l) )); then
                echo "    ✅ Confidence válido (0-1)"
            else
                echo "    ❌ Confidence fora do range [0,1]: $confidence"
            fi
        fi
    done
else
    echo "  ⚠️  jq não está instalado - não é possível verificar campos automaticamente"
fi

echo ""
echo "✅ Teste de lote concluído!"
