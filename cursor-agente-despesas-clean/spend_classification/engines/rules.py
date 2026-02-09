"""
Módulo de Regras Puras

Contém funções puras para inferir informações de transações baseadas
em regras específicas de negócio.
"""

import re
from typing import Optional, Tuple, Dict, Any
from ..core.schemas import ClassificationResult


def infer_tipo_from_card(card: str) -> Optional[ClassificationResult]:
    """
    Infere o tipo de transação baseado no número/final do cartão.
    
    Regras:
    - Se cartão começa com "CC -" → tipo="débito" (alta confiança)
    - Caso contrário → retorna None
    
    Args:
        card: String com informações do cartão
        
    Returns:
        ClassificationResult com tipo inferido ou None se não aplicável
    """
    if not card or not isinstance(card, str):
        return None
    
    card_normalized = card.strip().upper()
    
    # Regra: CC - → débito
    if card_normalized.startswith("CC -"):
        return ClassificationResult(
            category="débito",
            confidence=0.95,
            classifier_used="rules_tipo",
            fallback_used=False,
            raw_prediction={
                "rule_applied": "cc_prefix",
                "original_card": card,
                "normalized_card": card_normalized
            }
        )
    
    return None


def infer_comp_from_card(card: str) -> Optional[ClassificationResult]:
    """
    Infere o compartilhamento (comp) baseado no número/final do cartão.
    
    Regras:
    - Se cartão contém "CASA" → comp="planilha comp"
    - Caso contrário → retorna None
    
    Args:
        card: String com informações do cartão
        
    Returns:
        ClassificationResult com comp inferido ou None se não aplicável
    """
    if not card or not isinstance(card, str):
        return None
    
    card_normalized = card.strip().upper()
    
    # Regra: CASA → planilha comp
    if "CASA" in card_normalized:
        return ClassificationResult(
            category="planilha comp",
            confidence=0.90,
            classifier_used="rules_comp",
            fallback_used=False,
            raw_prediction={
                "rule_applied": "casa_keyword",
                "original_card": card,
                "normalized_card": card_normalized
            }
        )
    
    return None


def parse_parcelas_from_desc(desc: str) -> Optional[Dict[str, Any]]:
    """
    Extrai informações de parcelamento da descrição da transação.
    
    Regras:
    - Se descrição contém padrão n/n (ex: 3/12) → retorna dict com parcelas
    - Caso contrário → retorna None
    
    Args:
        desc: String com descrição da transação
        
    Returns:
        Dict com {'no_da_parcela': int, 'parcelas': int} ou None se não encontrado
    """
    if not desc or not isinstance(desc, str):
        return None
    
    # Padrão para capturar parcelas: (n/n) ou [n/n] ou n/n
    patterns = [
        r'[\(\[]\s*(\d{1,2})\s*/\s*(\d{1,2})\s*[\)\]]',  # (3/12) ou [3/12]
        r'\b(\d{1,2})\s*/\s*(\d{1,2})\b'  # 3/12
    ]
    
    for pattern in patterns:
        match = re.search(pattern, desc)
        if match:
            no_parcela_str, total_parcelas_str = match.groups()
            
            try:
                no_da_parcela = int(no_parcela_str)
                parcelas = int(total_parcelas_str)
                
                # Validações básicas
                if 1 <= no_da_parcela <= parcelas and parcelas <= 99:
                    return {
                        'no_da_parcela': no_da_parcela,
                        'parcelas': parcelas,
                        'confidence': 0.95,
                        'pattern_used': pattern,
                        'original_match': match.group()
                    }
                    
            except ValueError:
                continue
    
    return None


def infer_titular_from_card(card: str) -> Optional[str]:
    """
    Infere o titular do cartão baseado no nome.
    
    Regras baseadas nos padrões do projeto original:
    - Se contém "aline" → "aline"
    - Se contém "angela" → "angela"  
    - Se contém "joao" ou "joão" → "joao"
    
    Args:
        card: String com informações do cartão
        
    Returns:
        String com nome do titular ou None se não identificado
    """
    if not card or not isinstance(card, str):
        return None
    
    card_lower = card.lower()
    
    # Mapeamento de titulares
    titular_patterns = {
        "aline": ["aline"],
        "angela": ["angela"],
        "joao": ["joao", "joão"]
    }
    
    for titular, patterns in titular_patterns.items():
        for pattern in patterns:
            if pattern in card_lower:
                return titular
    
    return None


def infer_final_cartao_from_card(card: str) -> Optional[str]:
    """
    Extrai os últimos 4 dígitos do cartão.
    
    Args:
        card: String com informações do cartão
        
    Returns:
        String com últimos 4 dígitos ou None se não encontrado
    """
    if not card or not isinstance(card, str):
        return None
    
    # Procura por todas as sequências de 4 dígitos e retorna a última
    matches = re.findall(r"(\d{4})", card)
    return matches[-1] if matches else None


