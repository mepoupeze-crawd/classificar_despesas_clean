#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Prepara o ambiente para processamento de PDF, limpando caches e processos Python.

.DESCRIPTION
    Este script:
    1. Para TODOS os processos Python em execução (incluindo processos filhos)
    2. Verifica e para múltiplas instâncias do servidor rodando
    3. Limpa todos os diretórios __pycache__
    4. Verifica se há pacotes instalados via pip que possam conflitar
    5. Verifica a localização do módulo card_pdf_parser
    6. Configura PYTHONPATH e variáveis de ambiente para desenvolvimento
    7. Prepara o ambiente para execução com reload automático

.PARAMETER StartServer
    Se especificado, inicia o servidor após preparar o ambiente.

.PARAMETER Port
    Porta do servidor (padrão: 8081). Usado apenas se StartServer for True.

.PARAMETER UninstallConflictingPackages
    Se especificado, desinstala automaticamente pacotes conflitantes encontrados via pip.

.EXAMPLE
    .\scripts\prepare-environment.ps1
    
.EXAMPLE
    .\scripts\prepare-environment.ps1 -StartServer -Port 8081
    
.EXAMPLE
    .\scripts\prepare-environment.ps1 -UninstallConflictingPackages
#>

param(
    [switch]$StartServer = $false,
    [int]$Port = 8081,
    [switch]$UninstallConflictingPackages = $false
)

$workspace = "E:\Documentos\IA\Cursor - agente_despesas"
Set-Location $workspace

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Preparando Ambiente para PDF Parsing" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Parar TODOS os processos Python (incluindo processos filhos)
Write-Host "[1/7] Parando TODOS os processos Python..." -ForegroundColor Yellow
$pythonProcs = Get-Process python -ErrorAction SilentlyContinue
$pythonwProcs = Get-Process pythonw -ErrorAction SilentlyContinue
$allPythonProcs = @($pythonProcs) + @($pythonwProcs) | Where-Object { $_ -ne $null }

if ($allPythonProcs) {
    $count = ($allPythonProcs | Measure-Object).Count
    Write-Host "   Encontrado(s) $count processo(s) Python..." -ForegroundColor Gray
    
    # Parar processos filhos primeiro
    foreach ($proc in $allPythonProcs) {
        try {
            $children = Get-CimInstance Win32_Process | Where-Object { $_.ParentProcessId -eq $proc.Id }
            foreach ($child in $children) {
                try {
                    Stop-Process -Id $child.ProcessId -Force -ErrorAction SilentlyContinue
                    Write-Host "   [OK] Processo filho $($child.ProcessId) encerrado." -ForegroundColor Gray
                } catch { }
            }
        } catch { }
    }
    
    # Parar processos principais
    $allPythonProcs | Stop-Process -Force -ErrorAction SilentlyContinue
    Write-Host "   [OK] $count processo(s) Python encerrado(s)." -ForegroundColor Green
    Start-Sleep -Seconds 3  # Aguardar mais tempo para garantir que processos foram finalizados
} else {
    Write-Host "   [OK] Nenhum processo Python em execucao." -ForegroundColor Gray
}

# 2. Verificar e parar múltiplas instâncias do servidor na porta específica
Write-Host "[2/7] Verificando instancias do servidor na porta $Port..." -ForegroundColor Yellow
try {
    $netstatOutput = netstat -ano | Select-String ":$Port\s"
    if ($netstatOutput) {
        $pids = $netstatOutput | ForEach-Object {
            if ($_ -match '\s+(\d+)\s*$') {
                $matches[1]
            }
        } | Select-Object -Unique
        
        if ($pids) {
            Write-Host "   [ATENCAO] Encontrado(s) processo(s) usando a porta ${Port}:" -ForegroundColor Yellow
            foreach ($processId in $pids) {
                try {
                    $proc = Get-Process -Id $processId -ErrorAction SilentlyContinue
                    if ($proc) {
                        Write-Host "      PID $processId - $($proc.ProcessName) - $($proc.Path)" -ForegroundColor Yellow
                        Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
                        Write-Host "      [OK] Processo $processId encerrado." -ForegroundColor Green
                    }
                } catch {
                    Write-Host "      [AVISO] Nao foi possivel encerrar processo $processId" -ForegroundColor Yellow
                }
            }
            Start-Sleep -Seconds 2
        } else {
            Write-Host "   [OK] Nenhum processo usando a porta $Port." -ForegroundColor Green
        }
    } else {
        Write-Host "   [OK] Nenhum processo usando a porta $Port." -ForegroundColor Green
    }
} catch {
    Write-Host "   [AVISO] Nao foi possivel verificar processos na porta $Port`: ${_}" -ForegroundColor Yellow
}

# 3. Limpar todos os caches __pycache__ e arquivos .pyc
Write-Host "[3/7] Limpando caches Python..." -ForegroundColor Yellow
$cacheDirs = Get-ChildItem -Path . -Filter __pycache__ -Recurse -Directory -ErrorAction SilentlyContinue
$pycFiles = Get-ChildItem -Path . -Filter *.pyc -Recurse -File -ErrorAction SilentlyContinue
$pyoFiles = Get-ChildItem -Path . -Filter *.pyo -Recurse -File -ErrorAction SilentlyContinue

