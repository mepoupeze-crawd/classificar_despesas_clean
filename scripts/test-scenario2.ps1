#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Executa cenário de teste: fatura_cartao_2.pdf vs output_esperado2.json

.DESCRIPTION
    Processa o PDF e compara com o output esperado.

.EXAMPLE
    .\scripts\test-scenario2.ps1
#>

$workspace = "E:\Documentos\IA\Cursor - agente_despesas"
Set-Location $workspace

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Cenário de Teste 2" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

python test_scenario2.py

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n[SUCESSO] Teste passou!" -ForegroundColor Green
} else {
    Write-Host "`n[FALHA] Teste falhou!" -ForegroundColor Red
}

exit $exitCode



