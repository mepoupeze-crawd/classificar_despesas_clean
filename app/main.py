#!/usr/bin/env python3
"""
Microserviço FastAPI para Classificação de Despesas

Este microserviço expõe endpoints para classificar transações usando
o módulo spend_classification desenvolvido.
"""

import os
import time
import signal
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Importa o pipeline de classificação
from spend_classification.engines.pipeline import ClassificationPipeline
from spend_classification.core.schemas import ExpenseTransaction, Prediction

# Importa rotas de feedback
from app.routes_feedback import router as feedback_router

# Importa rotas de parsing de PDF
try:
    from card_pdf_parser.api import router as parse_itau_router
    PDF_PARSER_AVAILABLE = True
except ImportError:
    PDF_PARSER_AVAILABLE = False
    parse_itau_router = None

# Importa configuração centralizada
from app.config import (
    get_model_dir,
    get_feedback_dir,
    ensure_directories_exist,
    bootstrap_model_from_bundled
)

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa FastAPI
app = FastAPI(
    title="Expense Classification API",
    description="""
    ## Microserviço para Classificação de Despesas
    
    Este microserviço utiliza o módulo `spend_classification` para classificar transações financeiras
    usando múltiplos engines de classificação com fallback inteligente.
    
    ### 🚀 Funcionalidades
    
    - **Normalização Textual**: Sempre ativa (lowercase, remoção de acentos, etc.)
    - **Regras Determinísticas**: Controlada por `ENABLE_DETERMINISTIC_RULES` (padrão: `false`)
    - **Similaridade TF-IDF**: Controlada por `ENABLE_TFIDF_SIMILARITY` (padrão: `false`)
    - **Model Adapter**: Sempre ativo (RandomForest + TF-IDF)
    - **Fallback IA**: Controlado por `ENABLE_FALLBACK_AI` (padrão: `true`)
    - **Tipo de Modelo**: Controlado por `USE_PIPELINE_MODEL` (padrão: `true`)
    - **Parser de Fatura Itaú**: Upload de PDF para extração estruturada via `/parse_itau`
    
    ### 🔧 Configuração
    
    Configure as variáveis de ambiente no arquivo `.env`:
    
    ```env
    # Feature Flags
    ENABLE_DETERMINISTIC_RULES=false
    ENABLE_TFIDF_SIMILARITY=false
    ENABLE_FALLBACK_AI=true
    USE_PIPELINE_MODEL=true
    
    # Thresholds
    SIMILARITY_THRESHOLD=0.70
    MODEL_THRESHOLD=0.70
    
    # API Keys para Fallback IA (opcional)
    OPENAI_API_KEY=your_key_here
    ANTHROPIC_API_KEY=your_key_here
    SERPAPI_API_KEY=your_key_here
    ```
    
    ### 🎯 Tipos de Modelo
    
    - **Pipeline Model** (`USE_PIPELINE_MODEL=true`): Usa `modelo_natureza_do_gasto.pkl` (padrão)
    - **Separate Components** (`USE_PIPELINE_MODEL=false`): Usa `vectorizer.pkl` + `classifier.pkl`
    
    ### 📊 Resposta da API
    
    O campo `needs_keys` indica se faltam API keys para o fallback IA:
    - `needs_keys: true` - Fallback IA habilitado mas faltam chaves
    - `needs_keys: false` - Fallback IA habilitado e chaves disponíveis
    - `needs_keys: null` - Fallback IA desabilitado
    
    ### 🎯 Métodos de Classificação
    
    - `rules_engine` - Regras determinísticas
    - `similarity_engine` - Similaridade TF-IDF
    - `model_adapter` - Modelo RandomForest
    - `ai_fallback` - Fallback com IA (OpenAI/Anthropic)
    - `fallback` - Fallback padrão para casos de dúvida
    """,
    version="1.1.0",
    contact={
        "name": "Expense Classification API",
        "url": "https://github.com/your-repo/expense-classification",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Configura variáveis de ambiente com defaults
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.9"))
MODEL_THRESHOLD = float(os.getenv("MODEL_THRESHOLD", "0.70"))
ENABLE_FALLBACK_AI = os.getenv("ENABLE_FALLBACK_AI", "true").lower() == "true"

# Obter diretórios configurados (com suporte a DATA_DIR)
MODEL_DIR = get_model_dir()
FEEDBACK_DIR = get_feedback_dir()

# Garantir que diretórios existem
ensure_directories_exist()

# Bootstrap: copiar modelo bundled para volume persistente se necessário
bootstrap_model_from_bundled()

# Logs de verificação no boot
import glob
modelo_existe = os.path.exists(os.path.join(MODEL_DIR, "modelo_natureza_do_gasto.pkl"))
feedback_files_count = len(glob.glob(os.path.join(FEEDBACK_DIR, "feedback_*.csv")))
print(f"INFO: Boot - MODEL_DIR={MODEL_DIR} FEEDBACK_DIR={FEEDBACK_DIR} modelo_existe={modelo_existe} feedback_files={feedback_files_count}")

# Inicializa o pipeline de classificação
pipeline = ClassificationPipeline(
    similarity_threshold=SIMILARITY_THRESHOLD,
    model_adapter_threshold=MODEL_THRESHOLD,
    model_adapter_path=MODEL_DIR
)

# Variável para controlar shutdown gracioso
shutdown_event = asyncio.Event()

def signal_handler(signum, frame):
    """Handler para SIGTERM/SIGINT para shutdown gracioso."""
    print(f"Recebido sinal {signum}, iniciando shutdown gracioso...")
    shutdown_event.set()

# Registrar handlers de sinal
signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)

# Configurar CORS
# Permitir requisições do domínio de produção e localhost para desenvolvimento
allowed_origins = [
    "https://fin.exemplo.site",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8080",
]

# Permitir origens adicionais via variável de ambiente (separadas por vírgula)
env_origins = os.getenv("CORS_ORIGINS", "")
if env_origins:
    allowed_origins.extend([origin.strip() for origin in env_origins.split(",")])

# Registrar endpoint de health check ANTES de QUALQUER middleware ou router
# Isso garante que o endpoint sempre esteja disponível, independente de configurações
@app.get("/health", include_in_schema=True)
async def health_check():
    """Endpoint de health check."""
    return {"status": "ok"}

@app.get("/test-openai-connection", include_in_schema=True)
async def test_openai_connection():
    """
    Endpoint de teste para diagnosticar problemas de conexão com OpenAI.
    APENAS PARA DESENVOLVIMENTO - Não deve estar disponível em produção.

    Este endpoint testa:
    - Se a API key está configurada corretamente
    - Se consegue estabelecer conexão com a API da OpenAI
    - Qual é o erro específico em caso de falha

    Returns:
        dict: Status do teste com detalhes do erro (se houver)
    """
    # Proteção: apenas disponível em modo debug
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    if not DEBUG_MODE:
        raise HTTPException(
            status_code=404,
            detail="Endpoint não encontrado"
        )

    import traceback
    from datetime import datetime
    
    result = {
        "timestamp": datetime.utcnow().isoformat(),
        "status": "unknown",
        "openai_key_present": False,
        "openai_key_length": 0,
        "openai_key_prefix": None,
        "error": None,
        "error_type": None,
        "error_details": None,
        "connection_test": None
    }
    
    # 1. Verificar se a chave está presente
    # FIX: Limpar quebras de linha e espaços (Secret Manager pode adicionar \r\n)
    openai_key_raw = os.getenv('OPENAI_API_KEY')
    openai_key = openai_key_raw.strip() if openai_key_raw else None
    result["openai_key_present"] = bool(openai_key)
    
    if openai_key:
        result["openai_key_length"] = len(openai_key)
        # Mostrar apenas os primeiros 10 caracteres para segurança
        result["openai_key_prefix"] = openai_key[:10] + "..." if len(openai_key) > 10 else "***"
    
    if not result["openai_key_present"]:
        result["status"] = "error"
        result["error"] = "OPENAI_API_KEY não está configurada ou está vazia"
        result["error_type"] = "MissingAPIKey"
        return result
    
    # 2. Tentar importar a biblioteca OpenAI
    try:
        from openai import OpenAI
        from openai import APIConnectionError, APITimeoutError, APIError, AuthenticationError
    except ImportError as e:
        result["status"] = "error"
        result["error"] = f"Erro ao importar biblioteca OpenAI: {str(e)}"
        result["error_type"] = "ImportError"
        # Logging server-side (não expor stack trace ao cliente)
        import logging
        logging.error(f"ImportError in /test-openai-connection: {traceback.format_exc()}")
        return result
    
    # 3. Tentar criar o cliente
    try:
        # FIX: Criar httpx client explícito para evitar problemas de conexão no Cloud Run
        # O SDK da OpenAI usa httpx internamente, que pode ter comportamento diferente do requests
        try:
            import httpx
            http_client = httpx.Client(
                timeout=60.0,
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                http2=False,  # Desabilitar HTTP/2 que pode causar problemas no Cloud Run
                verify=True,
                follow_redirects=True
            )
            client = OpenAI(
                api_key=openai_key,
                http_client=http_client,
                timeout=60.0,
                max_retries=0  # Sem retries para diagnóstico mais rápido
            )
        except ImportError:
            # Fallback se httpx não estiver disponível
            client = OpenAI(
                api_key=openai_key,
                timeout=60.0,
                max_retries=0
            )
        result["connection_test"] = "client_created"
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Erro ao criar cliente OpenAI: {str(e)}"
        result["error_type"] = type(e).__name__
        # Logging server-side (não expor stack trace ao cliente)
        import logging
        logging.error(f"Exception creating OpenAI client: {traceback.format_exc()}")
        return result
    
    # 4. Tentar fazer uma chamada simples à API
    try:
        start_time = time.time()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Responda apenas: OK"}],
            max_tokens=5,
            timeout=60.0
        )
        elapsed_time = (time.time() - start_time) * 1000  # em milissegundos
        
        result["status"] = "success"
        result["connection_test"] = "api_call_successful"
        result["response_time_ms"] = round(elapsed_time, 2)
        result["response_content"] = response.choices[0].message.content.strip()
        result["model_used"] = response.model
        
    except APIConnectionError as e:
        result["status"] = "error"
        result["error"] = f"Erro de conexão: {str(e)}"
        result["error_type"] = "APIConnectionError"
        result["error_details"] = str(e)
        result["connection_test"] = "connection_failed"
        # Tentar obter mais detalhes
        if hasattr(e, 'message'):
            result["error_message"] = e.message
        if hasattr(e, 'request'):
            result["request_info"] = str(e.request) if e.request else None
            
    except APITimeoutError as e:
        result["status"] = "error"
        result["error"] = f"Timeout na conexão: {str(e)}"
        result["error_type"] = "APITimeoutError"
        result["error_details"] = str(e)
        result["connection_test"] = "timeout"
        
    except AuthenticationError as e:
        result["status"] = "error"
        result["error"] = f"Erro de autenticação (chave inválida): {str(e)}"
        result["error_type"] = "AuthenticationError"
        result["error_details"] = str(e)
        result["connection_test"] = "authentication_failed"
        
    except APIError as e:
        result["status"] = "error"
        result["error"] = f"Erro na API OpenAI: {str(e)}"
        result["error_type"] = "APIError"
        result["error_details"] = str(e)
        if hasattr(e, 'status_code'):
            result["status_code"] = e.status_code
        result["connection_test"] = "api_error"
        
    except Exception as e:
        result["status"] = "error"
        result["error"] = f"Erro inesperado: {str(e)}"
        result["error_type"] = type(e).__name__
        # Logging server-side (não expor stack trace ao cliente)
        import logging
        logging.error(f"Unexpected error in /test-openai-connection: {traceback.format_exc()}")
        result["connection_test"] = "unexpected_error"

    return result

