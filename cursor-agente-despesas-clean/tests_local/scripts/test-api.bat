@echo off
REM Script para testar a API no Windows

echo ========================================
echo  Agente de Despesas - Testar API
echo ========================================
echo.

REM Verificar se curl está disponível
curl --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] curl nao encontrado, usando PowerShell...
    powershell -ExecutionPolicy Bypass -File "test-api.ps1"
    pause
    exit /b 0
)

echo [INFO] Testando API com curl...
echo.

REM Testar health check
echo [TEST] Health Check...
curl -s http://localhost:8080/healthz
if errorlevel 1 (
    echo [ERRO] Falha ao conectar com a API!
    echo Certifique-se de que o servidor está rodando em http://localhost:8080
    echo Execute 'run.bat' para iniciar o servidor.
    echo.
    pause
    exit /b 1
)

echo.
echo.

REM Testar classificação
echo [TEST] Classificação de Transações...
curl -X POST "http://localhost:8080/v1/classify" ^
  -H "Content-Type: application/json" ^
  -d "[{\"description\": \"Netflix Com\", \"amount\": 44.90, \"date\": \"2024-01-01T00:00:00\", \"card_holder\": \"CC - Aline Silva\"}, {\"description\": \"Uber Viagem\", \"amount\": 25.50, \"date\": \"2024-01-01T00:00:00\", \"card_holder\": \"Final 1234 - Joao Santos\"}]"

echo.
echo.
echo [INFO] Testes da API concluídos!
echo.
echo Para mais testes, acesse:
echo   - Swagger UI: http://localhost:8080/docs
echo   - ReDoc: http://localhost:8080/redoc
echo.
pause
