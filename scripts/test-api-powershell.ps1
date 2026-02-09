# Script PowerShell para testar API sem jq
# Testa health check e classificação

$ErrorActionPreference = "Stop"

$API_URL = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8081" }

Write-Host "🧪 Testando API de Classificação de Despesas" -ForegroundColor Cyan
Write-Host "=============================================="
Write-Host "API URL: $API_URL"
Write-Host ""

# 1. Testar health check
Write-Host "1️⃣ Testando health check..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$API_URL/healthz" -Method GET -UseBasicParsing
    if ($healthResponse.status -eq "ok") {
        Write-Host "✅ Health check OK: $($healthResponse | ConvertTo-Json)" -ForegroundColor Green
    } else {
        Write-Host "❌ Health check falhou: $($healthResponse | ConvertTo-Json)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Erro no health check: $_" -ForegroundColor Red
    Write-Host "💡 Certifique-se de que a API está rodando em $API_URL" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 2. Testar classificação
Write-Host "2️⃣ Testando classificação..." -ForegroundColor Yellow

$testPayload = @(
    @{
        description = "Netflix Com"
        amount = 44.90
        date = "2024-01-01T00:00:00"
    }
) | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$API_URL/v1/classify" -Method POST -Body $testPayload -ContentType "application/json" -UseBasicParsing
    
    Write-Host "✅ Classificação OK" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Resposta:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10 | Write-Host
    
    # Verificar campos
    if ($response.predictions -and $response.predictions.Count -gt 0) {
        $pred = $response.predictions[0]
        Write-Host ""
        Write-Host "🔍 Campos verificados:" -ForegroundColor Yellow
        Write-Host "  Label: $($pred.label)" -ForegroundColor Cyan
        Write-Host "  Confidence: $($pred.confidence)" -ForegroundColor Cyan
        Write-Host "  Method: $($pred.method_used)" -ForegroundColor Cyan
        Write-Host "  Elapsed: $($pred.elapsed_ms)ms" -ForegroundColor Cyan
    }
} catch {
    Write-Host "❌ Erro na classificação: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "Resposta do servidor: $responseBody" -ForegroundColor Yellow
    }
    exit 1
}

Write-Host ""
Write-Host "🎉 Testes concluídos com sucesso!" -ForegroundColor Green

