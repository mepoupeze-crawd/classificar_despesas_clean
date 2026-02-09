# Script: cleanup-docker.ps1
# Limpeza completa do Docker para desenvolvimento

Write-Host "🧹 Iniciando limpeza completa do Docker..." -ForegroundColor Yellow

# 1. Parar Docker Compose
Write-Host "1. Parando Docker Compose..." -ForegroundColor Cyan
docker compose down 2>$null
docker compose -f docker-compose.yml down 2>$null

# 2. Parar todos os containers
Write-Host "2. Parando todos os containers..." -ForegroundColor Cyan
$containers = docker ps -q
if ($containers) {
    docker stop $containers
    Write-Host "   Containers parados: $($containers.Count)" -ForegroundColor Green
} else {
    Write-Host "   Nenhum container ativo" -ForegroundColor Green
}

# 3. Remover containers parados
Write-Host "3. Removendo containers parados..." -ForegroundColor Cyan
$stoppedContainers = docker ps -aq
if ($stoppedContainers) {
    docker rm $stoppedContainers
    Write-Host "   Containers removidos: $($stoppedContainers.Count)" -ForegroundColor Green
} else {
    Write-Host "   Nenhum container para remover" -ForegroundColor Green
}

# 4. Verificar portas
Write-Host "4. Verificando portas..." -ForegroundColor Cyan
$port8081 = netstat -ano | Select-String ":8081"
if ($port8081) {
    Write-Host "   ⚠️ Porta 8081 ainda em uso:" -ForegroundColor Yellow
    Write-Host $port8081 -ForegroundColor Red
} else {
    Write-Host "   ✅ Porta 8081 livre" -ForegroundColor Green
}

# 5. Limpeza de recursos
Write-Host "5. Limpando recursos Docker..." -ForegroundColor Cyan
docker system prune -f | Out-Null
Write-Host "   ✅ Recursos limpos" -ForegroundColor Green

# 6. Status final
Write-Host "=== Status Pós-Limpeza ===" -ForegroundColor Cyan
Write-Host "Containers ativos:" -ForegroundColor Yellow
docker ps

Write-Host "Porta 8081:" -ForegroundColor Yellow
netstat -ano | Select-String ":8081"

Write-Host "Imagens:" -ForegroundColor Yellow
docker images | Select-String "ml-service"

Write-Host "🎉 Limpeza completa finalizada!" -ForegroundColor Green
