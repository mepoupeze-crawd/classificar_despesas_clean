# Script de smoke test para container Docker (PowerShell)
# Testa build, execução, health check e classificação

param(
    [int]$MaxWaitTime = 30,
    [int]$PollInterval = 2
)

# Variáveis
$ImageName = "ml-service:local"
$ContainerName = "ml-service-smoke-test"
$Port = 8081
$HealthUrl = "http://localhost:$Port/healthz"
$ClassifyUrl = "http://localhost:$Port/v1/classify"

# Função para limpeza
function Cleanup {
    Write-Host "`n🧹 Limpando container..." -ForegroundColor Yellow
    try {
        docker stop $ContainerName 2>$null
        docker rm $ContainerName 2>$null
    } catch {
        # Ignorar erros de limpeza
    }
}

# Registrar limpeza no final
$null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { Cleanup }

Write-Host "🚀 Iniciando smoke test do container Docker" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

try {
    # 1. Build da imagem
    Write-Host "`n📦 Fazendo build da imagem..." -ForegroundColor Yellow
    $buildResult = docker build -t $ImageName .
    if ($LASTEXITCODE -ne 0) {
        throw "Erro no build da imagem"
    }
    Write-Host "✅ Build concluído" -ForegroundColor Green

    # 2. Executar container em background
    Write-Host "`n🚀 Executando container em background..." -ForegroundColor Yellow
    $runResult = docker run -d --name $ContainerName -p "${Port}:8080" $ImageName
    if ($LASTEXITCODE -ne 0) {
        throw "Erro ao executar container"
    }
    Write-Host "✅ Container iniciado" -ForegroundColor Green

    # 3. Polling de /healthz
    Write-Host "`n🏥 Aguardando health check..." -ForegroundColor Yellow
    Write-Host "URL: $HealthUrl" -ForegroundColor Cyan
    Write-Host "Timeout: ${MaxWaitTime}s" -ForegroundColor Cyan

    $elapsed = 0
    $healthOk = $false
    
    while ($elapsed -lt $MaxWaitTime) {
        try {
            $healthResponse = Invoke-WebRequest -Uri $HealthUrl -Method GET -UseBasicParsing -TimeoutSec 5
            if ($healthResponse.StatusCode -eq 200) {
                Write-Host "`n✅ Health check OK (${elapsed}s)" -ForegroundColor Green
                $healthOk = $true
                break
            }
        } catch {
            # Continuar tentando
        }
        
        Write-Host "." -NoNewline -ForegroundColor Yellow
        Start-Sleep -Seconds $PollInterval
        $elapsed += $PollInterval
    }

    if (-not $healthOk) {
        Write-Host "`n❌ Timeout no health check após ${MaxWaitTime}s" -ForegroundColor Red
        Write-Host "📋 Logs do container:" -ForegroundColor Yellow
        docker logs $ContainerName
        throw "Health check timeout"
    }

    # 4. Testar classificação
    Write-Host "`n🎯 Testando classificação..." -ForegroundColor Yellow

    # Verificar se arquivo de exemplo existe
    if (-not (Test-Path "app\samples\tx_single.json")) {
        throw "Arquivo app\samples\tx_single.json não encontrado"
    }

    Write-Host "📄 Arquivo: app\samples\tx_single.json" -ForegroundColor Cyan
    Write-Host "📤 Enviando requisição..." -ForegroundColor Cyan

    # Executar POST /v1/classify
    $body = Get-Content "app\samples\tx_single.json" -Raw
    $response = Invoke-WebRequest -Uri $ClassifyUrl -Method POST -Body $body -ContentType "application/json" -UseBasicParsing

    Write-Host "📊 Código HTTP: $($response.StatusCode)" -ForegroundColor Cyan

    # 5. Verificar HTTP 200
    if ($response.StatusCode -ne 200) {
        Write-Host "❌ HTTP $($response.StatusCode) - Esperado 200" -ForegroundColor Red
        Write-Host "📋 Resposta:" -ForegroundColor Yellow
        Write-Host $response.Content
        throw "HTTP status code incorreto"
    }
    Write-Host "✅ HTTP 200 OK" -ForegroundColor Green

    # 6. Verificar presença de predictions[0].label
    Write-Host "`n🔍 Verificando campos obrigatórios..." -ForegroundColor Yellow

    $jsonResponse = $response.Content | ConvertFrom-Json
    
    Write-Host "📊 Resposta da API:" -ForegroundColor Green
    $jsonResponse | ConvertTo-Json -Depth 10 | Write-Host

    # Verificar campos importantes
    $prediction = $jsonResponse.predictions[0]
    
    Write-Host "`n🔍 Campos verificados:" -ForegroundColor Yellow
    Write-Host "  Label: $($prediction.label)" -ForegroundColor Cyan
    Write-Host "  Confidence: $($prediction.confidence)" -ForegroundColor Cyan
    Write-Host "  Method: $($prediction.method_used)" -ForegroundColor Cyan

    if ($prediction.label -and $prediction.label -ne "") {
        Write-Host "✅ Label encontrado: $($prediction.label)" -ForegroundColor Green
    } else {
        Write-Host "❌ Label não encontrado" -ForegroundColor Red
        throw "Label não encontrado"
    }

    if ($prediction.confidence -ge 0 -and $prediction.confidence -le 1) {
        Write-Host "✅ Confidence válido: $($prediction.confidence)" -ForegroundColor Green
    } else {
        Write-Host "❌ Confidence fora do range [0,1]: $($prediction.confidence)" -ForegroundColor Red
        throw "Confidence inválido"
    }

    Write-Host ""
    Write-Host "🎉 Smoke test concluído com sucesso!" -ForegroundColor Green
    Write-Host "================================================" -ForegroundColor Green
    Write-Host "✅ Build da imagem: OK" -ForegroundColor Green
    Write-Host "✅ Container executando: OK" -ForegroundColor Green
    Write-Host "✅ Health check: OK" -ForegroundColor Green
    Write-Host "✅ Classificação: OK" -ForegroundColor Green
    Write-Host "✅ Campos obrigatórios: OK" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 Container será parado automaticamente" -ForegroundColor Yellow

} catch {
    Write-Host "`n❌ Erro no smoke test: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "📋 Logs do container:" -ForegroundColor Yellow
    docker logs $ContainerName
    exit 1
} finally {
    # Limpeza sempre executada
    Cleanup
}

exit 0
