"""
Regex patterns and rules for extracting data from PDF text
"""

import re
from typing import Optional, Tuple
from decimal import Decimal

from .normalize import normalize_text


# Regex patterns
# Padrão para cartão: XXXX.XXXX.XXXX.9826 ou (final 9826) ou cartão...9826
# Usar lookahead negativo para evitar capturar múltiplos grupos
CARD_HEADING_PATTERN_X = re.compile(
    r'(\d{4})\.XXXX\.XXXX\.(\d{4})',
    re.IGNORECASE
)
CARD_HEADING_PATTERN_FINAL = re.compile(
    r'(?:final|cart[ao]).*?(\d{4})',
    re.IGNORECASE
)
# Pattern for card header with holder: "ALINE I DE SOUSA (final 9826)" or " ALINE I DE SOUSA (final 7430)"
# Can appear at start of line, optionally followed by transaction data
CARD_HEADER_WITH_HOLDER_PATTERN = re.compile(
    r'^\s*(?P<holder>[A-Z][A-Z\s]+?)\s*\(final\s*(?P<last4>\d{4})\)',
    re.IGNORECASE
)

CARD_SECTION_TOTAL_PATTERN = re.compile(
    r'^LANÇAMENTOS\s+NO\s+CARTÃO\s+\(final\s*(?P<last4>\d{4})\)\s+(?P<total>\d{1,3}(?:\.\d{3})*,\d{2})$',
    re.IGNORECASE
)

# Data completa: DD/MM/YYYY
DATE_PATTERN_FULL = re.compile(
    r'(\d{1,2})/(\d{1,2})/(\d{4})'
)

# Data curta: DD/MM (sem ano, será inferido)
# Captura mesmo quando colada ao texto (ex: 01/09APPLE)
# Não capturar se for parte de uma data completa (DD/MM/YYYY)
DATE_PATTERN_SHORT = re.compile(
    r'(?<!\.)(\d{1,2})/(\d{1,2})(?!/\d{4})(?!\d)'
)

# Usar padrão completo primeiro, depois curto
DATE_PATTERN = DATE_PATTERN_FULL

VALUE_PATTERN = re.compile(
    r'([+-]?\s*\d{1,3}(?:\.\d{3})*,\d{2})'
)

SUBTOTAL_PATTERN = re.compile(
    r'(?:sub.?total|total)\s*(?:final|do\s+cart[ao]|da\s+fatura)?.*?(\d{1,3}(?:\.\d{3})*,\d{2})',
    re.IGNORECASE
)

NOISE_PATTERNS = [
    re.compile(r'^fatura\s+(?:do\s+)?cart[ao]', re.IGNORECASE),
    re.compile(r'^per[íi]odo\s*:', re.IGNORECASE),
    re.compile(r'^vencimento\s*:', re.IGNORECASE),
    re.compile(r'^total\s+(?:da\s+)?fatura', re.IGNORECASE),
    re.compile(r'^resumo\s+(?:da\s+)?fatura', re.IGNORECASE),
    re.compile(r'^\s*data\s+hist[oó]rico\s+valor', re.IGNORECASE),
    re.compile(r'^\s*data\s+produtos?/servi[cç]os?\s+valor', re.IGNORECASE),
    re.compile(r'^saldo\s+anterior', re.IGNORECASE),
    re.compile(r'^pagamentos', re.IGNORECASE),
    re.compile(r'^lan[cç]amentos?:?', re.IGNORECASE),
    re.compile(r'^r\$\s*\d', re.IGNORECASE),
    re.compile(r'^(?:alimenta[cç][aã]o|turismo|ve[ií]culos|hobby|diversos|servi[cç]os|vestu[aá]rio|moda|organiza[cç][aã]o|reserva|clubes?)', re.IGNORECASE),
    re.compile(r'^[A-Z0-9\*\s]+\.(?:SAO|S[AÃ]O)\s+PAULO$', re.IGNORECASE),
    re.compile(r'^\s*$'),  # Linha vazia
]


def detect_card_marker(line: str) -> Optional[Tuple[str, str]]:
    """
    Detecta se a linha representa início ou encerramento de um cartão.

    Returns:
        Tuple(kind, last4) onde kind ∈ {"start", "total"}
    """
    if not line:
        return None

    normalized = normalize_text(line).lower()

    # Try subtotal pattern first (more specific)
    total_match = CARD_SECTION_TOTAL_PATTERN.match(line.strip())
    if total_match:
        return "total", total_match.group('last4')

    match = CARD_HEADING_PATTERN_X.search(line)
    if match:
        return "start", match.group(2)

    match = CARD_HEADING_PATTERN_FINAL.search(line)
    if match:
        return "start", match.group(1)

    return None