def apply_comp_rules_by_titular(
    comp_prediction: str, 
    card: str
) -> Optional[str]:
    """
    Aplica regras específicas de compartilhamento baseadas no titular.
    
    Regras baseadas no código original:
    - Angela: sempre "planilha comp"
    - Aline: regras específicas por final do cartão
    - João: evita forçar "planilha comp" quando sem confiança
    
    Args:
        comp_prediction: Predição original do compartilhamento
        card: String com informações do cartão
        
    Returns:
        String com compartilhamento ajustado ou None se não aplicável
    """
    if not card:
        return comp_prediction
    
    titular = infer_titular_from_card(card)
    final_cartao = infer_final_cartao_from_card(card)
    
    if not titular:
        return comp_prediction
    
    # Angela: sempre planilha comp
    if titular == "angela":
        return "planilha comp"
    
    # Aline: regras por final do cartão
    if titular == "aline" and final_cartao:
        # Finais específicos para planilha comp
        finais_planilha = {"0951", "4147"}
        # Finais específicos para gastos pessoais
        finais_gastos = {"8805", "9558"}
        
        if final_cartao in finais_planilha:
            return "planilha comp"
        elif final_cartao in finais_gastos:
            return "Gastos Aline"
    
    # João: evita forçar planilha comp quando sem confiança
    if titular == "joao" and isinstance(comp_prediction, str) and comp_prediction.lower().startswith("duvida"):
        return ""
    
    return comp_prediction


def clean_transaction_description(desc: str) -> str:
    """
    Limpa a descrição da transação removendo elementos desnecessários.
    
    Args:
        desc: String com descrição original
        
    Returns:
        String com descrição limpa
    """
    if not desc or not isinstance(desc, str):
        return ""
    
    # Remove datas no formato DD/MM/YYYY ou DD-MM-YYYY
    desc = re.sub(r'\b(\d{2,4})[/-](\d{1,2})[/-](\d{2,4})\b', '', desc)
    
    # Remove palavras genéricas (mas não "compra" que é útil)
    desc = re.sub(r'\b(pagamento|anuidade|debito|credito|pix)\b', '', desc, flags=re.IGNORECASE)
    
    # Remove espaços duplicados e bordas
    desc = re.sub(r'\s+', ' ', desc).strip()
    
    return desc


def extract_establishment_name(desc: str) -> str:
    """
    Extrai o nome do estabelecimento da descrição.
    
    Args:
        desc: String com descrição da transação
        
    Returns:
        String com nome do estabelecimento limpo
    """
    if not desc or not isinstance(desc, str):
        return ""
    
    text = desc.upper()
    
    # Remove prefixos genéricos (mas mantém "LOJA" que é parte do nome)
    prefixes = ["PIX", "TED", "DOC", "PAGAMENTO", "CARTAO", "CARTÃO", 
               "DEB", "CRED", "ENVIO", "ENVIADO", "COMPRA"]
    
    for prefix in prefixes:
        text = re.sub(f"\\b{prefix}\\b", '', text, flags=re.IGNORECASE)
    
    # Remove datas
    text = re.sub(r'\d{2}/\d{2}/\d{4}', '', text)
    
    # Remove símbolos
    text = re.sub(r'[-–—]', '', text)
    
    # Remove padrões de parcelas
    text = re.sub(r'[\(\[]\s*(\d{1,2})\s*/\s*(\d{1,2})\s*[\)\]]', '', text)
    
    # Remove espaços duplicados e converte para título
    text = re.sub(r'\s+', ' ', text).strip().title()
    
    return text


def validate_parcelas_consistency(no_parcela: int, total_parcelas: int) -> bool:
    """
    Valida se os números de parcelas são consistentes.
    
    Args:
        no_parcela: Número da parcela atual
        total_parcelas: Total de parcelas
        
    Returns:
        True se consistente, False caso contrário
    """
    return (
        1 <= no_parcela <= total_parcelas and
        total_parcelas <= 99 and
        no_parcela <= 99
    )


def get_rule_confidence(rule_name: str) -> float:
    """
    Retorna o nível de confiança padrão para uma regra específica.
    
    Args:
        rule_name: Nome da regra
        
    Returns:
        Float com nível de confiança entre 0.0 e 1.0
    """
    confidence_map = {
        "cc_prefix": 0.95,
        "casa_keyword": 0.90,
        "parcelas_pattern": 0.95,
        "titular_pattern": 0.85,
        "final_cartao": 0.80,
        "comp_rules": 0.90
    }
    
    return confidence_map.get(rule_name, 0.70)
