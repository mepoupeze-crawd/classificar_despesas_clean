"""
Engine de Regras

Implementa um sistema de regras baseado em padrões para classificação
de despesas, útil para casos específicos e conhecidos.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
import logging
from ..core.contracts import ClassifierInterface
from ..core.schemas import ExpenseTransaction, ClassificationResult
from ..core.constants import CATEGORIES, TEXT_CLEANING_PATTERNS
from .rules import (
    infer_tipo_from_card,
    infer_comp_from_card,
    parse_parcelas_from_desc,
    infer_titular_from_card,
    infer_final_cartao_from_card,
    apply_comp_rules_by_titular,
    clean_transaction_description,
    extract_establishment_name
)


class RulesEngine(ClassifierInterface):
    """
    Engine de regras para classificação de despesas.
    
    Usa padrões de texto e regras específicas para classificar
    transações conhecidas com alta confiança.
    """
    
    def __init__(self):
        """Inicializa o engine de regras."""
        self.rules: List[Dict[str, Any]] = []
        self.logger = logging.getLogger(__name__)
        self._setup_default_rules()
    
    def classify(self, transaction: ExpenseTransaction) -> ClassificationResult:
        """
        Classifica uma transação usando regras.
        
        Args:
            transaction: Transação a ser classificada
            
        Returns:
            Resultado da classificação
        """
        # Aplicar regras do cartão primeiro
        card_result = self._apply_card_rules(transaction)
        if card_result:
            return card_result
        
        # Aplicar regras de titular
        titular_result = self._apply_titular_rules(transaction)
        if titular_result:
            return titular_result
        
        # Aplicar regras padrão de descrição
        text = self._prepare_text(transaction)
        
        for rule in self.rules:
            if self._match_rule(rule, text, transaction):
                return ClassificationResult(
                    category=rule["category"],
                    confidence=rule["confidence"],
                    classifier_used="rules_engine",
                    fallback_used=False,
                    raw_prediction={
                        "matched_rule": rule["name"],
                        "pattern": rule["pattern"]
                    }
                )
        
        # Nenhuma regra encontrada - retornar categoria vazia
        return ClassificationResult(
            category="",
            confidence=0.0,
            classifier_used="rules_engine",
            fallback_used=False,
            raw_prediction={
                "reason": "no_rules_matched",
                "description": transaction.description
            }
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
        return 0.8
    
    def add_rule(self, rule: Dict[str, Any]) -> None:
        """
        Adiciona uma nova regra ao engine.
        
        Args:
            rule: Dicionário com a definição da regra
        """
        required_fields = ["name", "pattern", "category", "confidence"]
        for field in required_fields:
            if field not in rule:
                raise ValueError(f"Rule must have field: {field}")
        
        if rule["category"] not in CATEGORIES:
            raise ValueError(f"Unknown category: {rule['category']}")
        
        self.rules.append(rule)
        self.logger.info(f"Regra adicionada: {rule['name']}")
    
    def remove_rule(self, rule_name: str) -> bool:
        """
        Remove uma regra pelo nome.
        
        Args:
            rule_name: Nome da regra a ser removida
            
        Returns:
            True se a regra foi removida, False se não encontrada
        """
        original_count = len(self.rules)
        self.rules = [r for r in self.rules if r["name"] != rule_name]
        
        removed = len(self.rules) < original_count
        if removed:
            self.logger.info(f"Regra removida: {rule_name}")
        
        return removed
    
    def get_rules(self) -> List[Dict[str, Any]]:
        """
        Retorna todas as regras configuradas.
        
        Returns:
            Lista de regras
        """
        return self.rules.copy()
    
    def _prepare_text(self, transaction: ExpenseTransaction) -> str:
        """
        Prepara o texto para matching de regras.
        
        Args:
            transaction: Transação a ser processada
            
        Returns:
            Texto limpo e normalizado
        """
        text = transaction.description.lower()
        
        # Remove datas
        text = re.sub(TEXT_CLEANING_PATTERNS["date_pattern"], '', text)
        
        # Remove palavras genéricas
        text = re.sub(TEXT_CLEANING_PATTERNS["generic_words"], '', text, flags=re.IGNORECASE)
        
        # Remove espaços duplicados
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _match_rule(self, rule: Dict[str, Any], text: str, transaction: ExpenseTransaction) -> bool:
        """
        Verifica se uma regra corresponde à transação.
        
        Args:
            rule: Regra a ser testada
            text: Texto limpo da transação
            transaction: Transação original
            
        Returns:
            True se a regra corresponde
        """
        # Matching por padrão de texto
        if "pattern" in rule:
            pattern = rule["pattern"]
            if isinstance(pattern, str):
                if rule.get("exact_match", False):
                    return pattern.lower() in text
                else:
                    return bool(re.search(pattern, text, re.IGNORECASE))
            elif isinstance(pattern, list):
                return any(p.lower() in text for p in pattern)
        
        # Matching por condições específicas
        if "conditions" in rule:
            return self._check_conditions(rule["conditions"], transaction)
        
        return False
    
    def _check_conditions(self, conditions: Dict[str, Any], transaction: ExpenseTransaction) -> bool:
        """
        Verifica condições específicas da transação.
        
        Args:
            conditions: Condições a serem verificadas
            transaction: Transação a ser testada
            
        Returns:
            True se todas as condições são atendidas
        """
        for condition, value in conditions.items():
            if condition == "amount_range":
                min_amount, max_amount = value
                if not (min_amount <= transaction.amount <= max_amount):
                    return False
            
            elif condition == "card_holder":
                if transaction.card_holder and value.lower() not in transaction.card_holder.lower():
                    return False
            
            elif condition == "origin":
                if transaction.origin and value.lower() not in transaction.origin.lower():
                    return False
            
            elif condition == "installments":
                if transaction.installments != value:
                    return False
        
        return True
    
    def _apply_card_rules(self, transaction: ExpenseTransaction) -> Optional[ClassificationResult]:
        """
        Aplica regras baseadas no cartão da transação.
        
        Args:
            transaction: Transação a ser processada
            
        Returns:
            ClassificationResult se regra aplicada, None caso contrário
        """
        if not transaction.card_holder:
            return None
        
        # Aplicar regras do rules.py
        tipo_result = infer_tipo_from_card(transaction.card_holder)
        comp_result = infer_comp_from_card(transaction.card_holder)
        
        # Se encontrou tipo de débito, retornar
        if tipo_result and tipo_result.category == "débito":
            return ClassificationResult(
                category="débito",
                confidence=tipo_result.confidence,
                classifier_used="rules_engine",
                fallback_used=False,
                raw_prediction={
                    "rule_type": "card_tipo",
                    "card": transaction.card_holder,
                    "original_result": tipo_result.raw_prediction
                }
            )
        
        # Se encontrou compartilhamento, retornar
        if comp_result:
            return ClassificationResult(
                category=comp_result.category,
                confidence=comp_result.confidence,
                classifier_used="rules_engine",
                fallback_used=False,
                raw_prediction={
                    "rule_type": "card_comp",
                    "card": transaction.card_holder,
                    "original_result": comp_result.raw_prediction
                }
            )
        
        return None
    
    
    def _apply_titular_rules(self, transaction: ExpenseTransaction) -> Optional[ClassificationResult]:
        """
        Aplica regras baseadas no titular do cartão.
        
        Args:
            transaction: Transação a ser processada
            
        Returns:
            ClassificationResult se regra aplicada, None caso contrário
        """
        if not transaction.card_holder:
            return None
        
        titular = infer_titular_from_card(transaction.card_holder)
        final_cartao = infer_final_cartao_from_card(transaction.card_holder)
        
        if titular:
            # Aplicar regras de compartilhamento baseadas no titular
            comp_prediction = ""
            comp_result = apply_comp_rules_by_titular(comp_prediction, transaction.card_holder)
            
            if comp_result:
                return ClassificationResult(
                    category=comp_result,
                    confidence=0.85,
                    classifier_used="rules_engine",
                    fallback_used=False,
                    raw_prediction={
                        "rule_type": "titular_comp",
                        "titular": titular,
                        "final_cartao": final_cartao,
                        "card": transaction.card_holder,
                        "comp_result": comp_result
                    }
                )
            
            # Se não encontrou compartilhamento específico, não classificar automaticamente
            # Deixa para outros engines (similarity, model) ou fallback
        
        return None
    
    def _setup_default_rules(self) -> None:
        """Configura regras padrão baseadas em padrões conhecidos."""
        default_rules = [
            # Streaming e Mensalidades
            {
                "name": "netflix",
                "pattern": r"netflix",
                "category": "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)",
                "confidence": 0.95
            },
            {
                "name": "spotify",
                "pattern": r"spotify",
                "category": "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)",
                "confidence": 0.95
            },
            {
                "name": "disney_plus",
                "pattern": r"disney.*plus",
                "category": "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)",
                "confidence": 0.95
            },
            {
                "name": "prime_video",
                "pattern": r"prime.*video|amazon.*prime",
                "category": "Gastos com mensalidades (Gympass, Spotfy, Unicef e Rappi)",
                "confidence": 0.95
            },
            
            # Transporte
            {
                "name": "uber",
                "pattern": [r"uber", r"99.*app"],
                "category": "Combustível/ Passagens/ Uber / Sem Parar",
                "confidence": 0.90
            },
            {
                "name": "gasolina_posto",
                "pattern": [r"posto", r"shell", r"ipiranga", r"petrobras", r"br distribuidora"],
                "category": "Combustível/ Passagens/ Uber / Sem Parar",
                "confidence": 0.85
            },
            
            # Supermercados
            {
                "name": "supermercado_carrefour",
                "pattern": r"carrefour",
                "category": "Supermercado",
                "confidence": 0.90
            },
            {
                "name": "supermercado_extra",
                "pattern": r"extra",
                "category": "Supermercado",
                "confidence": 0.90
            },
            {
                "name": "supermercado_walmart",
                "pattern": r"walmart",
                "category": "Supermercado",
                "confidence": 0.90
            },
            {
                "name": "supermercado_atacadao",
                "pattern": r"atacad[aã]o",
                "category": "Supermercado",
                "confidence": 0.90
            },
            
            # Farmácias
            {
                "name": "farmacia_drogasil",
                "pattern": r"drogasil",
                "category": "Farmácia",
                "confidence": 0.90
            },
            {
                "name": "farmacia_pague_menos",
                "pattern": r"pague.*menos",
                "category": "Farmácia",
                "confidence": 0.90
            },
            {
                "name": "farmacia_raia",
                "pattern": r"raia",
                "category": "Farmácia",
                "confidence": 0.90
            },
            
            # Restaurantes e Delivery
            {
                "name": "restaurante_ifood",
                "pattern": r"ifood",
                "category": "Restaurantes/ Bares/ Lanchonetes",
                "confidence": 0.90
            },
            {
                "name": "restaurante_rappi",
                "pattern": r"rappi",
                "category": "Restaurantes/ Bares/ Lanchonetes",
                "confidence": 0.90
            },
            {
                "name": "restaurante_uber_eats",
                "pattern": r"uber.*eats",
                "category": "Restaurantes/ Bares/ Lanchonetes",
                "confidence": 0.90
            },
            
            # Viagens
            {
                "name": "viagem_booking",
                "pattern": r"booking",
                "category": "Viagens / Férias",
                "confidence": 0.90
            },
            {
                "name": "viagem_airbnb",
                "pattern": r"airbnb",
                "category": "Viagens / Férias",
                "confidence": 0.90
            },
            {
                "name": "viagem_decolar",
                "pattern": r"decolar",
                "category": "Viagens / Férias",
                "confidence": 0.90
            },
            
            # Educação
            {
                "name": "educacao_cultura_inglesa",
                "pattern": r"cultura.*inglesa",
                "category": "Gastos com Educação (Inglês, MBA, Pós)",
                "confidence": 0.90
            },
            {
                "name": "educacao_kumon",
                "pattern": r"kumon",
                "category": "Gastos com Educação (Inglês, MBA, Pós)",
                "confidence": 0.90
            },
            
            # Saúde e Cuidados Pessoais
            {
                "name": "saude_nutricionista",
                "pattern": r"nutricionista",
                "category": "Cuidados Pessoais (Nutricionista / Medico / Suplemento)",
                "confidence": 0.85
            },
            {
                "name": "saude_medico",
                "pattern": r"medico|médico|clínica|hospital",
                "category": "Cuidados Pessoais (Nutricionista / Medico / Suplemento)",
                "confidence": 0.85
            },
            
            # Contas e Serviços
            {
                "name": "conta_luz",
                "pattern": r"conta.*luz|energia.*elétrica|cemig|light|enel",
                "category": "Conta de luz",
                "confidence": 0.95
            },
            {
                "name": "conta_gas",
                "pattern": r"conta.*g[aá]s|g[aá]s.*natural",
                "category": "Conta de gás",
                "confidence": 0.95
            },
            {
                "name": "internet_tv",
                "pattern": r"internet|tv.*cabo|net.*virtua|oi.*fibra|vivo.*fibra",
                "category": "Internet & TV a cabo",
                "confidence": 0.90
            },
            
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
        
        self.logger.info(f"Configuradas {len(default_rules)} regras padrão")
    
    def get_rules_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas das regras.
        
        Returns:
            Dicionário com estatísticas
        """
        categories = {}
        for rule in self.rules:
            cat = rule["category"]
            categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_rules": len(self.rules),
            "categories_covered": len(categories),
            "rules_by_category": categories,
            "average_confidence": sum(r["confidence"] for r in self.rules) / len(self.rules)
        }