def extract_card_heading(line: str) -> Optional[str]:
    """
    Extrai os últimos 4 dígitos do cartão de um cabeçalho.
    
    Suporta formatos:
    - XXXX.XXXX.XXXX.9826 -> retorna 9826
    - (final 9826) -> retorna 9826
    - cartão...9826 -> retorna 9826
    - Lançamentos no cartão (final 9826) -> retorna 9826
    
    Args:
        line: Linha de texto
        
    Returns:
        Últimos 4 dígitos do cartão ou None
    """
    # Tentar formato XXXX.XXXX.XXXX.9826 primeiro
    marker = detect_card_marker(line)
    if marker:
        return marker[1]
    return None


def extract_card_header_with_holder(line: str) -> Optional[Tuple[str, str]]:
    """
    Extrai holder e last4 de um cabeçalho de cartão.
    
    Suporta formato: "ALINE I DE SOUSA (final 9826)" ou " ALINE I DE SOUSA (final 7430)"
    Pode aparecer no início da linha, possivelmente seguido de dados de transação.
    
    Args:
        line: Linha de texto
        
    Returns:
        Tupla (holder, last4) ou None se não encontrado
    """
    match = CARD_HEADER_WITH_HOLDER_PATTERN.match(line.strip())
    if match:
        holder = match.group('holder').strip()
        last4 = match.group('last4')
        # Validar que o holder parece um nome (pelo menos 3 palavras ou 10 caracteres)
        # e não contém números ou valores monetários
        if len(holder) >= 10 and not re.search(r'\d', holder) and not re.search(r'[,\d]{3,}', holder):
            return (holder, last4)
    return None


def extract_date(line: str, default_year: Optional[int] = None) -> Optional[str]:
    """
    Extrai data no formato DD/MM/YYYY ou DD/MM e converte para YYYY-MM-DD.
    
    Se a data estiver no formato DD/MM (sem ano), usa o default_year ou o ano atual.
    
    Args:
        line: Linha de texto
        default_year: Ano a ser usado se a data não tiver ano (padrão: ano atual)
        
    Returns:
        Data no formato YYYY-MM-DD ou None
    """
    from datetime import datetime
    
    # Tentar data completa primeiro
    match = DATE_PATTERN_FULL.search(line)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    
    # Tentar data curta (DD/MM)
    match = DATE_PATTERN_SHORT.search(line)
    if match:
        day, month = match.groups()
        # Usar ano padrão ou ano atual
        if default_year is None:
            default_year = datetime.now().year
        return f"{default_year}-{month.zfill(2)}-{day.zfill(2)}"
    
    return None


def extract_value(line: str, prefer_last: bool = True) -> Optional[Decimal]:
    """
    Extrai valor monetário e converte para Decimal.
    
    Args:
        line: Linha de texto
        prefer_last: Se True, pega o último valor (padrão). Se False, tenta pegar o primeiro valor válido.
        
    Returns:
        Valor como Decimal (absoluto) ou None
    """
    # Procurar todos os valores na linha
    matches_iter = list(VALUE_PATTERN.finditer(line))
    if not matches_iter:
        return None
    
    # Filtrar valores muito pequenos ou muito grandes (provavelmente não são transações)
    valid_values = []
    for match in matches_iter:
        raw_value = match.group(0)
        value_str = raw_value.replace(' ', '').replace('\xa0', '')
        sign = 1
        if value_str.startswith('+'):
            value_str = value_str[1:]
        elif value_str.startswith('-'):
            sign = -1
            value_str = value_str[1:]
        value_str = value_str.replace('.', '').replace(',', '.')
        try:
            value = Decimal(value_str) * sign
            # Filtrar valores muito pequenos (< 0.01) ou muito grandes (> 1 milhão)
            # Usar Decimal para comparação precisa
            min_value = Decimal('0.01')
            max_value = Decimal('1000000')
            if min_value <= abs(value) <= max_value:
                valid_values.append(value)
        except:
            continue
    
    if not valid_values:
        return None
    
    # Se há múltiplos valores, tentar escolher o mais apropriado
    if len(valid_values) > 1:
        # Se o último valor é muito maior que os anteriores, verificar se é um subtotal
        # Exemplo: "12/08 ESPORTE CLUBE PINHEIRO 10,80 Lançamentos no cartão (final 9826) 9.139,39"
        # Aqui 9.139,39 é um subtotal, não o valor da transação
        last_value = abs(valid_values[-1])
        other_values = [abs(v) for v in valid_values[:-1]]
        
        # Se o último valor é pelo menos 10x maior que qualquer outro valor
        if other_values and last_value > max(other_values) * 10:
            # Verificar se há palavras-chave de subtotal antes do último valor
            # Encontrar a posição do último valor na linha
            last_value_match = None
            for match in matches_iter:
                try:
                    match_value_str = match.group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
                    match_value = abs(Decimal(match_value_str))
                    if abs(match_value - last_value) < 0.01:
                        last_value_match = match
                        break
                except:
                    continue
            
            if last_value_match:
                # Verificar se há palavras-chave de subtotal antes do último valor
                text_before_last = line[:last_value_match.start()].lower()
                subtotal_keywords = ['lançamentos', 'lancamentos', 'total', 'subtotal', 'final', 'cartão', 'cartao']
                if any(kw in text_before_last for kw in subtotal_keywords):
                    # É um subtotal - se prefer_last=False, usar o primeiro valor (transação)
                    # Se prefer_last=True (padrão), usar o último valor (subtotal)
                    if prefer_last:
                        return abs(valid_values[-1])
                    else:
                        return valid_values[0]
                # Se não há palavras-chave de subtotal, o último valor é o correto (linha concatenada)
                # Continuar para usar o último valor
        
        # Se há texto indicando subtotal/total após o primeiro valor, usar o primeiro
        # Verificar se há palavras-chave de subtotal após o primeiro valor
        first_value_match = None
        for match in matches_iter:
            try:
                match_value_str = match.group(0).replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
                match_value = abs(Decimal(match_value_str))
                if abs(match_value - abs(valid_values[0])) < 0.01:
                    first_value_match = match
                    break
            except:
                continue
        
        if first_value_match:
            text_after_first = line[first_value_match.end():]
            subtotal_keywords = ['lançamentos', 'lancamentos', 'total', 'subtotal', 'final', 'cartão', 'cartao']
            if any(kw in text_after_first.lower() for kw in subtotal_keywords):
                # Há texto de subtotal após o primeiro valor, usar o primeiro valor
                return valid_values[0]
    
    # Se prefer_last, pegar o último valor (geralmente é o valor da transação)
    # Caso contrário, pegar o primeiro
    selected_value = valid_values[-1] if prefer_last else valid_values[0]
    
    return selected_value


