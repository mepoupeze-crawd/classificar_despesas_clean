"""
PDF text extraction with column detection and L→R ordering
"""

from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict, Union
import pdfplumber
import re
import statistics
import io
from .rules import (
    VALUE_PATTERN,
    CARD_HEADER_WITH_HOLDER_PATTERN,
    TRANSACTION_BLOCK_HEADER_PATTERN,
    BLOCK_SECOND_LINE_PATTERN,
    SECTION_COMPRAS_SAQUES_PATTERN,
    SECTION_PRODUTOS_SERVICOS_PATTERN,
    SECTION_PARCELADAS_PATTERN,
    SECTION_LIMITES_PATTERN,
    SECTION_ENCARGOS_PATTERN,
    CARD_SECTION_TOTAL_PATTERN,
    extract_card_header_with_holder,
)


@dataclass
class Char:
    """Representa um caractere extraído do PDF."""
    char: str
    x0: float
    x1: float
    y0: float
    y1: float
    page_num: int


def extract_chars_from_pdf(pdf_path: Union[str, bytes, io.BytesIO]) -> List[Char]:
    """
    Extrai caracteres do PDF página por página.
    
    Args:
        pdf_path: Caminho para o arquivo PDF, bytes do PDF, ou BytesIO
        
    Returns:
        Lista de caracteres ordenados por página e posição
    """
    chars = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                page_chars = page.chars
                for char_data in page_chars:
                    chars.append(Char(
                        char=char_data.get('text', ''),
                        x0=char_data.get('x0', 0),
                        x1=char_data.get('x1', 0),
                        y0=char_data.get('top', 0),
                        y1=char_data.get('bottom', 0),
                        page_num=page_num
                    ))
    except Exception as e:
        raise ValueError(f"Erro ao extrair texto do PDF: {str(e)}")
    
    return chars


DATE_TOKEN_PATTERN = re.compile(r"\d{1,2}/\d{1,2}")


def _group_words_by_rows(words: List[dict], y_tolerance: float = 2.5) -> List[List[dict]]:
    """
    Agrupa palavras por linhas usando a coordenada Y (top).

    Args:
        words: Lista de palavras extraídas do pdfplumber
        y_tolerance: tolerância em pontos para considerar mesma linha

    Returns:
        Lista de linhas (cada linha é uma lista de palavras)
    """
    if not words:
        return []

    sorted_words = sorted(words, key=lambda w: (w["top"], w["x0"]))
    rows: List[List[dict]] = []
    current_row: List[dict] = []
    current_top: Optional[float] = None

    for word in sorted_words:
        top = word.get("top")
        if top is None:
            continue

        if current_row and current_top is not None and abs(top - current_top) > y_tolerance:
            rows.append(current_row)
            current_row = []
            current_top = None

        current_row.append(word)
        if current_top is None:
            current_top = top

    if current_row:
        rows.append(current_row)

    return rows


def _detect_column_split_from_rows(rows: List[List[dict]]) -> Optional[float]:
    """
    Detecta divisão entre colunas baseada na posição X das linhas (primeira palavra).
    """
    first_positions = [
        row[0]["x0"]
        for row in rows
        if row and isinstance(row[0].get("x0"), (int, float)) and DATE_TOKEN_PATTERN.match(row[0].get("text", ""))
    ]

    if len(first_positions) < 2:
        return None

    first_positions.sort()
    largest_gap = 0.0
    split = None

    for left, right in zip(first_positions, first_positions[1:]):
        gap = right - left
        if gap > largest_gap:
            largest_gap = gap
            split = (left + right) / 2

    # Considerar que há duas colunas quando o gap é significativo
    if largest_gap < 60:  # heurística
        return None

    return split


