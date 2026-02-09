#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Gera output_esperado2.json a partir de fatura_cartao_2.pdf.

.DESCRIPTION
    Este script executa o processamento do PDF fatura_cartao_2.pdf e gera
    o arquivo tests/output_esperado2.json com o resultado esperado.

.EXAMPLE
    .\scripts\generate-output2.ps1
#>

$workspace = "E:\Documentos\IA\Cursor - agente_despesas"
Set-Location $workspace

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Gerador de Output Esperado 2" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Executar script Python
python test_generate_output2.py

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n[SUCESSO] Output esperado gerado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "`n[FALHA] Erro ao gerar output esperado." -ForegroundColor Red
}

exit $exitCode



