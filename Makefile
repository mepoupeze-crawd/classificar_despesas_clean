# Makefile para o projeto Agente de Despesas

.PHONY: help run run-api test install clean demo docker-build docker-run docker-stop

# Variáveis
VENV = venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
UVICORN = $(VENV)/bin/uvicorn
PYTEST = $(VENV)/bin/pytest

# Cores para output
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Mostra esta ajuda
	@echo "$(GREEN)Agente de Despesas - Comandos Disponíveis:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Instala dependências e cria ambiente virtual
	@echo "$(GREEN)Instalando dependências...$(NC)"
	python -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)Instalação concluída!$(NC)"
	@echo "$(YELLOW)Para ativar o ambiente virtual: source $(VENV)/bin/activate$(NC)"

run: ## Executa o microserviço FastAPI (legacy)
	@echo "$(GREEN)Iniciando microserviço FastAPI...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(RED)Ambiente virtual não encontrado. Execute 'make install' primeiro.$(NC)"; \
		exit 1; \
	fi
	$(UVICORN) app.main:app --reload --host 0.0.0.0 --port 8080

run-api: ## Executa a API FastAPI (novo target)
	@echo "$(GREEN)Iniciando API FastAPI...$(NC)"
	uvicorn app.main:app --reload --port 8080

test: ## Executa a suíte de testes
	@echo "$(GREEN)Executando testes...$(NC)"
	pytest -q

test-api: ## Executa apenas os testes da API
	@echo "$(GREEN)Executando testes da API...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(RED)Ambiente virtual não encontrado. Execute 'make install' primeiro.$(NC)"; \
		exit 1; \
	fi
	$(PYTEST) spend_classification/tests/test_api.py -v

demo: ## Executa o demo do microserviço
	@echo "$(GREEN)Executando demo...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(RED)Ambiente virtual não encontrado. Execute 'make install' primeiro.$(NC)"; \
		exit 1; \
	fi
	$(PYTHON) app/demo.py

pipeline: ## Executa o pipeline completo de classificação
	@echo "$(GREEN)Executando pipeline completo...$(NC)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(RED)Ambiente virtual não encontrado. Execute 'make install' primeiro.$(NC)"; \
		exit 1; \
	fi
	$(PYTHON) pipeline_gastos.py

clean: ## Remove arquivos temporários e cache
	@echo "$(GREEN)Limpando arquivos temporários...$(NC)"
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache
	rm -rf .coverage
	@echo "$(GREEN)Limpeza concluída!$(NC)"

clean-venv: ## Remove o ambiente virtual
	@echo "$(YELLOW)Removendo ambiente virtual...$(NC)"
	rm -rf $(VENV)
	@echo "$(GREEN)Ambiente virtual removido!$(NC)"

status: ## Mostra status do projeto
	@echo "$(GREEN)Status do Projeto:$(NC)"
	@echo "  Ambiente virtual: $(if $(wildcard $(VENV)),$(GREEN)Instalado$(NC),$(RED)Não instalado$(NC))"
	@echo "  Python: $(shell python --version 2>/dev/null || echo '$(RED)Não encontrado$(NC)')"
	@echo "  Arquivos principais:"
	@ls -la app/main.py 2>/dev/null && echo "    $(GREEN)✓$(NC) app/main.py" || echo "    $(RED)✗$(NC) app/main.py"
	@ls -la pipeline_gastos.py 2>/dev/null && echo "    $(GREEN)✓$(NC) pipeline_gastos.py" || echo "    $(RED)✗$(NC) pipeline_gastos.py"
	@ls -la requirements.txt 2>/dev/null && echo "    $(GREEN)✓$(NC) requirements.txt" || echo "    $(RED)✗$(NC) requirements.txt"

# Comandos de desenvolvimento
dev-install: install ## Instala dependências de desenvolvimento
	$(PIP) install pytest pytest-cov black flake8

format: ## Formata o código com black
	@echo "$(GREEN)Formatando código...$(NC)"
	$(VENV)/bin/black .

lint: ## Executa linting com flake8
	@echo "$(GREEN)Executando linting...$(NC)"
	$(VENV)/bin/flake8 .

coverage: ## Executa testes com cobertura
	@echo "$(GREEN)Executando testes com cobertura...$(NC)"
	$(PYTEST) spend_classification/tests/ --cov=spend_classification --cov-report=html --cov-report=term

# Comandos de API
api-health: ## Testa health check da API
	@echo "$(GREEN)Testando health check...$(NC)"
	curl -s http://localhost:8080/healthz | jq . || echo "$(RED)API não está rodando ou jq não está instalado$(NC)"

api-test: ## Testa classificação via API
	@echo "$(GREEN)Testando classificação via API...$(NC)"
	curl -X POST "http://localhost:8080/v1/classify" \
		-H "Content-Type: application/json" \
		-d '[{"description": "Netflix Com", "amount": 44.90, "date": "2024-01-01T00:00:00", "card_holder": "CC - Aline Silva"}]' | jq . || echo "$(RED)API não está rodando ou jq não está instalado$(NC)"

# Comando padrão
.DEFAULT_GOAL := help

# Comandos Docker
docker-build: ## Build da imagem Docker
	@echo "$(GREEN)Fazendo build da imagem Docker...$(NC)"
	docker build -t ml-service:local .

docker-run: ## Executa container Docker
	@echo "$(GREEN)Executando container Docker...$(NC)"
	docker run --rm -p 8080:8080 --env-file .env ml-service:local

docker-stop: ## Para container Docker (best-effort)
	@echo "$(YELLOW)Parando container Docker...$(NC)"
	@docker stop ml-service:local 2>/dev/null || echo "$(YELLOW)Container não estava rodando$(NC)"
	@docker rm ml-service:local 2>/dev/null || echo "$(YELLOW)Container não existia$(NC)"