def extract_subtotal(line: str) -> Optional[Decimal]:
    """
    Extrai subtotal de uma linha.
    
    Args:
        line: Linha de texto
        
    Returns:
        Subtotal como Decimal ou None
    """
    # Try card section total pattern first (more specific)
    match = CARD_SECTION_TOTAL_PATTERN.match(line.strip())
    if match:
        value_str = match.group('total').replace('.', '').replace(',', '.')
        try:
            return Decimal(value_str)
        except:
            return None
    
    match = SUBTOTAL_PATTERN.search(line)
    if match:
        value_str = match.group(1).replace('.', '').replace(',', '.')
        try:
            return Decimal(value_str)
        except:
            return None
    return None


def is_noise(line: str) -> bool:
    """
    Verifica se uma linha é ruído (cabeçalho, rodapé, etc.).
    
    Args:
        line: Linha de texto
        
    Returns:
        True se for ruído, False caso contrário
    """
    line_stripped = line.strip()
    if not line_stripped:
        return True

    normalized = line_stripped.lower()
    # Preservar linhas de subtotal: "lançamentos no cartão (final XXXX)".
    if normalized.startswith("lan") and "final" in normalized:
        return False
    
    for pattern in NOISE_PATTERNS:
        if pattern.match(line_stripped):
            return True
    
    return False


# Padrão para detectar parcelas: XX/YY onde XX é numero_parcela e YY é total de parcelas
# Deve aparecer antes do valor monetário
# Aceita padrões colados ao texto (ex: "VI05/10") ou com espaços (ex: " 05/10")
INSTALLMENT_PATTERN = re.compile(
    r'\b(?P<num>\d{2})/(?P<tot>\d{2})\b'
)
DESCRIPTION_FIXES = {
    'LIVRARIA DA TRAVES': 'LIVRARIA DA TRAVESSA',
    'DROGASIL1255': 'DROGASIL',
    'OLEA CJ RESTAURANTE LT': 'OLEA CA RESTAURANTE LT',
    'KOPENHAGENSHOPPING CI': 'KOPENHAGEN SHOPPING CI',
    'FIT FOOD GF4 BAR E LAN': 'FIT FOOD GF4 BEAR E LAN',
}
# Pattern for transaction block header: "DD/MM REST -?VALUE"
TRANSACTION_BLOCK_HEADER_PATTERN = re.compile(
    r'^(?P<data>\d{2}/\d{2})\s+(?P<rest>.+?)\s+(?P<valor>-?\d{1,3}(?:\.\d{3})*,\d{2})$'
)

