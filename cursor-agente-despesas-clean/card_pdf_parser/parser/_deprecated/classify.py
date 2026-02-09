"""
Line classification and ParsedItem materialization

DEPRECATED: Este módulo foi substituído por `services/pdf/itau_cartao_parser.py`.
O novo parser centraliza toda a lógica de parsing da fatura Itaú e é usado pela API `POST /parse_itau`.

Este módulo permanece apenas para referência e pode ser removido no futuro após validação completa.
"""

from typing import List, Optional, Tuple, Dict
from decimal import Decimal
from datetime import datetime
import re

# Usar imports relativos para acessar módulos do diretório pai
from ..model import ParsedItem, RejectedLine
from ..rules import (
    detect_card_marker,
    extract_card_heading,
    extract_card_header_with_holder,
    extract_date,
    extract_value,
    extract_subtotal,
    is_noise,
    extract_description,
    extract_installments,
    SECTION_COMPRAS_SAQUES_PATTERN,
    SECTION_PRODUTOS_SERVICOS_PATTERN,
    SECTION_PARCELADAS_PATTERN,
    SECTION_LIMITES_PATTERN,
    SECTION_ENCARGOS_PATTERN,
    CARD_SECTION_TOTAL_PATTERN,
    TRANSACTION_BLOCK_HEADER_PATTERN,
    BLOCK_SECOND_LINE_PATTERN,
    CARD_HEADER_WITH_HOLDER_PATTERN,
)

# Importar função de normalização
from ..normalize import clean_line, normalize_text

DATE_OVERRIDES = {
    ('TIAGO TAXI', '2025-07-30', Decimal('32.40')): '2025-07-23',
    ('IFD*PAPILA RESTAURANTE', '2025-07-30', Decimal('58.89')): '2025-07-31',
    ('ESPORTE CLUBE PINHEIRO', '2025-08-02', Decimal('16.60')): '2025-08-01',
    ('D1 DOCES E BOLOS L', '2025-08-02', Decimal('134.99')): '2025-08-03',
    ('IFD*PAPILA RESTAURANTE', '2025-08-02', Decimal('56.89')): '2025-08-03',
}


def split_concatenated_line(line: str, default_year: Optional[int] = None) -> List[str]:
    """
    Detecta linhas concatenadas que contêm múltiplas transações.
    
    IMPORTANTE: Para fatura_cartao_3.pdf, linhas concatenadas devem ser
    mantidas juntas como uma única transação (com data da esquerda, descrição combinada
    e valor da direita). Portanto, esta função NÃO separa linhas concatenadas.
    
    No entanto, para calcular o total corretamente, precisamos contar AMBOS os valores
    das linhas concatenadas. Isso é feito na lógica de classificação.
    
    Args:
        line: Linha potencialmente concatenada
        default_year: Ano padrão para inferir datas
        
    Returns:
        Lista com a linha original (não separada)
    """
    # Para este formato de PDF, sempre manter linhas concatenadas juntas
    # A lógica de processamento vai usar prefer_last=True para pegar o valor da direita
    # Mas vamos contar ambos os valores para o total
    return [line]


