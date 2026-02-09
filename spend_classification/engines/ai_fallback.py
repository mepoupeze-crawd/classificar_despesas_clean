"""
AI Fallback Engine

Implementa fallback para IA quando o classificador interno retorna "duvida".
Suporta OpenAI e Anthropic APIs com validação de chaves.
"""

import os
import logging
import time
import re
import requests
from typing import Optional, Dict, Any, Tuple
from ..core.schemas import ExpenseTransaction

logger = logging.getLogger(__name__)


class AIFallbackEngine:
    """
    Engine de fallback IA para casos de dúvida.
    
    Suporta OpenAI e Anthropic APIs para classificação de despesas
    quando o classificador interno não consegue determinar a categoria.
    """
    
    def __init__(self):
        """Inicializa o engine de fallback IA."""
        # Garantir que .env foi carregado
        # No Docker, variáveis podem vir de env_file (já no os.environ) ou precisar carregar do .env
        from dotenv import load_dotenv
        
        # Tentar carregar .env de múltiplos locais possíveis
        env_paths = [
            '.env',  # Diretório atual
            '/app/.env',  # Dentro do container Docker
            os.path.join(os.path.dirname(__file__), '../../.env'),  # Relativo ao módulo
            os.path.join(os.getcwd(), '.env'),  # Diretório de trabalho atual
        ]
        
        env_loaded = False
        for env_path in env_paths:
            if os.path.exists(env_path):
                load_dotenv(env_path, override=False)
                env_loaded = True
                logger.debug(f"Carregado .env de: {env_path}")
                break
        
        if not env_loaded:
            # Tentar carregar sem especificar caminho (procura automaticamente)
            load_dotenv(override=False)
            logger.debug("Tentativa de carregar .env do diretório padrão")
        
        self.enabled = os.getenv('ENABLE_FALLBACK_AI', 'true').lower() == 'true'
        # FIX: Limpar quebras de linha e espaços (Secret Manager pode adicionar \r\n)
        openai_key_raw = os.getenv('OPENAI_API_KEY')
        self.openai_key = openai_key_raw.strip() if openai_key_raw else None
        
        anthropic_key_raw = os.getenv('ANTHROPIC_API_KEY')
        self.anthropic_key = anthropic_key_raw.strip() if anthropic_key_raw else None
        
        serpapi_key_raw = os.getenv('SERPAPI_API_KEY')
        self.serpapi_key = serpapi_key_raw.strip() if serpapi_key_raw else None
        
        # Debug: logar status das chaves (sem expor valores completos)
        logger.info(f"AI Fallback - Enabled: {self.enabled}")
        logger.info(f"AI Fallback - OpenAI key present: {bool(self.openai_key and self.openai_key.strip())}")
        logger.info(f"AI Fallback - Anthropic key present: {bool(self.anthropic_key and self.anthropic_key.strip())}")
        logger.info(f"AI Fallback - SerpAPI key present: {bool(self.serpapi_key and self.serpapi_key.strip())}")
        
        # Debug adicional: verificar se variáveis estão em os.environ (Docker env_file)
        logger.info(f"AI Fallback - OPENAI_API_KEY in os.environ: {'OPENAI_API_KEY' in os.environ}")
        logger.info(f"AI Fallback - SERPAPI_API_KEY in os.environ: {'SERPAPI_API_KEY' in os.environ}")
        
        # Validar chaves se fallback estiver habilitado
        self.has_valid_keys = self._validate_api_keys()
        
        if self.enabled and not self.has_valid_keys:
            logger.warning("ENABLE_FALLBACK_AI=true mas faltam API Keys. Defina OPENAI_API_KEY/ANTHROPIC_API_KEY e (opcional) SERPAPI_API_KEY no .env ou como variáveis de ambiente.")
            logger.warning(f"Valores atuais - OpenAI: {'presente' if self.openai_key else 'ausente'}, Anthropic: {'presente' if self.anthropic_key else 'ausente'}, SerpAPI: {'presente' if self.serpapi_key else 'ausente'}")
        elif self.enabled and self.has_valid_keys:
            logger.info("AI Fallback habilitado e API keys configuradas corretamente.")
    
    def _validate_api_keys(self) -> bool:
        """
        Valida se pelo menos uma API key está disponível e não está vazia.
        
        Returns:
            True se pelo menos uma chave válida (não vazia) estiver disponível
        """
        openai_valid = bool(self.openai_key and self.openai_key.strip())
        anthropic_valid = bool(self.anthropic_key and self.anthropic_key.strip())
        return openai_valid or anthropic_valid
    
    def _extrair_nome_estabelecimento(self, texto: str) -> str:
        """
        Extrai o nome do estabelecimento de uma descrição de transação.
        
        Args:
            texto: Texto da descrição da transação
            
        Returns:
            Nome do estabelecimento limpo
        """
        texto = texto.upper()
        
        # Remove prefixos genéricos
        texto = re.sub(r'\b(PIX|TED|DOC|PAGAMENTO|CARTAO|CARTÃO|DEB|CRED|ENVIO|ENVIADO|COMPRA|LOJA)\b', '', texto, flags=re.IGNORECASE)
        
        # Remove datas e símbolos
        texto = re.sub(r'\d{2}/\d{2}/\d{4}', '', texto)
        texto = re.sub(r'[-–—]', '', texto)
        
        return texto.strip().title()
    
    def _buscar_estabelecimento_serpapi(self, termo_busca: str) -> str:
        """
        Busca informações sobre um estabelecimento usando SerpAPI.
        
        Args:
            termo_busca: Termo de busca para o estabelecimento
            
        Returns:
            Contexto obtido do SerpAPI ou string vazia se falhar
        """
        if not self.serpapi_key:
            return ""
        
        try:
            params = {
                "q": termo_busca,
                "hl": "pt-br",
                "gl": "br",
                "api_key": self.serpapi_key,
                "engine": "google"
            }
            
            response = requests.get("https://serpapi.com/search", params=params, timeout=10)
            data = response.json()
            
            resultados = data.get("organic_results", [])
            snippets = [res.get("snippet", "") for res in resultados if "snippet" in res]
            
            # Retornar até 3 snippets como contexto
            return "\n".join(snippets[:3])
            
        except Exception as e:
            logger.warning(f"Erro ao buscar no SerpAPI: {e}")
            return ""
    
    def classify(self, transaction: ExpenseTransaction) -> Optional[Dict[str, Any]]:
        """
        Classifica uma transação usando IA quando o resultado é "duvida".
        
        Args:
            transaction: Transação para classificar
            
        Returns:
            Resultado da classificação IA ou None se não aplicável
        """
        if not self.enabled:
            logger.debug("AI Fallback desabilitado por feature flag")
            return None
            
        if not self.has_valid_keys:
            logger.debug("AI Fallback habilitado mas faltam API keys")
            return None
        
        try:
            # Tentar OpenAI primeiro se disponível
            if self.openai_key:
                result = self._classify_with_openai(transaction)
                if result:
                    return result
            
            # Tentar Anthropic se OpenAI falhou ou não está disponível
            if self.anthropic_key:
                result = self._classify_with_anthropic(transaction)
                if result:
                    return result
            
            logger.warning("Todas as APIs de IA falharam")
            return None
            
        except Exception as e:
            logger.error(f"Erro no AI Fallback: {e}")
            return None
    
    def _classify_with_openai(self, transaction: ExpenseTransaction) -> Optional[Dict[str, Any]]:
        """
        Classifica usando OpenAI API.
        
        Args:
            transaction: Transação para classificar
            
        Returns:
            Resultado da classificação ou None se falhar
        """
        # CRÍTICO: Re-validar API key no momento da chamada (não confiar apenas no __init__)
        # No Cloud Run, variáveis podem não estar disponíveis no momento do __init__
        # FIX: Limpar quebras de linha e espaços (Secret Manager pode adicionar \r\n)
        openai_key_raw = os.getenv('OPENAI_API_KEY') or self.openai_key
        openai_key = openai_key_raw.strip() if openai_key_raw else None
        
        # Validar que a key está presente e não vazia
        if not openai_key:
            logger.error("OPENAI_API_KEY não está disponível no momento da chamada")
            logger.error(f"self.openai_key presente: {bool(self.openai_key)}, os.getenv presente: {bool(os.getenv('OPENAI_API_KEY'))}")
            return None
        
        # Log de diagnóstico (sem expor o valor da key)
        logger.debug(f"OpenAI API key validada: length={len(openai_key)}, prefix={openai_key[:10]}...")
        
        max_retries = 3
        retry_delay = 1  # segundos
        
        for attempt in range(max_retries):
            try:
                # Importar OpenAI apenas quando necessário
                from openai import OpenAI
                from openai import APIConnectionError, APITimeoutError, APIError
                
                logger.debug(f"Tentando classificação OpenAI (tentativa {attempt + 1}/{max_retries})")
                
                # Configurar cliente com timeout maior e configurações de conexão
                # IMPORTANTE: Usar a key re-validada, não self.openai_key que pode estar None
                # FIX: Criar httpx client explícito para evitar problemas de conexão no Cloud Run
                # O SDK da OpenAI usa httpx internamente, que pode ter comportamento diferente do requests
                try:
                    import httpx
                    # Criar httpx client com configurações explícitas que funcionam no Cloud Run
                    http_client = httpx.Client(
                        timeout=60.0,
                        limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
                        http2=False,  # Desabilitar HTTP/2 que pode causar problemas no Cloud Run
                        verify=True,  # Verificar certificados SSL
                        follow_redirects=True
                    )
                    client = OpenAI(
                        api_key=openai_key,
                        http_client=http_client,
                        timeout=60.0,
                        max_retries=0  # Desabilitar retries internos para diagnóstico mais claro
                    )
                except ImportError:
                    # Fallback se httpx não estiver disponível (não deveria acontecer)
                    logger.warning("httpx não disponível, usando client padrão")
                    client = OpenAI(
                        api_key=openai_key,
                        timeout=60.0,
                        max_retries=0
                    )
                
                # Construir prompt para classificação
                prompt = self._build_classification_prompt(transaction)
                
                # Fazer chamada para API
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Você é um especialista em classificação de despesas pessoais."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=100,
                    temperature=0.3,
                    timeout=60.0  # Timeout explícito na chamada
                )
                
                # Extrair resposta
                classification = response.choices[0].message.content.strip()
                
                # Parsear resposta para extrair categoria e confiança
                category, confidence = self._parse_ai_response(classification)
                
                if category and confidence > 0.5:  # Threshold mínimo para IA
                    return {
                        "label": category,
                        "confidence": confidence,
                        "method_used": "ai_fallback_openai",
                        "raw_response": classification
                    }
                
                return None
                
            except APIConnectionError as e:
                error_msg = f"Erro de conexão OpenAI (tentativa {attempt + 1}/{max_retries}): {str(e)}"
                logger.warning(error_msg)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Backoff exponencial
                    continue
                else:
                    logger.error(f"Falha após {max_retries} tentativas: {error_msg}")
                    return None
                    
            except APITimeoutError as e:
                error_msg = f"Timeout na conexão OpenAI (tentativa {attempt + 1}/{max_retries}): {str(e)}"
                logger.warning(error_msg)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    logger.error(f"Falha após {max_retries} tentativas: {error_msg}")
                    return None
                    
            except APIError as e:
                # Erros de API (401, 403, 429, 500, etc.)
                error_msg = f"Erro na API OpenAI (tentativa {attempt + 1}/{max_retries}): {str(e)}"
                logger.warning(error_msg)
                # Para erros de API, não fazemos retry (exceto 429 - rate limit)
                if hasattr(e, 'status_code') and e.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                return None
                
            except Exception as e:
                error_msg = f"Erro inesperado na classificação OpenAI (tentativa {attempt + 1}/{max_retries}): {type(e).__name__}: {str(e)}"
                logger.warning(error_msg)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    logger.error(f"Falha após {max_retries} tentativas: {error_msg}")
                    return None
        
        return None
    
    def _classify_with_anthropic(self, transaction: ExpenseTransaction) -> Optional[Dict[str, Any]]:
        """
        Classifica usando Anthropic API.
        
        Args:
            transaction: Transação para classificar
            
        Returns:
            Resultado da classificação ou None se falhar
        """
        # CRÍTICO: Re-validar API key no momento da chamada (não confiar apenas no __init__)
        # FIX: Limpar quebras de linha e espaços (Secret Manager pode adicionar \r\n)
        anthropic_key_raw = os.getenv('ANTHROPIC_API_KEY') or self.anthropic_key
        anthropic_key = anthropic_key_raw.strip() if anthropic_key_raw else None
        
        # Validar que a key está presente e não vazia
        if not anthropic_key:
            logger.error("ANTHROPIC_API_KEY não está disponível no momento da chamada")
            return None
        
        max_retries = 3
        retry_delay = 1  # segundos
        
        for attempt in range(max_retries):
            try:
                # Importar Anthropic apenas quando necessário
                import anthropic
                
                # Tentar importar exceções específicas (podem variar por versão)
                try:
                    from anthropic import APIConnectionError, APITimeoutError, APIError
                except ImportError:
                    # Fallback para exceções genéricas se não disponíveis
                    APIConnectionError = Exception
                    APITimeoutError = Exception
                    APIError = Exception
                
                logger.debug(f"Tentando classificação Anthropic (tentativa {attempt + 1}/{max_retries})")
                
                # Configurar cliente com timeout maior
                # IMPORTANTE: Usar a key re-validada, não self.anthropic_key que pode estar None
                client = anthropic.Anthropic(
                    api_key=anthropic_key,
                    timeout=60.0  # Timeout aumentado para 60 segundos
                )
                
                # Construir prompt para classificação
                prompt = self._build_classification_prompt(transaction)
                
                # Fazer chamada para API
                response = client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=100,
                    temperature=0.3,
                    timeout=60.0,  # Timeout explícito
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extrair resposta
                classification = response.content[0].text.strip()
                
                # Parsear resposta para extrair categoria e confiança
                category, confidence = self._parse_ai_response(classification)
                
                if category and confidence > 0.5:  # Threshold mínimo para IA
                    return {
                        "label": category,
                        "confidence": confidence,
                        "method_used": "ai_fallback_anthropic",
                        "raw_response": classification
                    }
                
                return None
                
            except APIConnectionError as e:
                error_msg = f"Erro de conexão Anthropic (tentativa {attempt + 1}/{max_retries}): {str(e)}"
                logger.warning(error_msg)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Backoff exponencial
                    continue
                else:
                    logger.error(f"Falha após {max_retries} tentativas: {error_msg}")
                    return None
                    
            except APITimeoutError as e:
                error_msg = f"Timeout na conexão Anthropic (tentativa {attempt + 1}/{max_retries}): {str(e)}"
                logger.warning(error_msg)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    logger.error(f"Falha após {max_retries} tentativas: {error_msg}")
                    return None
                    
            except APIError as e:
                # Erros de API (401, 403, 429, 500, etc.)
                error_msg = f"Erro na API Anthropic (tentativa {attempt + 1}/{max_retries}): {str(e)}"
                logger.warning(error_msg)
                # Para erros de API, não fazemos retry (exceto 429 - rate limit)
                if hasattr(e, 'status_code') and e.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                return None
                
            except Exception as e:
                error_msg = f"Erro inesperado na classificação Anthropic (tentativa {attempt + 1}/{max_retries}): {type(e).__name__}: {str(e)}"
                logger.warning(error_msg)
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                else:
                    logger.error(f"Falha após {max_retries} tentativas: {error_msg}")
                    return None
        
        return None
    
    def _build_classification_prompt(self, transaction: ExpenseTransaction) -> str:
        """
        Constrói prompt para classificação IA.
        
        Args:
            transaction: Transação para classificar
            
        Returns:
            Prompt formatado para IA
        """
        categories = [
            "Conta de luz", "Conta de gás", "Internet & TV a cabo",
            "Moradia (Financiamento/ Aluguel/ Condominio)",
            "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)",
            "Planos de celular", "Gastos com Diarista",
            "Gastos com Educação (Inglês, MBA, Pós)", "Farmácia",
            "Supermercado", "Casamento", "Restaurantes/ Bares/ Lanchonetes",
            "Viagens / Férias", "Carro (Manutenção/ IPVA/ Seguro)",
            "Combustível/ Passagens/ Uber / Sem Parar",
            "Cuidados Pessoais (Nutricionista / Medico / Suplemento)",
            "Gastos com casa (outros)", "Gastos com presentes",
            "Gastos pessoais", "Gastos com Cachorro", "Futevolei",
            "Financiamento/Condominio", "Obra casa",
            "Inteligência Artificial", "Investimento", "Salário"
        ]
        
        estabelecimento = self._extrair_nome_estabelecimento(transaction.description)
        estabelecimento_contexto = self._buscar_estabelecimento_serpapi(estabelecimento)
        
        # Construir prompt base
        prompt_parts = [
            "Você é um assistente financeiro inteligente com acesso a ferramentas de busca como o SerpAPI.",
            "Sua tarefa é analisar uma transação da fatura de cartão de crédito e classificá-la corretamente com base nas informações obtidas online.",
            "",
            f"### Transação:",
            f'"{transaction.description}"',
            "",
            f"### Estabelecimento identificado:",
            f'"{estabelecimento}"'
        ]
        
        # Adicionar contexto do SerpAPI se disponível
        if estabelecimento_contexto and estabelecimento_contexto.strip():
            prompt_parts.extend([
                "",
                "### Resultado da pesquisa na internet:",
                f'"{estabelecimento_contexto}"'
            ])
        else:
            prompt_parts.append("")
        
        prompt_parts.extend([
            "",
            "### Categorias disponíveis:",
            ', '.join(categories),
            "",
            "Com base nas informações acima, siga os passos:",
            "1. Determine o setor de atividade ou tipo de serviço prestado pelo estabelecimento.",
            "2. Escolha uma única categoria da lista que melhor representa o tipo de gasto.",
            "",
            "Responda APENAS com o formato:",
            "CATEGORIA: [nome da categoria]",
            "CONFIANÇA: [0.0-1.0]",
            "",
            "Exemplo:",
            "CATEGORIA: Supermercado",
            "CONFIANÇA: 0.85"
        ])
        
        return "\n".join(prompt_parts)
    
    def _parse_ai_response(self, response: str) -> Tuple[Optional[str], float]:
        """
        Parseia resposta da IA para extrair categoria e confiança.
        
        Args:
            response: Resposta bruta da IA
            
        Returns:
            Tupla com (categoria, confiança)
        """
        try:
            lines = response.strip().split('\n')
            category = None
            confidence = 0.0
            
            for line in lines:
                line = line.strip()
                if line.startswith('CATEGORIA:'):
                    category = line.replace('CATEGORIA:', '').strip()
                elif line.startswith('CONFIANÇA:'):
                    try:
                        confidence = float(line.replace('CONFIANÇA:', '').strip())
                    except ValueError:
                        confidence = 0.5  # Fallback
            
            return category, confidence
            
        except Exception as e:
            logger.warning(f"Erro ao parsear resposta IA: {e}")
            return None, 0.0
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status do engine de fallback IA.
        
        Returns:
            Dicionário com status e configurações
        """
        return {
            "enabled": self.enabled,
            "has_valid_keys": self.has_valid_keys,
            "openai_available": bool(self.openai_key),
            "anthropic_available": bool(self.anthropic_key),
            "serpapi_available": bool(self.serpapi_key)
        }


def create_ai_fallback_engine() -> AIFallbackEngine:
    """
    Função de fábrica para criar uma instância de AIFallbackEngine.
    
    Returns:
        Instância de AIFallbackEngine
    """
    return AIFallbackEngine()
