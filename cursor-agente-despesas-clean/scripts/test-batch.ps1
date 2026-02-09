# Script PowerShell para testar classificação de lote de transações
# Executa POST /v1/classify com app/samples/tx_batch.json

Write-Host "🎯 Testando classificação de lote de transações..." -ForegroundColor Green

# Verificar se o arquivo de exemplo existe
if (-not (Test-Path "app\samples\tx_batch.json")) {
    Write-Host "❌ Arquivo app\samples\tx_batch.json não encontrado!" -ForegroundColor Red
    exit 1
}

# Verificar se a API está rodando
Write-Host "🔍 Verificando se a API está rodando..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-WebRequest -Uri "http://localhost:8080/healthz" -Method GET -UseBasicParsing
    if ($healthResponse.StatusCode -eq 200) {
        Write-Host "✅ API está rodando!" -ForegroundColor Green
    } else {
        throw "API não respondeu corretamente"
    }
} catch {
    Write-Host "❌ API não está rodando em http://localhost:8080" -ForegroundColor Red
    Write-Host "💡 Execute 'make run-api' ou 'uvicorn app.main:app --reload --port 8080' primeiro" -ForegroundColor Yellow
    exit 1
}

# Executar teste
Write-Host "📤 Enviando requisição de classificação em lote..." -ForegroundColor Yellow
Write-Host "📄 Arquivo: app\samples\tx_batch.json" -ForegroundColor Cyan
Write-Host ""

try {
    $body = Get-Content "app\samples\tx_batch.json" -Raw
    $response = Invoke-WebRequest -Uri "http://localhost:8080/v1/classify" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    
    Write-Host "📊 Resposta da API:" -ForegroundColor Green
    $jsonResponse = $response.Content | ConvertFrom-Json
    $jsonResponse | ConvertTo-Json -Depth 10 | Write-Host
    
    Write-Host ""
    Write-Host "🔍 Verificando campos obrigatórios..." -ForegroundColor Yellow
    
    # Verificar informações do lote
    Write-Host "  Total de transações: $($jsonResponse.total_transactions)" -ForegroundColor Cyan
    Write-Host "  Predictions retornadas: $($jsonResponse.predictions.Count)" -ForegroundColor Cyan
    Write-Host "  Tempo total: $($jsonResponse.elapsed_ms)ms" -ForegroundColor Cyan
    
    # Verificar cada predição
    for ($i = 0; $i -lt $jsonResponse.predictions.Count; $i++) {
        $prediction = $jsonResponse.predictions[$i]
        Write-Host "  Transação $($i + 1):" -ForegroundColor Cyan
        Write-Host "    Label: $($prediction.label)" -ForegroundColor White
        Write-Host "    Confidence: $($prediction.confidence)" -ForegroundColor White
        Write-Host "    Method: $($prediction.method_used)" -ForegroundColor White
        
        # Verificar se confidence está no range [0,1]
        if ($prediction.confidence -ge 0 -and $prediction.confidence -le 1) {
            Write-Host "    ✅ Confidence válido (0-1)" -ForegroundColor Green
        } else {
            Write-Host "    ❌ Confidence fora do range [0,1]: $($prediction.confidence)" -ForegroundColor Red
        }
    }
    
} catch {
    Write-Host "❌ Erro ao executar teste: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Teste de lote concluído!" -ForegroundColor Green
