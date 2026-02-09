"""
Engine de Fallback para IA

Implementa o fallback para inteligência artificial usando ChatGPT
e SerpApi quando os modelos de ML não têm confiança suficiente.
"""

import re
from typing import List, Dict, Any, Optional
import logging
import requests
from openai import OpenAI
import os
from ..core.contracts import ClassifierInterface
from ..core.schemas import ExpenseTransaction, ClassificationResult
from ..core.constants import CATEGORIES, API_CONFIG, MESSAGES


class AIFallbackEngine(ClassifierInterface):
    """
    Engine de fallback para IA.
    
    Usa ChatGPT + SerpApi para classificar transações quando
    os modelos de ML não têm confiança suficiente.
    """
    
    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        serpapi_key: Optional[str] = None
    ):
        """
        Inicializa o engine de IA.
        
        Args:
            openai_api_key: Chave da API OpenAI
            serpapi_key: Chave da API SerpApi
        """
        self.openai_client = None
        self.serpapi_key = serpapi_key or os.getenv("SERP_API_KEY")
        self.logger = logging.getLogger(__name__)
        
        # Configura OpenAI
        openai_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = OpenAI(api_key=openai_key)
        else:
            self.logger.warning("OpenAI API key not provided")
    
    def classify(self, transaction: ExpenseTransaction) -> ClassificationResult:
        """
        Classifica uma transação usando IA.
        
        Args:
            transaction: Transação a ser classificada
            
        Returns:
            Resultado da classificação
        """
        if not self.openai_client:
            return ClassificationResult(
                category="",
                confidence=0.0,
                classifier_used="ai_fallback",
                fallback_used=True
            )
        
        try:
            # Extrai nome do estabelecimento
            establishment = self._extract_establishment(transaction.description)
            
            # Busca contexto na internet
            context = self._search_establishment(establishment)
            
            # Gera classificação com ChatGPT
            category, confidence = self._classify_with_chatgpt(
                transaction.description,
                establishment,
                context
            )
            
            return ClassificationResult(
                category=category,
                confidence=confidence,
                classifier_used="ai_fallback",
                fallback_used=True,
                ai_context=context
            )
            
        except Exception as e:
            self.logger.error(f"Erro na classificação IA: {e}")
            return ClassificationResult(
                category="",
                confidence=0.0,
                classifier_used="ai_fallback",
                fallback_used=True
            )
    
    def batch_classify(self, transactions: List[ExpenseTransaction]) -> List[ClassificationResult]:
        """
        Classifica múltiplas transações em lote.
        
        Args:
            transactions: Lista de transações
            
        Returns:
            Lista de resultados
        """
        return [self.classify(t) for t in transactions]
    
    def get_confidence_threshold(self) -> float:
        """Retorna o threshold de confiança."""
        return 0.6  # IA geralmente tem confiança moderada
    
    def _extract_establishment(self, description: str) -> str:
        """
        Extrai o nome do estabelecimento da descrição.
        
        Args:
            description: Descrição da transação
            
        Returns:
            Nome do estabelecimento limpo
        """
        text = description.upper()
        
        # Remove prefixos genéricos
        prefixes = ["PIX", "TED", "DOC", "PAGAMENTO", "CARTAO", "CARTÃO", 
                   "DEB", "CRED", "ENVIO", "ENVIADO", "COMPRA", "LOJA"]
        
        for prefix in prefixes:
            text = re.sub(f"\\b{prefix}\\b", '', text, flags=re.IGNORECASE)
        
        # Remove datas
        text = re.sub(r'\\d{2}/\\d{2}/\\d{4}', '', text)
        
        # Remove símbolos
        text = re.sub(r'[-–—]', '', text)
        
        # Remove espaços duplicados
        text = re.sub(r'\\s+', ' ', text).strip()
        
        return text.title()
    
    def _search_establishment(self, establishment: str) -> str:
        """
        Busca informações sobre o estabelecimento no SerpApi.
        
        Args:
            establishment: Nome do estabelecimento
            
        Returns:
            Contexto encontrado sobre o estabelecimento
        """
        if not self.serpapi_key or not establishment:
            return ""
        
        try:
            params = {
                "q": establishment,
                "hl": API_CONFIG["serpapi"]["hl"],
                "gl": API_CONFIG["serpapi"]["gl"],
                "api_key": self.serpapi_key,
                "engine": API_CONFIG["serpapi"]["engine"]
            }
            
            response = requests.get(
                "https://serpapi.com/search",
                params=params,
                timeout=API_CONFIG["serpapi"]["timeout"]
            )
            
            data = response.json()
            results = data.get("organic_results", [])
            
            # Extrai snippets dos primeiros resultados
            snippets = []
            for result in results[:API_CONFIG["serpapi"]["max_results"]]:
                snippet = result.get("snippet", "")
                if snippet:
                    snippets.append(snippet)
            
            context = "\\n".join(snippets)
            
            if context:
                self.logger.debug(f"Contexto encontrado para {establishment}")
            else:
                self.logger.warning(f"Nenhum contexto encontrado para {establishment}")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar no SerpApi: {e}")
            return ""
    
    def _classify_with_chatgpt(
        self,
        description: str,
        establishment: str,
        context: str
    ) -> tuple[str, float]:
        """
        Classifica usando ChatGPT.
        
        Args:
            description: Descrição original da transação
            establishment: Nome do estabelecimento
            context: Contexto da busca
            
        Returns:
            Tupla com (categoria, confiança)
        """
        try:
            prompt = self._build_prompt(description, establishment, context)
            
            response = self.openai_client.chat.completions.create(
                model=API_CONFIG["openai"]["model"],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=API_CONFIG["openai"]["max_tokens"],
                temperature=API_CONFIG["openai"]["temperature"]
            )
            
            result = response.choices[0].message.content.strip()
            
            # Parse do resultado
            category, confidence = self._parse_chatgpt_response(result)
            
            self.logger.debug(f"ChatGPT result: {result}")
            
            return category, confidence
            
        except Exception as e:
            self.logger.error(f"Erro ao consultar ChatGPT: {e}")
            return "", 0.0
    
    def _build_prompt(self, description: str, establishment: str, context: str) -> str:
        """
        Constrói o prompt para o ChatGPT.
        
        Args:
            description: Descrição da transação
            establishment: Nome do estabelecimento
            context: Contexto da busca
            
        Returns:
            Prompt formatado
        """
        categories_text = "\\n".join([f"- {cat}" for cat in CATEGORIES])
        
        prompt = f"""
Você é um assistente financeiro inteligente com acesso a ferramentas de busca como o SerpApi.
Sua tarefa é analisar uma transação da fatura de cartão de crédito e classificá-la corretamente com base nas informações obtidas online.

### Transação:
"{description}"

### Estabelecimento identificado:
"{establishment}"

### Resultado da pesquisa na internet:
"{context}"

### Categorias disponíveis:
{categories_text}

Com base nas informações acima, siga os passos:
1. Determine o setor de atividade ou tipo de serviço prestado pelo estabelecimento.
2. Escolha uma única categoria da lista que melhor representa o tipo de gasto.

Formato de resposta esperado:
"CATEGORIA|CONFIANCA"
Onde:
- CATEGORIA é uma das categorias da lista acima
- CONFIANCA é um número entre 0.0 e 1.0

Se não tiver certeza suficiente, responda:
"Gastos pessoais|0.0"
"""
        
        return prompt
    
    def _parse_chatgpt_response(self, response: str) -> tuple[str, float]:
        """
        Faz parse da resposta do ChatGPT.
        
        Args:
            response: Resposta do ChatGPT
            
        Returns:
            Tupla com (categoria, confiança)
        """
        try:
            # Procura por formato "CATEGORIA|CONFIANCA"
            if "|" in response:
                parts = response.split("|", 1)
                category = parts[0].strip()
                confidence = float(parts[1].strip())
                
                # Valida categoria
                if category not in CATEGORIES:
                    category = "Gastos pessoais"
                
                # Valida confiança
                confidence = max(0.0, min(1.0, confidence))
                
                return category, confidence
            
            # Se não conseguir fazer parse, retorna padrão
            return "", 0.0
            
        except Exception as e:
            self.logger.warning(f"Erro ao fazer parse da resposta ChatGPT: {e}")
            return "", 0.0
    
    def test_connection(self) -> Dict[str, bool]:
        """
        Testa as conexões com as APIs.
        
        Returns:
            Dicionário com status das conexões
        """
        results = {
            "openai": False,
            "serpapi": False
        }
        
        # Testa OpenAI
        if self.openai_client:
            try:
                # Teste simples
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                results["openai"] = True
            except Exception as e:
                self.logger.warning(f"OpenAI connection test failed: {e}")
        
        # Testa SerpApi
        if self.serpapi_key:
            try:
                params = {
                    "q": "test",
                    "api_key": self.serpapi_key,
                    "engine": "google"
                }
                response = requests.get(
                    "https://serpapi.com/search",
                    params=params,
                    timeout=5
                )
                results["serpapi"] = response.status_code == 200
            except Exception as e:
                self.logger.warning(f"SerpApi connection test failed: {e}")
        
        return results
    
    def get_ai_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do engine de IA.
        
        Returns:
            Dicionário com estatísticas
        """
        return {
            "openai_available": self.openai_client is not None,
            "serpapi_available": self.serpapi_key is not None,
            "connection_status": self.test_connection(),
            "api_config": API_CONFIG
        }
