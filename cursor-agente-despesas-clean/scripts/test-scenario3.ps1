# Script para testar o parsing de fatura_cartao_3.pdf
$workspace = Split-Path -Parent $PSScriptRoot
Set-Location $workspace

Write-Host "Executando teste de validacao para fatura_cartao_3.pdf..." -ForegroundColor Cyan
python test_scenario3.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nTeste concluido com sucesso!" -ForegroundColor Green
} else {
    Write-Host "`nTeste falhou!" -ForegroundColor Red
    exit 1
}



