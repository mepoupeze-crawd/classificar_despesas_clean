# Script: cleanup-project-only.ps1
# Limpeza específica apenas para este projeto (agente_despesas)
# NÃO afeta outros containers Docker

Write-Host "🧹 Limpeza específica do projeto agente_despesas..." -ForegroundColor Yellow

# 1. Parar apenas containers deste projeto
Write-Host "1. Parando containers do projeto agente_despesas..." -ForegroundColor Cyan
docker compose down 2>$null
docker compose -f docker-compose.yml down 2>$null

# 2. Parar apenas containers com nomes relacionados ao projeto
Write-Host "2. Parando containers específicos do projeto..." -ForegroundColor Cyan
$projectContainers = docker ps -q --filter "name=cursor-agente_despesas" --filter "name=ml-service"
if ($projectContainers) {
    docker stop $projectContainers
    Write-Host "   Containers do projeto parados: $($projectContainers.Count)" -ForegroundColor Green
} else {
    Write-Host "   Nenhum container do projeto ativo" -ForegroundColor Green
}

# 3. Remover apenas containers parados do projeto
Write-Host "3. Removendo containers parados do projeto..." -ForegroundColor Cyan
$stoppedProjectContainers = docker ps -aq --filter "name=cursor-agente_despesas" --filter "name=ml-service"
if ($stoppedProjectContainers) {
    docker rm $stoppedProjectContainers
    Write-Host "   Containers do projeto removidos: $($stoppedProjectContainers.Count)" -ForegroundColor Green
} else {
    Write-Host "   Nenhum container do projeto para remover" -ForegroundColor Green
}

# 4. Verificar porta específica do projeto
Write-Host "4. Verificando porta 8081 (projeto)..." -ForegroundColor Cyan
$port8081 = netstat -ano | Select-String ":8081"
if ($port8081) {
    Write-Host "   ⚠️ Porta 8081 ainda em uso:" -ForegroundColor Yellow
    Write-Host $port8081 -ForegroundColor Red
} else {
    Write-Host "   ✅ Porta 8081 livre" -ForegroundColor Green
}

# 5. Limpeza apenas de recursos não utilizados (sem remover containers de outros projetos)
Write-Host "5. Limpando recursos não utilizados..." -ForegroundColor Cyan
docker system prune -f | Out-Null
Write-Host "   ✅ Recursos não utilizados limpos" -ForegroundColor Green

# 6. Status final - apenas containers relacionados ao projeto
Write-Host "=== Status Pós-Limpeza (Projeto) ===" -ForegroundColor Cyan
Write-Host "Containers do projeto:" -ForegroundColor Yellow
docker ps --filter "name=cursor-agente_despesas" --filter "name=ml-service"

Write-Host "Porta 8081:" -ForegroundColor Yellow
netstat -ano | Select-String ":8081"

Write-Host "Imagens do projeto:" -ForegroundColor Yellow
docker images | Select-String "ml-service"

Write-Host "🎉 Limpeza específica do projeto finalizada!" -ForegroundColor Green
Write-Host "ℹ️ Outros containers Docker não foram afetados" -ForegroundColor Cyan
