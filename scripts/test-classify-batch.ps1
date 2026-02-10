# Script PowerShell para testar classificação em lote (sem jq)
# Usa apenas comandos PowerShell nativos

$ErrorActionPreference = "Stop"

$API_URL = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8081" }

Write-Host "🧪 Testando classificação em lote" -ForegroundColor Cyan
Write-Host "=================================="
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
    exit 1
}

Write-Host ""

# 2. Preparar payload de teste (múltiplas transações)
Write-Host "2️⃣ Preparando payload de teste (lote)..." -ForegroundColor Yellow

$testPayload = @(
    @{
        description = "Netflix Com"
        amount = 44.90
        date = "2024-01-01T00:00:00"
    },
    @{
        description = "Supermercado Extra"
        amount = 250.50
        date = "2024-01-02T00:00:00"
    },
    @{
        description = "Posto Shell"
        amount = 150.00
        date = "2024-01-03T00:00:00"
    }
)

$jsonPayload = $testPayload | ConvertTo-Json -Depth 10
Write-Host "Payload: $($testPayload.Count) transações" -ForegroundColor Gray
Write-Host ""

# 3. Testar classificação
Write-Host "3️⃣ Enviando requisição de classificação em lote..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$API_URL/v1/classify" -Method POST -Body $jsonPayload -ContentType "application/json" -UseBasicParsing
    
    Write-Host "✅ Classificação em lote realizada com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Resumo:" -ForegroundColor Cyan
    Write-Host "  Total de transações: $($response.total_transactions)" -ForegroundColor Cyan
    Write-Host "  Predictions retornadas: $($response.predictions.Count)" -ForegroundColor Cyan
    Write-Host "  Tempo total: $($response.elapsed_ms)ms" -ForegroundColor Cyan
    Write-Host ""
    
    # Mostrar cada predição
    Write-Host "🔍 Detalhes das predições:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $response.predictions.Count; $i++) {
        $pred = $response.predictions[$i]
        Write-Host "  Transação $($i + 1):" -ForegroundColor Cyan
        Write-Host "    Label: $($pred.label)" -ForegroundColor Gray
        Write-Host "    Confidence: $($pred.confidence)" -ForegroundColor Gray
        Write-Host "    Method: $($pred.method_used)" -ForegroundColor Gray
        Write-Host "    Elapsed: $($pred.elapsed_ms)ms" -ForegroundColor Gray
        Write-Host ""
    }
    
    Write-Host "📊 Resposta completa (JSON):" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10 | Write-Host
    
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

