param(
    [int]$Port = 8081,
    [string]$OutputPath = "parse_output.json"
)

$workspace = "E:\Documentos\IA\Cursor - agente_despesas"
Set-Location $workspace

Write-Host "==> Encerrando processos python ativos..." -ForegroundColor Cyan
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
if ($pythonProcs) {
    $pythonProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "   Processos encerrados." -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "   Nenhum processo python em execução." -ForegroundColor Gray
}

Write-Host "==> Limpando cache Python..." -ForegroundColor Cyan
$cacheDirs = Get-ChildItem -Path $workspace -Filter __pycache__ -Recurse -Directory -ErrorAction SilentlyContinue
if ($cacheDirs) {
    $cacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   Cache limpo." -ForegroundColor Green
} else {
    Write-Host "   Nenhum cache encontrado." -ForegroundColor Gray
}

Write-Host "==> Configurando PYTHONPATH..." -ForegroundColor Cyan
$previousPythonPath = $env:PYTHONPATH
$env:PYTHONPATH = "$workspace;$env:PYTHONPATH"
Write-Host "   PYTHONPATH configurado." -ForegroundColor Green

Write-Host "==> Iniciando servidor FastAPI..." -ForegroundColor Cyan
$previousPort = $env:PORT
$previousOutput = $env:OUTPUT_JSON
$env:PORT = "$Port"

# Usar python -B para não criar arquivos .pyc e garantir código atualizado
# Usar variável de ambiente RELOAD=true para forçar reload dos módulos
$env:RELOAD = "true"
$serverProcess = Start-Process -FilePath "python" -ArgumentList "-B", "run_server.py" -WorkingDirectory $workspace -WindowStyle Hidden -PassThru

try {
    $healthUrl = "http://localhost:$Port/healthz"
    Write-Host "   Aguardando servidor responder em $healthUrl ..." -ForegroundColor Gray
    $maxAttempts = 20
    $delaySeconds = 1
    $serverReady = $false

    for ($i = 1; $i -le $maxAttempts; $i++) {
        if ($serverProcess.HasExited) {
            throw "Servidor finalizou antes de responder ao health check."
        }
        try {
            $response = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2
            if ($response.StatusCode -eq 200) {
                $serverReady = $true
                break
            }
        } catch {
            Start-Sleep -Seconds $delaySeconds
        }
    }

    if (-not $serverReady) {
        throw "Servidor não inicializou a tempo."
    }

    Write-Host "   Servidor online!" -ForegroundColor Green

    $fullOutputPath = if ([System.IO.Path]::IsPathRooted($OutputPath)) {
        $OutputPath
    } else {
        Join-Path $workspace $OutputPath
    }

    if (Test-Path $fullOutputPath) {
        Remove-Item $fullOutputPath -Force -ErrorAction SilentlyContinue
    }
    $env:OUTPUT_JSON = $fullOutputPath

    Write-Host "==> Executando parsing (.\\scripts\\test-parse-itau.ps1)..." -ForegroundColor Cyan
    & .\scripts\test-parse-itau.ps1

    if (-not (Test-Path $fullOutputPath)) {
        throw "Arquivo de saída não foi gerado em $fullOutputPath."
    }

    Write-Host "==> Output salvo em: $fullOutputPath" -ForegroundColor Green
}
catch {
    Write-Host "ERRO: $($_.Exception.Message)" -ForegroundColor Red
    throw
}
finally {
    Write-Host "==> Finalizando servidor..." -ForegroundColor Cyan
    if ($serverProcess -and -not $serverProcess.HasExited) {
        Stop-Process -Id $serverProcess.Id -Force -ErrorAction SilentlyContinue
        try { Wait-Process -Id $serverProcess.Id -Timeout 5 } catch { }
    }
    if ($null -ne $previousPort) {
        $env:PORT = $previousPort
    } else {
        Remove-Item Env:PORT -ErrorAction SilentlyContinue
    }
    if ($null -ne $previousOutput) {
        $env:OUTPUT_JSON = $previousOutput
    } else {
        Remove-Item Env:OUTPUT_JSON -ErrorAction SilentlyContinue
    }
    if ($null -ne $previousPythonPath) {
        $env:PYTHONPATH = $previousPythonPath
    } else {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    Write-Host "   Servidor encerrado." -ForegroundColor Green
}