$totalRemoved = 0
if ($cacheDirs) {
    $count = ($cacheDirs | Measure-Object).Count
    $cacheDirs | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    $totalRemoved += $count
    Write-Host "   [OK] $count diretorio(s) __pycache__ removido(s)." -ForegroundColor Green
}
if ($pycFiles) {
    $count = ($pycFiles | Measure-Object).Count
    $pycFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    $totalRemoved += $count
    Write-Host "   [OK] $count arquivo(s) .pyc removido(s)." -ForegroundColor Green
}
if ($pyoFiles) {
    $count = ($pyoFiles | Measure-Object).Count
    $pyoFiles | Remove-Item -Force -ErrorAction SilentlyContinue
    $totalRemoved += $count
    Write-Host "   [OK] $count arquivo(s) .pyo removido(s)." -ForegroundColor Green
}
if ($totalRemoved -eq 0) {
    Write-Host "   [OK] Nenhum cache encontrado." -ForegroundColor Gray
}

# 4. Verificar pacotes instalados via pip e verificar se estão sendo usados
Write-Host "[4/7] Verificando pacotes instalados via pip..." -ForegroundColor Yellow
$conflictingPackages = @()
try {
    $pipOutput = pip list 2>&1 | Out-String
    if ($pipOutput -match "card-pdf-parser|card_pdf_parser") {
        $installedPackages = $pipOutput -split "`n" | Select-String -Pattern "card-pdf-parser|card_pdf_parser"
        foreach ($pkg in $installedPackages) {
            $pkgName = ($pkg -split '\s+')[0]
            $conflictingPackages += $pkgName
            Write-Host "   [ATENCAO] Pacote encontrado instalado via pip: $pkgName" -ForegroundColor Yellow
            
            # Verificar se o pacote está sendo usado em vez do código local
            try {
                $modulePathOutput = python -c "import $($pkgName.Replace('-', '_')); import os; print(os.path.dirname($($pkgName.Replace('-', '_')).__file__))" 2>&1
                if ($modulePathOutput -and -not ($modulePathOutput -is [System.Management.Automation.ErrorRecord])) {
                    $modulePath = $modulePathOutput.ToString().Trim()
                    $expectedPath = Join-Path $workspace "card_pdf_parser"
                    if ($modulePath -ne $expectedPath) {
                        Write-Host "   [ERRO] Python esta usando: $modulePath" -ForegroundColor Red
                        Write-Host "   [ERRO] Esperado: $expectedPath" -ForegroundColor Red
                        Write-Host "   [ERRO] O pacote instalado via pip esta sendo usado em vez do codigo local!" -ForegroundColor Red
                    }
                }
            } catch {
                Write-Host "   [AVISO] Nao foi possivel verificar localizacao do pacote." -ForegroundColor Yellow
            }
        }
        
        if ($conflictingPackages.Count -gt 0) {
            Write-Host "   [ATENCAO] Isso pode causar conflito com o codigo local." -ForegroundColor Yellow
            if ($UninstallConflictingPackages) {
                Write-Host "   [ACAO] Desinstalando pacotes conflitantes..." -ForegroundColor Cyan
                foreach ($pkg in $conflictingPackages) {
                    try {
                        pip uninstall $pkg -y 2>&1 | Out-Null
                        Write-Host "   [OK] Pacote $pkg desinstalado." -ForegroundColor Green
                    } catch {
                        Write-Host "   [ERRO] Falha ao desinstalar $pkg`: ${_}" -ForegroundColor Red
                    }
                }
            } else {
                Write-Host "   [DICA] Para desinstalar automaticamente, execute:" -ForegroundColor Cyan
                Write-Host "          .\scripts\prepare-environment.ps1 -UninstallConflictingPackages" -ForegroundColor Cyan
                Write-Host "   [DICA] Ou manualmente: pip uninstall $($conflictingPackages -join ' ') -y" -ForegroundColor Cyan
            }
        }
    } else {
        Write-Host "   [OK] Nenhum pacote conflitante encontrado." -ForegroundColor Green
    }
} catch {
    Write-Host "   [AVISO] Nao foi possivel verificar pacotes instalados`: ${_}" -ForegroundColor Yellow
}

