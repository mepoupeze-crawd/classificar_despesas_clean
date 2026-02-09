#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Executa teste de validação do parser de PDF fatura_cartao_2.pdf contra o output_esperado2.json.

.DESCRIPTION
    Este script executa o teste de validação que:
    1. Processa o PDF fatura_cartao_2.pdf
    2. Gera parse_output2.json
    3. Compara com tests/output_esperado2.json
    4. Reporta todas as diferenças encontradas

.EXAMPLE
    .\scripts\test-parse-validation2.ps1
#>

$workspace = "E:\Documentos\IA\Cursor - agente_despesas"
Set-Location $workspace

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Teste de Validacao do Parser PDF 2" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Executar teste Python
python test_parse_pdf_validation2.py

$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n[SUCESSO] Teste passou - Outputs sao identicos!" -ForegroundColor Green
} else {
    Write-Host "`n[FALHA] Teste falhou - Verifique as diferencas acima." -ForegroundColor Red
}

exit $exitCode