def _rows_to_text(rows: List[List[dict]], split_x: Optional[float] = None) -> List[str]:
    """
    Converte linhas (palavras) em textos, respeitando colunas esquerda->direita.
    """
    if not rows:
        return []

    left_rows: List[Tuple[float, str]] = []
    right_rows: List[Tuple[float, str]] = []

    value_only_pattern = re.compile(r"^\d{1,3}(?:\.\d{3})*,\d{2}$")

    column_margin = 90.0 if split_x is not None else 0.0

    for row in rows:
        row_sorted = sorted(row, key=lambda w: w["x0"])
        row_top = min(word.get("top", 0.0) for word in row_sorted if isinstance(word.get("top"), (int, float)))

        if split_x is None:
            text = " ".join(word.get("text", "") for word in row_sorted).strip()
            if text:
                left_rows.append((row_top, text))
            continue

        # Criar segmentos baseados em gaps horizontais
        segments: List[List[dict]] = []
        current_segment: List[dict] = []
        previous_x1: Optional[float] = None

        for word in row_sorted:
            x0 = word.get("x0", 0.0)
            x1 = word.get("x1", x0)

            if current_segment and previous_x1 is not None and x0 - previous_x1 > 40:
                segments.append(current_segment)
                current_segment = []

            current_segment.append(word)
            previous_x1 = x1

        if current_segment:
            segments.append(current_segment)

        # Mesclar segmentos que representam valores com o segmento anterior
        merged_segments: List[List[dict]] = []
        for segment in segments:
            # Se o primeiro item for um valor e o próximo for uma data, associar valor ao segmento anterior
            if (
                len(segment) > 1
                and value_only_pattern.fullmatch(segment[0].get("text", ""))
                and DATE_TOKEN_PATTERN.match(segment[1].get("text", ""))
                and merged_segments
            ):
                merged_segments[-1].append(segment[0])
                segment = segment[1:]

            segment_text = " ".join(word.get("text", "") for word in segment).strip()
            if not segment_text:
                continue

            if merged_segments and value_only_pattern.fullmatch(segment_text):
                merged_segments[-1].extend(segment)
            else:
                merged_segments.append(segment)

        left_parts: List[str] = []
        right_parts: List[str] = []

        for segment in merged_segments:
            segment_text = " ".join(word.get("text", "") for word in segment).strip()
            if not segment_text:
                continue

            first_x = segment[0].get("x0", 0.0)
            effective_split = split_x + column_margin if split_x is not None else None

            # Identificar se o texto começa com um valor monetário.
            value_match = VALUE_PATTERN.match(segment_text)
            clean_segment = segment_text
            remaining_text = ""
            if value_match:
                clean_segment = value_match.group(0).strip()
                remaining_text = segment_text[len(value_match.group(0)) :].strip()

            # Valores monetários costumam ficar próximos ao limiar de coluna.
            # Se aparentar ser um valor e estiver ligeiramente à direita do split,
            # ainda assim o consideramos parte da coluna esquerda.
            if effective_split is not None and first_x >= effective_split:
                right_parts.append(segment_text)
            else:
                left_parts.append(clean_segment)
                if remaining_text:
                    right_parts.append(remaining_text)

        if left_parts:
            left_rows.append((row_top, " ".join(part for part in left_parts if part)))
        if right_parts:
            right_rows.append((row_top, " ".join(part for part in right_parts if part)))

    # Ordenar cada coluna por posição vertical (de cima para baixo)
    left_rows.sort(key=lambda item: item[0])
    right_rows.sort(key=lambda item: item[0])

    # Retornar: todas as linhas da esquerda primeiro, depois todas as linhas da direita
    return [text for _, text in left_rows] + [text for _, text in right_rows]


def detect_column_split(chars: List[Char], page_num: int) -> Optional[float]:
    """
    Detecta o ponto de divisão entre colunas usando K-means ou mediana.
    
    Args:
        chars: Lista de caracteres
        page_num: Número da página
        
    Returns:
        Posição X do split ou None
    """
    # Filtrar caracteres da página
    page_chars = [c for c in chars if c.page_num == page_num]
    
    if not page_chars:
        return None
    
    # Obter posições X1 (fim dos caracteres)
    x_positions = [c.x1 for c in page_chars if c.char.strip()]
    
    if not x_positions:
        return None
    
    # Tentar usar K-means se disponível
    try:
        from sklearn.cluster import KMeans
        import numpy as np
        
        if len(x_positions) < 2:
            return None
        
        X = np.array(x_positions).reshape(-1, 1)
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        kmeans.fit(X)
        
        # O split é o ponto médio entre os dois clusters
        centers = sorted(kmeans.cluster_centers_.flatten())
        if len(centers) == 2:
            return (centers[0] + centers[1]) / 2
    except ImportError:
        pass
    
    # Fallback: usar mediana
    sorted_x = sorted(x_positions)
    median_idx = len(sorted_x) // 2
    return sorted_x[median_idx] if sorted_x else None


