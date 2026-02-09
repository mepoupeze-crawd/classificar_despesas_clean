# Spend Classification Module

Módulo responsável por classificar a Natureza do Gasto de transações bancárias, utilizando uma combinação de modelos de machine learning e inteligência artificial.

## 🎯 Visão Geral

O módulo `spend_classification` é um sistema inteligente de classificação de despesas que combina múltiplas estratégias para garantir alta precisão na categorização de transações bancárias.

### Principais Funcionalidades

- **Classificação Automática**: Usa modelos ML treinados para classificar transações
- **Fallback Inteligente**: Integra ChatGPT + SerpApi quando confiança é baixa
- **Sistema de Regras**: Engine de regras para padrões conhecidos
- **Similaridade**: Classificação baseada em transações similares
- **Pipeline Flexível**: Sistema modular e configurável
- **Feedback Loop**: Sistema de feedback para melhoria contínua

## 📁 Estrutura do Módulo

```
spend_classification/
├── core/                    # Contratos, schemas e constantes
│   ├── contracts.py         # Interfaces e contratos base
│   ├── schemas.py           # Estruturas de dados (Pydantic)
│   ├── constants.py         # Constantes do sistema
│   └── __init__.py
├── engines/                 # Engines de classificação
│   ├── classifier.py        # Classificador principal
│   ├── ml_model.py          # Modelo de ML
│   ├── rules_engine.py      # Engine de regras
│   ├── similarity_engine.py # Engine de similaridade
│   ├── ai_fallback.py       # Fallback para IA
│   ├── pipeline.py          # Pipeline de processamento
│   └── __init__.py
├── tests/                   # Testes unitários
│   ├── test_core.py         # Testes do módulo core
│   ├── test_engines.py      # Testes dos engines
│   ├── test_integration.py  # Testes de integração
│   ├── test_smoke.py        # Teste de fumaça
│   └── __init__.py
├── __init__.py              # Módulo principal
└── README.md               # Esta documentação
```

## 🚀 Como Usar

### Instalação

O módulo está integrado ao projeto principal. Certifique-se de que as dependências estão instaladas:

```bash
pip install pandas scikit-learn pydantic openai requests
```

### Uso Básico

```python
from spend_classification import ExpenseClassifier, ExpenseTransaction
from datetime import datetime

# Cria uma transação
transaction = ExpenseTransaction(
    description="Netflix Com",
    amount=44.90,
    date=datetime.now()
)

# Classifica a transação
classifier = ExpenseClassifier()
result = classifier.classify(transaction)

print(f"Categoria: {result.category}")
print(f"Confiança: {result.confidence}")
print(f"Classificador usado: {result.classifier_used}")
```

### Uso com Pipeline

```python
from spend_classification import ClassificationPipeline, RulesEngine, SimilarityEngine

# Configura pipeline
pipeline = ClassificationPipeline()
pipeline.add_stage("rules", RulesEngine())
pipeline.add_stage("similarity", SimilarityEngine())

# Processa múltiplas transações
transactions = [
    ExpenseTransaction("Netflix Com", 44.90, datetime.now()),
    ExpenseTransaction("Drogasil", 25.50, datetime.now()),
    ExpenseTransaction("Carrefour", 150.00, datetime.now())
]

results = pipeline.process(transactions)

for result in results:
    print(f"{result.category} - {result.confidence:.2f}")
```

## 🧠 Engines Disponíveis

### 1. RulesEngine
Classifica baseado em padrões e regras predefinidas.

```python
from spend_classification.engines import RulesEngine

engine = RulesEngine()

# Adiciona regra personalizada
engine.add_rule({
    "name": "minha_loja",
    "pattern": "minha_loja",
    "category": "Gastos pessoais",
    "confidence": 0.9
})
```

### 2. SimilarityEngine
Classifica baseado em similaridade com exemplos históricos.

```python
from spend_classification.engines import SimilarityEngine

engine = SimilarityEngine()

# Adiciona exemplo personalizado
engine.add_example({
    "text": "Minha Loja Favorita",
    "category": "Gastos pessoais"
})
```

### 3. MLClassifier
Usa modelos de machine learning treinados.

```python
from spend_classification.engines import MLClassifier

classifier = MLClassifier(model_type="natureza_do_gasto")
result = classifier.classify(transaction)
```

### 4. AIFallbackEngine
Fallback para IA quando outros métodos falham.

```python
from spend_classification.engines import AIFallbackEngine

engine = AIFallbackEngine(
    openai_api_key="sua_chave_openai",
    serpapi_key="sua_chave_serpapi"
)
```

## ⚙️ Configuração

### Constantes

```python
from spend_classification.core.constants import (
    CATEGORIES,           # Lista de categorias disponíveis
    CONFIDENCE_THRESHOLD, # Threshold de confiança (padrão: 0.7)
    MODEL_PATHS,          # Caminhos dos modelos ML
    API_CONFIG           # Configurações das APIs
)
```

### Schemas

```python
from spend_classification.core.schemas import (
    ExpenseTransaction,    # Schema de transação
    ClassificationResult,  # Schema de resultado
    ModelMetrics,         # Schema de métricas
    FeedbackData          # Schema de feedback
)
```

