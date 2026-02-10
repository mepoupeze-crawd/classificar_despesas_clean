@echo off
REM Script para testar classificação de transação única (Windows)
REM Executa POST /v1/classify com app/samples/tx_single.json

echo 🎯 Testando classificação de transação única...

REM Verificar se o arquivo de exemplo existe
if not exist "app\samples\tx_single.json" (
    echo ❌ Arquivo app\samples\tx_single.json não encontrado!
    exit /b 1
)

REM Verificar se a API está rodando
echo 🔍 Verificando se a API está rodando...
curl -s http://localhost:8080/healthz >nul 2>&1
if errorlevel 1 (
    echo ❌ API não está rodando em http://localhost:8080
    echo 💡 Execute 'make run-api' ou 'uvicorn app.main:app --reload --port 8080' primeiro
    exit /b 1
)

echo ✅ API está rodando!

REM Executar teste
echo 📤 Enviando requisição de classificação...
echo 📄 Arquivo: app\samples\tx_single.json
echo.

curl -s -X POST "http://localhost:8080/v1/classify" ^
  -H "Content-Type: application/json" ^
  -d @app\samples\tx_single.json

echo.
echo ✅ Teste concluído!
echo 💡 Para análise detalhada da resposta, use PowerShell ou instale jq
