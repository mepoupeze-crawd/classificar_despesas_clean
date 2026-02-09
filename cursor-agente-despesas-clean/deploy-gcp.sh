#!/bin/bash
# Script de deploy para GCP Cloud Run
# Automatiza build, push e deploy da aplicação

set -e

# Configurações (editar conforme necessário)
PROJECT_ID="${PROJECT_ID:-<YOUR_GCP_PROJECT_ID>}"
SERVICE_NAME="${SERVICE_NAME:-agente-despesas-us}"
REGION="${REGION:-us-central1}"
IMAGE_NAME="us-central1-docker.pkg.dev/${PROJECT_ID}/ml-repo/ml-service"
TAG="${TAG:-v1}"

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
echo "Imagem: $IMAGE_NAME:$TAG"
echo ""

# Verificar se PROJECT_ID foi configurado
if [ "$PROJECT_ID" = "<SEU_PROJECT_ID>" ]; then
    echo -e "${RED}❌ PROJECT_ID não configurado${NC}"
    echo "Configure a variável PROJECT_ID:"
    echo "  export PROJECT_ID=seu-projeto-id"
    echo "  ou edite o script diretamente"
    exit 1
fi

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

# 2. Configurar Docker
echo -e "${YELLOW}🐳 Configurando Docker para GCP...${NC}"
gcloud auth configure-docker southamerica-east1-docker.pkg.dev

# 3. Build e push
echo -e "${YELLOW}📦 Fazendo build e push...${NC}"
gcloud builds submit --tag $IMAGE_NAME:$TAG

# 4. Deploy no Cloud Run
echo -e "${YELLOW}🌐 Fazendo deploy no Cloud Run...${NC}"
echo -e "${YELLOW}📝 Configurando variáveis de ambiente para persistência...${NC}"
echo "  MODEL_DIR=/data/models (volume persistente)"
echo "  FEEDBACK_DIR=/data/feedbacks (volume persistente)"
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:$TAG \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars "PORT=8080,MODEL_DIR=/data/models,FEEDBACK_DIR=/data/feedbacks,SIMILARITY_THRESHOLD=0.70,MODEL_THRESHOLD=0.70,ENABLE_FALLBACK_AI=${ENABLE_FALLBACK_AI:-true},OPENAI_API_KEY=${OPENAI_API_KEY:-},ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-},SERPAPI_API_KEY=${SERPAPI_API_KEY:-}"

# 5. Obter URL do serviço
echo -e "${GREEN}🔗 URL do serviço:${NC}"
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo $SERVICE_URL

# 6. Testar health check
echo -e "${YELLOW}🏥 Testando health check...${NC}"
if curl -s -f "$SERVICE_URL/healthz" > /dev/null; then
    echo -e "${GREEN}✅ Health check OK${NC}"
else
    echo -e "${RED}❌ Health check falhou${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Deploy concluído com sucesso!${NC}"
echo "================================================"
echo -e "${GREEN}✅ Build da imagem: OK${NC}"
echo -e "${GREEN}✅ Push para registry: OK${NC}"
echo -e "${GREEN}✅ Deploy no Cloud Run: OK${NC}"
echo -e "${GREEN}✅ Health check: OK${NC}"
echo ""
echo -e "${YELLOW}💡 Para testar a classificação:${NC}"
echo "curl -X POST \"$SERVICE_URL/v1/classify\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '[{\"description\": \"Netflix Com\", \"amount\": 44.90, \"date\": \"2024-01-01\"}]'"
