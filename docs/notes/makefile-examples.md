# Exemplos de Uso dos Comandos Make e Scripts

## Comandos Make (Unix/Linux/macOS)

### Desenvolvimento Local
```bash
# Iniciar API
make run-api

# Em outro terminal, executar testes
make test

# Testar health check
curl http://localhost:8080/healthz
```

### Docker
```bash
# Build da imagem
make docker-build

# Executar container
make docker-run

# Parar container (se necessário)
make docker-stop
```

## Scripts de Teste

### Unix/Linux/macOS
```bash
# Tornar scripts executáveis
chmod +x scripts/test-single.sh scripts/test-batch.sh

# Testar transação única
./scripts/test-single.sh

# Testar lote de transações
./scripts/test-batch.sh
```

### Windows (CMD)
```cmd
REM Testar transação única
scripts\test-single.bat

REM Testar lote de transações
scripts\test-batch.bat
```

### Windows (PowerShell)
```powershell
# Testar transação única
.\scripts\test-single.ps1

# Testar lote de transações
.\scripts\test-batch.ps1
```

## Fluxo Completo de Desenvolvimento

### 1. Desenvolvimento Local
```bash
# Terminal 1: Iniciar API
make run-api

# Terminal 2: Testar
./scripts/test-single.sh
```

### 2. Testes com Docker
```bash
# Build e execução
make docker-build
make docker-run

# Em outro terminal, testar
./scripts/test-batch.sh
```

### 3. Validação Completa
```bash
# Testes unitários
make test

# Testes de integração
./scripts/test-single.sh
./scripts/test-batch.sh
```

## Equivalentes Windows

| Comando Make | Equivalente Windows |
|--------------|-------------------|
| `make run-api` | `uvicorn app.main:app --reload --port 8080` |
| `make test` | `pytest -q` |
| `make docker-build` | `docker build -t ml-service:local .` |
| `make docker-run` | `docker run --rm -p 8080:8080 --env-file .env ml-service:local` |
| `make docker-stop` | `docker stop ml-service:local` |
