# Exemplos de Uso do Smoke Test

## O que é o Smoke Test

O smoke test é um teste automatizado que valida todo o ciclo de vida do container Docker:
1. **Build** da imagem `ml-service:local`
2. **Execução** em background expondo porta 8080
3. **Polling** de `/healthz` até 30s
4. **POST** `/v1/classify` com `app/samples/tx_single.json`
5. **Verificação** de HTTP 200 e presença de `predictions[0].label`
6. **Limpeza** automática do container (sempre, mesmo em erro)

## Comandos de Execução

### Unix/Linux/macOS
```bash
# Tornar script executável
chmod +x scripts/docker-smoke.sh

# Executar smoke test
./scripts/docker-smoke.sh
```

### Windows (CMD)
```cmd
REM Executar smoke test
scripts\docker-smoke.bat
```

### Windows (PowerShell)
```powershell
# Executar smoke test
.\scripts\docker-smoke.ps1

# Com parâmetros personalizados
.\scripts\docker-smoke.ps1 -MaxWaitTime 60 -PollInterval 3
```

## Saída Esperada (Sucesso)

```
🚀 Iniciando smoke test do container Docker
================================================

📦 Fazendo build da imagem...
✅ Build concluído

🚀 Executando container em background...
✅ Container iniciado

🏥 Aguardando health check...
URL: http://localhost:8080/healthz
Timeout: 30s
✅ Health check OK (5s)

🎯 Testando classificação...
📄 Arquivo: app/samples/tx_single.json
📤 Enviando requisição...
📊 Código HTTP: 200
✅ HTTP 200 OK

🔍 Verificando campos obrigatórios...
📊 Resposta da API:
{
  "predictions": [
    {
      "label": "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)",
      "confidence": 0.95,
      "method_used": "model_adapter",
      "elapsed_ms": 5.2,
      "transaction_id": null,
      "needs_keys": null
    }
  ],
  "elapsed_ms": 15.2,
  "total_transactions": 1
}

🔍 Campos verificados:
  Label: Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)
  Confidence: 0.95
  Method: model_adapter
✅ Label encontrado: Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)
✅ Confidence válido: 0.95

🎉 Smoke test concluído com sucesso!
================================================
✅ Build da imagem: OK
✅ Container executando: OK
✅ Health check: OK
✅ Classificação: OK
✅ Campos obrigatórios: OK

💡 Container será parado automaticamente
```

## Critérios de Sucesso

- ✅ **Status de saída**: 0 (sucesso) ou ≠0 (erro)
- ✅ **Build**: Imagem construída sem erros
- ✅ **Container**: Executando em background na porta 8080
- ✅ **Health check**: Responde `/healthz` em até 30s
- ✅ **Classificação**: POST `/v1/classify` retorna HTTP 200
- ✅ **Campos obrigatórios**: `predictions[0].label` presente
- ✅ **Limpeza**: Container parado automaticamente

## Troubleshooting

### Timeout no Health Check
```
❌ Timeout no health check após 30s
📋 Logs do container:
```
**Solução**: Verificar se Docker está rodando e porta 8080 está livre

### Erro no Build
```
❌ Erro no build da imagem
```
**Solução**: Verificar se Dockerfile existe e dependências estão corretas

### Campos Não Encontrados
```
❌ Label não encontrado
```
**Solução**: Verificar se modelos estão presentes no container

## Integração com CI/CD

O smoke test pode ser facilmente integrado em pipelines de CI/CD:

```yaml
# GitHub Actions exemplo
- name: Smoke Test
  run: ./scripts/docker-smoke.sh

# GitLab CI exemplo
smoke_test:
  script:
    - ./scripts/docker-smoke.sh
```