## 🧪 Testes

### Executar Todos os Testes

```bash
python -m pytest spend_classification/tests/ -v
```

### Teste de Fumaça

```bash
python -m pytest spend_classification/tests/test_smoke.py -v
```

### Testes Específicos

```bash
# Testes do core
python -m pytest spend_classification/tests/test_core.py -v

# Testes dos engines
python -m pytest spend_classification/tests/test_engines.py -v

# Testes de integração
python -m pytest spend_classification/tests/test_integration.py -v
```

## 📊 Categorias Disponíveis

O sistema suporta as seguintes categorias de despesas:

- Conta de luz
- Conta de gás
- Internet & TV a cabo
- Moradia (Financiamento/ Aluguel/ Condominio)
- Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)
- Planos de celular
- Gastos com Diarista
- Gastos com Educação (Inglês, MBA, Pós)
- Farmácia
- Supermercado
- Casamento
- Restaurantes/ Bares/ Lanchonetes
- Viagens / Férias
- Carro (Manutenção/ IPVA/ Seguro)
- Combustível/ Passagens/ Uber / Sem Parar
- Cuidados Pessoais (Nutricionista / Medico / Suplemento)
- Gastos com casa (outros)
- Gastos com presentes
- Gastos pessoais
- Gastos com Cachorro
- Futevolei
- Financiamento/Condominio
- Obra casa
- Inteligência Artificial
- Investimento
- Salário

## 🔧 Extensibilidade

### Adicionando Novo Engine

```python
from spend_classification.core.contracts import ClassifierInterface

class MeuEngine(ClassifierInterface):
    def classify(self, transaction):
        # Sua lógica de classificação
        return ClassificationResult(
            category="Minha Categoria",
            confidence=0.8,
            classifier_used="meu_engine"
        )
    
    def batch_classify(self, transactions):
        return [self.classify(t) for t in transactions]
    
    def get_confidence_threshold(self):
        return 0.7
```

### Adicionando Nova Regra

```python
engine = RulesEngine()
engine.add_rule({
    "name": "regra_personalizada",
    "pattern": r"minha.*loja",
    "category": "Gastos pessoais",
    "confidence": 0.9,
    "conditions": {
        "amount_range": [10.0, 100.0]
    }
})
```

## 📈 Performance

### Processamento Paralelo

O pipeline suporta processamento paralelo para grandes volumes:

```python
pipeline = ClassificationPipeline(enable_parallel=True)
pipeline.max_workers = 8  # Configura número de workers

results = pipeline.process(large_transaction_list)
```

### Cache

O sistema suporta cache de predições:

```python
from spend_classification.core.constants import CACHE_CONFIG

# Configurações de cache
CACHE_CONFIG["enable_memory_cache"] = True
CACHE_CONFIG["cache_ttl"] = 3600  # 1 hora
```

## 🔍 Monitoramento

### Estatísticas do Pipeline

```python
stats = pipeline.get_pipeline_stats()
print(f"Total de etapas: {stats['total_stages']}")
print(f"Etapas habilitadas: {stats['enabled_stages']}")

# Estatísticas por etapa
for stage_name, stage_stats in stats['stages'].items():
    print(f"{stage_name}: {stage_stats['stats']['success_rate']:.2%}")
```

### Métricas de Performance

```python
from spend_classification.core.schemas import ProcessingStats

stats = pipeline.get_processing_stats(transactions)
print(f"Transações processadas: {stats.total_transactions}")
print(f"Taxa de sucesso: {stats.successful_classifications / stats.total_transactions:.2%}")
print(f"Confiança média: {stats.average_confidence:.2f}")
```

## 🚨 Solução de Problemas

### Erro: "Model not loaded"
```python
# Verifica se o modelo está carregado
classifier = MLClassifier()
if not classifier.model:
    print("Modelo não carregado. Verifique o caminho do arquivo.")
```

### Erro: "OpenAI API key not provided"
```python
# Configura API key
import os
os.environ["OPENAI_API_KEY"] = "sua_chave_aqui"

engine = AIFallbackEngine()
```

### Baixa Precisão
```python
# Ajusta threshold de confiança
classifier = ExpenseClassifier(confidence_threshold=0.8)

# Adiciona mais regras
rules_engine = RulesEngine()
rules_engine.add_rule({
    "name": "padrao_especifico",
    "pattern": "seu_padrao",
    "category": "Categoria Correta",
    "confidence": 0.95
})
```

## 📝 Logs

O sistema usa logging padrão do Python:

```python
import logging

# Configura nível de log
logging.basicConfig(level=logging.INFO)

# Logs específicos do módulo
logger = logging.getLogger("spend_classification")
logger.info("Sistema inicializado")
```

## 🤝 Contribuição

Para contribuir com o módulo:

1. Adicione testes para novas funcionalidades
2. Mantenha a cobertura de testes alta
3. Siga os padrões de código existentes
4. Documente novas APIs e funcionalidades

## 📄 Licença

Este módulo faz parte do projeto Agente de Despesas e segue a mesma licença.

---

**Versão**: 1.0.0  
**Autor**: Agente Despesas  
**Última Atualização**: Outubro 2025
