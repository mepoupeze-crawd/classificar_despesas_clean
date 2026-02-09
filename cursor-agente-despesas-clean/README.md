# Sistema de Classificação de Despesas

Sistema inteligente para classificação automática da **Natureza do Gasto** e campos derivados (tipo, parcelas, compartilhamento) usando regras determinísticas, similaridade TF-IDF e modelos de Machine Learning.

## 🚀 Quick Start

### Pronto para uso: Docker Compose (Recomendado)

O ambiente está configurado para rodar com **Docker Compose** na porta **8081**

#### Comandos essenciais:

```bash
# 1. Subir o ambiente (primeira vez)
docker-compose up -d

# 2. Ver logs em tempo real
docker-compose logs -f

# 3. Parar o ambiente
docker-compose down

# 4. Reiniciar (após mudanças no código)
docker-compose restart

# 5. Rebuild completo (após mudanças no Dockerfile ou dependências)
docker-compose up -d --build

# 6. Health check
curl http://localhost:8081/health
```

#### Testar classificação:
```bash
curl -X POST "http://localhost:8081/v1/classify" \
  -H "Content-Type: application/json" \
  -d @app/samples/tx_single.json
```

#### Testar parsing de fatura Itaú (PDF):
```bash
curl -X POST "http://localhost:8081/parse_itau" \
  -H "accept: application/json" \
  -F "file=@./fatura_cartao.pdf"
```
> Resultado com as transações extraídas também fica salvo em `parse_output.json` ao executar `python parse_pdf_direct.py` ou `.\scripts\run-parse-itau.ps1`.

#### Atualizar após mudanças no código:
```bash
# Após fazer push para main ou alterações locais
docker-compose restart  # Reinicia com o código atual
```

**Nota**: Mudanças no código Python não requerem rebuild. Apenas `restart` é suficiente. Use `--build` apenas para mudanças em `requirements.txt` ou `Dockerfile`.

**Dependências fixas (sklearn/joblib)**: após alterar `requirements.txt` para pinagem de versões (por exemplo, `scikit-learn==1.6.1` e `joblib==1.4.2`), execute `docker-compose build` ou refaça a imagem no ambiente de deploy para garantir que a versão correta seja usada em produção. Valide a imagem com `pip show scikit-learn joblib` dentro do container após o build.

---

## 1. Visão Geral

### O que faz
- **Classifica Natureza do Gasto** de transações bancárias automaticamente
- **Inferência de campos derivados**: tipo (crédito/débito), parcelas, compartilhamento
- **Pipeline híbrido**: Regras → Similaridade → Modelo ML → Fallback
- **API FastAPI** para integração com sistemas externos
- **Testes automatizados** com 173 testes cobrindo todos os componentes

### Pontos-chave
- ✅ **Execução local** sem dependências externas obrigatórias
- ✅ **API REST** com documentação interativa
- ✅ **Thresholds configuráveis** via variáveis de ambiente
- ✅ **Modelos sklearn** treinados com validação cruzada e calibração
- ✅ **Sistema de feedback** para melhoria contínua
- ✅ **Pipeline de retreino** automatizado com backup e validação
- ✅ **Testes de diagnóstico** para validação de casos específicos

## 2. Stack Tecnológica

### Linguagem e Runtime
- **Python 3.11**: Linguagem principal do projeto
- **Docker**: Containerização para deploy e desenvolvimento
- **Docker Compose**: Orquestração de containers para ambiente local

### Framework Web e API
- **FastAPI 0.104+**: Framework web moderno e assíncrono para construção da API REST
- **Uvicorn**: Servidor ASGI de alta performance
- **Pydantic 2.0+**: Validação de dados e serialização

### Machine Learning e Processamento de Dados
- **scikit-learn 1.6.1**: Biblioteca principal para ML
  - `LogisticRegression`: Classificador linear balanceado
  - `LinearSVC`: Support Vector Classifier
  - `CalibratedClassifierCV`: Calibração de probabilidades
  - `TfidfVectorizer`: Vetorização de texto
  - `StratifiedKFold`: Validação cruzada estratificada
- **pandas 1.5+**: Manipulação e análise de dados
- **numpy 1.21+**: Computação numérica
- **joblib 1.4.2**: Serialização de modelos ML

### Processamento de Documentos
- **pdfplumber 0.10+**: Extração de texto e dados de PDFs
- **PyPDF2 3.0+**: Processamento adicional de PDFs
- **openpyxl 3.0+**: Leitura de arquivos Excel
- **xlrd 2.0+**: Suporte adicional para Excel

### APIs Externas (Opcionais)
- **OpenAI API**: Fallback inteligente com GPT-4o-mini
- **Anthropic API**: Fallback alternativo com Claude-3-haiku
- **SerpAPI**: Busca de contexto sobre estabelecimentos

### Ferramentas de Desenvolvimento
- **pytest 7.0+**: Framework de testes automatizados
- **python-dotenv**: Gerenciamento de variáveis de ambiente
- **requests**: Cliente HTTP para APIs externas

### Infraestrutura e Deploy
- **Docker**: Containerização
- **Google Cloud Run**: Plataforma de deploy serverless (opcional)
- **GCP Artifact Registry**: Registry de imagens Docker (opcional)

### Estrutura de Dados
- **CSV**: Formato principal para dados de treinamento e feedbacks
- **JSON**: Formato de comunicação da API REST
- **PKL (joblib)**: Serialização de modelos treinados

## 3. Arquitetura

### Fluxo de Classificação
```
Transação → Regras → Similaridade (TF-IDF) → Modelo sklearn → Fallback IA → "duvida"
```

**Nota**: Regras determinísticas e TF-IDF podem ser desabilitados via feature flags.

### Estrutura do Projeto
```
📁 spend_classification/
├── core/           # Contratos, schemas e constantes
├── engines/        # Regras, similaridade, model_adapter, pipeline
└── tests/          # Suíte automatizada (173 testes)

📁 app/             # Serviço FastAPI
├── main.py         # Endpoints /healthz, /v1/classify e /parse_itau
├── routes_feedback.py  # Endpoints de feedback e pipeline
├── services/       # Serviços de ingestão e pipeline
└── samples/        # Payloads de exemplo

📁 modelos/         # Artefatos .pkl (modelos sklearn treinados)
📁 inputs/          # Dados de entrada (faturas, extratos)
📁 outputs/         # Resultados processados
📁 feedbacks/       # Correções manuais para retreinamento

📄 treinar_modelo.py  # Script de treinamento com validação cruzada
```

### Comunicação entre Componentes
- **Pipeline** orquestra: RulesEngine → SimilarityClassifier → ModelAdapter → AIFallbackEngine
- **Thresholds** configuráveis: `SIMILARITY_THRESHOLD=0.70`, `MODEL_THRESHOLD=0.70`
- **Feature flags** controlam quais engines estão ativos
- **FastAPI** expõe endpoints que delegam para o pipeline

## 4. Classificações Possíveis (Natureza do Gasto)

### Lista Canônica de Categorias
*Gerada automaticamente das fontes do projeto: constants.py, modelos sklearn e CSVs históricos*

#### ✅ Disponível no Modelo
- Carro (Manutenção/ IPVA/ Seguro)
- Casamento
- Combustível/ Passagens/ Uber / Sem Parar
- Conta de gás
- Conta de luz
- Cuidados Pessoais (Nutricionista / Medico / Suplemento)
- Farmácia
- Financiamento/Condominio
- Futevolei
- Gastos com Cachorro
- Gastos com casa (outros)
- Gastos com Diarista
- Gastos com Educação (Inglês, MBA, Pós)
- Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)
- Gastos com presentes
- Gastos pessoais
- Internet & TV a cabo
- Inteligência Artificial
- Investimento
- Moradia (Financiamento/ Aluguel/ Condominio)
- Obra casa
- Planos de celular
- Restaurantes/ Bares/ Lanchonetes
- Salário
- Supermercado
- Viagens / Férias

#### 📊 Somente no Histórico
- duvida *(categoria especial para baixa confiança)*

## 5. Regras de Classificação

### 4.1 Regras Determinísticas (Opcional)
**Status**: Desabilitado por padrão (`ENABLE_DETERMINISTIC_RULES=false`)

#### **tipo**: Detecção de Débito
- **Regra**: Se `card` começar com "CC -" → tipo = "débito" (confiança: 0.95)
- **Aplicação**: Primeira regra executada, alta prioridade

#### **comp**: Compartilhamento por Cartão
- **Regra**: Se `card` contém "CASA" → comp = "planilha comp" (confiança: 0.90)
- **Aplicação**: Detecta gastos compartilhados da casa

#### **parcelas**: Extração de Parcelamento
- **Regra**: Detectar padrão n/m (ex: "3/12") em descrições
- **Aplicação**: Preenche `no_da_parcela` e `parcelas` automaticamente
- **Exemplo**: "Compra 3/12" → no_da_parcela=3, parcelas=12