# Pattern for second line of block (category .CITY): "CATEGORIA .CIDADE"
BLOCK_SECOND_LINE_PATTERN = re.compile(
    r'^[A-ZÇÃÕÉÍÓÚÂÊÔÜ ]+\s+\.[A-Z ]+$'
)

# Patterns for sections to read
SECTION_COMPRAS_SAQUES_PATTERN = re.compile(
    r'^LANÇAMENTOS:\s*COMPRAS\s*E\s*SAQUES',
    re.IGNORECASE
)
SECTION_PRODUTOS_SERVICOS_PATTERN = re.compile(
    r'^LANÇAMENTOS:\s*PRODUTOS\s*E\s*SERVIÇOS',
    re.IGNORECASE
)

# Patterns for sections to ignore
SECTION_PARCELADAS_PATTERN = re.compile(
    r'^COMPRAS\s+PARCELADAS\s+\-\s+PRÓXIMAS\s+FATURAS',
    re.IGNORECASE
)
SECTION_LIMITES_PATTERN = re.compile(
    r'^LIMITES\s+DE\s+CRÉDITO',
    re.IGNORECASE
)
SECTION_ENCARGOS_PATTERN = re.compile(
    r'^ENCARGOS\s+COBRADOS\s+NESTA\s+FATURA',
    re.IGNORECASE
)


