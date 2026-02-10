#!/bin/bash
# Script de exemplo para deploy no Google Cloud Run
# Demonstra como configurar e fazer deploy da aplicação

set -e

# Configurações
PROJECT_ID="your-project-id"
SERVICE_NAME="expense-classification"
REGION="us-central1"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Preparando deploy para Cloud Run..."

# 1. Build da imagem
echo "📦 Fazendo build da imagem Docker..."
docker build -t ${IMAGE_NAME} .

# 2. Push para Google Container Registry
echo "⬆️  Fazendo push da imagem..."
docker push ${IMAGE_NAME}

# 3. Deploy no Cloud Run
echo "🌐 Fazendo deploy no Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --port 8080 \
    --memory 1Gi \
    --cpu 1 \
    --max-instances 10 \
    --set-env-vars "PORT=8080,MODEL_DIR=./modelos,SIMILARITY_THRESHOLD=0.70,MODEL_THRESHOLD=0.70,ENABLE_FALLBACK_AI=${ENABLE_FALLBACK_AI:-true},ENABLE_DETERMINISTIC_RULES=false,ENABLE_TFIDF_SIMILARITY=false,USE_PIPELINE_MODEL=true,OPENAI_API_KEY=${OPENAI_API_KEY:-},ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY:-},SERPAPI_API_KEY=${SERPAPI_API_KEY:-}"

echo "✅ Deploy concluído!"
echo "🔗 URL do serviço:"
gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)'

echo "🧪 Testando health check..."
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')
curl -f "${SERVICE_URL}/healthz" && echo "✅ Health check OK!"
