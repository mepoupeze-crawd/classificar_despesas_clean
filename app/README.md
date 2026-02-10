# API FastAPI - Classificação de Despesas

## 📖 Documentação Oficial

**A documentação completa está disponível no [README.md](../README.md) (raiz do projeto).**

Este arquivo contém apenas informações específicas da API FastAPI.

## 🚀 Execução Rápida

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar .env (opcional)
cp env.example .env

# 3. Iniciar servidor
uvicorn app.main:app --port 8080 --host 127.0.0.1
```

## 📡 Endpoints

- **GET /healthz** - Health check
- **POST /v1/classify** - Classificar transações

## 🧪 Testes

```bash
# Teste automatizado
python test_samples.py

# Teste manual
curl -X POST "http://127.0.0.1:8080/v1/classify" \
  -H "Content-Type: application/json" \
  -d @app/samples/tx_single.json
```

---

**Para documentação completa, configuração detalhada e troubleshooting, consulte o [README.md](../README.md) principal.**