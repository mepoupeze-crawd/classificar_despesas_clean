# Script PowerShell para testar classificação usando arquivo JSON (sem jq)
# Usa apenas comandos PowerShell nativos

$ErrorActionPreference = "Stop"

$API_URL = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8081" }
$JSON_FILE = if ($args[0]) { $args[0] } else { "app/samples/tx_single.json" }

Write-Host "🧪 Testando classificação usando arquivo JSON" -ForegroundColor Cyan
Write-Host "=============================================="
Write-Host "API URL: $API_URL"
Write-Host "Arquivo: $JSON_FILE"
Write-Host ""

# Verificar se arquivo existe
if (-not (Test-Path $JSON_FILE)) {
    Write-Host "❌ Arquivo não encontrado: $JSON_FILE" -ForegroundColor Red
    Write-Host "💡 Uso: .\scripts\test-from-file.ps1 [caminho-do-arquivo.json]" -ForegroundColor Yellow
    Write-Host "   Exemplo: .\scripts\test-from-file.ps1 app\samples\tx_single.json" -ForegroundColor Yellow
    exit 1
}

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

# 2. Ler arquivo JSON
Write-Host "2️⃣ Lendo arquivo JSON..." -ForegroundColor Yellow
try {
    $jsonContent = Get-Content $JSON_FILE -Raw | ConvertFrom-Json
    Write-Host "✅ Arquivo lido com sucesso" -ForegroundColor Green
    Write-Host "  Transações encontradas: $($jsonContent.Count)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Erro ao ler arquivo JSON: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 3. Converter para JSON string
$jsonPayload = $jsonContent | ConvertTo-Json -Depth 10

# 4. Testar classificação
Write-Host "3️⃣ Enviando requisição de classificação..." -ForegroundColor Yellow

try {
    $response = Invoke-RestMethod -Uri "$API_URL/v1/classify" -Method POST -Body $jsonPayload -ContentType "application/json" -UseBasicParsing
    
    Write-Host "✅ Classificação realizada com sucesso!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Resumo:" -ForegroundColor Cyan
    Write-Host "  Total de transações: $($response.total_transactions)" -ForegroundColor Cyan
    Write-Host "  Predictions retornadas: $($response.predictions.Count)" -ForegroundColor Cyan
    Write-Host "  Tempo total: $($response.elapsed_ms)ms" -ForegroundColor Cyan
    Write-Host ""
    
    # Mostrar cada predição
    if ($response.predictions -and $response.predictions.Count -gt 0) {
        Write-Host "🔍 Detalhes das predições:" -ForegroundColor Yellow
        for ($i = 0; $i -lt $response.predictions.Count; $i++) {
            $pred = $response.predictions[$i]
            Write-Host "  Transação $($i + 1):" -ForegroundColor Cyan
            Write-Host "    Label: $($pred.label)" -ForegroundColor White
            Write-Host "    Confidence: $($pred.confidence)" -ForegroundColor White
            Write-Host "    Method: $($pred.method_used)" -ForegroundColor White
            Write-Host "    Elapsed: $($pred.elapsed_ms)ms" -ForegroundColor White
            if ($pred.transaction_id) {
                Write-Host "    Transaction ID: $($pred.transaction_id)" -ForegroundColor Gray
            }
            Write-Host ""
        }
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

