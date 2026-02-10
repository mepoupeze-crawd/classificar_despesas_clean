@echo off
REM Script para instalar dependências no Windows

echo ========================================
echo  Agente de Despesas - Instalação
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Instale Python 3.10+ primeiro.
    echo.
    pause
    exit /b 1
)

echo [INFO] Python encontrado:
python --version

REM Criar ambiente virtual se não existir
if not exist "venv" (
    echo [INFO] Criando ambiente virtual...
    python -m venv venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar ambiente virtual!
        pause
        exit /b 1
    )
    echo [INFO] Ambiente virtual criado com sucesso!
) else (
    echo [INFO] Ambiente virtual já existe.
)

REM Ativar ambiente virtual
echo [INFO] Ativando ambiente virtual...
call venv\Scripts\activate.bat

REM Atualizar pip
echo [INFO] Atualizando pip...
python -m pip install --upgrade pip

REM Instalar dependências
echo [INFO] Instalando dependências...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependências!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Instalação concluída com sucesso!
echo.
echo Para usar o projeto:
echo   1. Execute 'run.bat' para iniciar o servidor
echo   2. Execute 'test.bat' para rodar os testes
echo   3. Acesse http://localhost:8080/docs para documentação
echo.
pause