def split_into_columns(chars: List[Char], page_num: int, split_x: float) -> Tuple[List[Char], List[Char]]:
    """
    Divide caracteres em coluna esquerda e direita.
    
    Args:
        chars: Lista de caracteres
        page_num: Número da página
        split_x: Posição X do split
        
    Returns:
        Tupla (coluna_esquerda, coluna_direita)
    """
    page_chars = [c for c in chars if c.page_num == page_num]
    
    left = [c for c in page_chars if c.x1 <= split_x]
    right = [c for c in page_chars if c.x1 > split_x]
    
    return left, right


def group_chars_into_lines(chars: List[Char], tolerance: float = 2.0) -> List[str]:
    """
    Agrupa caracteres em linhas baseado na proximidade vertical.
    
    Args:
        chars: Lista de caracteres
        tolerance: Tolerância em pontos para agrupar caracteres na mesma linha
        
    Returns:
        Lista de linhas de texto
    """
    if not chars:
        return []
    
    # Ordenar por Y (topo) e depois por X (esquerda)
    sorted_chars = sorted(chars, key=lambda c: (c.y0, c.x0))
    
    lines = []
    current_line_chars = []
    current_y = None
    
    for char in sorted_chars:
        if char.y0 is None:
            continue
        
        if current_y is None or abs(char.y0 - current_y) <= tolerance:
            # Mesma linha
            current_line_chars.append(char)
            if current_y is None:
                current_y = char.y0
        else:
            # Nova linha
            if current_line_chars:
                # Ordenar caracteres da linha por X
                current_line_chars.sort(key=lambda c: c.x0)
                line_text = ''.join(c.char for c in current_line_chars)
                lines.append(line_text)
            
            current_line_chars = [char]
            current_y = char.y0
    
    # Adicionar última linha
    if current_line_chars:
        current_line_chars.sort(key=lambda c: c.x0)
        line_text = ''.join(c.char for c in current_line_chars)
        lines.append(line_text)
    
    return lines


@dataclass
class ColumnState:
    """Estado de processamento por coluna."""
    in_section: bool = False
    ignore: bool = False
    current_last4: Optional[str] = None
    current_holder: Optional[str] = None
    pending_block: Optional[List[str]] = None


def _detect_column_split_x0(words: List[dict]) -> Optional[float]:
    """
    Detecta divisão entre colunas usando mediana de x0 ou k-means=2.
    
    Args:
        words: Lista de palavras extraídas do pdfplumber
        
    Returns:
        Posição X do split ou None
    """
    if not words:
        return None
    
    x0_positions = [w.get('x0', 0) for w in words if isinstance(w.get('x0'), (int, float))]
    if len(x0_positions) < 2:
        return None
    
    # Try k-means if sklearn available
    try:
        from sklearn.cluster import KMeans
        import numpy as np
        
        if len(x0_positions) < 2:
            return None
        
        X = np.array(x0_positions).reshape(-1, 1)
        kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
        kmeans.fit(X)
        
        centers = sorted(kmeans.cluster_centers_.flatten())
        if len(centers) == 2:
            return (centers[0] + centers[1]) / 2
    except ImportError:
        pass
    
    # Fallback: usar mediana
    sorted_x = sorted(x0_positions)
    median_idx = len(sorted_x) // 2
    return sorted_x[median_idx] if sorted_x else None


def _words_to_line_text(words: List[dict]) -> str:
    """Converte lista de palavras em texto de linha."""
    sorted_words = sorted(words, key=lambda w: w.get('x0', 0))
    return ' '.join(w.get('text', '') for w in sorted_words).strip()


