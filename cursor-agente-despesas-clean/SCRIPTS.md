# Scripts de Conveniência

Este projeto inclui scripts para facilitar o uso do microserviço FastAPI.

## 🪟 Windows

### Scripts Disponíveis:
- `install.bat` - Instala dependências e cria ambiente virtual
- `run.bat` - Executa o microserviço FastAPI
- `test.bat` - Executa a suíte de testes
- `test-api.bat` - Testa a API com curl (fallback para PowerShell)
- `test-api.ps1` - Testa a API com PowerShell (recomendado para Windows)

### Como Usar:
```cmd
# 1. Instalar dependências
install.bat

# 2. Executar servidor
run.bat

# 3. Em outro terminal, testar API (PowerShell recomendado)
test-api.ps1
# ou
test-api.bat

# 4. Executar testes
test.bat
```

### Teste Manual com PowerShell:
```powershell
# Teste rápido no PowerShell
Invoke-WebRequest -Uri "http://localhost:8080/healthz" -Method GET

# Teste de classificação
$jsonData = @'
[
    {
        "description": "Netflix Com",
        "amount": 44.90,
        "date": "2024-01-01T00:00:00",
        "card_holder": "CC - Aline Silva"
    }
]
'@

Invoke-WebRequest -Uri "http://localhost:8080/v1/classify" -Method POST -Body $jsonData -ContentType "application/json"
```

## 🐧 Linux/Mac

### Scripts Disponíveis:
- `Makefile` - Comandos make para todas as operações
- `test-api.sh` - Testa a API com curl

### Como Usar:
```bash
# 1. Instalar dependências
make install

# 2. Executar servidor
make run

# 3. Em outro terminal, testar API
make api-test
# ou
./test-api.sh

# 4. Executar testes
make test

# 5. Ver todos os comandos disponíveis
make help
```

## 📋 Comandos Make Disponíveis

```bash
make help          # Mostra todos os comandos disponíveis
make install       # Instala dependências e cria ambiente virtual
make run           # Executa o microserviço FastAPI
make test          # Executa a suíte de testes
make test-api      # Executa apenas os testes da API
make demo          # Executa o demo do microserviço
make pipeline      # Executa o pipeline completo de classificação
make clean         # Remove arquivos temporários e cache
make clean-venv    # Remove o ambiente virtual
make status        # Mostra status do projeto
make api-health    # Testa health check da API
make api-test      # Testa classificação via API
```

## 🔧 Comandos de Desenvolvimento

```bash
make dev-install   # Instala dependências de desenvolvimento
make format        # Formata o código com black
make lint          # Executa linting com flake8
make coverage      # Executa testes com cobertura
```

## 🌐 URLs Importantes

Quando o servidor estiver rodando:
- **API**: http://localhost:8080
- **Health Check**: http://localhost:8080/healthz
- **Classificação**: http://localhost:8080/v1/classify
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

## 🚨 Solução de Problemas

### Windows
- **"Python não encontrado"**: Instale Python 3.10+ e adicione ao PATH
- **"curl não encontrado"**: Instale curl ou use PowerShell com `Invoke-WebRequest`
- **"Ambiente virtual não encontrado"**: Execute `install.bat` primeiro

### Linux/Mac
- **"make: command not found"**: Instale make (`sudo apt install make` no Ubuntu)
- **"jq não encontrado"**: Instale jq (`sudo apt install jq` no Ubuntu)
- **"curl não encontrado"**: Instale curl (`sudo apt install curl` no Ubuntu)

## 📝 Exemplo de Uso Completo

### Windows:
```cmd
# Terminal 1: Instalar e executar
install.bat
run.bat

# Terminal 2: Testar
test-api.bat
```

### Linux/Mac:
```bash
# Terminal 1: Instalar e executar
make install
make run

# Terminal 2: Testar
make api-test
```

## 🎯 Próximos Passos

Após executar os scripts:
1. **Teste a API** usando os scripts de teste
2. **Acesse a documentação** em http://localhost:8080/docs
3. **Execute os testes** para verificar se tudo está funcionando
4. **Explore o código** para entender como funciona
