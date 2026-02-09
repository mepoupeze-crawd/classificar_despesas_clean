#!/bin/bash
# Script de smoke test para container Docker
# Testa build, execução, health check e classificação

set -e

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Variáveis
IMAGE_NAME="ml-service:local"
CONTAINER_NAME="ml-service-smoke-test"
PORT="8081"
HEALTH_URL="http://localhost:$PORT/healthz"
CLASSIFY_URL="http://localhost:$PORT/v1/classify"
MAX_WAIT_TIME=30
POLL_INTERVAL=2

# Função para limpeza
cleanup() {
    echo -e "\n${YELLOW}🧹 Limpando container...${NC}"
    docker stop "$CONTAINER_NAME" 2>/dev/null || true
    docker rm "$CONTAINER_NAME" 2>/dev/null || true
}

# Registrar trap para limpeza sempre
trap cleanup EXIT

echo -e "${GREEN}🚀 Iniciando smoke test do container Docker${NC}"
echo "================================================"

# 1. Build da imagem
echo -e "\n${YELLOW}📦 Fazendo build da imagem...${NC}"
if ! docker build -t "$IMAGE_NAME" .; then
    echo -e "${RED}❌ Erro no build da imagem${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Build concluído${NC}"

# 2. Executar container em background
echo -e "\n${YELLOW}🚀 Executando container em background...${NC}"
if ! docker run -d --name "$CONTAINER_NAME" -p "$PORT:8080" "$IMAGE_NAME"; then
    echo -e "${RED}❌ Erro ao executar container${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Container iniciado${NC}"

# 3. Polling de /healthz
echo -e "\n${YELLOW}🏥 Aguardando health check...${NC}"
echo "URL: $HEALTH_URL"
echo "Timeout: ${MAX_WAIT_TIME}s"

elapsed=0
while [ $elapsed -lt $MAX_WAIT_TIME ]; do
    if curl -s -f "$HEALTH_URL" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Health check OK (${elapsed}s)${NC}"
        break
    fi
    
    echo -n "."
    sleep $POLL_INTERVAL
    elapsed=$((elapsed + POLL_INTERVAL))
done

if [ $elapsed -ge $MAX_WAIT_TIME ]; then
    echo -e "\n${RED}❌ Timeout no health check após ${MAX_WAIT_TIME}s${NC}"
    echo -e "${YELLOW}📋 Logs do container:${NC}"
    docker logs "$CONTAINER_NAME"
    exit 1
fi

# 4. Testar classificação
echo -e "\n${YELLOW}🎯 Testando classificação...${NC}"

# Verificar se arquivo de exemplo existe
if [ ! -f "app/samples/tx_single.json" ]; then
    echo -e "${RED}❌ Arquivo app/samples/tx_single.json não encontrado${NC}"
    exit 1
fi

echo "📄 Arquivo: app/samples/tx_single.json"
echo "📤 Enviando requisição..."

# Executar POST /v1/classify
response=$(curl -s -w "\n%{http_code}" -X POST "$CLASSIFY_URL" \
    -H "Content-Type: application/json" \
    -d @app/samples/tx_single.json)

# Separar resposta e código HTTP
http_code=$(echo "$response" | tail -n1)
response_body=$(echo "$response" | head -n -1)

echo "📊 Código HTTP: $http_code"

# 5. Verificar HTTP 200
if [ "$http_code" != "200" ]; then
    echo -e "${RED}❌ HTTP $http_code - Esperado 200${NC}"
    echo -e "${YELLOW}📋 Resposta:${NC}"
    echo "$response_body"
    exit 1
fi
echo -e "${GREEN}✅ HTTP 200 OK${NC}"

# 6. Verificar presença de predictions[0].label
echo -e "\n${YELLOW}🔍 Verificando campos obrigatórios...${NC}"

if command -v jq > /dev/null; then
    # Usar jq se disponível
    label=$(echo "$response_body" | jq -r '.predictions[0].label // "null"')
    confidence=$(echo "$response_body" | jq -r '.predictions[0].confidence // "null"')
    method_used=$(echo "$response_body" | jq -r '.predictions[0].method_used // "null"')
    
    echo "📊 Resposta da API:"
    echo "$response_body" | jq '.'
    
    echo ""
    echo "🔍 Campos verificados:"
    echo "  Label: $label"
    echo "  Confidence: $confidence"
    echo "  Method: $method_used"
    
    if [ "$label" != "null" ] && [ "$label" != "" ]; then
        echo -e "${GREEN}✅ Label encontrado: $label${NC}"
    else
        echo -e "${RED}❌ Label não encontrado${NC}"
        exit 1
    fi
    
    if [ "$confidence" != "null" ] && [ "$confidence" != "" ]; then
        if (( $(echo "$confidence >= 0 && $confidence <= 1" | bc -l) )); then
            echo -e "${GREEN}✅ Confidence válido: $confidence${NC}"
        else
            echo -e "${RED}❌ Confidence fora do range [0,1]: $confidence${NC}"
            exit 1
        fi
    else
        echo -e "${RED}❌ Confidence não encontrado${NC}"
        exit 1
    fi
else
    # Fallback sem jq
    echo -e "${YELLOW}⚠️  jq não está instalado - verificando com grep${NC}"
    echo "📊 Resposta da API:"
    echo "$response_body"
    
    if echo "$response_body" | grep -q '"label"'; then
        echo -e "${GREEN}✅ Campo 'label' encontrado${NC}"
    else
        echo -e "${RED}❌ Campo 'label' não encontrado${NC}"
        exit 1
    fi
    
    if echo "$response_body" | grep -q '"confidence"'; then
        echo -e "${GREEN}✅ Campo 'confidence' encontrado${NC}"
    else
        echo -e "${RED}❌ Campo 'confidence' não encontrado${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}🎉 Smoke test concluído com sucesso!${NC}"
echo "================================================"
echo -e "${GREEN}✅ Build da imagem: OK${NC}"
echo -e "${GREEN}✅ Container executando: OK${NC}"
echo -e "${GREEN}✅ Health check: OK${NC}"
echo -e "${GREEN}✅ Classificação: OK${NC}"
echo -e "${GREEN}✅ Campos obrigatórios: OK${NC}"
echo ""
echo -e "${YELLOW}💡 Container será parado automaticamente${NC}"