#### **Normalização Textual** (Sempre Ativa)
- **Lowercase**: Todas as descrições convertidas para minúsculas
- **Limpeza**: Remoção de caracteres especiais e espaços extras
- **Acentos**: Mantidos para melhor matching com histórico
- **Remoção de palavras genéricas**: Remove palavras como "pagamento", "compra", "anuidade", "debito", "credito", "pix" para melhor precisão
- **Remoção de datas**: Remove datas no formato DD/MM/YYYY ou DD/MM
- **Remoção de parcelas**: Remove padrões de parcelas como "(02/03)", "(1/12)", etc.
- **Remoção de prefixos**: Remove prefixos comuns como "Evo*", "Bkg*", "Htm*", "Ifd*", etc.
- **Limpeza de parênteses**: Remove parênteses vazios e caracteres residuais

### 4.2 Similaridade TF-IDF (Opcional)
**Status**: Desabilitado por padrão (`ENABLE_TFIDF_SIMILARITY=false`)
- **Fonte**: `modelo_despesas_completo.csv` (base de treinamento)
- **Métrica**: Cosseno entre vetores TF-IDF
- **Threshold padrão**: 0.70 (`SIMILARITY_THRESHOLD`)
- **Comportamento**: Se score ≥ 0.70, aceita classificação
- **Fallback**: Se < 0.70, passa para modelo ML

### 4.3 Classificador sklearn
- **Método**: `predict_proba` para confiança
- **Threshold padrão**: 0.70 (`MODEL_THRESHOLD`)
- **Comportamento**: Se confiança ≥ 0.70, aceita classificação
- **Fallback**: Se < 0.70, marca como "duvida"

### 4.4 Resultado com Baixa Confiança
- **Rotulagem**: "duvida" (confiança: 0.3)
- **Tratamento**: Requer feedback manual serviço de melhoria
- **Justificativa**: Evita classificações incorretas com baixa confiança

### 4.5 Fallback IA (Habilitado)
**Status**: Habilitado por padrão (`ENABLE_FALLBACK_AI=true`)
- **Uso**: Quando o classificador interno retorna "duvida"
- **APIs Suportadas**: OpenAI (GPT-4o-mini) e Anthropic (Claude-3-haiku)
- **Configuração**: Requer pelo menos uma chave de API (`OPENAI_API_KEY` ou `ANTHROPIC_API_KEY`)
- **Comportamento**: 
  - Se API keys disponíveis: usa IA para classificar casos de dúvida
  - Se API keys ausentes: retorna "duvida" com `needs_keys=true`
- **Threshold**: Confiança mínima de 0.5 para aceitar resultado da IA
- **Integração SerpAPI**: Busca automaticamente contexto sobre estabelecimentos via SerpAPI quando configurado
- **Prompt enriquecido**: Inclui informações de busca web no contexto para melhor classificação
- **Extração de estabelecimento**: Remove prefixos genéricos e datas para buscar informações mais relevantes

## 6. Contrato de Entrada/Saída

### Entrada (POST /v1/classify)
```json
[
  {
    "id": "optional_id",
    "description": "Netflix Com",
    "amount": 44.90,
    "date": "2024-10-18T10:00:00",
    "card_holder": "João",
    "card_number": "1234",
    "installments": 3,
    "installment_number": 1
  }
]
```

### Entrada (POST /parse_itau)
A requisição deve enviar a fatura Itaú em PDF via `multipart/form-data` no campo `file`.

```bash
curl -X POST "http://localhost:8081/parse_itau" \
  -H "accept: application/json" \
  -F "file=@./fatura_cartao.pdf"
```

### Saída (POST /parse_itau)
```json
{
  "items": [
    {
      "date": "2025-06-12",
      "description": "SEPHORA CIDJARDIN 04/05",
      "amount": 83.0,
      "last4": "9826",
      "flux": "Saida"
    }
    // ...demais transações extraídas
  ],
  "stats": {
    "total_lines": 245,
    "matched": 128,
    "rejected": 15,
    "sum_abs_values": 12155.52,
    "sum_saida": 12000.33,
    "sum_entrada": 155.19,
    "by_card": {
      "9826": {
        "control_total": 6821.45,
        "calculated_total": 6821.45,
        "delta": 0.0
      }
    }
  },
  "rejects": [
    {
      "line": "SAUDE.SAO PAULO",
      "reason": "Linha não reconhecida (sem data, valor ou subtotal)"
    }
    // ...linhas descartadas para auditoria
  ]
}
```

#### Scripts de apoio
- `scripts/test-parse-itau.ps1` – Envia a fatura para `POST /parse_itau` e imprime/gera JSON de saída.
- `scripts/run-parse-itau.ps1` – Mata processos Python antigos, sobe o servidor (`run_server.py`), aguarda `/healthz`, executa o teste acima e salva `parse_output.json`.
- `parse_pdf_direct.py` – Executa o parser localmente (sem HTTP) usando `card_pdf_parser` e grava `parse_output.json`.

### Saída
```json
{
  "predictions": [
    {
      "label": "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)",
      "confidence": 0.95,
      "method_used": "rules_engine",
      "elapsed_ms": 2.5,
      "transaction_id": "optional_id",
      "needs_keys": null,
      "raw_prediction": {...}
    }
  ],
  "elapsed_ms": 15.2,
  "total_transactions": 1
}
```

### Campos de Resposta
- **label**: Categoria predita
- **confidence**: Confiança da predição (0.0-1.0)
- **method_used**: Método usado ("rules_engine", "similarity_engine", "model_adapter", "ai_fallback_openai", "ai_fallback_anthropic", "fallback", "error")
- **elapsed_ms**: Tempo de processamento em milissegundos
- **transaction_id**: ID da transação original (opcional)
- **needs_keys**: Indica se faltam API keys para fallback IA (opcional, apenas quando true)
- **raw_prediction**: Dados brutos da predição para debugging

### Campos Derivados
- **tipo**: "crédito" ou "débito" (inferido por regras)
- **parcelas**: Total de parcelas (extraído de descrição)
- **no_da_parcela**: Parcela atual (extraído de descrição)
- **comp**: Compartilhamento (inferido por regras)

## 7. API de Feedback

### O que é o endpoint /v1/feedback

O endpoint `/v1/feedback` permite registrar **correções do usuário** em transações classificadas para posterior incorporação ao modelo de treinamento. Essas correções são essenciais para melhorar continuamente a precisão do sistema de classificação.

**Finalidade**: Coletar feedback manual para retreino dos modelos e melhoria da acurácia.

### Campos Aceitos

#### Campos Obrigatórios
- **`transactionId`** (string): ID único da transação
- **`description`** (string): Descrição da transação - "Aonde Gastou"
- **`amount`** (number): Valor unitário da transação (deve ser > 0)
- **`date`** (string): Data da transação no formato ISO

#### Campos Principais (Opcionais)
- **`source`** (string): Tipo/fonte da transação (ex: "crédito", "débito")
- **`card`** (string): Informações do cartão
- **`modelVersion`** (string): Versão do modelo usado na classificação
- **`createdAt`** (string): Timestamp de criação do feedback

#### Campos Editáveis (Opcionais)
- **`category`** (string): Natureza do Gasto - categoria corrigida
- **`flux`** (string): Entrada/Saída - fluxo da transação
- **`comp`** (string): Comp - informação adicional
- **`parcelas`** (number): Número total de parcelas (default: 1)
- **`numero_parcela`** (number): Número da parcela atual

### Mapeamento para CSV

Os campos são mapeados para as seguintes colunas do CSV (na ordem especificada):

| Campo de Entrada | Coluna CSV | Descrição |
|------------------|------------|-----------|
| `description` | **Aonde Gastou** | Descrição da transação |
| `category` | **Natureza do Gasto** | Categoria corrigida (vazio se ausente) |
| `amount * parcelas` | **Valor Total** | Valor total calculado |
| `parcelas` | **Parcelas** | Total de parcelas (default: 1) |
| `numero_parcela` | **No da Parcela** | Parcela atual (vazio se ausente) |
| `amount` | **Valor Unitário** | Valor unitário da transação |
| `source` | **tipo** | Tipo/fonte da transação |
| `comp` | **Comp** | Informação adicional |
| `date` | **Data** | Data da transação |
| `card` | **cartao** | Informações do cartão |
| `transactionId` | **transactionId** | ID único da transação |
| `modelVersion` | **modelVersion** | Versão do modelo |
| `createdAt` | **createdAt** | Timestamp (preenchido automaticamente se ausente) |
| `flux` | **flux** | Fluxo da transação |

### Localização dos Arquivos

**Diretório**: `feedbacks/`
**Padrão do nome**: `feedback_YYYY-MM-DD.csv`
**Exemplo**: `feedbacks/feedback_2024-01-15.csv`

Os arquivos são criados automaticamente com cabeçalho na primeira execução do dia.

### Exemplos de Uso

#### curl (Unix/Linux/macOS)

