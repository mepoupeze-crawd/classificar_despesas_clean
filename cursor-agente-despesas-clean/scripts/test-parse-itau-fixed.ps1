# Script PowerShell para testar parsing de PDF Itau (sem jq)
# Equivalente ao comando: curl -F "file=@./fatura_cartao.pdf" http://localhost:8081/parse_itau | jq .

$ErrorActionPreference = "Stop"

$API_URL = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8081" }
$PDF_PATH = if ($env:PDF_PATH) { $env:PDF_PATH } else { "./fatura_cartao.pdf" }

Write-Host "Testando parsing de PDF Itau" -ForegroundColor Cyan
Write-Host "================================="
Write-Host "API URL: $API_URL"
Write-Host "PDF: $PDF_PATH"
Write-Host ""

# Verificar se PDF existe
if (-not (Test-Path $PDF_PATH)) {
    Write-Host "Erro: PDF nao encontrado em $PDF_PATH" -ForegroundColor Red
    Write-Host "Certifique-se de que o arquivo existe ou especifique o caminho:" -ForegroundColor Yellow
    Write-Host "   `$env:PDF_PATH = 'caminho/para/fatura_cartao.pdf'" -ForegroundColor Yellow
    exit 1
}

# 1. Testar health check primeiro
Write-Host "1. Testando health check..." -ForegroundColor Yellow
try {
    $healthResponse = Invoke-RestMethod -Uri "$API_URL/healthz" -Method GET -UseBasicParsing -ErrorAction Stop
    if ($healthResponse.status -eq "ok") {
        Write-Host "Health check OK" -ForegroundColor Green
    } else {
        Write-Host "Health check falhou: $($healthResponse | ConvertTo-Json)" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "Erro no health check: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Certifique-se de que a API esta rodando em $API_URL" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# 2. Testar parsing de PDF
Write-Host "2. Testando parsing de PDF..." -ForegroundColor Yellow
Write-Host "   Arquivo: $PDF_PATH" -ForegroundColor Gray
Write-Host "   Tamanho: $([math]::Round((Get-Item $PDF_PATH).Length / 1KB, 2)) KB" -ForegroundColor Gray
Write-Host ""

try {
    # Usar System.Net.Http para multipart/form-data (mais confiavel)
    Add-Type -AssemblyName System.Net.Http -ErrorAction SilentlyContinue
    
    Write-Host "   Enviando requisicao..." -ForegroundColor Gray
    
    $response = $null
    $useHttpClient = $false
    
    # Metodo 1: Tentar usar System.Net.Http.HttpClient (mais confiavel)
    try {
        $httpClient = New-Object System.Net.Http.HttpClient
        $httpClient.Timeout = New-TimeSpan -Seconds 60
        $content = New-Object System.Net.Http.MultipartFormDataContent
        
        $fileBytes = [System.IO.File]::ReadAllBytes($PDF_PATH)
        $fileName = [System.IO.Path]::GetFileName($PDF_PATH)
        $byteArrayContent = New-Object System.Net.Http.ByteArrayContent($fileBytes)
        $byteArrayContent.Headers.ContentType = New-Object System.Net.Http.Headers.MediaTypeHeaderValue("application/pdf")
        
        $content.Add($byteArrayContent, "file", $fileName)
        
        $responseTask = $httpClient.PostAsync("$API_URL/parse_itau", $content)
        $httpResponse = $responseTask.Result
        
        if ($httpResponse.IsSuccessStatusCode) {
            $responseContent = $httpResponse.Content.ReadAsStringAsync().Result
            $response = $responseContent | ConvertFrom-Json
            $useHttpClient = $true
            Write-Host "   Metodo HttpClient OK" -ForegroundColor Gray
        } else {
            $errorBody = $httpResponse.Content.ReadAsStringAsync().Result
            throw New-Object System.Exception("HTTP $($httpResponse.StatusCode): $errorBody")
        }
        
        $httpClient.Dispose()
    } catch {
        Write-Host "   HttpClient falhou: $($_.Exception.Message)" -ForegroundColor Yellow
        $useHttpClient = $false
    }
    
    # Metodo 2: Fallback para multipart manual se HttpClient falhou
    if (-not $useHttpClient) {
        Write-Host "   Usando metodo alternativo (multipart manual)..." -ForegroundColor Yellow
        
        $fileBytes = [System.IO.File]::ReadAllBytes($PDF_PATH)
        $fileName = [System.IO.Path]::GetFileName($PDF_PATH)
        
        # Gerar boundary unico
        $boundary = [System.Guid]::NewGuid().ToString()
        $LF = "`r`n"
        
        # Construir corpo completo
        $bodyLines = @()
        $bodyLines += "--$boundary"
        $bodyLines += "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`""
        $bodyLines += "Content-Type: application/pdf"
        $bodyLines += ""
        
        # Converter header para bytes
        $headerText = ($bodyLines -join $LF) + $LF
        $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($headerText)
        
        # Footer
        $footerText = "$LF--$boundary--$LF"
        $footerBytes = [System.Text.Encoding]::UTF8.GetBytes($footerText)
        
        # Combinar: header + file + footer
        $bodyBytes = New-Object byte[] ($headerBytes.Length + $fileBytes.Length + $footerBytes.Length)
        [System.Buffer]::BlockCopy($headerBytes, 0, $bodyBytes, 0, $headerBytes.Length)
        [System.Buffer]::BlockCopy($fileBytes, 0, $bodyBytes, $headerBytes.Length, $fileBytes.Length)
        [System.Buffer]::BlockCopy($footerBytes, 0, $bodyBytes, $headerBytes.Length + $fileBytes.Length, $footerBytes.Length)
        
        # Fazer requisicao usando WebRequest (mais confiavel que Invoke-RestMethod para multipart)
        try {
            $webRequest = [System.Net.WebRequest]::Create("$API_URL/parse_itau")
            $webRequest.Method = "POST"
            $webRequest.ContentType = "multipart/form-data; boundary=$boundary"
            $webRequest.ContentLength = $bodyBytes.Length
            
            $requestStream = $webRequest.GetRequestStream()
            $requestStream.Write($bodyBytes, 0, $bodyBytes.Length)
            $requestStream.Close()
            
            $webResponse = $webRequest.GetResponse()
            $responseStream = $webResponse.GetResponseStream()
            $streamReader = New-Object System.IO.StreamReader($responseStream)
            $responseContent = $streamReader.ReadToEnd()
            $streamReader.Close()
            $responseStream.Close()
            $webResponse.Close()
            
            $response = $responseContent | ConvertFrom-Json
        } catch {
            Write-Host "   Erro no metodo alternativo: $($_.Exception.Message)" -ForegroundColor Red
            throw
        }
    }
    
    Write-Host "Parsing realizado com sucesso!" -ForegroundColor Green
    Write-Host ""
    
    # Exibir resposta formatada (equivalente ao jq .)
    Write-Host "Resposta (JSON formatado):" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    $jsonOutput = $null
    try {
        $jsonOutput = $response | ConvertTo-Json -Depth 10
        if ($jsonOutput) {
            Write-Host $jsonOutput
        } else {
            Write-Host "Resposta vazia" -ForegroundColor Yellow
        }
    } catch {
        $errorMsg = $_.Exception.Message
        Write-Host "Erro ao formatar resposta: $errorMsg" -ForegroundColor Yellow
        Write-Host "Tentando exibir resposta alternativa..." -ForegroundColor Yellow
        if ($response) {
            Write-Host ($response | Out-String)
        }
    }
    Write-Host ""
    
    # Verificar estrutura
    Write-Host "Verificando estrutura..." -ForegroundColor Yellow
    
    # Items
    if ($response.items) {
        Write-Host "  Items: $($response.items.Count) transacoes extraidas" -ForegroundColor Green
        if ($response.items.Count -gt 0) {
            Write-Host "     Primeira transacao:" -ForegroundColor Gray
            $firstItem = $response.items[0]
            Write-Host "       Date: $($firstItem.date)" -ForegroundColor Gray
            Write-Host "       Description: $($firstItem.description)" -ForegroundColor Gray
            Write-Host "       Amount: $($firstItem.amount)" -ForegroundColor Gray
            Write-Host "       Last4: $($firstItem.last4)" -ForegroundColor Gray
        }
    } else {
        Write-Host "  Items nao encontrado" -ForegroundColor Yellow
    }
    
    # Stats
    if ($response.stats) {
        Write-Host "  Stats encontrado" -ForegroundColor Green
        Write-Host "     Total lines: $($response.stats.total_lines)" -ForegroundColor Gray
        Write-Host "     Matched: $($response.stats.matched)" -ForegroundColor Gray
        Write-Host "     Rejected: $($response.stats.rejected)" -ForegroundColor Gray
        Write-Host "     Sum abs values: $($response.stats.sum_abs_values)" -ForegroundColor Gray
        
        # Verificar by_card
        if ($response.stats.by_card) {
            Write-Host "     By card:" -ForegroundColor Gray
            foreach ($card in $response.stats.by_card.PSObject.Properties.Name) {
                $cardStats = $response.stats.by_card.$card
                Write-Host "       Cartao ${card}:" -ForegroundColor Cyan
                Write-Host "         Control total: $($cardStats.control_total)" -ForegroundColor Gray
                Write-Host "         Calculated total: $($cardStats.calculated_total)" -ForegroundColor Gray
                Write-Host "         Delta: $($cardStats.delta)" -ForegroundColor $(if ($cardStats.delta -le 0.01) { "Green" } else { "Yellow" })
                
                if ($cardStats.delta -gt 0.01) {
                    Write-Host "         Delta acima da tolerancia (0.01)" -ForegroundColor Yellow
                } else {
                    Write-Host "         Delta dentro da tolerancia" -ForegroundColor Green
                }
            }
        }
    } else {
        Write-Host "  Stats nao encontrado" -ForegroundColor Yellow
    }
    
    # Rejects
    if ($response.rejects) {
        Write-Host "  Rejects: $($response.rejects.Count) linhas rejeitadas" -ForegroundColor $(if ($response.rejects.Count -eq 0) { "Green" } else { "Yellow" })
        if ($response.rejects.Count -gt 0 -and $response.rejects.Count -le 5) {
            Write-Host "     Primeiras rejeicoes:" -ForegroundColor Gray
            for ($i = 0; $i -lt [Math]::Min($response.rejects.Count, 3); $i++) {
                $rejectLine = $response.rejects[$i].line
                $linePreview = if ($rejectLine.Length -gt 50) { $rejectLine.Substring(0, 50) + "..." } else { $rejectLine }
                Write-Host "       $($i + 1). $($response.rejects[$i].reason): $linePreview" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "  Rejects nao encontrado" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Teste concluido com sucesso!" -ForegroundColor Green
    
} catch {
    Write-Host "Erro no parsing: $($_.Exception.Message)" -ForegroundColor Red
    
    # Verificar se e erro 404 (endpoint nao existe)
    if ($_.Exception.Response -and $_.Exception.Response.StatusCode -eq 404) {
        Write-Host ""
        Write-Host "Endpoint /parse_itau nao encontrado!" -ForegroundColor Yellow
        Write-Host "O endpoint pode nao estar implementado ainda." -ForegroundColor Yellow
        Write-Host "Verifique se o modulo card_pdf_parser esta instalado e configurado." -ForegroundColor Yellow
    } elseif ($_.Exception.Response) {
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host ""
            Write-Host "Resposta do servidor:" -ForegroundColor Yellow
            Write-Host $responseBody -ForegroundColor Yellow
        } catch {
            Write-Host "Erro ao ler resposta do servidor" -ForegroundColor Yellow
        }
    }
    
    exit 1
}