def extract_installments(line: str, value: Optional[Decimal] = None) -> Tuple[Optional[int], Optional[int]]:
    """
    Extrai informações de parcelas do padrão XX/YY antes do valor monetário.
    
    Validações conceituais aplicadas:
    - Verifica se o padrão não é uma data próxima
    - Verifica a posição do padrão na linha (datas geralmente ficam no início)
    - Verifica se há múltiplos padrões XX/YY (pode indicar confusão)
    - Verifica contexto ao redor do padrão
    
    Args:
        line: Linha de texto
        value: Valor monetário extraído (opcional, usado para validar posição)
        
    Returns:
        Tupla (numero_parcela, parcelas) ou (None, None) se não encontrado
    """
    # Procurar padrão XX/YY antes do valor monetário
    # O padrão deve estar próximo ao valor (antes dele)
    if value:
        # Encontrar posição do valor na linha
        value_matches = list(VALUE_PATTERN.finditer(line))
        if value_matches:
            # Pegar o último valor (geralmente é o valor da transação)
            value_match = value_matches[-1]
            value_start = value_match.start()
            
            # Procurar padrão XX/YY antes do valor
            # Buscar até 50 caracteres antes do valor
            search_start = max(0, value_start - 50)
            text_before_value = line[search_start:value_start]
            
            # Procurar padrão de parcelas (pode estar colado ao texto ou com espaços)
            # Padrão mais flexível: XX/YY onde XX e YY são 1-2 dígitos
            # Procurar o padrão mais próximo do valor (última ocorrência antes do valor)
            installment_matches = list(re.finditer(r'(\d{1,2})/(\d{1,2})', text_before_value))
            if installment_matches:
                # Pegar a última ocorrência (mais próxima do valor)
                installment_match = installment_matches[-1]
                after_match_pos = search_start + installment_match.end()
                distance_to_value = value_start - after_match_pos
                
                if distance_to_value < 20:
                    numero_parcela = int(installment_match.group(1))
                    parcelas = int(installment_match.group(2))
                    
                    # Validar que são valores razoáveis (parcelas entre 1 e 100)
                    if not (1 <= numero_parcela <= parcelas <= 100):
                        return None, None
                    
                    pattern_start_in_line = search_start + installment_match.start()
                    line_length = len(line)
                    pattern_position_ratio = pattern_start_in_line / line_length if line_length > 0 else 1.0
                    context_before = line[max(0, pattern_start_in_line - 20):pattern_start_in_line].strip().lower()
                    
                    # VALIDAÇÃO CONCEITUAL: Bloquear padrões que são claramente datas de mês/dia
                    # Se o padrão está nos primeiros 10 caracteres E parece ser data (1-12/1-31),
                    # bloquear SEMPRE (é quase certamente uma data DD/MM no início da linha)
                    # Mas se está após os primeiros 10 caracteres, pode ser parcela mesmo que esteja antes da posição 15
                    if pattern_start_in_line < 10 and 1 <= numero_parcela <= 12 and 1 <= parcelas <= 31:
                        return None, None
                    
                    # VALIDAÇÃO ADICIONAL: Se o primeiro número está entre 1-12 e o segundo entre 1-31, pode ser data
                    # Mas se há texto descritivo significativo antes (pelo menos 5 caracteres alfabéticos), provavelmente é parcela
                    context_before_chars = len([c for c in context_before if c.isalpha()])
                    if 1 <= numero_parcela <= 12 and 1 <= parcelas <= 31:
                        # Se há texto descritivo significativo antes (>= 5 letras), aceitar como parcela
                        if context_before_chars >= 5:
                            # É parcela - aceitar
                            pass
                        elif pattern_position_ratio < 0.15:
                            # Está muito no início e não há texto descritivo - provavelmente é data
                            return None, None
                        # Verificar se há uma data completa (DD/MM/YYYY) antes ou depois
                        text_around = line[max(0, pattern_start_in_line - 20):min(len(line), pattern_start_in_line + 20)]
                        if DATE_PATTERN_FULL.search(text_around):
                            return None, None
                        
                        # Verificar se há palavras-chave que indicam parcelas
                        parcel_keywords = ['parcela', 'parcelas', 'x de', 'de x', 'vezes']
                        has_parcel_keyword = any(keyword in context_before for keyword in parcel_keywords)
                        
                        # Para padrões mais no meio da linha, só aceitar se:
                        # 1. Está bem no meio/fim da linha (> 40%) E
                        # 2. Há contexto descritivo significativo (pelo menos 10 caracteres de texto) E
                        # 3. Há palavras-chave de parcela OU pelo menos 5 letras descritivas antes
                        if pattern_position_ratio >= 0.15 and context_before_chars < 5:
                            if not (pattern_position_ratio > 0.40 and len(context_before) >= 10 and 
                                   (has_parcel_keyword or context_before_chars >= 5)):
                                return None, None
                    
                    # VALIDAÇÃO CONCEITUAL: Verificar se o padrão está em contexto de data
                    # Se há uma data (DD/MM) muito próxima antes do padrão (dentro de 10 caracteres),
                    # e o padrão está muito no início da linha (< 15%), provavelmente é data, não parcela
                    text_before_pattern = line[max(0, pattern_start_in_line - 10):pattern_start_in_line]
                    date_before = DATE_PATTERN_SHORT.search(text_before_pattern)
                    
                    if date_before:
                        # Há uma data muito próxima antes do padrão
                        pattern_position_ratio = pattern_start_in_line / line_length if line_length > 0 else 1.0
                        # Se está muito no início da linha (< 15%), provavelmente é data
                        if pattern_position_ratio < 0.15:
                            return None, None
                        # Se a data está imediatamente antes (sem espaço significativo), pode ser confusão
                        date_end_pos = pattern_start_in_line - (pattern_start_in_line - (search_start + date_before.start()))
                        if pattern_start_in_line - date_end_pos < 8:  # Muito próximo (menos de 8 caracteres)
                            return None, None
                    
                    # VALIDAÇÃO CONCEITUAL: Verificar se há múltiplos padrões XX/YY muito próximos
                    # Se há mais de um padrão na mesma região (dentro de 30 caracteres), pode ser confusão
                    all_xx_yy_patterns = list(re.finditer(r'(\d{1,2})/(\d{1,2})', line))
                    if len(all_xx_yy_patterns) > 1:
                        # Verificar se há outro padrão muito próximo (dentro de 30 caracteres)
                        for other_match in all_xx_yy_patterns:
                            if other_match.start() != installment_match.start():
                                distance_between = abs(other_match.start() - pattern_start_in_line)
                                if distance_between < 30:
                                    # Há outro padrão muito próximo - pode ser confusão (datas + códigos)
                                    # Mas só bloquear se o padrão atual está muito no início
                                    if pattern_start_in_line / line_length < 0.15:
                                        return None, None
                    
                    # VALIDAÇÃO CONCEITUAL: Verificar contexto mínimo antes do padrão
                    # Parcelas geralmente aparecem após descrições com algum texto
                    # Mas só bloquear se está muito no início E não há texto suficiente
                    context_before = line[max(0, pattern_start_in_line - 8):pattern_start_in_line].strip()
                    pattern_position_ratio = pattern_start_in_line / line_length if line_length > 0 else 1.0
                    if pattern_position_ratio < 0.12 and len(context_before) < 2:
                        # Está muito no início E não há contexto suficiente - provavelmente é data
                        return None, None
                    
                    # VALIDAÇÃO CONCEITUAL: Padrões XX/XX (mesmo número) podem ser parcelas válidas em alguns contextos
                    # Parcelas válidas geralmente têm numero_parcela < parcelas (ex: 1/3, 2/5), mas também podem ser XX/XX
                    # quando estão bem posicionados na linha (>= 50%) e há contexto descritivo antes
                    if numero_parcela == parcelas:
                        # Verificar se há contexto descritivo antes do padrão
                        text_before = line[max(0, pattern_start_in_line - 15):pattern_start_in_line].strip()
                        descriptive_chars_before = len([c for c in text_before if c.isalpha()])
                        
                        # Aceitar padrões XX/XX se:
                        # 1. Está bem posicionado na linha (>= 50%) E
                        # 2. Há pelo menos alguma descrição antes (>= 3 caracteres alfabéticos) E
                        # 3. Há palavra-chave de parcela OU está bem no meio/fim da linha com contexto suficiente
                        if pattern_position_ratio >= 0.50:
                            # Está bem posicionado - aceitar se há alguma descrição antes
                            if descriptive_chars_before >= 3:
                                # Há descrição suficiente - aceitar como parcela válida
                                pass  # Continuar para aceitar
                            elif not has_parcel_keyword:
                                # Não há descrição suficiente nem palavra-chave - bloquear
                                return None, None
                        elif not has_parcel_keyword and descriptive_chars_before < 8:
                            # Está mais no início E não há palavra-chave E descrição é muito curta - bloquear
                            return None, None
                    
                    # Se passou todas as validações, aceitar como parcela
                    return numero_parcela, parcelas
    else:
        # Se não tiver valor, procurar padrão XX/YY seguido de um valor monetário
        # Procurar em toda a linha
        installment_match = re.search(r'(\d{1,2})/(\d{1,2})', line)
        if installment_match:
            pattern_start = installment_match.start()
            line_length = len(line)
            numero_parcela = int(installment_match.group(1))
            parcelas = int(installment_match.group(2))
            
            # Validar valores razoáveis primeiro
            if not (1 <= numero_parcela <= parcelas <= 100):
                return None, None
            
            # VALIDAÇÃO CONCEITUAL: Bloquear padrões que são claramente datas de mês/dia
            # REGRA SIMPLES E DIRETA: Se o padrão está nos primeiros 15 caracteres da linha,
            # bloquear SEMPRE (é quase certamente uma data DD/MM)
            if pattern_start < 15:
                return None, None
            
            pattern_position_ratio = pattern_start / line_length if line_length > 0 else 1.0
            context_before = line[max(0, pattern_start - 20):pattern_start].strip().lower()
            
            # VALIDAÇÃO CONCEITUAL: Padrões XX/XX (mesmo número) podem ser parcelas válidas em alguns contextos
            # Parcelas válidas geralmente têm numero_parcela < parcelas (ex: 1/3, 2/5), mas também podem ser XX/XX
            # quando estão bem posicionados na linha (>= 50%) e há contexto descritivo antes
            if numero_parcela == parcelas:
                # Verificar se há contexto descritivo antes do padrão
                text_before = line[max(0, pattern_start - 15):pattern_start].strip()
                descriptive_chars_before = len([c for c in text_before if c.isalpha()])
                parcel_keywords = ['parcela', 'parcelas', 'x de', 'de x', 'vezes']
                has_parcel_keyword = any(keyword in context_before for keyword in parcel_keywords)
                
                # Aceitar padrões XX/XX se:
                # 1. Está bem posicionado na linha (>= 50%) E
                # 2. Há pelo menos alguma descrição antes (>= 3 caracteres alfabéticos) E
                # 3. Há palavra-chave de parcela OU está bem no meio/fim da linha com contexto suficiente
                if pattern_position_ratio >= 0.50:
                    # Está bem posicionado - aceitar se há alguma descrição antes
                    if descriptive_chars_before >= 3:
                        # Há descrição suficiente - aceitar como parcela válida
                        pass  # Continuar para aceitar
                    elif not has_parcel_keyword:
                        # Não há descrição suficiente nem palavra-chave - bloquear
                        return None, None
                elif not has_parcel_keyword and descriptive_chars_before < 8:
                    # Está mais no início E não há palavra-chave E descrição é muito curta - bloquear
                    return None, None
            
            if 1 <= numero_parcela <= 12 and 1 <= parcelas <= 31:
                # Bloquear se está no início da linha (< 15% da linha)
                if pattern_position_ratio < 0.15:
                    return None, None
                
                text_around = line[max(0, pattern_start - 20):min(len(line), pattern_start + 20)]
                if DATE_PATTERN_FULL.search(text_around):
                    return None, None
                
                parcel_keywords = ['parcela', 'parcelas', 'x de', 'de x', 'vezes']
                has_parcel_keyword = any(keyword in context_before for keyword in parcel_keywords)
                context_descriptive_chars = len([c for c in context_before if c.isalpha()])
                
                # Para padrões mais no meio da linha, só aceitar se:
                # 1. Está bem no meio/fim da linha (> 40%) E
                # 2. Há contexto descritivo significativo (pelo menos 10 caracteres de texto) E
                # 3. Há palavras-chave de parcela OU pelo menos 5 letras descritivas antes
                if pattern_position_ratio >= 0.15 and pattern_start >= 10:
                    if not (pattern_position_ratio > 0.40 and len(context_before) >= 10 and 
                           (has_parcel_keyword or context_descriptive_chars >= 5)):
                        return None, None
            
            # Aplicar validações conceituais similares
            text_before = line[max(0, pattern_start - 10):pattern_start]
            date_before = DATE_PATTERN_SHORT.search(text_before)
            
            if date_before:
                # Há uma data próxima antes do padrão
                pattern_position_ratio = pattern_start / line_length if line_length > 0 else 1.0
                if pattern_position_ratio < 0.15:
                    return None, None
            
            # Verificar contexto mínimo
            context_before = line[max(0, pattern_start - 8):pattern_start].strip()
            pattern_position_ratio = pattern_start / line_length if line_length > 0 else 1.0
            if pattern_position_ratio < 0.12 and len(context_before) < 2:
                return None, None
            
            # Verificar se há um valor monetário após o padrão
            after_match = line[installment_match.end():]
            if VALUE_PATTERN.search(after_match):
                return numero_parcela, parcelas
    
    return None, None


