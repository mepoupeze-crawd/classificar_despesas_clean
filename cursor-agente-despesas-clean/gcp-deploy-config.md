# Configurações de Deploy para GCP Cloud Run

## Variáveis de Ambiente por Ambiente

### Desenvolvimento
```bash
export PROJECT_ID="meu-projeto-dev"
export SERVICE_NAME="ml-service-dev"
export TAG="dev-v1"
export REGION="southamerica-east1"
```

### Staging
```bash
export PROJECT_ID="meu-projeto-staging"
export SERVICE_NAME="ml-service-staging"
export TAG="staging-v1"
export REGION="southamerica-east1"
```

### Produção
```bash
export PROJECT_ID="meu-projeto-prod"
export SERVICE_NAME="ml-service"
export TAG="v1"
export REGION="southamerica-east1"
```

## Comandos de Deploy

### Deploy Rápido
```bash
# Configurar ambiente
export PROJECT_ID="meu-projeto"
export TAG="v1"

# Deploy
./deploy-gcp.sh
```

### Deploy com Configurações Personalizadas
```bash
# Deploy com configurações específicas
PROJECT_ID="meu-projeto" \
SERVICE_NAME="ml-service-custom" \
TAG="custom-v1" \
REGION="us-central1" \
./deploy-gcp.sh
```

## Validação Pós-Deploy

### Health Check
```bash
# Obter URL do serviço
SERVICE_URL=$(gcloud run services describe ml-service --region southamerica-east1 --format 'value(status.url)')

# Testar health check
curl -f "$SERVICE_URL/healthz"
```

### Teste de Classificação
```bash
# Testar classificação
curl -X POST "$SERVICE_URL/v1/classify" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "description": "Netflix Com",
      "amount": 44.90,
      "date": "2024-01-01"
    }
  ]'
```

## Troubleshooting

### Erro de Autenticação
```bash
# Reautenticar
gcloud auth login
gcloud auth configure-docker southamerica-east1-docker.pkg.dev
```

### Erro de Permissões
```bash
# Verificar permissões
gcloud projects get-iam-policy $PROJECT_ID

# Adicionar permissões necessárias
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="user:seu-email@exemplo.com" \
  --role="roles/run.admin"
```

### Erro de Registry
```bash
# Criar registry se não existir
gcloud artifacts repositories create ml-repo \
  --repository-format=docker \
  --location=southamerica-east1
```
