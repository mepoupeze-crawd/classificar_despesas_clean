# Script PowerShell para testar a API
# test-api.ps1

Write-Host "========================================" -ForegroundColor Green
Write-Host " Agente de Despesas - Testar API (PowerShell)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""

# Testar health check
Write-Host "[TEST] Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/healthz" -Method GET
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Health check OK" -ForegroundColor Green
        Write-Host $response.Content
    } else {
        Write-Host "❌ Health check falhou com status: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Falha ao conectar com a API!" -ForegroundColor Red
    Write-Host "Certifique-se de que o servidor está rodando em http://localhost:8080" -ForegroundColor Yellow
    Write-Host "Execute 'run.bat' para iniciar o servidor." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host ""

# Testar classificação
Write-Host "[TEST] Classificação de Transações..." -ForegroundColor Yellow

$jsonData = @'
[
    {
        "description": "Netflix Com",
        "amount": 44.90,
        "date": "2024-01-01T00:00:00",
        "card_holder": "CC - Aline Silva"
    },
    {
        "description": "Uber Viagem",
        "amount": 25.50,
        "date": "2024-01-01T00:00:00",
        "card_holder": "Final 1234 - Joao Santos"
    },
    {
        "description": "Supermercado Extra",
        "amount": 89.90,
        "date": "2024-01-01T00:00:00",
        "card_holder": "Final 5678 - Angela Casa"
    }
]
'@

try {
    $response = Invoke-WebRequest -Uri "http://localhost:8080/v1/classify" -Method POST -Body $jsonData -ContentType "application/json"
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Classificação OK" -ForegroundColor Green
        Write-Host $response.Content
    } else {
        Write-Host "❌ Classificação falhou com status: $($response.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Falha na classificação!" -ForegroundColor Red
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host ""
Write-Host "[INFO] Testes da API concluídos!" -ForegroundColor Green
Write-Host ""
Write-Host "Para mais testes, acesse:" -ForegroundColor Cyan
Write-Host "  - Swagger UI: http://localhost:8080/docs" -ForegroundColor Cyan
Write-Host "  - ReDoc: http://localhost:8080/redoc" -ForegroundColor Cyan
Write-Host ""
Write-Host "Pressione qualquer tecla para continuar..." -ForegroundColor Yellow
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
