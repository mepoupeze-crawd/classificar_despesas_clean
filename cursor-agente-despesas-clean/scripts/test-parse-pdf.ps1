# Script PowerShell para testar parsing de PDF (sem jq)
# Testa endpoint /parse_itau se disponível

$ErrorActionPreference = "Stop"

$API_URL = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8081" }
$PDF_PATH = if ($env:PDF_PATH) { $env:PDF_PATH } else { "./fatura_cartao.pdf" }

Write-Host "🧪 Testando parsing de PDF Itaú" -ForegroundColor Cyan
Write-Host "================================="
Write-Host "API URL: $API_URL"
Write-Host "PDF: $PDF_PATH"
Write-Host ""

# Verificar se PDF existe
if (-not (Test-Path $PDF_PATH)) {
    Write-Host "❌ Erro: PDF não encontrado em $PDF_PATH" -ForegroundColor Red
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

# 2. Testar parsing
Write-Host "2️⃣ Testando parsing de PDF..." -ForegroundColor Yellow

try {
    # Preparar multipart/form-data corretamente
    $fileBytes = [System.IO.File]::ReadAllBytes($PDF_PATH)
    $fileName = [System.IO.Path]::GetFileName($PDF_PATH)
    
    # Gerar boundary único
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    # Construir corpo da requisição multipart
    $headerLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"",
        "Content-Type: application/pdf",
        ""
    )
    
    $footerLine = "$LF--$boundary--$LF"
    
    # Converter partes para bytes
    $headerText = $headerLines -join $LF
    $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($headerText + $LF)
    $footerBytes = [System.Text.Encoding]::UTF8.GetBytes($footerLine)
    
    # Combinar: header + file + footer
    $bodyBytes = New-Object byte[] ($headerBytes.Length + $fileBytes.Length + $footerBytes.Length)
    [System.Buffer]::BlockCopy($headerBytes, 0, $bodyBytes, 0, $headerBytes.Length)
    [System.Buffer]::BlockCopy($fileBytes, 0, $bodyBytes, $headerBytes.Length, $fileBytes.Length)
    [System.Buffer]::BlockCopy($footerBytes, 0, $bodyBytes, $headerBytes.Length + $fileBytes.Length, $footerBytes.Length)
    
    # Headers
    $headers = @{
        "Content-Type" = "multipart/form-data; boundary=$boundary"
    }
    
    Write-Host "   Enviando requisição (tamanho: $([math]::Round($bodyBytes.Length / 1KB, 2)) KB)..." -ForegroundColor Gray
    
    # Fazer requisição
    $response = Invoke-RestMethod -Uri "$API_URL/parse_itau" -Method POST -Body $bodyBytes -Headers $headers -UseBasicParsing
    
    Write-Host "✅ Parsing OK" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Resposta:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10 | Write-Host
    
    # Verificar estrutura
    Write-Host ""
    Write-Host "🔍 Verificando estrutura..." -ForegroundColor Yellow
    
    if ($response.items) {
        Write-Host "  Items: $($response.items.Count)" -ForegroundColor Cyan
    }
    
    if ($response.stats) {
        Write-Host "  Stats:" -ForegroundColor Cyan
        Write-Host "    Total lines: $($response.stats.total_lines)" -ForegroundColor Gray
        Write-Host "    Matched: $($response.stats.matched)" -ForegroundColor Gray
        Write-Host "    Rejected: $($response.stats.rejected)" -ForegroundColor Gray
        Write-Host "    Sum abs values: $($response.stats.sum_abs_values)" -ForegroundColor Gray
        
        if ($response.stats.by_card) {
            Write-Host "    By card:" -ForegroundColor Gray
            foreach ($card in $response.stats.by_card.PSObject.Properties.Name) {
                $cardStats = $response.stats.by_card.$card
                Write-Host "      Card $card:" -ForegroundColor Gray
                Write-Host "        Control: $($cardStats.control_total)" -ForegroundColor Gray
                Write-Host "        Calculated: $($cardStats.calculated_total)" -ForegroundColor Gray
                Write-Host "        Delta: $($cardStats.delta)" -ForegroundColor $(if ($cardStats.delta -le 0.01) { "Green" } else { "Yellow" })
            }
        }
    }
    
    if ($response.rejects) {
        Write-Host "  Rejects: $($response.rejects.Count)" -ForegroundColor Cyan
    }
    
} catch {
    Write-Host "❌ Erro no parsing: $_" -ForegroundColor Red
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