**Item único:**
```bash
curl -X POST "http://localhost:8080/v1/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": {
      "transactionId": "tx_001",
      "description": "Netflix Com",
      "amount": 44.90,
      "date": "2024-01-15T00:00:00Z",
      "source": "crédito",
      "card": "Final 8073 - JOAO G B CALICE",
      "category": "Entretenimento",
      "parcelas": 1,
      "modelVersion": "v1.2.0"
    }
  }'
```

**Lote de itens:**
```bash
curl -X POST "http://localhost:8080/v1/feedback" \
  -H "Content-Type: application/json" \
  -d '{
    "feedback": [
      {
        "transactionId": "tx_001",
        "description": "Netflix Com",
        "amount": 44.90,
        "date": "2024-01-15T00:00:00Z",
        "category": "Entretenimento"
      },
      {
        "transactionId": "tx_002",
        "description": "Pao De Acucar-0061",
        "amount": 401.68,
        "date": "2024-01-15T00:00:00Z",
        "category": "Supermercado"
      }
    ]
  }'
```

#### PowerShell (Windows)

**Item único:**
```powershell
$body = @{
  feedback = @{
    transactionId = "tx_001"
    description = "Netflix Com"
    amount = 44.90
    date = "2024-01-15T00:00:00Z"
    source = "crédito"
    card = "Final 8073 - JOAO G B CALICE"
    category = "Entretenimento"
    parcelas = 1
    modelVersion = "v1.2.0"
  }
} | ConvertTo-Json -Depth 3

Invoke-RestMethod -Uri "http://localhost:8080/v1/feedback" -Method POST -Body $body -ContentType "application/json"
```

**Lote de itens:**
```powershell
$body = @{
  feedback = @(
    @{
      transactionId = "tx_001"
      description = "Netflix Com"
      amount = 44.90
      date = "2024-01-15T00:00:00Z"
      category = "Entretenimento"
    },
    @{
      transactionId = "tx_002"
      description = "Pao De Acucar-0061"
      amount = 401.68
      date = "2024-01-15T00:00:00Z"
      category = "Supermercado"
    }
  )
} | ConvertTo-Json -Depth 4

Invoke-RestMethod -Uri "http://localhost:8080/v1/feedback" -Method POST -Body $body -ContentType "application/json"
```

### Resposta Esperada

**Status**: `201 Created`

```json
{
  "saved_rows": 2,
  "file_path": "feedbacks/feedback_2024-01-15.csv",
  "columns": [
    "Aonde Gastou",
    "Natureza do Gasto",
    "Valor Total",
    "Parcelas",
    "No da Parcela",
    "Valor Unitário",
    "tipo",
    "Comp",
    "Data",
    "cartao",
    "transactionId",
    "modelVersion",
    "createdAt",
    "flux"
  ]
}
```

### Boas Práticas

- **Envio em lote**: Prefira enviar múltiplos feedbacks por dia em uma única requisição
- **Tamanho do payload**: Evite payloads gigantes (sugerimos < 5.000 itens por POST)
- **Timezone**: O arquivo usa a data do servidor (não precisa especificar timezone)
- **Deduplicação**: TransactionIds repetidos são registrados novamente (comportamento intencional)
- **Concorrência**: O sistema é thread-safe para múltiplas requisições simultâneas

### Troubleshooting

#### Erro 422 - Campos Obrigatórios Ausentes
```json
{
  "detail": [
    {
      "loc": ["body", "feedback", 0, "transactionId"],
      "msg": "field required",
      "type": "missing"
    }
  ]
}
```
**Solução**: Verificar se todos os campos obrigatórios estão presentes: `transactionId`, `description`, `amount`, `date`

#### Erro 422 - Amount Inválido
```json
{
  "detail": [
    {
      "loc": ["body", "feedback", 0, "amount"],
      "msg": "Input should be greater than 0",
      "type": "greater_than"
    }
  ]
}
```
**Solução**: O campo `amount` deve ser maior que 0

#### Permissões de Escrita na Pasta feedbacks/
```
ERROR: Permission denied: 'feedbacks/feedback_2024-01-15.csv'
```
**Solução**: Verificar permissões de escrita no diretório `feedbacks/` ou criar o diretório se não existir

#### Onde Ver Logs
- **Desenvolvimento local**: Logs aparecem no terminal onde o servidor está rodando
- **Docker**: `docker logs <container_id>`
- **Cloud Run**: Logs disponíveis no Google Cloud Console
- **Swagger UI**: Documentação interativa disponível em `/docs`

### Documentação Interativa

Para testar o endpoint interativamente, acesse:
- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

### Pipeline de Ingestão e Retreino (Implementado)

O sistema agora inclui um **pipeline completo de ingestão e retreino** implementado e testado, com endpoints dedicados para gerenciar todo o fluxo de dados.

#### **🔄 Endpoints do Pipeline**

| Endpoint | Método | Descrição |
|----------|--------|-----------|
| `/v1/feedback/pipeline/status` | GET | Status completo do pipeline |
| `/v1/feedback/pipeline/collect` | POST | Coleta feedbacks não processados |
| `/v1/feedback/pipeline/merge` | POST | Mescla feedbacks com dataset principal |
| `/v1/feedback/pipeline/retrain` | POST | Retreina modelos com dados atualizados |
| `/v1/feedback/pipeline/run-complete` | POST | Executa pipeline completo |
| `/v1/feedback/pipeline/backup/list` | GET | Lista backups disponíveis |
| `/v1/feedback/pipeline/clear-processed` | POST | Limpa arquivos processados |

#### **📊 Status do Pipeline**

```bash
# Verificar status atual
curl -X GET "http://localhost:8080/v1/feedback/pipeline/status"
```

**Resposta:**
```json
{
  "pipeline_status": "operational",
  "feedback_files": {
    "total_found": 5,
    "processed_count": 3,
    "pending_count": 2,
    "files": ["feedback_2024-01-15.csv", "feedback_2024-01-16.csv"],
    "processed_files": ["feedback_2024-01-13.csv", "feedback_2024-01-14.csv"]
  },
  "models": {
    "directory": "modelos",
    "count": 3,
    "files": {
      "modelo_natureza_do_gasto.pkl": 1703123456.789,
      "modelo_comp.pkl": 1703123456.789,
      "modelo_parcelas.pkl": 1703123456.789
    },
    "last_updated": 1703123456.789
  },
  "backups": {
    "count": 2,
    "files": ["modelo_despesas_completo.csv.backup_20240115_120000"]
  },
  "dataset_base": {
    "file": "modelo_despesas_completo.csv",
    "exists": true,
    "info": {
      "exists": true,
      "columns": 14,
      "sample_rows": 5,
      "file_size": 1024000
    }
  }
}
```

#### **🚀 Pipeline Completo**

```bash
# Executar pipeline completo (recomendado para produção)
curl -X POST "http://localhost:8080/v1/feedback/pipeline/run-complete"
```

**Fluxo automático:**
1. **Coleta** feedbacks não processados
2. **Mescla** com dataset principal
3. **Cria backup** automático
4. **Retreina** modelos
5. **Valida** qualidade dos resultados

#### **🔧 Operações Individuais**

```bash
# 1. Coletar feedbacks
curl -X POST "http://localhost:8080/v1/feedback/pipeline/collect"

# 2. Mesclar com dataset
curl -X POST "http://localhost:8080/v1/feedback/pipeline/merge"

# 3. Retreinar modelos
curl -X POST "http://localhost:8080/v1/feedback/pipeline/retrain"
```

#### **💾 Gerenciamento de Backups**

```bash
# Listar backups disponíveis
curl -X GET "http://localhost:8080/v1/feedback/pipeline/backup/list"
```

**Resposta:**
```json
{
  "success": true,
  "backups": [
    {
      "file": "modelo_despesas_completo.csv.backup_20240115_120000",
      "created": 1703123456.789,
      "size": 1024000,
      "exists": true
    }
  ],
  "count": 1
}
```

#### **🔄 Controle de Processamento**

```bash
# Limpar arquivos processados (para reprocessar)
curl -X POST "http://localhost:8080/v1/feedback/pipeline/clear-processed"
```

#### **📈 Métricas e Monitoramento**

O pipeline fornece métricas detalhadas em cada operação:

- **Feedbacks coletados**: Quantidade de arquivos processados
- **Registros integrados**: Total de registros adicionados
- **Duplicatas removidas**: Estatísticas de limpeza
- **Modelos atualizados**: Lista de modelos retreinados
- **Qualidade**: Resultados das validações
- **Tempo de execução**: Duração de cada etapa

#### **⚠️ Considerações Importantes**

1. **Backup Automático**: Dataset original é sempre preservado
2. **Controle de Duplicação**: TransactionIds duplicados são detectados
3. **Validação de Qualidade**: Múltiplas validações em cada etapa
4. **Timeout**: Retreino tem limite de 10 minutos
5. **Idempotência**: Operações podem ser executadas múltiplas vezes
6. **Rollback**: Sistema pode ser restaurado em caso de erro

#### **🎯 Casos de Uso**