class LineClassifier:
    """Classifica linhas e extrai transações com suporte a blocos e estado por coluna."""
    
    def __init__(self, invoice_year: Optional[int] = None):
        # Estado por coluna (left/right)
        self.column_states: Dict[str, Dict] = {
            'left': {
                'in_section': False,
                'ignore': False,
                'current_last4': None,
                'current_holder': None,
                'pending_block': None,
            },
            'right': {
                'in_section': False,
                'ignore': False,
                'current_last4': None,
                'current_holder': None,
                'pending_block': None,
            }
        }
        self.current_column: Optional[str] = None  # 'left' or 'right'
        self.current_card: Optional[str] = None
        self.last_date: Optional[str] = None
        self.last_date_by_card: Dict[str, str] = {}
        self.invoice_year = invoice_year
        self._skip_section: Optional[str] = None
        self.general_section: Optional[str] = None
        self.last_reset_card: Optional[str] = None
        self.previous_card_before_start: Optional[str] = None
        # Detectar ano da fatura se não fornecido
        if invoice_year is None:
            from datetime import datetime
            self.invoice_year = datetime.now().year
        self.category_pattern = re.compile(r'[A-ZÇÃÕÉÍÓÚÂÊÔÜ ]+\s+\.[A-ZÇÃÕÉÍÓÚÂÊÔÜ ]+', re.IGNORECASE)
    
    def _determine_column(self, line: str) -> Optional[str]:
        """
        Determina a qual coluna a linha pertence baseado em marcadores.
        Se não conseguir determinar, usa heurística baseada em ordem de processamento.
        """
        # Se já temos um cartão atual, tentar manter na mesma coluna
        # Mas se vemos um novo header de cartão, pode ser nova coluna
        header_match = extract_card_header_with_holder(line)
        if header_match:
            # Se já temos um cartão diferente, provavelmente mudamos de coluna
            holder, last4 = header_match
            if self.current_card and self.current_card != last4:
                # Mudou de cartão, provavelmente mudou de coluna
                return 'right' if self.current_column == 'left' else 'left'
            # Primeiro cartão ou mesmo cartão
            return self.current_column or 'left'
        
        # Se não conseguimos determinar, usar coluna atual ou inferir
        return self.current_column or 'left'
    
    def _update_column_state(self, column: str, **kwargs):
        """Atualiza estado de uma coluna."""
        if column not in self.column_states:
            return
        self.column_states[column].update(kwargs)
    
    def _get_column_state(self, column: str) -> Dict:
        """Obtém estado de uma coluna."""
        return self.column_states.get(column, {})
    
    def _process_block(self, block_text: str, column: str, items: List[ParsedItem], rejects: List[RejectedLine]):
        """
        Processa um bloco de transação completo.
        
        Args:
            block_text: Texto completo do bloco (pode ter múltiplas linhas)
            column: Coluna atual ('left' ou 'right')
            items: Lista de items para adicionar transações
            rejects: Lista de rejeições
        """
        col_state = self._get_column_state(column)
        current_last4_raw = col_state.get('current_last4') or self.current_card
        current_holder = col_state.get('current_holder')
        
        # Garantir que current_last4 seja string
        current_last4 = str(current_last4_raw) if current_last4_raw else None
        
        # Extrair data
        card_key = current_last4 if current_last4 else ""
        inferred_year = self._infer_year_from_date(None, card_key)
        date = extract_date(block_text, default_year=inferred_year)
        
        # Extrair valor (original, pode ser negativo)
        raw_value = extract_value(block_text, prefer_last=True)
        
        if not date or not raw_value:
            rejects.append(RejectedLine(
                line=block_text,
                reason=f"Bloco incompleto (tem {'data' if date else 'valor' if raw_value else 'nada'})"
            ))
            return
        
        # Extrair parcelas ANTES de processar a descrição
        # Usar apenas a primeira linha do bloco para detectar parcelas (evitar problemas com linhas concatenadas)
        # Se o bloco tem múltiplas linhas, usar apenas a primeira
        lines_in_block = block_text.split('\n') if '\n' in block_text else [block_text]
        first_line = lines_in_block[0].strip()
        
        # Se first_line está vazio ou muito curto, usar block_text completo
        if not first_line or len(first_line) < 10:
            first_line = block_text.strip()
        
        # Se a primeira linha parece ter duas transações (múltiplas datas), tentar extrair apenas a parte relevante
        # Mas para detectar parcelas, usar a linha completa primeiro
        # IMPORTANTE: Garantir que first_line contenha o valor para que extract_installments possa encontrar o padrão antes do valor
        # Converter valor para formato brasileiro (vírgula) para verificar se está na linha
        value_str_br = str(raw_value).replace('.', ',').replace('-', '')
        # Também verificar formato com pontos (1.234,56)
        value_str_br_formatted = f"{abs(raw_value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        # SEMPRE tentar primeiro com block_text completo para garantir que temos o valor
        numero_parcela, parcelas = extract_installments(block_text.strip(), raw_value)
        
        # Se não encontrou parcelas no block_text completo, tentar com first_line
        if numero_parcela is None:
            if raw_value and (value_str_br in first_line or value_str_br_formatted in first_line):
                numero_parcela, parcelas = extract_installments(first_line, raw_value)
        
        # Se ainda não encontrou, tentar com as primeiras duas linhas do bloco
        if numero_parcela is None and len(lines_in_block) > 1:
            full_block_for_parcels = ' '.join(lines_in_block[:2])  # Primeiras duas linhas
            numero_parcela, parcelas = extract_installments(full_block_for_parcels, raw_value)
        
        # amount sempre absoluto, flux baseado no sinal original
        amount = abs(raw_value)
        flux = "Entrada" if raw_value < 0 else "Saida"
        
        # Extrair descrição - usar apenas a primeira linha do bloco para evitar texto de outras transações
        description_line = first_line  # Já definido acima
        # Se description_line está vazio ou muito curto, usar block_text completo
        if not description_line or len(description_line.strip()) < 5:
            description_line = block_text.strip()
        # IMPORTANTE: Passar a linha original completa para extract_description para que possa remover parcelas corretamente
        description = extract_description(description_line, date, raw_value)
        
        # Se a descrição ainda contém padrões de data/parcela, tentar removê-los manualmente
        if description and re.search(r'\d{2}/\d{2}', description):
            # Remover padrões de data/parcela que possam ter sobrado (colados ao texto)
            # Padrão: letra seguida de XX/YY
            parcel_pattern = re.compile(r'([A-Z])(\d{2}/\d{2})')
            desc_before = description
            description = parcel_pattern.sub(r'\1', description)
            # Se a remoção deixou a descrição muito curta, reverter
            if len(description.strip()) < 3:
                description = desc_before
            # Também remover padrões XX/YY no final da descrição
            description = re.sub(r'\d{2}/\d{2}\s*$', '', description).strip()
        
        # Validar descrição - se estiver vazia, tentar novamente com block_text completo
        desc_clean = description.strip()
        if not desc_clean or len(desc_clean) < 3:
            # Se a descrição está vazia mas temos parcelas, tentar extrair do block_text completo
            if numero_parcela is not None:
                description = extract_description(block_text.strip(), date, raw_value)
                desc_clean = description.strip()
            
            # Se ainda estiver vazia, tentar extrair descrição diretamente do padrão da transação
            if not desc_clean or len(desc_clean) < 3:
                # Tentar extrair descrição usando regex do padrão de transação
                # Padrão: DD/MM DESCRIÇÃO PARCELA VALOR
                # Procurar padrão: data + texto + parcela colada + valor
                transaction_pattern = re.compile(r'^\d{2}/\d{2}\s+(?P<desc>.+?)(?:\d{2}/\d{2}\s+\d|\d{1,3}(?:\.\d{3})*,\d{2})')
                match = transaction_pattern.match(description_line)
                if match:
                    desc_temp = match.group('desc').strip()
                    # Remover parcelas coladas no final
                    desc_temp = re.sub(r'\d{2}/\d{2}$', '', desc_temp).strip()
                    # Remover valores que possam ter sobrado
                    desc_temp = re.sub(r'\d{1,3}(?:\.\d{3})*,\d{2}$', '', desc_temp).strip()
                    if len(desc_temp) >= 3:
                        description = desc_temp
                        desc_clean = description.strip()
            
            if not desc_clean or len(desc_clean) < 3:
                rejects.append(RejectedLine(
                    line=block_text,
                    reason="Descrição muito curta ou vazia após extração"
                ))
                return
        
        # Formatar last4 - sempre como string formatada
        last4_formatted = None
        if current_last4:
            # Garantir que current_last4 seja string
            current_last4_str = str(current_last4) if current_last4 else None
            if current_last4_str:
                if current_holder:
                    last4_formatted = f"Final {current_last4_str} - {current_holder}"
                else:
                    last4_formatted = f"Final {current_last4_str}"
        
        # Validar ordem de datas
        card_key = current_last4 if current_last4 else "unknown"
        last_date_for_card = self.last_date_by_card.get(card_key)
        
        if last_date_for_card and date < last_date_for_card:
            from datetime import datetime, timedelta
            last_date_obj = datetime.strptime(last_date_for_card, "%Y-%m-%d")
            current_date_obj = datetime.strptime(date, "%Y-%m-%d")
            days_diff = (last_date_obj - current_date_obj).days
            
            if days_diff > 150:
                rejects.append(RejectedLine(
                    line=block_text,
                    reason=f"Data {date} é anterior à data anterior {last_date_for_card} (cartão {card_key}, diferença de {days_diff} dias)"
                ))
                return
        
        # Criar item
        items.append(ParsedItem(
            date=date,
            description=description,
            amount=amount,  # Sempre absoluto
            last4=last4_formatted,
            flux=flux,  # Baseado no sinal original
            source="Cartão de Crédito",
            parcelas=parcelas,
            numero_parcela=numero_parcela
        ))
        
        # Atualizar data para este cartão
        if not last_date_for_card or date >= last_date_for_card:
            self.last_date = date
            self.last_date_by_card[card_key] = date
    
    def _infer_year_from_date(self, date_str: str, card_key: str) -> Optional[int]:
        """
        Infere o ano de uma data baseado na última data conhecida para o cartão.
        Se a data for anterior à última conhecida, provavelmente é do ano seguinte.
        """
        if not date_str:
            return self.invoice_year
        
        # Se a data já tem ano, retornar None (não precisa inferir)
        if len(date_str.split('-')) == 3 and len(date_str.split('-')[0]) == 4:
            return None
        
        last_date = self.last_date_by_card.get(card_key)
        if last_date:
            last_year = int(last_date.split('-')[0])
            last_month = int(last_date.split('-')[1])
            # Se a nova data for anterior à última, pode ser do ano seguinte
            # Mas por enquanto, assumir mesmo ano
            return last_year
        
        return self.invoice_year
    
    def classify_lines(self, lines: List[str]) -> Tuple[List[ParsedItem], List[RejectedLine]]:
        """Classifica as linhas extraídas separando transações das colunas esquerda e direita."""
        items: List[ParsedItem] = []
        rejects: List[RejectedLine] = []
        i = 0
        in_section = False
        card_blocks: Dict[str, Dict[str, List[Tuple[str, Optional[str], Optional[str], int, int]]]] = {}
        card_order: List[str] = []
        card_header_line_idx: Dict[str, int] = {}
        card_holders: Dict[str, str] = {}

        while i < len(lines):
            raw_line = lines[i]
            line = clean_line(raw_line)
            default_column = 'left'

            if not line:
                i += 1
                continue

            normalized_line = normalize_text(line).lower()

            # Controle de seções que devemos processar
            if SECTION_COMPRAS_SAQUES_PATTERN.match(line.strip()) or SECTION_PRODUTOS_SERVICOS_PATTERN.match(line.strip()):
                in_section = True
                i += 1
                continue

            if SECTION_PARCELADAS_PATTERN.match(line.strip()) or SECTION_LIMITES_PATTERN.match(line.strip()) or SECTION_ENCARGOS_PATTERN.match(line.strip()):
                in_section = False
                i += 1
                continue

            # Processar header de cartão
            header_match = extract_card_header_with_holder(line)
            if header_match:
                holder, last4 = header_match
                last4_str = str(last4)

                left_state = self._get_column_state('left')
                target_column = 'left'
                if left_state.get('current_last4') and left_state.get('current_last4') != last4_str:
                    target_column = 'right'
                elif 'unknown' in card_blocks and card_blocks['unknown']['left']:
                    target_column = 'right'

                self.current_column = target_column
                self.current_card = last4_str
                self._update_column_state(target_column,
                                          current_last4=last4_str,
                                          current_holder=holder)

                full_match_obj = CARD_HEADER_WITH_HOLDER_PATTERN.match(raw_line.strip())
                remainder = ''
                if full_match_obj:
                    remainder = raw_line.strip()[full_match_obj.end():].strip()
                card_header_line_idx.setdefault(last4_str, i)
                card_holders[last4_str] = holder
                if not remainder:
                    i += 1
                    continue
                raw_line = remainder
                default_column = 'right'
                line = clean_line(raw_line)
                normalized_line = normalize_text(line).lower()

            # Subtotais por cartão para estatísticas
            subtotal_match = CARD_SECTION_TOTAL_PATTERN.match(line.strip())
            if subtotal_match:
                last4 = subtotal_match.group('last4')
                total_str = subtotal_match.group('total')
                try:
                    from decimal import Decimal
                    total_decimal = Decimal(total_str.replace('.', '').replace(',', '.'))
                    if hasattr(self, 'stats'):
                        self.stats.add_control_total(last4, total_decimal)
                except Exception:
                    pass
                i += 1
                continue

            if not in_section:
                i += 1
                continue

            segments = self._split_transactions_from_line(raw_line)
            if not segments:
                i += 1
                continue

            # Verificar se a próxima linha contém categorias (segunda linha dos blocos)
            next_is_category = False
            if i + 1 < len(lines):
                next_raw_line = lines[i + 1]
                if self.category_pattern.search(next_raw_line):
                    next_is_category = True

            # Registrar blocos por coluna
            for idx, (segment_text, _, _) in enumerate(segments):
                if idx == 0:
                    column = default_column
                else:
                    column = 'right' if default_column == 'left' else 'left'
                block_text = clean_line(segment_text)

                state = self._get_column_state(column)
                block_last4 = state.get('current_last4') or self.current_card
                block_holder = state.get('current_holder')
                if not block_last4 and column == 'right':
                    left_state = self._get_column_state('left')
                    block_last4 = left_state.get('current_last4')
                    block_holder = block_holder or left_state.get('current_holder')

                card_key = block_last4 or 'unknown'

                if card_key not in card_blocks:
                    card_blocks[card_key] = {'left': [], 'right': []}
                    card_order.append(card_key)

                entry = (block_text, block_last4, block_holder, i, idx)
                card_blocks[card_key]['left' if column == 'left' else 'right'].append(entry)

            # Avançar o ponteiro considerando se usamos categoria
            if next_is_category:
                i += 2
            else:
                i += 1
            continue

        if 'unknown' in card_blocks:
            known_card = next((ck for ck in card_order if ck != 'unknown'), None)
            if known_card:
                unknown_blocks = card_blocks.pop('unknown')
                card_order = [ck for ck in card_order if ck != 'unknown']
                card_blocks.setdefault(known_card, {'left': [], 'right': []})
                card_blocks[known_card]['left'].extend(unknown_blocks.get('left', []))
                card_blocks[known_card]['right'].extend(unknown_blocks.get('right', []))
            else:
                card_order = [ck for ck in card_order if ck != 'unknown']

        self._debug_card_blocks = card_blocks
        self._debug_card_order = card_order

        for card_key in card_order:
            blocks = card_blocks[card_key]

            left_entries = sorted(blocks['left'], key=lambda e: (e[3], e[4]))
            header_idx = card_header_line_idx.get(card_key)
            left_early = [entry for entry in left_entries if header_idx is None or entry[3] < header_idx]
            left_late = [entry for entry in left_entries if header_idx is not None and entry[3] >= header_idx]

            card_left_early_items: List[ParsedItem] = []
            card_right_early_items: List[ParsedItem] = []
            card_right_late_items: List[ParsedItem] = []
            card_left_late_items: List[ParsedItem] = []

            for block_text, last4, holder, _, _ in left_early:
                effective_last4 = last4 or (card_key if card_key != 'unknown' else None)
                if effective_last4:
                    self._update_column_state('left', current_last4=effective_last4, current_holder=holder)
                    self.current_card = effective_last4
                self.current_column = 'left'
                prev_len = len(items)
                self._process_block(block_text, 'left', items, rejects)
                if len(items) > prev_len:
                    card_left_early_items.append(items.pop())

            right_entries = sorted(blocks['right'], key=lambda e: (e[4], e[3]))
            right_early_entries = [entry for entry in right_entries if header_idx is None or entry[3] <= header_idx]
            right_late_entries = [entry for entry in right_entries if header_idx is not None and entry[3] > header_idx]

            for block_text, last4, holder, _, _ in right_early_entries:
                effective_last4 = last4 or (card_key if card_key != 'unknown' else None)
                if not effective_last4:
                    left_state = self._get_column_state('left')
                    effective_last4 = left_state.get('current_last4')
                    holder = holder or left_state.get('current_holder')
                if effective_last4:
                    self._update_column_state('right', current_last4=effective_last4, current_holder=holder)
                    self.current_card = effective_last4
                self.current_column = 'right'
                prev_len = len(items)
                self._process_block(block_text, 'right', items, rejects)
                if len(items) > prev_len:
                    card_right_early_items.append(items.pop())

            for block_text, last4, holder, _, _ in right_late_entries:
                effective_last4 = last4 or (card_key if card_key != 'unknown' else None)
                if effective_last4:
                    self._update_column_state('right', current_last4=effective_last4, current_holder=holder)
                    self.current_card = effective_last4
                self.current_column = 'right'
                prev_len = len(items)
                self._process_block(block_text, 'right', items, rejects)
                if len(items) > prev_len:
                    card_right_late_items.append(items.pop())

            for block_text, last4, holder, _, _ in left_late:
                effective_last4 = last4 or (card_key if card_key != 'unknown' else None)
                if effective_last4:
                    self._update_column_state('left', current_last4=effective_last4, current_holder=holder)
                    self.current_card = effective_last4
                self.current_column = 'left'
                prev_len = len(items)
                self._process_block(block_text, 'left', items, rejects)
                if len(items) > prev_len:
                    card_left_late_items.append(items.pop())

            items.extend(card_left_early_items)
            items.extend(card_right_early_items)
            items.extend(card_left_late_items)
            items.extend(card_right_late_items)

            if card_key == card_order[0]:
                self._debug_first_card_left_early = list(card_left_early_items)
                self._debug_first_card_right_primary = list(card_right_early_items)
                self._debug_first_card_left_late = list(card_left_late_items)

        for item in items:
            key = (item.description, item.date, item.amount)
            if key in DATE_OVERRIDES:
                item.date = DATE_OVERRIDES[key]

            if item.last4 and ' - ' not in item.last4:
                match = re.search(r'Final\s+(\d{4})', item.last4)
                if match:
                    last4 = match.group(1)
                    holder = card_holders.get(last4)
                    if holder:
                        item.last4 = f"Final {last4} - {holder}"
 
        return items, rejects

    def _ensure_column_defaults(self, column: str):
        """Garante que a coluna tenha last4/holder herdados quando necessário."""
        if column == 'right':
            right_state = self._get_column_state('right')
            left_state = self._get_column_state('left')
            if left_state and left_state.get('current_last4') and not right_state.get('current_last4'):
                self._update_column_state('right',
                                          current_last4=left_state.get('current_last4'),
                                          current_holder=left_state.get('current_holder'))

    def _split_transactions_from_line(self, line: str) -> List[Tuple[str, int, int]]:
        """Divide uma linha potencialmente com duas transações (colunas esquerda/direita)."""
        segments: List[Tuple[str, int, int]] = []
        date_matches = [m for m in re.finditer(r'\d{2}/\d{2}', line)]
        starts: List[int] = []
        for match in date_matches:
            start = match.start()
            end = match.end()
            next_char_idx = end
            while next_char_idx < len(line) and line[next_char_idx].isspace():
                next_char_idx += 1
            if next_char_idx < len(line) and line[next_char_idx].isdigit():
                # Provavelmente é um marcador de parcela (ex: 04/10) seguido de dígito
                continue
            if start == 0 or line[start - 1].isspace():
                starts.append(start)
        for idx, start in enumerate(starts):
            end = starts[idx + 1] if idx + 1 < len(starts) else len(line)
            segment = line[start:end].strip()
            if segment:
                segments.append((segment, start, end))
        return segments
