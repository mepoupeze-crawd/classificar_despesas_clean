@echo off
REM Script para executar o microserviço FastAPI no Windows

echo ========================================
echo  Agente de Despesas - FastAPI Server
echo ========================================
echo.

REM Verificar se o ambiente virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual nao encontrado!
    echo Execute 'make install' ou 'install.bat' primeiro.
    echo.
    pause
    exit /b 1
)

REM Ativar ambiente virtual
echo [INFO] Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Verificar se uvicorn está instalado
python -c "import uvicorn" 2>nul
if errorlevel 1 (
    echo [ERRO] uvicorn nao encontrado!
    echo Execute 'pip install -r requirements.txt' primeiro.
    echo.
    pause
    exit /b 1
)

REM Iniciar servidor
echo [INFO] Iniciando microserviço FastAPI...
echo [INFO] Servidor será executado em: http://localhost:8080
echo [INFO] Documentação: http://localhost:8080/docs
echo [INFO] Pressione Ctrl+C para parar o servidor
echo.

uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

echo.
echo [INFO] Servidor parado.
pause