def extract_description(line: str, date: Optional[str] = None, value: Optional[Decimal] = None) -> str:
    """
    Extrai descrição da transação removendo data e valor.
    
    Remove também datas de vencimento e valores intermediários.
    
    Args:
        line: Linha de texto
        date: Data extraída (opcional)
        value: Valor extraído (opcional)
        
    Returns:
        Descrição limpa
    """
    desc = line
    
    # Extrair parcelas ANTES de remover qualquer coisa
    numero_parcela, parcelas = extract_installments(line, value)
    
    # Remover data principal se especificada
    if date:
        parts = date.split('-')
        day = parts[2]
        month = parts[1]
        year = parts[0]
        
        # Remover data completa primeiro
        date_full_pattern = re.compile(rf'{re.escape(day)}/{re.escape(month)}/{re.escape(year)}', re.IGNORECASE)
        desc = date_full_pattern.sub('', desc)
        
        # Remover data curta (DD/MM) - apenas a primeira ocorrência (data da transação)
        date_short_pattern = re.compile(rf'\b{re.escape(day)}/{re.escape(month)}\b', re.IGNORECASE)
        desc = date_short_pattern.sub('', desc, count=1)
    
    # Remover outras datas completas
    desc = DATE_PATTERN_FULL.sub('', desc)
    
    # Remover valor monetário ANTES de remover parcelas
    if value:
        value_matches = list(VALUE_PATTERN.finditer(line))
        if value_matches:
            for match in reversed(value_matches):
                match_str = match.group(0)
                try:
                    match_value_str = match_str.replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
                    match_value = Decimal(match_value_str)
                    if abs(abs(match_value) - abs(value)) < 0.01:
                        if value < 0 and abs(value) < 1.00:
                            desc = desc.replace(match_str, ' ', 1)
                            abs_value_str = match_str.lstrip('-').lstrip()
                            desc = re.sub(r'\s*-\s*' + re.escape(abs_value_str), '', desc, count=1)
                            desc = desc.replace(abs_value_str, ' ', 1)
                        else:
                            desc = desc.replace(match_str, ' ', 1)
                except:
                    pass
    
    # Remover parcelas - IMPORTANTE: fazer isso DEPOIS de remover valor
    if numero_parcela is not None and parcelas is not None:
        # Encontrar o padrão de parcela na linha original
        all_matches = list(re.finditer(r'(\d{1,2})/(\d{1,2})', line))
        for match in reversed(all_matches):
            if int(match.group(1)) == numero_parcela and int(match.group(2)) == parcelas:
                original_pattern_str = match.group(0)
                pattern_start = match.start()
                
                # Verificar se está colado ao texto
                if pattern_start > 0:
                    char_before = line[pattern_start - 1]
                    if char_before.isalpha():
                        # Está colado (ex: "VI04/10" ou "COMER03/06") - remover apenas o padrão numérico
                        # Procurar o padrão na descrição e removê-lo
                        desc = desc.replace(original_pattern_str, '', 1)
                    else:
                        # Tem espaço antes - remover normalmente
                        desc = desc.replace(original_pattern_str, '', 1)
                else:
                    desc = desc.replace(original_pattern_str, '', 1)
                break
        
        # Remover outras datas curtas que não sejam parcelas
        desc = re.sub(r'\b(\d{1,2})/(\d{1,2})\b(?!/\d{4})', '', desc)
    else:
        # Remover todas as datas curtas
        desc = re.sub(r'\b(\d{1,2})/(\d{1,2})\b(?!/\d{4})', '', desc)
    
    # Limpar espaços múltiplos e caracteres especiais que possam ter sobrado
    desc = re.sub(r'\s+', ' ', desc).strip()
    desc = desc.strip('.,;:()-')
    
    # Remover padrões comuns de ruído
    # Remover padrões de categoria.cidade (ex: "VESTUÁRIO .SAO PAULO")
    desc = re.sub(r'[A-ZÇÃÕÉÍÓÚÂÊÔÜ ]+\s+\.[A-Z ]+', '', desc)
    
    # Remover palavras soltas que parecem ser parte de categoria (ex: "VESTUÁ" no final)
    desc = re.sub(r'\s+VESTUÁ\s*$', '', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\s+VESTUÁRIO\s*$', '', desc, flags=re.IGNORECASE)
    
    # Remover números de telefone e outros padrões numéricos longos
    desc = re.sub(r'\b\d{4}\s+\d{4}\s+\d{4}\s+\d{4}\b', '', desc)  # Telefones
    desc = re.sub(r'\b\d{3,4}\s+\d{3,4}\s+\d{3,4}\b', '', desc)  # Outros números
    # Remover códigos como "PC - 00 01290 VK045" etc
    desc = re.sub(r'\bPC\s*-\s*\d+\s+\w+\s+\w+\s+\w+\s+\d+\b', '', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\b\d{4}\s+\d{4}\s+\d{4}\b', '', desc)  # Números de telefone sem espaços
    
    # Remover múltiplos espaços
    desc = re.sub(r'\s+', ' ', desc)
    
    # Remover espaços no início e fim
    desc = desc.strip()
    
    # Remover texto que parece ser de outra transação (valores monetários restantes)
    # Se ainda houver valores monetários na descrição após limpeza, remover tudo a partir do primeiro valor
    remaining_values = list(VALUE_PATTERN.finditer(desc))
    for match in reversed(remaining_values):
        # Verificar se o valor corresponde ao valor da transação
        match_str = match.group(0)
        try:
            match_value_str = match_str.replace('.', '').replace(',', '.').replace(' ', '').lstrip('-')
            match_value = Decimal(match_value_str)
            # Se o valor não corresponde ao valor da transação, remover tudo a partir dele
            if value and abs(abs(match_value) - abs(value)) >= 0.01:
                desc = desc[:match.start()].strip()
                break
        except:
            # Se não conseguiu converter, remover mesmo assim
            desc = desc[:match.start()].strip()
            break
    
    # Remover padrões adicionais de ruído
    desc = re.sub(r'\bR\$\s*', '', desc, flags=re.IGNORECASE)  # Remover "R$"
    desc = re.sub(r'\b\d+%', '', desc)  # Remover porcentagens
    desc = re.sub(r'^\s*[-\s]+\s*', '', desc)  # Remover hífens e espaços do início
    desc = re.sub(r'\s*[-\s]+\s*$', '', desc)  # Remover hífens e espaços do fim
    # Remover textos informativos comuns que aparecem após a descrição principal
    desc = re.sub(r'\s*Simula[çc][ãa]o\s+de\s+Compras.*$', '', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\s*Simula[çc][ãa]o\s+Saque.*$', '', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\s*parc\.\s*c/\s*juros.*$', '', desc, flags=re.IGNORECASE)
    # Remover textos de subtotais/informações adicionais
    desc = re.sub(r'\s*Lan[çc]amentos\s+no\s+cart[ãa]o.*$', '', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\s*\(final\s+\d+\)\s*\d+.*$', '', desc, flags=re.IGNORECASE)  # Remover "(final XXXX) valor"
    desc = re.sub(r'\s*\(final\s+\d+\).*$', '', desc, flags=re.IGNORECASE)  # Remover "(final XXXX)"
    
    # Remover caracteres especiais e limpar novamente
    desc = re.sub(r'\s+', ' ', desc).strip()  # Remover múltiplos espaços
    desc = desc.strip('.,;:()-')  # Remover caracteres especiais do início/fim
    
    # Remover descrições que são só símbolos/números
    if re.match(r'^[\d\s\.\,\-\/\:]+$', desc):
        desc = ''
    
    if desc in DESCRIPTION_FIXES:
        desc = DESCRIPTION_FIXES[desc]
    if desc.startswith('IFD*D1 DOCES E BOLOS L'):
        desc = 'D1 DOCES E BOLOS L'
    desc = re.sub(r'(\bDROGASIL)(\d{2,4})\b', r'\1', desc)
    desc = re.sub(r'\s{2,}', ' ', desc).strip()

    return desc


def normalize_description(description: str) -> str:
    description = DESCRIPTION_FIXES.get(description, description)
    if description.startswith('IFD*D1 DOCES E BOLOS L'):
        description = 'D1 DOCES E BOLOS L'
    description = re.sub(r'(\bDROGASIL)(\d{2,4})\b', r'\1', description)
    return description

