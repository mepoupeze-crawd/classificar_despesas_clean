# Script PowerShell para testar health check (sem jq)
# Usa apenas comandos PowerShell nativos

$ErrorActionPreference = "Stop"

$API_URL = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8081" }

Write-Host "🏥 Testando health check..." -ForegroundColor Cyan
Write-Host "URL: $API_URL/healthz"
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri "$API_URL/healthz" -Method GET -UseBasicParsing
    
    Write-Host "✅ Health check OK" -ForegroundColor Green
    Write-Host "Resposta: $($response | ConvertTo-Json -Compress)" -ForegroundColor Green
    
    if ($response.status -eq "ok") {
        Write-Host ""
        Write-Host "🎉 API está funcionando corretamente!" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "⚠️ Resposta inesperada: $($response | ConvertTo-Json)" -ForegroundColor Yellow
        exit 1
    }
} catch {
    Write-Host "❌ Health check falhou" -ForegroundColor Red
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Certifique-se de que:" -ForegroundColor Yellow
    Write-Host "  1. A API está rodando em $API_URL" -ForegroundColor Yellow
    Write-Host "  2. O Docker está rodando (se usando Docker Compose)" -ForegroundColor Yellow
    Write-Host "  3. A porta está correta (8081 para Docker Compose)" -ForegroundColor Yellow
    
    exit 1
}
