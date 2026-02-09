"""
Constantes do Sistema

Define todas as constantes utilizadas no sistema de classificação
de despesas, incluindo categorias, thresholds e configurações.
"""

from typing import List, Dict, Any
from pathlib import Path
from .schemas import ExpenseCategory


# === CATEGORIAS DE DESPESAS ===
CATEGORIES: List[str] = [
    "Conta de luz",
    "Conta de gás", 
    "Internet & TV a cabo",
    "Moradia (Financiamento/ Aluguel/ Condominio)",
    "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)",
    "Planos de celular",
    "Gastos com Diarista",
    "Gastos com Educação (Inglês, MBA, Pós)",
    "Farmácia",
    "Supermercado",
    "Casamento",
    "Restaurantes/ Bares/ Lanchonetes",
    "Viagens / Férias",
    "Carro (Manutenção/ IPVA/ Seguro)",
    "Combustível/ Passagens/ Uber / Sem Parar",
    "Cuidados Pessoais (Nutricionista / Medico / Suplemento)",
    "Gastos com casa (outros)",
    "Gastos com presentes",
    "Gastos pessoais",
    "Gastos com Cachorro",
    "Futevolei",
    "Financiamento/Condominio",
    "Obra casa",
    "Inteligência Artificial",
    "Investimento",
    "Salário",
    "Transferencia Interna"
]

# === THRESHOLDS E LIMITES ===
CONFIDENCE_THRESHOLD: float = 0.7  # Limite de confiança para usar fallback
MIN_CONFIDENCE: float = 0.1  # Confiança mínima aceitável
MAX_RETRIES: int = 3  # Máximo de tentativas para APIs externas

# === CAMINHOS DOS MODELOS ===
MODEL_PATHS: Dict[str, str] = {
    "natureza_do_gasto": "modelos/modelo_natureza_do_gasto.pkl",
    "comp": "modelos/modelo_comp.pkl", 
    "parcelas": "modelos/modelo_parcelas.pkl",
    "no_da_parcela": "modelos/modelo_no_da_parcela.pkl",
    "tipo": "modelos/modelo_tipo.pkl"
}

# === CONFIGURAÇÕES DE API ===
API_CONFIG: Dict[str, Dict[str, Any]] = {
    "openai": {
        "model": "gpt-4o-mini",
        "max_tokens": 100,
        "temperature": 0.3,
        "timeout": 30
    },
    "serpapi": {
        "engine": "google",
        "hl": "pt-br",
        "gl": "br",
        "max_results": 3,
        "timeout": 10
    }
}

# === REGRAS DE PROCESSAMENTO ===
TEXT_CLEANING_PATTERNS: Dict[str, str] = {
    "date_pattern": r'\b(\d{2,4})[/-](\d{1,2})[/-](\d{2,4})\b',
    "generic_words": r'\b(pagamento|compra|anuidade|debito|credito|pix)\b',
    "installment_pattern": r'[\(\[]\s*(\d{1,2})\s*/\s*(\d{1,2})\s*[\)\]]',
    "card_number_pattern": r"(\d{4})"
}

# === MAPEAMENTO DE TITULARES ===
CARD_HOLDER_MAPPING: Dict[str, List[str]] = {
    "aline": ["aline"],
    "angela": ["angela"], 
    "joao": ["joao", "joão"]
}

# === FINAIS DE CARTÃO POR TITULAR ===
CARD_FINALS_BY_HOLDER: Dict[str, Dict[str, List[str]]] = {
    "aline": {
        "gastos": ["8805", "9558"],
        "planilha": ["0951", "4147"]
    }
}

# === CONFIGURAÇÕES DE CLASSIFICAÇÃO ===
CLASSIFICATION_CONFIG: Dict[str, Any] = {
    "batch_size": 100,  # Tamanho do lote para processamento
    "enable_fallback": True,  # Habilitar fallback para IA
    "enable_parallel": True,  # Processamento paralelo
    "max_workers": 4,  # Número máximo de workers paralelos
    "cache_predictions": True,  # Cache de predições
    "cache_size": 1000  # Tamanho do cache
}

# === CONFIGURAÇÕES DE LOGGING ===
LOGGING_CONFIG: Dict[str, Any] = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_path": "logs/spend_classification.log",
    "max_file_size": 10 * 1024 * 1024,  # 10MB
    "backup_count": 5
}

# === CONFIGURAÇÕES DE VALIDAÇÃO ===
VALIDATION_CONFIG: Dict[str, Any] = {
    "min_description_length": 3,
    "max_description_length": 500,
    "min_amount": 0.01,
    "max_amount": 999999.99,
    "allowed_origins": ["fatura", "extrato", "base"],
    "allowed_types": ["crédito", "débito"]
}

# === MENSAGENS E TEXTOS ===
MESSAGES: Dict[str, str] = {
    "processing_start": "🧠 Iniciando processamento de {count} transações...",
    "processing_complete": "✅ Processamento concluído com sucesso.",
    "fallback_triggered": "🤖 Fallback para IA acionado para: {description}",
    "model_loaded": "📦 Modelo {model_name} carregado com sucesso.",
    "classification_complete": "🎯 Classificação concluída: {category} (confiança: {confidence:.2f})",
    "error_processing": "❌ Erro ao processar transação: {error}",
    "insufficient_confidence": "⚠️ Confiança insuficiente ({confidence:.2f}) para transação: {description}",
    "feedback_collected": "📝 Feedback coletado para melhoria do modelo.",
    "model_retraining": "🔄 Modelo sendo retreinado com novos dados..."
}

# === CONFIGURAÇÕES DE PERFORMANCE ===
PERFORMANCE_CONFIG: Dict[str, Any] = {
    "enable_profiling": False,
    "memory_monitoring": True,
    "cpu_monitoring": True,
    "max_memory_usage": 1024 * 1024 * 1024,  # 1GB
    "performance_log_interval": 100  # Log a cada N transações
}

# === CONFIGURAÇÕES DE CACHE ===
CACHE_CONFIG: Dict[str, Any] = {
    "enable_memory_cache": True,
    "enable_disk_cache": False,
    "cache_ttl": 3600,  # 1 hora
    "max_cache_entries": 10000,
    "cache_cleanup_interval": 300  # 5 minutos
}

# === CONFIGURAÇÕES DE SEGURANÇA ===
SECURITY_CONFIG: Dict[str, Any] = {
    "mask_sensitive_data": True,
    "log_sensitive_data": False,
    "encrypt_cache": False,
    "api_rate_limit": 100,  # requests per minute
    "max_request_size": 1024 * 1024  # 1MB
}
