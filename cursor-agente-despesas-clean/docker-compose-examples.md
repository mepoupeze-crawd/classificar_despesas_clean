# Exemplos de Uso do Docker Compose

## Configuração de Arquivos

### docker-compose.yml (Base)
```yaml
services:
  api:
    build: .
    ports:
      - "8080:8080"
    env_file:
      - .env
    environment:
      - PORT=8080
      - MODEL_DIR=/models
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8080/healthz')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
```

### docker-compose.override.yml (Desenvolvimento)
```yaml
services:
  api:
    volumes:
      - ./app:/app/app:ro  # Hot-reload
      - ./modelos:/models:ro  # Modelos locais
      - ./.env:/app/.env:ro  # Configuração local
    environment:
      - ENABLE_FALLBACK_AI=true
      - SIMILARITY_THRESHOLD=0.70
      - MODEL_THRESHOLD=0.70
      - TRAINING_DATA_FILE=modelo_despesas_completo.csv
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload", "--workers", "1"]
    healthcheck:
      disable: true
```

## Comandos de Uso

### Desenvolvimento Local
```bash
# Subir com hot-reload (usa override automaticamente)
docker compose up

# Subir em background
docker compose up -d

# Ver logs em tempo real
docker compose logs -f api

# Parar serviços
docker compose down

# Rebuild e subir
docker compose up --build
```

### Produção (sem override)
```bash
# Subir apenas com configuração base (simula Cloud Run)
docker compose -f docker-compose.yml up

# Ou usar docker run diretamente
docker run --rm -p 8080:8080 --env-file .env ml-service:local
```

## Testes

### Health Check
```bash
# Aguardar inicialização
sleep 10

# Testar health check
curl http://localhost:8080/healthz
```

### Classificação
```bash
# Testar classificação
curl -X POST "http://localhost:8080/v1/classify" \
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

### Erro de Volume
```
ERROR: for api  Cannot start service api: error while creating mount source path
```
**Solução**: Verificar se diretórios `app/` e `modelos/` existem

### Porta em Uso
```
ERROR: bind: address already in use
```
**Solução**: Parar outros serviços na porta 8080 ou usar porta diferente

### Hot-reload Não Funciona
```
WARNING: Watchfiles detected changes in 'app/main.py' but reload is not enabled
```
**Solução**: Verificar se `docker-compose.override.yml` está sendo usado

## Comparação: Docker Compose vs Cloud Run

| Aspecto | Docker Compose (Dev) | Cloud Run (Prod) |
|---------|---------------------|------------------|
| **Volumes** | ✅ Usa volumes locais | ❌ Sem volumes |
| **Hot-reload** | ✅ Suportado | ❌ Não suportado |
| **Arquivos locais** | ✅ Monta do host | ❌ Incluídos na imagem |
| **Configuração** | ✅ docker-compose.yml | ✅ gcloud run deploy |
| **Escalabilidade** | ❌ Single instance | ✅ Auto-scaling |
| **Custo** | ❌ Recursos locais | ✅ Pay-per-use |
| **Manutenção** | ❌ Manual | ✅ Gerenciado |

## Fluxo de Desenvolvimento Recomendado

1. **Desenvolvimento**: Use `docker compose up` para hot-reload
2. **Testes**: Use `docker compose -f docker-compose.yml up` para simular produção
3. **Deploy**: Use `./deploy-gcp.sh` para Cloud Run
4. **Validação**: Use smoke tests para validar antes do deploy