- **Integração Diária**: Processar feedbacks acumulados diariamente
- **Retreino Semanal**: Atualizar modelos semanalmente
- **Deploy**: Preparar sistema para produção
- **Manutenção**: Operações de manutenção programada
- **Desenvolvimento**: Testes e desenvolvimento com dados reais

#### **🔍 Troubleshooting do Pipeline**

| Problema | Solução |
|----------|---------|
| **Nenhum feedback encontrado** | Verificar se arquivos existem em `feedbacks/` |
| **Erro na mesclagem** | Verificar se dataset base existe e é válido |
| **Timeout no retreino** | Verificar tamanho dos dados e recursos do sistema |
| **Modelos não atualizados** | Verificar logs do `treinar_modelo.py` |
| **Backup não encontrado** | Verificar permissões de escrita no diretório |

## 8. Configuração para Containers

### Variáveis de Ambiente Suportadas

A aplicação está preparada para rodar 100% em container com as seguintes variáveis:

| Variável | Default | Descrição |
|----------|---------|-----------|
| `PORT` | `8080` | Porta do servidor FastAPI |
| `MODEL_DIR` | `./modelos` | Diretório dos modelos .pkl |
| `SIMILARITY_THRESHOLD` | `0.70` | Threshold para Similarity Engine |
| `MODEL_THRESHOLD` | `0.70` | Threshold para Model Adapter |
| `ENABLE_FALLBACK_AI` | `true` | Habilitar fallback com IA (padrão: habilitado) |
| `ENABLE_DETERMINISTIC_RULES` | `false` | Habilitar regras determinísticas |
| `ENABLE_TFIDF_SIMILARITY` | `false` | Habilitar similaridade TF-IDF |
| `USE_PIPELINE_MODEL` | `true` | Usar modelo pipeline completo |
| `TRAINING_DATA_FILE` | `modelo_despesas_completo.csv` | Arquivo CSV para treinamento |

### Características para Container

- ✅ **Health Check**: `GET /healthz` retorna `{"status":"ok"}`
- ✅ **Shutdown Gracioso**: Responde a SIGTERM sem pendências
- ✅ **Degradação Graciosa**: Funciona sem CSVs históricos
- ✅ **Modelos Flexíveis**: Carrega .pkl via MODEL_DIR
- ✅ **Porta Configurável**: Usa variável PORT (padrão 8080)

### Exemplo de Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Copiar modelos se existirem
COPY modelos/ ./modelos/

# Expor porta configurável
EXPOSE 8080

# Usar variável PORT
ENV PORT=8080
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Arquivos de Exemplo Incluídos

- **`Dockerfile.example`**: Dockerfile completo com health check
- **`docker-compose.example.yml`**: Configuração para desenvolvimento local
- **`deploy-cloud-run.example.sh`**: Script de deploy para Google Cloud Run
- **`validate-container.sh`**: Comandos de validação para testes

## 9. Rodar com Docker (Local)

### Pré-requisitos
- Docker instalado
- Arquivo `.env` configurado (opcional)

### Build e Execução

#### 1. Build da Imagem
```bash
# Build da imagem Docker
docker build -t ml-service:local .
```

#### 2. Executar Container
```bash
# Executar com arquivo .env (recomendado)
docker run --rm -p 8081:8080 --env-file .env ml-service:local

# Ou executar com variáveis inline
docker run --rm -p 8080:8080 \
  -e PORT=8080 \
  -e ENABLE_FALLBACK_AI=true \
  -e SIMILARITY_THRESHOLD=0.70 \
  -e MODEL_THRESHOLD=0.70 \
  -e MODEL_DIR=/models \
  ml-service:local
```

#### 3. Testar Aplicação
```bash
# Health check
curl http://localhost:8081/healthz

# Classificar transação única
curl -X POST "http://localhost:8081/v1/classify" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "description": "Netflix Com",
      "amount": 44.90,
      "date": "2024-01-01"
    }
  ]'
```

### Características do Container

- ✅ **Base**: `python:3.11-slim` (imagem otimizada)
- ✅ **Usuário não-root**: Executa como `appuser` para segurança
- ✅ **Health Check**: Verificação automática de saúde
- ✅ **Modelos**: Copiados para `/models` (paridade com Cloud Run)
- ✅ **Variáveis**: Configurações padrão otimizadas para container
- ✅ **Worker único**: Configurado para 1 worker (ideal para containers)

## 10. Comandos Make e Scripts Auxiliares

### Comandos Make Disponíveis

| Comando | Descrição | Equivalente Windows |
|---------|-----------|-------------------|
| `make run-api` | Inicia API FastAPI | `uvicorn app.main:app --reload --port 8080` |
| `make test` | Executa testes pytest | `pytest -q` |
| `make docker-build` | Build da imagem Docker | `docker build -t ml-service:local .` |
| `make docker-run` | Executa container Docker | `docker run --rm -p 8081:8080 --env-file .env ml-service:local` |
| `make docker-stop` | Para container Docker | `docker stop ml-service:local` |

### Scripts de Teste CLI

#### Unix/Linux/macOS
```bash
# Testar transação única
./scripts/test-single.sh

# Testar lote de transações
./scripts/test-batch.sh
```

#### Windows (CMD)
```cmd
REM Testar transação única
scripts\test-single.bat

REM Testar lote de transações
scripts\test-batch.bat
```

#### Windows (PowerShell)
```powershell
# Testar transação única
.\scripts\test-single.ps1

# Testar lote de transações
.\scripts\test-batch.ps1
```

### Exemplos de Uso

#### 1. Desenvolvimento Local
```bash
# Iniciar API
make run-api

# Em outro terminal, testar
./scripts/test-single.sh
```

#### 2. Testes com Docker
```bash
# Build e execução
make docker-build
make docker-run

# Em outro terminal, testar
./scripts/test-batch.sh
```

#### 3. Windows PowerShell
```powershell
# Iniciar API
uvicorn app.main:app --reload --port 8080

# Em outro terminal, testar
.\scripts\test-single.ps1
```

## 11. Smoke Test do Container (Local)

### O que é o Smoke Test

O smoke test é um teste automatizado que valida todo o ciclo de vida do container Docker:
1. **Build** da imagem
2. **Execução** em background
3. **Health check** com polling
4. **Classificação** de transação
5. **Validação** de campos obrigatórios
6. **Limpeza** automática do container

### Como Executar

#### Unix/Linux/macOS
```bash
# Tornar script executável
chmod +x scripts/docker-smoke.sh

# Executar smoke test
./scripts/docker-smoke.sh
```

#### Windows (CMD)
```cmd
REM Executar smoke test
scripts\docker-smoke.bat
```

#### Windows (PowerShell)
```powershell
# Executar smoke test
.\scripts\docker-smoke.ps1
```

### Saída Esperada (Sucesso)

```
🚀 Iniciando smoke test do container Docker
================================================

📦 Fazendo build da imagem...
✅ Build concluído

🚀 Executando container em background...
✅ Container iniciado

🏥 Aguardando health check...
URL: http://localhost:8081/healthz
Timeout: 30s
✅ Health check OK (5s)

🎯 Testando classificação...
📄 Arquivo: app/samples/tx_single.json
📤 Enviando requisição...
📊 Código HTTP: 200
✅ HTTP 200 OK

🔍 Verificando campos obrigatórios...
📊 Resposta da API:
{
  "predictions": [
    {
      "label": "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)",
      "confidence": 0.95,
      "method_used": "model_adapter",
      "elapsed_ms": 5.2,
      "transaction_id": null,
      "needs_keys": null
    }
  ],
  "elapsed_ms": 15.2,
  "total_transactions": 1
}

🔍 Campos verificados:
  Label: Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)
  Confidence: 0.95
  Method: model_adapter
✅ Label encontrado: Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)
✅ Confidence válido: 0.95

🎉 Smoke test concluído com sucesso!
================================================
✅ Build da imagem: OK
✅ Container executando: OK
✅ Health check: OK
✅ Classificação: OK
✅ Campos obrigatórios: OK

💡 Container será parado automaticamente
```

### Critérios de Sucesso

- ✅ **Status de saída**: 0 (sucesso) ou ≠0 (erro)
- ✅ **Build**: Imagem construída sem erros
- ✅ **Container**: Executando em background na porta 8081
- ✅ **Health check**: Responde `/healthz` em até 30s
- ✅ **Classificação**: POST `/v1/classify` retorna HTTP 200
- ✅ **Campos obrigatórios**: `predictions[0].label` presente
- ✅ **Limpeza**: Container parado automaticamente

### Troubleshooting

#### Timeout no Health Check
```
❌ Timeout no health check após 30s
📋 Logs do container:
```
**Solução**: Verificar se Docker está rodando e porta 8081 está livre

#### Erro no Build
```
❌ Erro no build da imagem
```
**Solução**: Verificar se Dockerfile existe e dependências estão corretas

#### Campos Não Encontrados
```
❌ Label não encontrado
```
**Solução**: Verificar se modelos estão presentes no container

