# Script PowerShell para testar classificação (sem jq)
# Usa apenas comandos PowerShell nativos

$ErrorActionPreference = "Stop"

$API_URL = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8081" }

Write-Host "🧪 Testando classificação de transações" -ForegroundColor Cyan
Write-Host "========================================"
Write-Host "API URL: $API_URL"
Write-Host ""

# 1. Testar health check primeiro
Write-Host "1️⃣ Testando health check..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$API_URL/healthz" -Method GET -UseBasicParsing
    if ($healthResponse.status -eq "ok") {
        Write-Host "✅ Health check OK" -ForegroundColor Green
    } else {
        Write-Host "❌ Health check falhou" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Erro no health check: $_" -ForegroundColor Red
    Write-Host "💡 Certifique-se de que a API está rodando em $API_URL" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 2. Preparar payload de teste
Write-Host "2️⃣ Preparando payload de teste..." -ForegroundColor Yellow

$testPayload = @(
    @{
        description = "Netflix Com"
        amount = 44.90
        date = "2024-01-01T00:00:00"
    }
)

$jsonPayload = $testPayload | ConvertTo-Json -Depth 10
Write-Host "Payload: $jsonPayload" -ForegroundColor Gray
Write-Host ""

# 3. Testar classificação
Write-Host "3️⃣ Enviando requisição de classificação..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$API_URL/v1/classify" -Method POST -Body $jsonPayload -ContentType "application/json" -UseBasicParsing
    
    Write-Host "✅ Classificação realizada com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Resposta completa:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10 | Write-Host
    
    # Verificar campos
    Write-Host ""
    Write-Host "🔍 Verificando campos..." -ForegroundColor Yellow
    
    if ($response.predictions -and $response.predictions.Count -gt 0) {
        $pred = $response.predictions[0]
        Write-Host "  ✅ Predictions encontradas: $($response.predictions.Count)" -ForegroundColor Green
        Write-Host "  Label: $($pred.label)" -ForegroundColor Cyan
        Write-Host "  Confidence: $($pred.confidence)" -ForegroundColor Cyan
        Write-Host "  Method: $($pred.method_used)" -ForegroundColor Cyan
        Write-Host "  Elapsed: $($pred.elapsed_ms)ms" -ForegroundColor Cyan
        
        # Validar confidence
        if ($pred.confidence -ge 0 -and $pred.confidence -le 1) {
            Write-Host "  ✅ Confidence válido (0-1)" -ForegroundColor Green
        } else {
            Write-Host "  ⚠️ Confidence fora do range [0,1]: $($pred.confidence)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ⚠️ Nenhuma predição encontrada" -ForegroundColor Yellow
    }
    
    if ($response.total_transactions) {
        Write-Host "  Total de transações: $($response.total_transactions)" -ForegroundColor Cyan
    }
    
    if ($response.elapsed_ms) {
        Write-Host "  Tempo total: $($response.elapsed_ms)ms" -ForegroundColor Cyan
    }
    
} catch {
    Write-Host "❌ Erro na classificação: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "Resposta do servidor: $responseBody" -ForegroundColor Yellow
        } catch {
            Write-Host "Não foi possível ler a resposta do servidor" -ForegroundColor Yellow
        }
    }
    exit 1
}

Write-Host ""
Write-Host "🎉 Teste concluído com sucesso!" -ForegroundColor Green