# 5. Verificar localização do módulo
Write-Host "[5/7] Verificando localizacao do modulo..." -ForegroundColor Yellow
try {
    $modulePathOutput = python -c "import card_pdf_parser; import os; print(os.path.dirname(card_pdf_parser.__file__))" 2>&1
    if ($modulePathOutput -and -not ($modulePathOutput -is [System.Management.Automation.ErrorRecord])) {
        $modulePath = $modulePathOutput.ToString().Trim()
        $expectedPath = Join-Path $workspace "card_pdf_parser"
        if ($modulePath -eq $expectedPath) {
            Write-Host "   [OK] Modulo usando codigo local: $modulePath" -ForegroundColor Green
        } else {
            Write-Host "   [ERRO] Modulo encontrado em: $modulePath" -ForegroundColor Red
            Write-Host "   [ERRO] Esperado em: $expectedPath" -ForegroundColor Red
            Write-Host "   [ERRO] O Python esta usando um pacote instalado em vez do codigo local!" -ForegroundColor Red
            Write-Host "   [DICA] Execute: .\scripts\prepare-environment.ps1 -UninstallConflictingPackages" -ForegroundColor Cyan
        }
    } else {
        Write-Host "   [AVISO] Nao foi possivel determinar a localizacao do modulo." -ForegroundColor Yellow
    }
} catch {
    Write-Host "   [AVISO] Erro ao verificar modulo`: ${_}" -ForegroundColor Yellow
}

# 6. Configurar PYTHONPATH e variáveis de ambiente
Write-Host "[6/7] Configurando PYTHONPATH e variaveis de ambiente..." -ForegroundColor Yellow
try {
    $pythonPathOutput = python -c "import sys; print(';'.join(sys.path))" 2>&1
    if ($pythonPathOutput -and -not ($pythonPathOutput -is [System.Management.Automation.ErrorRecord])) {
        $currentPythonPath = $pythonPathOutput.ToString()
        if ($currentPythonPath.Contains($workspace)) {
            Write-Host "   [OK] Workspace ja esta no PYTHONPATH." -ForegroundColor Green
        } else {
            Write-Host "   [ACAO] Adicionando workspace ao PYTHONPATH..." -ForegroundColor Cyan
            $env:PYTHONPATH = "$workspace;$env:PYTHONPATH"
            Write-Host "   [OK] PYTHONPATH atualizado." -ForegroundColor Green
        }
    } else {
        Write-Host "   [ACAO] Configurando PYTHONPATH..." -ForegroundColor Cyan
        $env:PYTHONPATH = "$workspace;$env:PYTHONPATH"
        Write-Host "   [OK] PYTHONPATH configurado." -ForegroundColor Green
    }
    
    # Configurar variável de ambiente RELOAD para desenvolvimento
    $env:RELOAD = "true"
    Write-Host "   [OK] RELOAD=true configurado para desenvolvimento (uvicorn --reload)." -ForegroundColor Green
} catch {
    Write-Host "   [AVISO] Erro ao configurar PYTHONPATH`: ${_}" -ForegroundColor Yellow
}

# 7. Verificar se o código está atualizado
Write-Host "[7/7] Verificando integridade do codigo..." -ForegroundColor Yellow
$criticalFiles = @(
    "card_pdf_parser\parser\rules.py",
    "card_pdf_parser\parser\classify.py",
    "card_pdf_parser\api.py",
    "run_server.py"
)
$allFilesExist = $true
foreach ($file in $criticalFiles) {
    $fullPath = Join-Path $workspace $file
    if (-not (Test-Path $fullPath)) {
        Write-Host "   [ERRO] Arquivo nao encontrado: $file" -ForegroundColor Red
        $allFilesExist = $false
    }
}
if ($allFilesExist) {
    Write-Host "   [OK] Todos os arquivos criticos encontrados." -ForegroundColor Green
} else {
    Write-Host "   [ERRO] Alguns arquivos criticos estao faltando!" -ForegroundColor Red
}

# Resumo final
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Ambiente Preparado!" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Configuracao aplicada:" -ForegroundColor Yellow
Write-Host "  - Todos os processos Python foram encerrados" -ForegroundColor Gray
Write-Host "  - Porta $Port verificada e liberada" -ForegroundColor Gray
Write-Host "  - Caches Python limpos" -ForegroundColor Gray
Write-Host "  - PYTHONPATH configurado: $workspace" -ForegroundColor Gray
Write-Host "  - RELOAD=true configurado (uvicorn --reload habilitado)" -ForegroundColor Gray
if ($conflictingPackages.Count -gt 0 -and -not $UninstallConflictingPackages) {
    Write-Host "  - [ATENCAO] Pacotes conflitantes encontrados (nao desinstalados)" -ForegroundColor Yellow
}

Write-Host "`nProximos passos:" -ForegroundColor Yellow
Write-Host "  1. Execute: .\scripts\run-parse-itau.ps1" -ForegroundColor Cyan
Write-Host "     OU" -ForegroundColor Gray
Write-Host "  2. Execute: python parse_pdf_direct.py" -ForegroundColor Cyan
Write-Host "`n"

# Opcional: Iniciar servidor
if ($StartServer) {
    Write-Host "Iniciando servidor na porta $Port com reload habilitado..." -ForegroundColor Cyan
    Write-Host "Pressione Ctrl+C para parar o servidor`n" -ForegroundColor Yellow
    
    $env:PORT = "$Port"
    $env:RELOAD = "true"
    python run_server.py
} else {
    Write-Host "Para iniciar o servidor automaticamente, execute:" -ForegroundColor Gray
    Write-Host "  .\scripts\prepare-environment.ps1 -StartServer -Port $Port`n" -ForegroundColor Cyan
}

