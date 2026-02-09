# Script para corrigir secrets no GCP removendo quebras de linha
# Uso: .\fix-secret-newlines.ps1

Write-Host "Corrigindo secrets no GCP (removendo \r\n)..." -ForegroundColor Cyan

# 1. OpenAI API Key
Write-Host "`n1. Corrigindo openai-api-key..." -ForegroundColor Yellow
try {
    $OPENAI_KEY = gcloud secrets versions access latest --secret="openai-api-key" 2>&1 | Out-String
    $OPENAI_KEY_CLEAN = $OPENAI_KEY.Trim()
    
    if ($OPENAI_KEY -ne $OPENAI_KEY_CLEAN) {
        Write-Host "  [AVISO] Encontrado \r\n no secret, limpando..." -ForegroundColor Yellow
        $OPENAI_KEY_CLEAN | gcloud secrets versions add openai-api-key --data-file=-
        Write-Host "  [OK] Secret atualizado" -ForegroundColor Green
    } else {
        Write-Host "  [OK] Secret ja esta limpo" -ForegroundColor Green
    }
} catch {
    Write-Host "  [ERRO] Erro ao processar openai-api-key: $_" -ForegroundColor Red
}

# 2. SerpAPI Key
Write-Host "`n2. Corrigindo serpapi-api-key..." -ForegroundColor Yellow
try {
    $SERPAPI_KEY = gcloud secrets versions access latest --secret="serpapi-api-key" 2>&1 | Out-String
    $SERPAPI_KEY_CLEAN = $SERPAPI_KEY.Trim()
    
    if ($SERPAPI_KEY -ne $SERPAPI_KEY_CLEAN) {
        Write-Host "  [AVISO] Encontrado \r\n no secret, limpando..." -ForegroundColor Yellow
        $SERPAPI_KEY_CLEAN | gcloud secrets versions add serpapi-api-key --data-file=-
        Write-Host "  [OK] Secret atualizado" -ForegroundColor Green
    } else {
        Write-Host "  [OK] Secret ja esta limpo" -ForegroundColor Green
    }
} catch {
    Write-Host "  [ERRO] Erro ao processar serpapi-api-key: $_" -ForegroundColor Red
}

Write-Host "`n[OK] Processo concluido!" -ForegroundColor Green
Write-Host "`n[DICA] Proximo passo: Fazer deploy do codigo corrigido" -ForegroundColor Cyan