@app.get("/test-connectivity", include_in_schema=True)
async def test_connectivity():
    """
    Endpoint de teste para diagnosticar problemas de conectividade de rede.
    
    Testa:
    - Resolução DNS
    - Conexão HTTP genérica
    - Conexão HTTPS para OpenAI
    - Conexão HTTPS para outros serviços
    
    Returns:
        dict: Resultados dos testes de conectividade
    """
    import socket
    import requests
    from datetime import datetime
    
    results = {
        "timestamp": datetime.utcnow().isoformat(),
        "tests": {}
    }
    
    # Teste 1: Resolução DNS
    try:
        ip = socket.gethostbyname("api.openai.com")
        results["tests"]["dns_openai"] = {
            "status": "success",
            "ip": ip,
            "hostname": "api.openai.com"
        }
    except socket.gaierror as e:
        results["tests"]["dns_openai"] = {
            "status": "error",
            "error": f"DNS resolution failed: {str(e)}",
            "error_type": "DNSResolutionError"
        }
    except Exception as e:
        results["tests"]["dns_openai"] = {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    # Teste 2: Conexão HTTP genérica (Google)
    try:
        response = requests.get("https://www.google.com", timeout=10)
        results["tests"]["http_google"] = {
            "status": "success",
            "status_code": response.status_code,
            "url": "https://www.google.com"
        }
    except requests.exceptions.ConnectionError as e:
        results["tests"]["http_google"] = {
            "status": "error",
            "error": f"Connection error: {str(e)}",
            "error_type": "ConnectionError"
        }
    except requests.exceptions.Timeout as e:
        results["tests"]["http_google"] = {
            "status": "error",
            "error": f"Timeout: {str(e)}",
            "error_type": "Timeout"
        }
    except Exception as e:
        results["tests"]["http_google"] = {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    # Teste 3: Conexão HTTPS para OpenAI (sem autenticação)
    try:
        response = requests.get("https://api.openai.com/v1/models", timeout=10)
        results["tests"]["https_openai"] = {
            "status": "success",
            "status_code": response.status_code,
            "url": "https://api.openai.com/v1/models",
            "note": "Status 401 é esperado (sem auth), mas indica que a conexão funciona"
        }
    except requests.exceptions.ConnectionError as e:
        results["tests"]["https_openai"] = {
            "status": "error",
            "error": f"Connection error: {str(e)}",
            "error_type": "ConnectionError",
            "diagnosis": "Cloud Run não consegue conectar à OpenAI - verifique VPC/Cloud NAT"
        }
    except requests.exceptions.Timeout as e:
        results["tests"]["https_openai"] = {
            "status": "error",
            "error": f"Timeout: {str(e)}",
            "error_type": "Timeout"
        }
    except Exception as e:
        results["tests"]["https_openai"] = {
            "status": "error",
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    # Resumo
    success_count = sum(1 for test in results["tests"].values() if test.get("status") == "success")
    total_count = len(results["tests"])
    results["summary"] = {
        "total_tests": total_count,
        "successful": success_count,
        "failed": total_count - success_count,
        "all_passed": success_count == total_count
    }
    
    return results

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Incluir rotas de feedback
app.include_router(feedback_router)

# Incluir rotas de parsing de PDF (se disponível)
if PDF_PARSER_AVAILABLE and parse_itau_router:
    app.include_router(parse_itau_router)

# Schemas Pydantic para a API
class ConfigurationRequest(BaseModel):
    """Schema para configuração de teste."""
    similarity_threshold: float = Field(0.70, ge=0.0, le=1.0, description="Threshold para Similarity Engine", example=0.70)
    model_threshold: float = Field(0.70, ge=0.0, le=1.0, description="Threshold para Model Adapter", example=0.70)
    enable_deterministic_rules: bool = Field(False, description="Habilitar regras determinísticas", example=False)
    enable_tfidf_similarity: bool = Field(False, description="Habilitar similaridade TF-IDF", example=False)
    enable_fallback_ai: bool = Field(True, description="Habilitar fallback IA", example=True)
    use_pipeline_model: bool = Field(True, description="Usar modelo pipeline (modelo_natureza_do_gasto.pkl)", example=True)

class TransactionRequest(BaseModel):
    """Schema para requisição de transação."""
    id: Optional[str] = Field(None, description="ID único da transação (opcional)")
    description: str = Field(..., description="Descrição da transação (obrigatório)", example="Netflix Com")
    amount: float = Field(..., gt=0.0, description="Valor da transação em reais (obrigatório)", example=44.90)
    date: str = Field(..., description="Data da transação no formato ISO (obrigatório)", example="2024-01-01")
    card_number: Optional[str] = Field(None, description="Número do cartão (opcional)")
    card_holder: Optional[str] = Field(None, description="Nome do portador do cartão (opcional)")
    origin: Optional[str] = Field(None, description="Origem da transação (opcional)")
    installments: Optional[int] = Field(None, description="Número total de parcelas (opcional)")
    installment_number: Optional[int] = Field(None, description="Número da parcela atual (opcional)")
    metadata: Optional[dict] = Field(None, description="Metadados adicionais (opcional)")
    
    class Config:
        extra = "forbid"
        validate_assignment = True
        arbitrary_types_allowed = True
        allow_population_by_field_name = True
        use_enum_values = True
        validate_all = True

class PredictionResponse(BaseModel):
    """Schema para resposta de predição."""
    label: str = Field(..., description="Categoria classificada da transação", example="Netflix")
    confidence: float = Field(..., ge=0.0, le=1.0001, description="Confiança da classificação (0.0 a 1.0)", example=0.95)
    method_used: str = Field(..., description="Método usado para classificação", example="rules_engine")
    elapsed_ms: float = Field(..., ge=0.0, description="Tempo de processamento em milissegundos", example=5.2)
    transaction_id: Optional[str] = Field(None, description="ID da transação processada")
    needs_keys: Optional[bool] = Field(None, description="Indica se faltam API keys para fallback IA (true/false/null)")
    raw_prediction: Optional[dict] = Field(None, description="Dados brutos da predição para debugging")
    
    class Config:
        # Permitir valores ligeiramente acima de 1.0 devido a precisão de ponto flutuante
        extra = "forbid"
        validate_assignment = True
        # Usar validação mais tolerante para confiança
        arbitrary_types_allowed = True
        # Permitir valores ligeiramente acima de 1.0 devido a precisão de ponto flutuante
        allow_population_by_field_name = True
        # Permitir valores ligeiramente acima de 1.0 devido a precisão de ponto flutuante
        use_enum_values = True
        # Permitir valores ligeiramente acima de 1.0 devido a precisão de ponto flutuante
        validate_all = True

class ClassificationResponse(BaseModel):
    """Schema para resposta de classificação."""
    predictions: List[PredictionResponse] = Field(..., description="Lista de predições para cada transação")
    elapsed_ms: float = Field(..., ge=0.0, description="Tempo total de processamento em milissegundos")
    total_transactions: int = Field(..., ge=0, description="Número total de transações processadas")
    
    class Config:
        # Permitir valores ligeiramente acima de 1.0 devido a precisão de ponto flutuante
        extra = "forbid"
        validate_assignment = True
        # Usar validação mais tolerante para confiança
        arbitrary_types_allowed = True
        # Permitir valores ligeiramente acima de 1.0 devido a precisão de ponto flutuante
        allow_population_by_field_name = True
        # Permitir valores ligeiramente acima de 1.0 devido a precisão de ponto flutuante
        use_enum_values = True
        # Permitir valores ligeiramente acima de 1.0 devido a precisão de ponto flutuante
        validate_all = True

def _check_api_key(key_name: str) -> bool:
    """
    Verifica se uma API key existe e tem valor não vazio.
    
    Args:
        key_name: Nome da variável de ambiente da API key
        
    Returns:
        True se a chave existe e tem valor não vazio
    """
    value = os.getenv(key_name)
    return bool(value and value.strip())

@app.get("/v1/status")
async def get_status():
    """
    📊 **Status detalhado dos engines e configurações**
    
    Retorna informações detalhadas sobre o status dos engines de classificação,
    feature flags ativas e configurações do sistema.
    """
    engine_status = pipeline.get_engine_status()
    
    return {
        "api_version": "1.1.0",
        "status": "operational",
        "feature_flags": {
            "deterministic_rules": {
                "enabled": os.getenv("ENABLE_DETERMINISTIC_RULES", "false").lower() == "true",
                "description": "Regras determinísticas para classificação"
            },
            "tfidf_similarity": {
                "enabled": os.getenv("ENABLE_TFIDF_SIMILARITY", "false").lower() == "true",
                "description": "Similaridade TF-IDF com histórico"
            },
            "ai_fallback": {
                "enabled": os.getenv("ENABLE_FALLBACK_AI", "true").lower() == "true",
                "description": "Fallback com IA para casos de dúvida"
            },
            "pipeline_model": {
                "enabled": os.getenv("USE_PIPELINE_MODEL", "true").lower() == "true",
                "description": "Usar modelo pipeline (modelo_natureza_do_gasto.pkl)"
            }
        },
        "engines": engine_status,
        "thresholds": {
            "similarity_threshold": SIMILARITY_THRESHOLD,
            "model_threshold": MODEL_THRESHOLD
        },
        "training_data": {
            "file": os.getenv("TRAINING_DATA_FILE", "modelo_despesas_completo.csv"),
            "description": "Arquivo CSV usado para treinamento dos modelos"
        },
        "ai_providers": {
            "openai": _check_api_key("OPENAI_API_KEY"),
            "anthropic": _check_api_key("ANTHROPIC_API_KEY"),
            "serpapi": _check_api_key("SERPAPI_API_KEY")
        }
    }

class ClassificationWithConfigRequest(BaseModel):
    """Schema para classificação com configuração personalizada."""
    transactions: List[TransactionRequest] = Field(..., description="Lista de transações para classificar")
    config: Optional[ConfigurationRequest] = Field(None, description="Configuração personalizada (opcional)")

@app.post("/v1/classify-with-config", response_model=ClassificationResponse)
async def classify_transactions_with_config(request: ClassificationWithConfigRequest):
    """
    🎯 **Classifica transações com configuração personalizada**
    
    Este endpoint permite configurar thresholds e feature flags para cada requisição.
    """
    transactions = request.transactions
    config = request.config
    
    if not transactions:
        raise HTTPException(status_code=400, detail="Lista de transações não pode estar vazia")
    
    try:
        # Aplicar configuração personalizada se fornecida
        if config:
            # Temporariamente atualizar variáveis de ambiente
            original_env = {}
            env_updates = {
                'SIMILARITY_THRESHOLD': str(config.similarity_threshold),
                'MODEL_THRESHOLD': str(config.model_threshold),
                'ENABLE_DETERMINISTIC_RULES': str(config.enable_deterministic_rules).lower(),
                'ENABLE_TFIDF_SIMILARITY': str(config.enable_tfidf_similarity).lower(),
                'ENABLE_FALLBACK_AI': str(config.enable_fallback_ai).lower(),
                'USE_PIPELINE_MODEL': str(config.use_pipeline_model).lower()
            }
            
            # Salvar valores originais e aplicar novos
            for key, value in env_updates.items():
                original_env[key] = os.getenv(key)
                os.environ[key] = value
            
            # Recriar pipeline com nova configuração
            temp_pipeline = ClassificationPipeline(
                similarity_threshold=config.similarity_threshold,
                model_adapter_threshold=config.model_threshold
            )
        else:
            temp_pipeline = pipeline
        
        # Converte requests para ExpenseTransaction
        expense_transactions = []
        for req in transactions:
            # Converte string de data para datetime
            from datetime import datetime
            try:
                date_obj = datetime.fromisoformat(req.date.replace('Z', '+00:00'))
            except ValueError:
                # Fallback para formato simples
                date_obj = datetime.fromisoformat(req.date)
            
            expense_transaction = ExpenseTransaction(
                description=req.description,
                amount=req.amount,
                date=date_obj,
                card_number=req.card_number,
                card_holder=req.card_holder,
                origin=req.origin,
                installments=req.installments,
                installment_number=req.installment_number,
                raw_data=req.metadata
            )
            expense_transactions.append(expense_transaction)
        
        # Executa classificação usando o pipeline
        start_time = time.perf_counter()
        predictions, elapsed_ms = temp_pipeline.predict_batch(expense_transactions)
        total_elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Restaurar variáveis de ambiente originais se config foi usado
        if config:
            for key, value in original_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        
        # Converte predições para response
        prediction_responses = []
        for pred in predictions:
            prediction_responses.append(PredictionResponse(
                label=pred.label,
                confidence=pred.confidence,
                method_used=pred.method_used,
                elapsed_ms=pred.elapsed_ms,
                transaction_id=pred.transaction_id,
                needs_keys=pred.needs_keys,
                raw_prediction=pred.raw_prediction
            ))
        
        return ClassificationResponse(
            predictions=prediction_responses,
            elapsed_ms=total_elapsed_ms,
            total_transactions=len(transactions)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na classificação: {str(e)}")

@app.post("/v1/classify", response_model=ClassificationResponse)
async def classify_transactions(transactions: List[TransactionRequest]):
    """
    🎯 **Classifica transações financeiras usando múltiplos engines**
    
    Este endpoint processa uma lista de transações e retorna suas classificações
    usando o pipeline de classificação com fallback inteligente.
    
    ### 🔄 Fluxo de Classificação
    
    1. **Normalização Textual** (sempre ativa)
    2. **Regras Determinísticas** (se habilitado)
    3. **Similaridade TF-IDF** (se habilitado)
    4. **Model Adapter** (RandomForest - sempre ativo)
    5. **Fallback IA** (se habilitado e resultado = "duvida")
    6. **Fallback Padrão** (se nenhum método atender threshold)
    
    ### 📊 Campos de Resposta
    
    - **`needs_keys`**: Indica status das API keys para fallback IA
    - **`method_used`**: Método que classificou a transação
    
    ### 🚨 Códigos de Erro
    
    - `400`: Lista de transações vazia
    - `500`: Erro interno na classificação
    """
    if not transactions:
        raise HTTPException(status_code=400, detail="Lista de transações não pode estar vazia")
    
    try:
        # Converte requests para ExpenseTransaction
        expense_transactions = []
        for req in transactions:
            # Converte string de data para datetime
            from datetime import datetime
            try:
                date_obj = datetime.fromisoformat(req.date.replace('Z', '+00:00'))
            except ValueError:
                # Fallback para formato simples
                date_obj = datetime.fromisoformat(req.date)
            
            expense_transaction = ExpenseTransaction(
                description=req.description,
                amount=req.amount,
                date=date_obj,
                card_number=req.card_number,
                card_holder=req.card_holder,
                origin=req.origin,
                installments=req.installments,
                installment_number=req.installment_number,
                raw_data=req.metadata
            )
            expense_transactions.append(expense_transaction)
        
        # Executa classificação usando o pipeline
        start_time = time.perf_counter()
        predictions, elapsed_ms = pipeline.predict_batch(expense_transactions)
        total_elapsed_ms = (time.perf_counter() - start_time) * 1000
        
        # Converte predições para response
        prediction_responses = []
        for pred in predictions:
            prediction_responses.append(PredictionResponse(
                label=pred.label,
                confidence=pred.confidence,
                method_used=pred.method_used,
                elapsed_ms=pred.elapsed_ms,
                transaction_id=pred.transaction_id,
                needs_keys=pred.needs_keys,
                raw_prediction=pred.raw_prediction
            ))
        
        return ClassificationResponse(
            predictions=prediction_responses,
            elapsed_ms=total_elapsed_ms,
            total_transactions=len(transactions)
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na classificação: {str(e)}")

@app.get("/")
async def root():
    """
    🏠 **Endpoint raiz com informações do serviço**
    
    Retorna informações básicas sobre a API, configurações ativas e status dos engines.
    """
    # Obter status dos engines
    engine_status = pipeline.get_engine_status()
    
    return {
        "service": "Expense Classification API",
        "version": "1.1.0",
        "status": "running",
        "features": {
            "deterministic_rules": os.getenv("ENABLE_DETERMINISTIC_RULES", "false").lower() == "true",
            "tfidf_similarity": os.getenv("ENABLE_TFIDF_SIMILARITY", "false").lower() == "true",
            "ai_fallback": os.getenv("ENABLE_FALLBACK_AI", "true").lower() == "true",
            "pipeline_model": os.getenv("USE_PIPELINE_MODEL", "true").lower() == "true"
        },
        "thresholds": {
            "similarity_threshold": SIMILARITY_THRESHOLD,
            "model_threshold": MODEL_THRESHOLD
        },
        "engines": engine_status,
        "training_data": os.getenv("TRAINING_DATA_FILE", "modelo_despesas_completo.csv")
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
