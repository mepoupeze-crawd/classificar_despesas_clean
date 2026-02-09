@echo off
REM Script de smoke test para container Docker (Windows CMD)
REM Testa build, execução, health check e classificação

setlocal enabledelayedexpansion

REM Variáveis
set IMAGE_NAME=ml-service:local
set CONTAINER_NAME=ml-service-smoke-test
set PORT=8081
set HEALTH_URL=http://localhost:%PORT%/healthz
set CLASSIFY_URL=http://localhost:%PORT%/v1/classify
set MAX_WAIT_TIME=30
set POLL_INTERVAL=2

echo 🚀 Iniciando smoke test do container Docker
echo ================================================

REM Função de limpeza (será chamada no final)
:cleanup
echo.
echo 🧹 Limpando container...
docker stop %CONTAINER_NAME% 2>nul
docker rm %CONTAINER_NAME% 2>nul
goto :eof

REM Registrar limpeza no final
set "CLEANUP_CALLED=0"

REM 1. Build da imagem
echo.
echo 📦 Fazendo build da imagem...
docker build -t %IMAGE_NAME% .
if errorlevel 1 (
    echo ❌ Erro no build da imagem
    call :cleanup
    exit /b 1
)
echo ✅ Build concluído

REM 2. Executar container em background
echo.
echo 🚀 Executando container em background...
docker run -d --name %CONTAINER_NAME% -p %PORT%:8080 %IMAGE_NAME%
if errorlevel 1 (
    echo ❌ Erro ao executar container
    call :cleanup
    exit /b 1
)
echo ✅ Container iniciado

REM 3. Polling de /healthz
echo.
echo 🏥 Aguardando health check...
echo URL: %HEALTH_URL%
echo Timeout: %MAX_WAIT_TIME%s

set elapsed=0
:health_loop
if %elapsed% geq %MAX_WAIT_TIME% (
    echo.
    echo ❌ Timeout no health check após %MAX_WAIT_TIME%s
    echo 📋 Logs do container:
    docker logs %CONTAINER_NAME%
    call :cleanup
    exit /b 1
)

curl -s -f %HEALTH_URL% >nul 2>&1
if not errorlevel 1 (
    echo.
    echo ✅ Health check OK (%elapsed%s)
    goto :health_ok
)

echo|set /p="."
timeout /t %POLL_INTERVAL% /nobreak >nul
set /a elapsed+=%POLL_INTERVAL%
goto :health_loop

:health_ok

REM 4. Testar classificação
echo.
echo 🎯 Testando classificação...

REM Verificar se arquivo de exemplo existe
if not exist "app\samples\tx_single.json" (
    echo ❌ Arquivo app\samples\tx_single.json não encontrado
    call :cleanup
    exit /b 1
)

echo 📄 Arquivo: app\samples\tx_single.json
echo 📤 Enviando requisição...

REM Executar POST /v1/classify
curl -s -X POST "%CLASSIFY_URL%" ^
    -H "Content-Type: application/json" ^
    -d @app\samples\tx_single.json > response.json

REM Verificar se curl foi bem-sucedido
if errorlevel 1 (
    echo ❌ Erro na requisição de classificação
    call :cleanup
    exit /b 1
)

echo 📊 Resposta da API:
type response.json

REM 5. Verificar presença de campos obrigatórios
echo.
echo 🔍 Verificando campos obrigatórios...

REM Verificar se contém "label"
findstr /C:"\"label\"" response.json >nul
if errorlevel 1 (
    echo ❌ Campo 'label' não encontrado
    call :cleanup
    exit /b 1
)
echo ✅ Campo 'label' encontrado

REM Verificar se contém "confidence"
findstr /C:"\"confidence\"" response.json >nul
if errorlevel 1 (
    echo ❌ Campo 'confidence' não encontrado
    call :cleanup
    exit /b 1
)
echo ✅ Campo 'confidence' encontrado

REM Limpar arquivo temporário
del response.json 2>nul

echo.
echo 🎉 Smoke test concluído com sucesso!
echo ================================================
echo ✅ Build da imagem: OK
echo ✅ Container executando: OK
echo ✅ Health check: OK
echo ✅ Classificação: OK
echo ✅ Campos obrigatórios: OK
echo.
echo 💡 Container será parado automaticamente

REM Limpeza final
call :cleanup
exit /b 0
