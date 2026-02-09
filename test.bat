@echo off
REM Script para executar testes no Windows

echo ========================================
echo  Agente de Despesas - Executar Testes
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

REM Verificar se pytest está instalado
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo [ERRO] pytest nao encontrado!
    echo Execute 'pip install -r requirements.txt' primeiro.
    echo.
    pause
    exit /b 1
)

REM Executar testes
echo [INFO] Executando suíte de testes...
echo.

python -m pytest spend_classification/tests/ -v

echo.
echo [INFO] Testes concluídos!
pause
