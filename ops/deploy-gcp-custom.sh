#!/bin/bash
# Script de deploy customizado para GCP Cloud Run
# Configurado para: <YOUR_PROJECT_ID>, us-central1, agente-despesas-us

set -e

# Configurações específicas
PROJECT_ID="${PROJECT_ID:-YOUR_GCP_PROJECT_ID}"
SERVICE_NAME="agente-despesas-us"
REGION="us-central1"
TAG="${TAG:-latest}"

# Cores para output
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Deploy para GCP Cloud Run${NC}"
echo "================================================"
echo "Projeto: $PROJECT_ID"
echo "Serviço: $SERVICE_NAME"
echo "Região: $REGION"
echo ""

# Verificar se gcloud está instalado
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI não encontrado${NC}"
    echo "Instale o Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Verificar se está autenticado
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${RED}❌ Não autenticado no gcloud${NC}"
    echo "Execute: gcloud auth login"
    exit 1
fi

# 1. Configurar projeto
echo -e "${YELLOW}📋 Configurando projeto...${NC}"
gcloud config set project $PROJECT_ID

# 2. Ler API keys do .env se existir
OPENAI_KEY=""
SERPAPI_KEY=""
ANTHROPIC_KEY=""

if [ -f .env ]; then
    echo -e "${YELLOW}📄 Lendo API keys do arquivo .env...${NC}"
    while IFS= read -r line || [ -n "$line" ]; do
        # Ignorar comentários e linhas vazias
        if [[ $line =~ ^[[:space:]]*# ]] || [[ -z "${line// }" ]]; then
            continue
        fi
        # Extrair OPENAI_API_KEY
        if [[ $line =~ ^OPENAI_API_KEY=(.+)$ ]]; then
            OPENAI_KEY="${BASH_REMATCH[1]}"
            # Remover aspas se houver
            OPENAI_KEY="${OPENAI_KEY#\"}"
            OPENAI_KEY="${OPENAI_KEY%\"}"
            OPENAI_KEY="${OPENAI_KEY#\'}"
            OPENAI_KEY="${OPENAI_KEY%\'}"
            echo "  ✅ OPENAI_API_KEY encontrada (${#OPENAI_KEY} caracteres)"
        fi
        # Extrair SERPAPI_API_KEY
        if [[ $line =~ ^SERPAPI_API_KEY=(.+)$ ]]; then
            SERPAPI_KEY="${BASH_REMATCH[1]}"
            # Remover aspas se houver
            SERPAPI_KEY="${SERPAPI_KEY#\"}"
            SERPAPI_KEY="${SERPAPI_KEY%\"}"
            SERPAPI_KEY="${SERPAPI_KEY#\'}"
            SERPAPI_KEY="${SERPAPI_KEY%\'}"
            echo "  ✅ SERPAPI_API_KEY encontrada (${#SERPAPI_KEY} caracteres)"
        fi
        # Extrair ANTHROPIC_API_KEY
        if [[ $line =~ ^ANTHROPIC_API_KEY=(.+)$ ]]; then
            ANTHROPIC_KEY="${BASH_REMATCH[1]}"
            # Remover aspas se houver
            ANTHROPIC_KEY="${ANTHROPIC_KEY#\"}"
            ANTHROPIC_KEY="${ANTHROPIC_KEY%\"}"
            ANTHROPIC_KEY="${ANTHROPIC_KEY#\'}"
            ANTHROPIC_KEY="${ANTHROPIC_KEY%\'}"
            echo "  ✅ ANTHROPIC_API_KEY encontrada (${#ANTHROPIC_KEY} caracteres)"
        fi
    done < .env
fi

# 3. Verificar se API keys foram encontradas ou estão em variáveis de ambiente
if [ -z "$OPENAI_KEY" ] && [ -n "${OPENAI_API_KEY}" ]; then
    OPENAI_KEY="${OPENAI_API_KEY}"
    echo "  ✅ OPENAI_API_KEY encontrada em variável de ambiente"
fi

if [ -z "$SERPAPI_KEY" ] && [ -n "${SERPAPI_API_KEY}" ]; then
    SERPAPI_KEY="${SERPAPI_API_KEY}"
    echo "  ✅ SERPAPI_API_KEY encontrada em variável de ambiente"
fi

if [ -z "$ANTHROPIC_KEY" ] && [ -n "${ANTHROPIC_API_KEY}" ]; then
    ANTHROPIC_KEY="${ANTHROPIC_API_KEY}"
    echo "  ✅ ANTHROPIC_API_KEY encontrada em variável de ambiente"
fi

# 4. Construir string de variáveis de ambiente
ENV_VARS="PORT=8080,MODEL_DIR=/models,SIMILARITY_THRESHOLD=0.70,MODEL_THRESHOLD=0.70,ENABLE_FALLBACK_AI=true"

if [ -n "$OPENAI_KEY" ]; then
    ENV_VARS="${ENV_VARS},OPENAI_API_KEY=${OPENAI_KEY}"
    echo -e "${GREEN}  ✅ OPENAI_API_KEY será configurada no deploy${NC}"
else
    echo -e "${YELLOW}  ⚠️  OPENAI_API_KEY não encontrada${NC}"
fi

if [ -n "$SERPAPI_KEY" ]; then
    ENV_VARS="${ENV_VARS},SERPAPI_API_KEY=${SERPAPI_KEY}"
    echo -e "${GREEN}  ✅ SERPAPI_API_KEY será configurada no deploy${NC}"
else
    echo -e "${YELLOW}  ⚠️  SERPAPI_API_KEY não encontrada${NC}"
fi

if [ -n "$ANTHROPIC_KEY" ]; then
    ENV_VARS="${ENV_VARS},ANTHROPIC_API_KEY=${ANTHROPIC_KEY}"
    echo -e "${GREEN}  ✅ ANTHROPIC_API_KEY será configurada no deploy${NC}"
fi

echo ""

# 5. Build e deploy usando --source (build source-based do Cloud Run)
echo -e "${YELLOW}📦 Fazendo build e deploy (source-based)...${NC}"
gcloud run deploy $SERVICE_NAME \
  --source . \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars "$ENV_VARS"

# 6. Obter URL do serviço
echo ""
echo -e "${GREEN}🔗 URL do serviço:${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo $SERVICE_URL

# 7. Aguardar alguns segundos para o serviço inicializar
echo ""
echo -e "${YELLOW}⏳ Aguardando inicialização do serviço...${NC}"
sleep 10

# 8. Testar health check
echo -e "${YELLOW}🏥 Testando health check...${NC}"
if curl -s -f "$SERVICE_URL/healthz" > /dev/null; then
    echo -e "${GREEN}✅ Health check OK${NC}"
else
    echo -e "${RED}❌ Health check falhou${NC}"
    exit 1
fi

# 9. Verificar status das API keys
echo ""
echo -e "${YELLOW}🔍 Verificando status das API keys...${NC}"
STATUS_RESPONSE=$(curl -s "$SERVICE_URL/v1/status")

# Extrair informações sobre API keys
if echo "$STATUS_RESPONSE" | grep -q '"has_valid_keys":true'; then
    echo -e "${GREEN}✅ API keys detectadas e válidas!${NC}"
    HAS_VALID_KEYS=true
else
    echo -e "${RED}❌ API keys não detectadas ou inválidas${NC}"
    HAS_VALID_KEYS=false
fi

# Mostrar detalhes
echo ""
echo "Detalhes das API keys:"
echo "$STATUS_RESPONSE" | grep -o '"ai_providers":{[^}]*}' || echo "  Não foi possível extrair informações"
echo "$STATUS_RESPONSE" | grep -o '"ai_fallback":{[^}]*}' || echo "  Não foi possível extrair informações"

echo ""
echo -e "${GREEN}🎉 Deploy concluído!${NC}"
echo "================================================"
echo -e "${GREEN}✅ Build e deploy: OK${NC}"
echo -e "${GREEN}✅ Health check: OK${NC}"
if [ "$HAS_VALID_KEYS" = true ]; then
    echo -e "${GREEN}✅ API keys: DETECTADAS${NC}"
else
    echo -e "${RED}❌ API keys: NÃO DETECTADAS${NC}"
    echo ""
    echo -e "${YELLOW}💡 Verifique:${NC}"
    echo "  1. Se as chaves estão no arquivo .env"
    echo "  2. Se as chaves não têm aspas extras"
    echo "  3. Se as chaves não estão vazias"
    echo "  4. Logs do serviço: gcloud run services logs read $SERVICE_NAME --region $REGION"
fi
echo ""
echo -e "${YELLOW}💡 Para testar a classificação:${NC}"
echo "curl -X POST \"$SERVICE_URL/v1/classify\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '[{\"description\": \"Netflix Com\", \"amount\": 44.90, \"date\": \"2024-01-01\"}]'"