## 12. Deploy no GCP Cloud Run

### Convenção de Imagem e Tags

#### Registry GCP
```
southamerica-east1-docker.pkg.dev/<SEU_PROJECT_ID>/ml-repo/ml-service:<tag>
```

#### Tags Recomendadas
- **Versões**: `v1`, `v2`, `v3`, etc.
- **Testes**: `latest` (apenas para desenvolvimento)
- **Ambientes**: `dev`, `staging`, `prod` (opcional)

#### Exemplos de Tags
```bash
# Versão específica
southamerica-east1-docker.pkg.dev/my-project/ml-repo/ml-service:v1

# Última versão
southamerica-east1-docker.pkg.dev/my-project/ml-repo/ml-service:latest

# Ambiente específico
southamerica-east1-docker.pkg.dev/my-project/ml-repo/ml-service:prod-v1
```

### Caminhos de Build

#### 1. Build Local (Debug)
```bash
# Build local para testes
docker build -t ml-service:local .

# Testar localmente
docker run --rm -p 8080:8080 ml-service:local

# Smoke test
./scripts/docker-smoke.sh
```

#### 2. Build Remoto (Produção)
```bash
# Configurar projeto
gcloud config set project <SEU_PROJECT_ID>

# Configurar Docker para GCP
gcloud auth configure-docker southamerica-east1-docker.pkg.dev

# Build e push em uma operação
gcloud builds submit --tag southamerica-east1-docker.pkg.dev/<SEU_PROJECT_ID>/ml-repo/ml-service:v1

# Deploy no Cloud Run
gcloud run deploy ml-service \
  --image southamerica-east1-docker.pkg.dev/<SEU_PROJECT_ID>/ml-repo/ml-service:v1 \
  --region southamerica-east1 \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars "PORT=8080,MODEL_DIR=/models,SIMILARITY_THRESHOLD=0.70,MODEL_THRESHOLD=0.70,ENABLE_FALLBACK_AI=true"
```

### Checklist Cloud Run Ready

- ✅ **App escuta PORT**: Configurado para usar variável `PORT` (default 8080)
- ✅ **Porta padrão 8080**: Definida no Dockerfile e variáveis de ambiente
- ✅ **Sem volumes obrigatórios**: Todos os artefatos incluídos na imagem
- ✅ **Modelos incluídos**: Copiados para `/models` no container
- ✅ **Health check disponível**: Endpoint `/healthz` implementado
- ✅ **Variáveis de ambiente**: Definidas no deploy do Cloud Run
- ✅ **Usuário não-root**: Execução segura como `appuser`
- ✅ **Worker único**: Configurado para 1 worker (ideal para containers)
- ✅ **Shutdown gracioso**: Responde a SIGTERM sem pendências

### Script de Deploy Completo

```bash
#!/bin/bash
# Script de deploy para GCP Cloud Run

set -e

# Configurações
PROJECT_ID="<SEU_PROJECT_ID>"
SERVICE_NAME="ml-service"
REGION="southamerica-east1"
IMAGE_NAME="southamerica-east1-docker.pkg.dev/${PROJECT_ID}/ml-repo/ml-service"
TAG="v1"

echo "🚀 Deploy para GCP Cloud Run"
echo "Projeto: $PROJECT_ID"
echo "Serviço: $SERVICE_NAME"
echo "Região: $REGION"
echo "Imagem: $IMAGE_NAME:$TAG"

# 1. Configurar projeto
echo "📋 Configurando projeto..."
gcloud config set project $PROJECT_ID

# 2. Configurar Docker
echo "🐳 Configurando Docker para GCP..."
gcloud auth configure-docker southamerica-east1-docker.pkg.dev

# 3. Build e push
echo "📦 Fazendo build e push..."
gcloud builds submit --tag $IMAGE_NAME:$TAG

# 4. Deploy no Cloud Run
echo "🌐 Fazendo deploy no Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME:$TAG \
  --region $REGION \
  --platform managed \
  --allow-unauthenticated \
  --port 8080 \
  --memory 1Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars "PORT=8080,MODEL_DIR=/models,SIMILARITY_THRESHOLD=0.70,MODEL_THRESHOLD=0.70,ENABLE_FALLBACK_AI=true"

# 5. Obter URL do serviço
echo "🔗 URL do serviço:"
gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)'

echo "✅ Deploy concluído!"
```

## 13. Docker Compose (Opcional)

### Quando Usar Docker Compose

O docker-compose é **opcional** e destinado apenas para **desenvolvimento local**. Para produção no GCP Cloud Run, use os comandos de deploy direto.

#### Vantagens do Docker Compose
- ✅ **Desenvolvimento rápido**: `docker compose up` sobe tudo
- ✅ **Hot-reload**: Mudanças no código refletem automaticamente
- ✅ **Configuração centralizada**: Variáveis em `.env`
- ✅ **Debugging facilitado**: Logs centralizados

#### Limitações e Trade-offs
- ❌ **Não compatível com Cloud Run**: Cloud Run não usa volumes
- ❌ **Apenas para desenvolvimento**: Não deve ser usado em produção
- ❌ **Dependência local**: Requer arquivos locais para hot-reload

### Configuração

#### Arquivos de Configuração
- **`docker-compose.yml`**: Configuração base (compatível com Cloud Run)
- **`docker-compose.override.yml`**: Configuração para desenvolvimento (volumes e hot-reload)

#### Estrutura dos Arquivos
```yaml
# docker-compose.yml (base)
services:
  api:
    build: .
    ports:
      - "8081:8080"
    env_file:
      - .env
    # Sem volumes - compatível com Cloud Run

# docker-compose.override.yml (desenvolvimento)
services:
  api:
    volumes:
      - ./app:/app/app:ro  # Hot-reload
      - ./modelos:/models:ro  # Modelos locais
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
```

### Como Usar

#### Desenvolvimento Local
```bash
# Subir com hot-reload (usa override)
docker compose up

# Subir em background
docker compose up -d

# Ver logs
docker compose logs -f api

# Parar
docker compose down
```

#### Produção (sem override)
```bash
# Subir sem volumes (simula Cloud Run)
docker compose -f docker-compose.yml up

# Ou usar docker run diretamente
docker run --rm -p 8081:8080 --env-file .env ml-service:local
```

### Testes com Docker Compose

#### Health Check
```bash
# Aguardar inicialização e testar
sleep 10
curl http://localhost:8081/healthz
```

#### Classificação
```bash
# Testar classificação
curl -X POST "http://localhost:8081/v1/classify" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "description": "Netflix Com",
      "amount": 44.90,
      "date": "2024-01-01"
    }
  ]'
```

### ⚠️ Importante: Cloud Run vs Docker Compose

| Aspecto | Docker Compose (Dev) | Cloud Run (Prod) |
|---------|---------------------|------------------|
| **Volumes** | ✅ Usa volumes locais | ❌ Sem volumes |
| **Hot-reload** | ✅ Suportado | ❌ Não suportado |
| **Arquivos locais** | ✅ Monta do host | ❌ Incluídos na imagem |
| **Configuração** | ✅ docker-compose.yml | ✅ gcloud run deploy |
| **Escalabilidade** | ❌ Single instance | ✅ Auto-scaling |

### Troubleshooting

#### Erro de Volume
```
ERROR: for api  Cannot start service api: error while creating mount source path
```
**Solução**: Verificar se diretórios `app/` e `modelos/` existem

#### Porta em Uso
```
ERROR: bind: address already in use
```
**Solução**: Parar outros serviços na porta 8080 ou usar porta diferente

#### Hot-reload Não Funciona
```
WARNING: Watchfiles detected changes in 'app/main.py' but reload is not enabled
```
**Solução**: Verificar se `docker-compose.override.yml` está sendo usado

## 14. Como Rodar Localmente

### Pré-requisitos
- Python 3.8+
- Ambiente virtual (recomendado)

### Passo a Passo

#### 1. Configurar Ambiente
```bash
# Criar ambiente virtual
python -m venv venv

# Ativar ambiente
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

#### 2. Configurar Variáveis (.env)
```bash
# Copiar arquivo de exemplo (na raiz do projeto)
cp .env.example .env

# Editar conforme necessário
# As variáveis principais são:

# Thresholds de classificação
SIMILARITY_THRESHOLD=0.4
MODEL_THRESHOLD=0.70

# Configurações do container
MODEL_DIR=./modelos
PORT=8080

# Feature flags (padrão: AI Fallback habilitado)
ENABLE_FALLBACK_AI=true
ENABLE_DETERMINISTIC_RULES=false
ENABLE_TFIDF_SIMILARITY=false
USE_PIPELINE_MODEL=true

# Arquivo de dados para treinamento
TRAINING_DATA_FILE=modelo_despesas_completo.csv

