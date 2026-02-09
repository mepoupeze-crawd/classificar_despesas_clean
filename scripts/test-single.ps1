# Script PowerShell para testar classificação de transação única
# Executa POST /v1/classify com app/samples/tx_single.json

Write-Host "🎯 Testando classificação de transação única..." -ForegroundColor Green

# Verificar se o arquivo de exemplo existe
if (-not (Test-Path "app\samples\tx_single.json")) {
    Write-Host "❌ Arquivo app\samples\tx_single.json não encontrado!" -ForegroundColor Red
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
Write-Host "📤 Enviando requisição de classificação..." -ForegroundColor Yellow
Write-Host "📄 Arquivo: app\samples\tx_single.json" -ForegroundColor Cyan
Write-Host ""

try {
    $body = Get-Content "app\samples\tx_single.json" -Raw
    $response = Invoke-WebRequest -Uri "http://localhost:8080/v1/classify" -Method POST -Body $body -ContentType "application/json" -UseBasicParsing
    
    Write-Host "📊 Resposta da API:" -ForegroundColor Green
    $jsonResponse = $response.Content | ConvertFrom-Json
    $jsonResponse | ConvertTo-Json -Depth 10 | Write-Host
    
    Write-Host ""
    Write-Host "🔍 Verificando campos obrigatórios..." -ForegroundColor Yellow
    
    # Verificar campos importantes
    $prediction = $jsonResponse.predictions[0]
    Write-Host "  Label: $($prediction.label)" -ForegroundColor Cyan
    Write-Host "  Confidence: $($prediction.confidence)" -ForegroundColor Cyan
    Write-Host "  Method: $($prediction.method_used)" -ForegroundColor Cyan
    Write-Host "  Elapsed: $($prediction.elapsed_ms)ms" -ForegroundColor Cyan
    
    # Verificar se confidence está no range [0,1]
    if ($prediction.confidence -ge 0 -and $prediction.confidence -le 1) {
        Write-Host "  ✅ Confidence válido (0-1)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Confidence fora do range [0,1]: $($prediction.confidence)" -ForegroundColor Red
    }
    
    if ($prediction.label -and $prediction.label -ne "") {
        Write-Host "  ✅ Label encontrado" -ForegroundColor Green
    } else {
        Write-Host "  ❌ Label não encontrado" -ForegroundColor Red
    }
    
} catch {
    Write-Host "❌ Erro ao executar teste: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Teste concluído!" -ForegroundColor Green
