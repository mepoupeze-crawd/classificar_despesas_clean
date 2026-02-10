"""
Engine de Similaridade

Implementa um sistema de classificação baseado em similaridade
de texto usando técnicas de NLP para encontrar transações similares.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from difflib import SequenceMatcher
import logging
from ..core.contracts import ClassifierInterface
from ..core.schemas import ExpenseTransaction, ClassificationResult
from ..core.constants import CATEGORIES


class SimilarityEngine(ClassifierInterface):
    """
    Engine de similaridade para classificação de despesas.
    
    Usa técnicas de similaridade de texto para encontrar transações
    similares e classificar baseado em exemplos históricos.
    """
    
    def __init__(self, similarity_threshold: float = 0.8):
        """
        Inicializa o engine de similaridade.
        
        Args:
            similarity_threshold: Threshold mínimo de similaridade
        """
        self.similarity_threshold = similarity_threshold
        self.examples: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
        self._setup_default_examples()
    
    def classify(self, transaction: ExpenseTransaction) -> ClassificationResult:
        """
        Classifica uma transação usando similaridade.
        
        Args:
            transaction: Transação a ser classificada
            
        Returns:
            Resultado da classificação
        """
        text = self._prepare_text(transaction)
        
        # Encontra a melhor correspondência
        best_match = self._find_best_match(text)
        
        if best_match and best_match["similarity"] >= self.similarity_threshold:
            return ClassificationResult(
                category=best_match["category"],
                confidence=best_match["similarity"],
                classifier_used="similarity_engine",
                fallback_used=False,
                raw_prediction={
                    "matched_example": best_match["example"],
                    "similarity_score": best_match["similarity"]
                }
            )
        
        # Nenhuma correspondência suficientemente similar
        return ClassificationResult(
            category="Gastos pessoais",
            confidence=0.2,
            classifier_used="similarity_engine",
            fallback_used=False
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
        return self.similarity_threshold
    
    def add_example(self, example: Dict[str, Any]) -> None:
        """
        Adiciona um novo exemplo ao engine.
        
        Args:
            example: Dicionário com exemplo de transação
        """
        required_fields = ["text", "category"]
        for field in required_fields:
            if field not in example:
                raise ValueError(f"Example must have field: {field}")
        
        if example["category"] not in CATEGORIES:
            raise ValueError(f"Unknown category: {example['category']}")
        
        # Prepara o texto do exemplo
        example["prepared_text"] = self._prepare_text_from_string(example["text"])
        
        self.examples.append(example)
        self.logger.debug(f"Exemplo adicionado: {example['text'][:50]}...")
    
    def remove_example(self, text: str) -> bool:
        """
        Remove um exemplo pelo texto.
        
        Args:
            text: Texto do exemplo a ser removido
            
        Returns:
            True se o exemplo foi removido, False se não encontrado
        """
        original_count = len(self.examples)
        self.examples = [e for e in self.examples if e["text"] != text]
        
        removed = len(self.examples) < original_count
        if removed:
            self.logger.debug(f"Exemplo removido: {text[:50]}...")
        
        return removed
    
    def get_examples(self) -> List[Dict[str, Any]]:
        """
        Retorna todos os exemplos configurados.
        
        Returns:
            Lista de exemplos
        """
        return self.examples.copy()
    
    def _prepare_text(self, transaction: ExpenseTransaction) -> str:
        """
        Prepara o texto da transação para comparação.
        
        Args:
            transaction: Transação a ser processada
            
        Returns:
            Texto limpo e normalizado
        """
        return self._prepare_text_from_string(transaction.description)
    
    def _prepare_text_from_string(self, text: str) -> str:
        """
        Prepara um texto string para comparação.
        
        Args:
            text: Texto a ser processado
            
        Returns:
            Texto limpo e normalizado
        """
        # Converte para minúsculo
        text = text.lower()
        
        # Remove datas
        text = re.sub(r'\b(\d{2,4})[/-](\d{1,2})[/-](\d{2,4})\b', '', text)
        
        # Remove palavras genéricas
        text = re.sub(r'\b(pagamento|compra|anuidade|debito|credito|pix)\b', '', text)
        
        # Remove símbolos especiais
        text = re.sub(r'[-–—]', '', text)
        
        # Remove espaços duplicados
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _find_best_match(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Encontra a melhor correspondência para um texto.
        
        Args:
            text: Texto a ser comparado
            
        Returns:
            Melhor correspondência encontrada ou None
        """
        best_match = None
        best_similarity = 0.0
        
        for example in self.examples:
            similarity = self._calculate_similarity(text, example["prepared_text"])
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = {
                    "similarity": similarity,
                    "category": example["category"],
                    "example": example["text"]
                }
        
        return best_match
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calcula a similaridade entre dois textos.
        
        Args:
            text1: Primeiro texto
            text2: Segundo texto
            
        Returns:
            Score de similaridade entre 0.0 e 1.0
        """
        # Usa SequenceMatcher para similaridade básica
        basic_similarity = SequenceMatcher(None, text1, text2).ratio()
        
        # Calcula similaridade por palavras-chave
        words1 = set(text1.split())
        words2 = set(text2.split())
        
        if not words1 or not words2:
            return basic_similarity
        
        # Similaridade de Jaccard
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        jaccard_similarity = intersection / union if union > 0 else 0.0
        
        # Combina as duas similaridades
        combined_similarity = (basic_similarity * 0.6) + (jaccard_similarity * 0.4)
        
        return combined_similarity
    
    def _setup_default_examples(self) -> None:
        """Configura exemplos padrão baseados em transações típicas."""
        default_examples = [
            {
                "text": "Netflix Com",
                "category": "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)"
            },
            {
                "text": "Ebn*Spotify",
                "category": "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)"
            },
            {
                "text": "99app *99app",
                "category": "Combustível/ Passagens/ Uber / Sem Parar"
            },
            {
                "text": "Carrefour",
                "category": "Supermercado"
            },
            {
                "text": "Drogasil",
                "category": "Farmácia"
            },
            {
                "text": "Shell",
                "category": "Combustível/ Passagens/ Uber / Sem Parar"
            },
            {
                "text": "iFood",
                "category": "Restaurantes/ Bares/ Lanchonetes"
            },
            {
                "text": "Booking Com Hotel",
                "category": "Viagens / Férias"
            },
            {
                "text": "Airbnb",
                "category": "Viagens / Férias"
            },
            {
                "text": "Cultura Inglesa",
                "category": "Gastos com Educação (Inglês, MBA, Pós)"
            },
            {
                "text": "Nutricionista",
                "category": "Cuidados Pessoais (Nutricionista / Medico / Suplemento)"
            },
            {
                "text": "Farmácia",
                "category": "Farmácia"
            },
            {
                "text": "Posto de Gasolina",
                "category": "Combustível/ Passagens/ Uber / Sem Parar"
            },
            {
                "text": "Restaurante",
                "category": "Restaurantes/ Bares/ Lanchonetes"
            },
            {
                "text": "Hotel",
                "category": "Viagens / Férias"
            }
        ]
        
        for example in default_examples:
            self.add_example(example)
        
        self.logger.info(f"Configurados {len(default_examples)} exemplos padrão")
    
    def get_similarity_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do engine de similaridade.
        
        Returns:
            Dicionário com estatísticas
        """
        categories = {}
        for example in self.examples:
            cat = example["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_examples": len(self.examples),
            "categories_covered": len(categories),
            "examples_by_category": categories,
            "similarity_threshold": self.similarity_threshold
        }
    
    def find_similar_examples(self, text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Encontra exemplos similares a um texto.
        
        Args:
            text: Texto para comparação
            limit: Número máximo de exemplos a retornar
            
        Returns:
            Lista de exemplos similares ordenados por similaridade
        """
        prepared_text = self._prepare_text_from_string(text)
        
        similarities = []
        for example in self.examples:
            similarity = self._calculate_similarity(prepared_text, example["prepared_text"])
            similarities.append({
                "example": example["text"],
                "category": example["category"],
                "similarity": similarity
            })
        
        # Ordena por similaridade (maior primeiro)
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        
        return similarities[:limit]