# API Keys para Fallback IA (opcional)
# Configure para usar AI Fallback e SerpAPI
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
SERPAPI_API_KEY=your_serpapi_key_here  # Recomendado para melhor classificação
```

#### 3. Preparar Dados e Modelos
```bash
# Garantir presença do arquivo de treinamento
# Por padrão usa modelo_despesas_completo.csv
# Pode ser alterado via TRAINING_DATA_FILE no .env

# Treinar modelos (usa arquivo configurado em TRAINING_DATA_FILE)
# O script executa validação cruzada, calibração e seleção automática do melhor modelo
python treinar_modelo.py

# O script gera os seguintes arquivos em modelos/:
# - modelo_natureza_do_gasto.pkl (pipeline completo)
# - vectorizer.pkl (componente TF-IDF)
# - classifier.pkl (componente classificador)
# - modelo_comp.pkl (compartilhamento)
# - modelo_parcelas.pkl (total de parcelas)
# - modelo_no_da_parcela.pkl (número da parcela)
# - modelo_tipo.pkl (tipo crédito/débito)

# Verificar se os modelos foram gerados corretamente
ls -la modelos/*.pkl
```

#### 4. Iniciar API
```bash
# Opção 1: Usando o script de conveniência (RECOMENDADO)
python run_server.py

# Opção 2: Usando uvicorn diretamente com PORT configurável
uvicorn app.main:app --reload --port ${PORT:-8080}

# Opção 3: Usando Python com path configurado
python -c "import sys; sys.path.insert(0, '.'); import uvicorn; from app.main import app; uvicorn.run(app, host='127.0.0.1', port=int(os.getenv('PORT', '8080')))"
```

### Endpoints Disponíveis

#### GET /healthz
```bash
curl http://127.0.0.1:8080/healthz
```
**Resposta**: `{"status":"ok"}`

#### POST /v1/classify
```bash
# Transação única
curl -X POST "http://127.0.0.1:8080/v1/classify" \
  -H "Content-Type: application/json" \
  -d @app/samples/tx_single.json

# Lote de transações
curl -X POST "http://127.0.0.1:8080/v1/classify" \
  -H "Content-Type: application/json" \
  -d @app/samples/tx_batch.json
```

### Payloads de Exemplo
- **`app/samples/tx_single.json`**: Transação única
- **`app/samples/tx_batch.json`**: 3 transações (regra, similaridade, modelo)

## 15. Como Testar

### Testes Automáticos (pytest)
```bash
# Suíte completa
python -m pytest spend_classification/tests -q

# Testes específicos
python -m pytest spend_classification/tests/test_rules.py -v
python -m pytest spend_classification/tests/test_similarity.py -v
python -m pytest spend_classification/tests/test_model_adapter.py -v
python -m pytest spend_classification/tests/test_pipeline.py -v
python -m pytest spend_classification/tests/test_e2e_pipeline.py -v
python -m pytest spend_classification/tests/test_api.py -v
```

### Testes da API (Script de Conveniência)
```bash
# Testar API completa (health + classificação)
python test_api.py

# Iniciar servidor
python run_server.py
```

### Testes Manuais (curl/PowerShell)

#### Windows PowerShell
```powershell
# Health check
Invoke-WebRequest -Uri "http://127.0.0.1:8080/healthz" -Method GET

# Classificação
$body = Get-Content "app\samples\tx_single.json" -Raw
Invoke-WebRequest -Uri "http://127.0.0.1:8080/v1/classify" -Method POST -Body $body -ContentType "application/json"
```

#### Linux/Mac
```bash
# Health check
curl http://127.0.0.1:8080/healthz

# Classificação
curl -X POST "http://127.0.0.1:8080/v1/classify" \
  -H "Content-Type: application/json" \
  -d @app/samples/tx_single.json
```

### Script de Teste Automatizado
```bash
# Executar script de teste
python test_samples.py
```

### Critérios de Aceite
- ✅ **predictions**: Lista preenchida
- ✅ **confidence**: Valor entre 0.0 e 1.0
- ✅ **elapsed_ms**: Tempo > 0
- ✅ **method_used**: "rules_engine", "similarity_engine" ou "model_adapter"
- ✅ **label**: Categoria válida ou "duvida"

## 16. Dados e Modelos

### Arquivos .pkl Necessários
```
modelos/
├── modelo_natureza_do_gasto.pkl    # Modelo principal (pipeline completo)
├── vectorizer.pkl                  # Vectorizer TF-IDF (componente separado)
├── classifier.pkl                  # Classificador (componente separado)
├── modelo_comp.pkl                 # Compartilhamento
├── modelo_parcelas.pkl             # Total de parcelas
├── modelo_no_da_parcela.pkl        # Número da parcela
└── modelo_tipo.pkl                 # Tipo (crédito/débito)
```

### Compatibilidade sklearn/joblib
- **Versão sklearn**: Compatível com modelos treinados
- **Joblib**: Usado para serialização/deserialização
- **Alinhamento**: Garantir compatibilidade de versões

### CSVs de Treinamento e Similaridade
- **Fonte**: `modelo_despesas_completo.csv` (configurável via `TRAINING_DATA_FILE`)
- **Comportamento**: Degrada graciosamente se ausente
- **Fallback**: SimilarityClassifier retorna None se arquivo não encontrado
- **Treinamento**: Script `treinar_modelo.py` usa arquivo configurado

## 16.1. Script de Treinamento (`treinar_modelo.py`)

### Visão Geral

O script `treinar_modelo.py` é responsável por treinar todos os modelos de classificação usados pelo sistema. Ele implementa um pipeline completo de Machine Learning com validação cruzada, calibração e seleção automática do melhor modelo.

### Como Usar

```bash
# Treinar modelos com arquivo padrão (modelo_despesas_completo.csv)
python treinar_modelo.py

# Ou especificar arquivo customizado via variável de ambiente
export TRAINING_DATA_FILE=meu_dataset.csv
python treinar_modelo.py
```

### Funcionalidades Principais

#### 1. **Limpeza e Normalização de Texto**
- **Remoção de datas**: Remove padrões de data (DD/MM/YYYY, DD-MM-YYYY)
- **Remoção de palavras genéricas**: Remove termos pouco discriminativos como "pagamento", "compra", "anuidade", "debito", "credito", "pix", "cartao"
- **Normalização de espaços**: Remove espaços extras e normaliza o texto
- **Preservação de termos importantes**: Mantém nomes de estabelecimentos e termos específicos que ajudam na classificação

#### 2. **Validação Cruzada Estratificada**
- **Método**: StratifiedKFold com 5 folds
- **Objetivo**: Garantir que cada fold tenha distribuição proporcional de classes
- **Métricas calculadas**: F1-macro, Brier score, AUC por classe
- **Seleção de modelo**: Escolhe o melhor modelo baseado no F1-macro médio na validação cruzada

#### 3. **Calibração de Probabilidades**
- **Modelos calibrados**: 
  - `LogisticRegression` com class_weight="balanced"
  - `CalibratedClassifierCV` com `LinearSVC` (método sigmoid, 3 folds)
- **Objetivo**: Garantir que as probabilidades preditas sejam calibradas e confiáveis
- **Métricas**: Brier score (quanto menor, melhor) e AUC por classe

#### 4. **Balanceamento de Classes**
- **Oversampling leve**: Aumenta classes minoritárias até 70% do tamanho da classe maior (`min_frac=0.7`)
- **Aplicação**: Apenas no conjunto de treino (não afeta validação/teste)
- **Objetivo**: Melhorar performance em classes desbalanceadas sem overfitting excessivo

#### 5. **Remoção de Classes Raras**
- **Critério**: Remove classes com menos de 2 exemplos
- **Justificativa**: Classes muito raras não podem ser aprendidas adequadamente
- **Aviso**: Sistema imprime warning listando classes removidas

#### 6. **Modelos Treinados**

O script treina 5 modelos auxiliares e 1 modelo principal:

**Modelos Auxiliares:**
- `modelo_comp.pkl`: Compartilhamento (usa informação do cartão)
- `modelo_parcelas.pkl`: Total de parcelas
- `modelo_no_da_parcela.pkl`: Número da parcela atual
- `modelo_tipo.pkl`: Tipo (crédito/débito)

**Modelo Principal:**
- `modelo_natureza_do_gasto.pkl`: Pipeline completo (TF-IDF + Classificador)
- `vectorizer.pkl`: Vectorizer TF-IDF (salvo separadamente)
- `classifier.pkl`: Classificador (salvo separadamente)

#### 7. **Testes de Diagnóstico**

Após o treinamento, o script executa testes de diagnóstico em casos específicos:

```python
test_cases = [
    ("Hb - Imares (04/04)", "Carro (Manutenção/ IPVA/ Seguro)"),
    ("Raiadrogasilsa", "Farmácia"),
    ("Ifd*Drogaria Penamar L", "Farmácia"),
    ("CREDITO DE SALARIO CNPJ 007526557000100", "Salário"),
]
```

Para cada caso, o script mostra:
- Texto original
- Texto limpo após normalização
- Categoria predita
- Confiança da predição
- Categoria esperada
- Se houve match

#### 8. **Métricas e Relatórios**

O script gera relatórios detalhados:

- **Classification Report**: Precision, recall, F1-score por classe
- **Matriz de Confusão**: Para classes destacadas (ex: "Restaurante", "Gastos Pessoais")
- **Brier Score**: Medida de calibração de probabilidades (quanto menor, melhor)
- **AUC por Classe**: Área sob a curva ROC para cada classe (One-vs-Rest)
- **F1-macro**: Média harmônica de precision e recall (macro-averaged)

### Exemplo de Saída

```
[INFO] Treinando modelo principal com validação estratificada e calibração...
[WARN] Removendo classes raras com apenas 1 exemplo: ['Categoria Rara']

Distribuição antes do oversampling: Counter({'Supermercado': 150, 'Restaurante': 80, ...})
Distribuição após oversampling leve: Counter({'Supermercado': 150, 'Restaurante': 105, ...})

[INFO] Validando modelo LogisticRegression (balanced) com StratifiedKFold...
[CV] LogisticRegression (balanced) - Fold 1/5: F1-macro=0.8523, Brier=0.1234
[CV] LogisticRegression (balanced) - Fold 2/5: F1-macro=0.8456, Brier=0.1256
...

[RESULTADOS - HOLD-OUT] LogisticRegression (balanced)
              precision    recall  f1-score   support
...
Brier score (quanto menor melhor): 0.1234
AUC por classe:
  - Supermercado: 0.9876
  - Restaurante: 0.9543
  ...

[OK] Melhor modelo: Calibrated LinearSVC (balanced) | F1-macro=0.8634 | Brier=0.1189

[TESTE] Verificando predições para casos específicos:
  Input: Hb - Imares (04/04)
  Cleaned: hb imares
  Predicted: Carro (Manutenção/ IPVA/ Seguro)
  Confidence: 0.892
  Expected: Carro (Manutenção/ IPVA/ Seguro)
  Match: True
```

### Configuração via Variáveis de Ambiente

```bash
# Arquivo de dados para treinamento
TRAINING_DATA_FILE=modelo_despesas_completo.csv
```

### Integração com Pipeline de Retreino

O script `treinar_modelo.py` é automaticamente chamado pelo pipeline de retreino quando você executa:

```bash
# Via API
curl -X POST "http://localhost:8080/v1/feedback/pipeline/retrain"

# Ou pipeline completo
curl -X POST "http://localhost:8080/v1/feedback/pipeline/run-complete"
```

O pipeline:
1. Coleta feedbacks não processados
2. Mescla com dataset principal
3. Cria backup automático
4. Executa `treinar_modelo.py` com o dataset atualizado
5. Valida qualidade dos novos modelos
6. Retorna métricas de sucesso

### Boas Práticas

- **Backup antes de retreinar**: O pipeline cria backup automático, mas é recomendado fazer backup manual também
- **Validação após treinamento**: Sempre valide os modelos com dados de teste antes de usar em produção
- **Monitoramento de métricas**: Compare F1-macro e Brier score entre versões para detectar regressões
- **Testes de diagnóstico**: Verifique se os casos de teste específicos continuam funcionando corretamente
- **Compatibilidade de versões**: Garanta que sklearn/joblib sejam compatíveis entre treinamento e produção

## 17. Desempenho e Observabilidade

### Boas Práticas
- **Vetorização em lote**: Processar múltiplas transações simultaneamente
- **Carregamento único**: Modelos carregados uma vez na inicialização
- **Medição de tempo**: `elapsed_ms` para cada transação e lote total

### Dicas de Tuning
- **Thresholds**: Ajustar `SIMILARITY_THRESHOLD` e `MODEL_THRESHOLD`
- **Corpus TF-IDF**: Expandir `modelo_despesas_completo.csv` para melhor similaridade
- **Limpeza de texto**: Refinar normalização para melhor matching

### Logs Sugeridos
- **Campos úteis**: transaction_id, method_used, confidence, elapsed_ms
- **Níveis**: INFO para operações normais, WARNING para baixa confiança
- **Rotação**: Configurar rotação de logs para evitar crescimento excessivo

## 18. Troubleshooting

### Erros Comuns

#### Arquivo de Modelo Ausente
```
ERROR: Arquivo vectorizer.pkl não encontrado em modelos/vectorizer.pkl
```
**Solução**: Executar `python treinar_modelo.py` para gerar modelos

#### CSV Ausente/Inválido
```
WARNING: Arquivo modelo_despesas_completo.csv não encontrado
```
**Solução**: SimilarityClassifier funciona sem arquivo (retorna None). Verifique `TRAINING_DATA_FILE` no .env

#### Thresholds Mal Configurados
```
WARNING: Confiança insuficiente (0.45) para transação
```
**Solução**: Ajustar `SIMILARITY_THRESHOLD` ou `MODEL_THRESHOLD` no .env

#### Resposta 422 (Payload Inválido)
```
422 Unprocessable Entity: Input should be a valid list
```
**Solução**: Verificar formato JSON - deve ser lista de transações

#### Fallback IA com `needs_keys=true`
```
"needs_keys": true
```
**Solução**: Configurar pelo menos uma API key (`OPENAI_API_KEY` ou `ANTHROPIC_API_KEY`) no .env

#### Feature Flags Não Funcionando
```
WARNING: Rules engine desabilitado por feature flag
```
**Solução**: Verificar valores das flags no .env (`ENABLE_DETERMINISTIC_RULES`, `ENABLE_TFIDF_SIMILARITY`, `ENABLE_FALLBACK_AI`)

### Isolamento de Problemas
```bash
# Testar cada engine individualmente
python -m pytest spend_classification/tests/test_rules.py -v
python -m pytest spend_classification/tests/test_similarity.py -v
python -m pytest spend_classification/tests/test_model_adapter.py -v
```

## 19. Guia de Contribuição Interna

### Padrão de Branches
- **`chore/`**: Limpeza, refatoração, configuração
- **`feat/`**: Novas funcionalidades
- **`fix/`**: Correções de bugs
- **`docs/`**: Documentação

### Adicionar Novas Regras
1. **Localização**: `spend_classification/engines/rules.py`
2. **Ordem**: Adicionar em `RulesEngine._setup_default_rules()`
3. **Testes**: Incluir em `spend_classification/tests/test_rules.py`
4. **Impacto**: Verificar ordem de decisão no pipeline

### Adicionar Novas Categorias
1. **Constants**: Adicionar em `spend_classification/core/constants.py`
2. **Schemas**: Atualizar `ExpenseCategory` enum
3. **Retreinamento**: Executar `python treinar_modelo.py`
4. **Testes**: Validar com dados de teste

### Atualizar Corpus/Modelo
1. **Backup**: Fazer backup dos modelos atuais e do dataset
   ```bash
   cp modelo_despesas_completo.csv modelo_despesas_completo.csv.backup
   cp -r modelos/ modelos_backup/
   ```

2. **Dados**: Adicionar novos dados em `modelo_despesas_completo.csv` (ou arquivo configurado via `TRAINING_DATA_FILE`)

3. **Retreinamento**: Executar script de treinamento
   ```bash
   # Via script direto
   python treinar_modelo.py
   
   # Ou via pipeline de retreino (recomendado - inclui backup automático)
   curl -X POST "http://localhost:8080/v1/feedback/pipeline/run-complete"
   ```

4. **Validação**: 
   - Verificar métricas de treinamento (F1-macro, Brier score)
   - Rodar testes automatizados: `python -m pytest spend_classification/tests -v`
   - Validar casos específicos através dos testes de diagnóstico do script
   - Comparar performance com versão anterior

5. **Deploy**: Substituir modelos em produção após validação bem-sucedida

## 19. Links Úteis

- **Documentação API**: http://localhost:8080/docs (Swagger UI)
- **ReDoc**: http://localhost:8080/redoc
- **Testes**: `python -m pytest spend_classification/tests -v`

## 20. Changelog

### v1.11.0 - Melhorias no Script de Treinamento
- ✅ **Validação Cruzada Estratificada**: Implementação completa com 5 folds para seleção robusta de modelos
- ✅ **Calibração de Probabilidades**: Suporte a CalibratedClassifierCV com LinearSVC para probabilidades calibradas
- ✅ **Métricas Avançadas**: Brier score e AUC por classe para avaliação de calibração e performance
- ✅ **Oversampling Leve**: Balanceamento inteligente de classes (min_frac=0.7) apenas no treino
- ✅ **Remoção Automática de Classes Raras**: Filtragem automática de classes com < 2 exemplos
- ✅ **Testes de Diagnóstico**: Validação automática de casos específicos após treinamento
- ✅ **Seleção Automática de Modelo**: Escolha do melhor modelo baseado em F1-macro médio na validação cruzada
- ✅ **Salvamento de Componentes**: Vectorizer e classifier salvos separadamente para flexibilidade
- ✅ **Limpeza de Texto Aprimorada**: Remoção de datas, palavras genéricas e normalização robusta
- ✅ **Documentação Completa**: Seção detalhada sobre script de treinamento no README
- ✅ **Relatórios Detalhados**: Classification report, matriz de confusão e métricas por classe
- ✅ **Integração com Pipeline**: Suporte completo ao pipeline de retreino via API

**Principais mudanças**:
- Script de treinamento agora usa validação cruzada estratificada para seleção de modelo
- Modelos calibrados garantem probabilidades mais confiáveis
- Testes de diagnóstico validam casos específicos automaticamente
- Documentação completa sobre processo de treinamento e métricas

### v1.10.0 - Pipeline Completo de Ingestão e Retreino
- ✅ **Pipeline Implementado**: Sistema completo de ingestão e retreino funcional
- ✅ **7 Novos Endpoints**: API completa para gerenciar todo o fluxo de dados
- ✅ **Controle de Duplicação**: Remoção automática de duplicatas por transactionId
- ✅ **Arquivo de Controle**: Prevenção de reprocessamento de arquivos
- ✅ **Validação Robusta**: Múltiplas validações de qualidade e integridade
- ✅ **Backup Automático**: Preservação automática de dados originais
- ✅ **Integração Completa**: Retreino automático com treinar_modelo.py
- ✅ **Monitoramento Detalhado**: Métricas e status em tempo real
- ✅ **Documentação Swagger**: 7 novos endpoints com documentação completa
- ✅ **Testes Abrangentes**: 24 cenários de teste com 100% de cobertura
- ✅ **README Atualizado**: Seção completa sobre pipeline de ingestão

### v1.9.0 - Ganchos para Integração de Feedbacks
- ✅ **Serviço de Ingestão**: `FeedbackIngestionService` com funções documentadas
- ✅ **Funções preparadas**: `collect_feedbacks()`, `merge_into_model_dataset()`, `write_merged_dataset()`
- ✅ **Validação de estrutura**: Verificação de 14 colunas padrão
- ✅ **Documentação completa**: Invariantes, riscos e fluxo de integração
- ✅ **Funções auxiliares**: Listagem de arquivos e validação implementadas
- ✅ **README atualizado**: Seção completa sobre pipeline de ingestão

### v1.8.0 - API de Feedback
- ✅ **Endpoint /v1/feedback**: API para registro de correções do usuário
- ✅ **Suporte a lote**: Aceita item único ou array de feedbacks
- ✅ **Persistência segura**: Append com locks para concorrência
- ✅ **Mapeamento automático**: Conversão para formato CSV com 14 colunas
- ✅ **Validações completas**: Campos obrigatórios e validação de tipos
- ✅ **Documentação Swagger**: Tags e exemplos completos
- ✅ **Testes automatizados**: Suíte completa com 9 cenários de teste
- ✅ **Documentação README**: Seção completa com exemplos curl/PowerShell

### v1.7.0 - Docker Compose para Desenvolvimento
- ✅ **Docker Compose**: Configuração opcional para desenvolvimento rápido
- ✅ **Hot-reload**: Suporte a reload automático em desenvolvimento
- ✅ **Separação de ambientes**: Base + override para dev vs prod
- ✅ **Paridade Cloud Run**: Configuração base compatível com Cloud Run
- ✅ **Documentação**: Seção completa com trade-offs e troubleshooting
- ✅ **Volumes opcionais**: Apenas para desenvolvimento local

### v1.6.0 - Preparação para GCP Cloud Run
- ✅ **Convenção de Tags**: Padronização para registry GCP
- ✅ **Caminhos de Build**: Local (debug) e remoto (produção)
- ✅ **Checklist Cloud Run**: Validação completa de requisitos
- ✅ **Script de Deploy**: Automatização completa do deploy
- ✅ **Documentação**: Seção completa de deploy no GCP
- ✅ **Zero Dependências Locais**: Imagem totalmente autocontida

### v1.5.0 - Smoke Test do Container
- ✅ **Smoke Test**: Teste automatizado completo do ciclo Docker
- ✅ **Scripts multiplataforma**: Unix (.sh), Windows (.bat/.ps1)
- ✅ **Validação completa**: Build, execução, health check, classificação
- ✅ **Limpeza automática**: Container sempre parado ao final
- ✅ **Polling inteligente**: Health check com timeout configurável
- ✅ **Validação de campos**: Verifica predictions[0].label e confidence
- ✅ **Documentação**: Seção completa com exemplos e troubleshooting

### v1.4.0 - Makefile e Scripts Auxiliares
- ✅ **Makefile**: Targets para desenvolvimento e Docker
- ✅ **Scripts CLI**: Testes automatizados para Unix e Windows
- ✅ **Comandos simplificados**: `make run-api`, `make test`, `make docker-build`
- ✅ **Scripts PowerShell**: Versões avançadas para Windows
- ✅ **Documentação**: Tabela de comandos e equivalentes Windows
- ✅ **Validação automática**: Scripts verificam campos obrigatórios

### v1.3.0 - Docker e Build Otimizado
- ✅ **Dockerfile**: Imagem otimizada com `python:3.11-slim`
- ✅ **Usuário não-root**: Execução segura como `appuser`
- ✅ **Build otimizado**: `.dockerignore` para reduzir tamanho da imagem
- ✅ **Health check**: Verificação automática de saúde do container
- ✅ **Modelos**: Copiados para `/models` (paridade com Cloud Run)
- ✅ **Worker único**: Configurado para 1 worker (ideal para containers)
- ✅ **Documentação**: Seção "Rodar com Docker" no README

### v1.2.0 - Preparação para Container
- ✅ **Container Ready**: Aplicação preparada para rodar 100% em container
- ✅ **Health Check**: Endpoint `/healthz` retorna `{"status":"ok"}`
- ✅ **Shutdown Gracioso**: Responde a SIGTERM sem pendências
- ✅ **Variável PORT**: Servidor usa porta da variável PORT (default 8080)
- ✅ **MODEL_DIR**: Carregamento de modelos via variável MODEL_DIR
- ✅ **Degradação Graciosa**: Funciona sem CSVs históricos
- ✅ **Feature Flags**: Padrões otimizados para container (todos desabilitados)
- ✅ **Documentação**: README atualizado com seção de containers

### v1.1.0 - Feature Flags e Fallback IA
- ✅ **Feature Flags**: Controle granular de engines via variáveis de ambiente
- ✅ **Fallback IA**: Integração com OpenAI e Anthropic para casos de dúvida
- ✅ **TRAINING_DATA_FILE**: Configuração flexível do arquivo de treinamento
- ✅ **Campo needs_keys**: Indicação quando faltam API keys para fallback IA
- ✅ **Configuração padrão**: Regras e TF-IDF desabilitados, Fallback IA habilitado
- ✅ **Validação de API keys**: Verificação automática na inicialização

### v1.0.0 - Migração para spend_classification
- ✅ **Nova arquitetura**: Pipeline modular com engines especializados
- ✅ **API FastAPI**: Endpoints REST padronizados
- ✅ **Testes automatizados**: 173 testes cobrindo todos os componentes
- ✅ **Thresholds configuráveis**: Via variáveis de ambiente
- ✅ **Documentação consolidada**: README único como fonte de verdade

### v0.x - Engines Legacy (Arquivados)
- 📁 **Arquivados**: Engines antigos movidos para `_archive/2024-12/legacy_engines/`
- 📁 **Testes legacy**: Movidos para `_archive/2024-12/legacy_engines_tests/`
- 🔗 **Referência**: Ver `_archive/` para histórico completo

---

### v1.9.0 - Melhorias de Normalização e Integração SerpAPI
- ✅ **Normalização aprimorada**: Remoção de palavras genéricas (pagamento, compra, anuidade, debito, credito, pix)
- ✅ **Limpeza de parênteses**: Remoção automática de parênteses vazios residuais
- ✅ **Extração de estabelecimento**: Método para extrair nome limpo do estabelecimento
- ✅ **Integração SerpAPI**: Busca automática de contexto sobre estabelecimentos via SerpAPI
- ✅ **Prompt aprimorado**: Estrutura melhorada com contexto de busca web para AI Fallback
- ✅ **Centralização .env**: Arquivo `.env.example` criado na raiz com todas as variáveis
- ✅ **Remoção de caracteres residuais**: Melhoria na normalização para remover elementos desnecessários
- ✅ **Documentação atualizada**: README com todas as mudanças documentadas

**Principais mudanças**:
- Similarity Engine agora remove palavras genéricas antes de calcular similaridade
- AI Fallback usa SerpAPI para enriquecer contexto quando disponível
- Normalização mais robusta remove parênteses vazios e caracteres especiais
- Arquivo `.env.example` disponível como template de configuração

## 📞 Suporte

Para dúvidas ou problemas:
1. **Verificar troubleshooting** (seção 17)
2. **Executar testes** para isolar problemas
3. **Consultar logs** da aplicação
4. **Validar configuração** (.env e modelos)

**Status**: ✅ Sistema estável e pronto para produção