def extract_lines_lr_order_block_based(pdf_path: str) -> List[str]:
    """
    DEPRECATED: Esta função foi substituída por `extract_lines_lr_order()` que é usada pelo novo parser.
    Mantida apenas para compatibilidade com testes/debug antigos.
    
    Extrai linhas do PDF usando extração baseada em blocos com estado por coluna.
    
    Processa páginas com duas colunas, mantendo estado independente por coluna:
    - Detecta seções a ler/ignorar
    - Extrai headers de cartão por coluna (holder + last4)
    - Processa transações em blocos
    - Extrai subtotais por cartão
    
    Args:
        pdf_path: Caminho para o arquivo PDF
        
    Returns:
        Lista de linhas ordenadas L→R (coluna esquerda primeiro, depois direita)
    """
    lines: List[str] = []
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                # Extrair palavras com parâmetros especificados
                words = page.extract_words(
                    x_tolerance=1,
                    y_tolerance=3,
                    use_text_flow=True
                )
                
                if not words:
                    continue
                
                # Agrupar palavras por linhas
                rows = _group_words_by_rows(words, y_tolerance=3)
                
                # Detectar split de colunas
                split_x = _detect_column_split_x0(words)
                
                if split_x is None:
                    # Sem colunas detectadas, processar como uma coluna
                    for row in rows:
                        line_text = _words_to_line_text(row)
                        if line_text:
                            lines.append(line_text)
                    continue
                
                # Processar linhas por coluna
                left_rows: List[Tuple[float, str]] = []
                right_rows: List[Tuple[float, str]] = []
                
                for row in rows:
                    row_text = _words_to_line_text(row)
                    if not row_text:
                        continue
                    
                    # Determinar a qual coluna pertence (baseado na primeira palavra)
                    if row:
                        first_x0 = row[0].get('x0', 0)
                        row_top = min(w.get('top', 0) for w in row if isinstance(w.get('top'), (int, float)))
                        
                        if first_x0 < split_x:
                            left_rows.append((row_top, row_text))
                        else:
                            right_rows.append((row_top, row_text))
                
                # Ordenar cada coluna por posição vertical
                left_rows.sort(key=lambda item: item[0])
                right_rows.sort(key=lambda item: item[0])
                
                # Adicionar linhas: esquerda primeiro, depois direita
                lines.extend(text for _, text in left_rows)
                lines.extend(text for _, text in right_rows)
    
    except Exception as exc:
        raise ValueError(f"Erro ao extrair texto do PDF: {exc}") from exc
    
    # Limpar linhas
    cleaned_lines: List[str] = []
    value_only_pattern = re.compile(r"^-?\s*\d{1,3}(?:\.\d{3})*,\d{2}$")
    
    for line in lines:
        normalized = re.sub(r"\s+", " ", line).strip()
        if not normalized:
            continue
        
        # Ignorar "Continua..."
        if normalized.upper().startswith("CONTINUA"):
            continue
        
        if value_only_pattern.match(normalized) and cleaned_lines:
            cleaned_lines[-1] = f"{cleaned_lines[-1]} {normalized}"
        else:
            cleaned_lines.append(normalized)
    
    return cleaned_lines


def extract_lines_lr_order(pdf_path: Union[str, bytes, io.BytesIO]) -> List[str]:
    """
    Extrai linhas do PDF na ordem L→R (coluna esquerda primeiro, depois direita).
    
    Args:
        pdf_path: Caminho para o arquivo PDF, bytes do PDF, ou BytesIO
        
    Returns:
        Lista de linhas ordenadas L→R
    """
    lines: List[str] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
                if words:
                    rows = _group_words_by_rows(words)
                    split_x = _detect_column_split_from_rows(rows)
                    page_lines = _rows_to_text(rows, split_x)
                    lines.extend(page_lines)
                else:
                    # Fallback: extrair caracteres diretamente da página já aberta
                    # Isso evita o problema de tentar reabrir um BytesIO consumido
                    page_chars: List[Char] = []
                    page_chars_data = page.chars
                    for char_data in page_chars_data:
                        page_chars.append(Char(
                            char=char_data.get('text', ''),
                            x0=char_data.get('x0', 0),
                            x1=char_data.get('x1', 0),
                            y0=char_data.get('top', 0),
                            y1=char_data.get('bottom', 0),
                            page_num=page.page_number
                        ))
                    
                    if page_chars:
                        split_x = detect_column_split(page_chars, page.page_number)
                        if split_x is None:
                            lines.extend(group_chars_into_lines(page_chars))
                        else:
                            left_chars, right_chars = split_into_columns(page_chars, page.page_number, split_x)
                            lines.extend(group_chars_into_lines(left_chars))
                            lines.extend(group_chars_into_lines(right_chars))
    except Exception as exc:
        raise ValueError(f"Erro ao extrair texto do PDF: {exc}") from exc

    # Limpar múltiplos espaços que possam ter sido gerados
    cleaned_lines: List[str] = []
    value_only_pattern = re.compile(r"^-?\s*\d{1,3}(?:\.\d{3})*,\d{2}$")

    for line in lines:
        normalized = re.sub(r"\s+", " ", line).strip()
        if not normalized:
            continue

        if value_only_pattern.match(normalized) and cleaned_lines:
            cleaned_lines[-1] = f"{cleaned_lines[-1]} {normalized}"
        else:
            cleaned_lines.append(normalized)

    return cleaned_lines

