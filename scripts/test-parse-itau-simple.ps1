# Script PowerShell simples para testar parsing de PDF (equivalente ao curl)
# Equivalente a: curl -F "file=@./fatura_cartao.pdf" http://localhost:8081/parse_itau | jq .

$ErrorActionPreference = "Stop"

$API_URL = if ($env:API_URL) { $env:API_URL } else { "http://localhost:8081" }
$PDF_PATH = if ($env:PDF_PATH) { $env:PDF_PATH } else { "./fatura_cartao.pdf" }

# Verificar se PDF existe
if (-not (Test-Path $PDF_PATH)) {
    Write-Host "Erro: PDF não encontrado em $PDF_PATH" -ForegroundColor Red
    exit 1
}

try {
    # Método 1: Tentar usar System.Net.Http (mais confiável)
    try {
        Add-Type -AssemblyName System.Net.Http -ErrorAction Stop
        
        $httpClient = New-Object System.Net.Http.HttpClient
        $content = New-Object System.Net.Http.MultipartFormDataContent
        
        $fileBytes = [System.IO.File]::ReadAllBytes($PDF_PATH)
        $fileName = [System.IO.Path]::GetFileName($PDF_PATH)
        $byteArrayContent = New-Object System.Net.Http.ByteArrayContent($fileBytes)
        $byteArrayContent.Headers.ContentType = New-Object System.Net.Http.Headers.MediaTypeHeaderValue("application/pdf")
        
        $content.Add($byteArrayContent, "file", $fileName)
        
        Write-Host "Enviando requisição para $API_URL/parse_itau..." -ForegroundColor Gray
        $response = $httpClient.PostAsync("$API_URL/parse_itau", $content).Result
        $responseContent = $response.Content.ReadAsStringAsync().Result
        
        $httpClient.Dispose()
        
        if ($response.IsSuccessStatusCode) {
            # Converter JSON para objeto e exibir formatado (equivalente ao jq .)
            $jsonObject = $responseContent | ConvertFrom-Json
            $jsonObject | ConvertTo-Json -Depth 10 | Write-Host
        } else {
            Write-Host "Erro HTTP $($response.StatusCode): $responseContent" -ForegroundColor Red
            if ($response.StatusCode -eq 404) {
                Write-Host "Endpoint /parse_itau não encontrado. Verifique se está implementado." -ForegroundColor Yellow
            }
            exit 1
        }
    } catch {
        # Método 2: Fallback manual (se System.Net.Http não disponível)
        Write-Host "Usando método alternativo para upload..." -ForegroundColor Yellow
        
        $fileBytes = [System.IO.File]::ReadAllBytes($PDF_PATH)
        $fileName = [System.IO.Path]::GetFileName($PDF_PATH)
        
        $boundary = [System.Guid]::NewGuid().ToString()
        $LF = "`r`n"
        
        $headerLines = @(
            "--$boundary",
            "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"",
            "Content-Type: application/pdf",
            ""
        )
        
        $footerLine = "$LF--$boundary--$LF"
        
        $headerText = $headerLines -join $LF
        $headerBytes = [System.Text.Encoding]::UTF8.GetBytes($headerText + $LF)
        $footerBytes = [System.Text.Encoding]::UTF8.GetBytes($footerLine)
        
        $bodyBytes = New-Object byte[] ($headerBytes.Length + $fileBytes.Length + $footerBytes.Length)
        [System.Buffer]::BlockCopy($headerBytes, 0, $bodyBytes, 0, $headerBytes.Length)
        [System.Buffer]::BlockCopy($fileBytes, 0, $bodyBytes, $headerBytes.Length, $fileBytes.Length)
        [System.Buffer]::BlockCopy($footerBytes, 0, $bodyBytes, $headerBytes.Length + $fileBytes.Length, $footerBytes.Length)
        
        $headers = @{
            "Content-Type" = "multipart/form-data; boundary=$boundary"
        }
        
        $response = Invoke-RestMethod -Uri "$API_URL/parse_itau" -Method POST -Body $bodyBytes -Headers $headers -UseBasicParsing
        $response | ConvertTo-Json -Depth 10 | Write-Host
    }
} catch {
    Write-Host "Erro: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        try {
            $statusCode = $_.Exception.Response.StatusCode.value__
            if ($statusCode -eq 404) {
                Write-Host "Endpoint /parse_itau não encontrado (404)." -ForegroundColor Yellow
                Write-Host "O endpoint pode não estar implementado ainda." -ForegroundColor Yellow
            } else {
                $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
                $responseBody = $reader.ReadToEnd()
                Write-Host "Resposta do servidor ($statusCode): $responseBody" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "Não foi possível ler a resposta do servidor" -ForegroundColor Yellow
        }
    }
    exit 1
}

