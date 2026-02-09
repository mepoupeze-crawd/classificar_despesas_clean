"""
Módulo de normalização de texto centralizada.

Esta função é usada tanto no treinamento quanto na predição para garantir
que os textos sejam normalizados de forma consistente.
"""

import re
from typing import Union


def normalize_description(text: Union[str, None]) -> str:
    """
    Normaliza descrição removendo datas, parcelas, prefixos e palavras genéricas.

    Esta função centraliza a lógica de normalização usada em:
    - treinar_modelo.py (treinamento)
    - ModelAdapter (predição)
    - SimilarityClassifier (similaridade TF-IDF)

    Exemplos:
    - "Hb - Imares (04/04)" → "imares"
    - "06/06/2025 - Drogasil1148" → "drogasil1148"
    - "Ifd*Drogaria Penamar L" → "drogaria penamar l"
    - "Evo*Usregen Ltda (02/03)" → "usregen ltda"

    Args:
        text: Texto a ser normalizado

    Returns:
        Texto normalizado em minúsculas e sem elementos irrelevantes
    """
    if not isinstance(text, str):
        return str(text).lower().strip() if text is not None else ""

    # Remover datas no início (DD/MM/YYYY ou DD/MM com hífen)
    text = re.sub(r'^(\d{2,4})[/-](\d{1,2})[/-](\d{2,4})\s*-\s*', '', text)

    # Remover datas no meio do texto
    text = re.sub(r'\b(\d{2,4})[/-](\d{1,2})[/-](\d{2,4})\b', '', text)

    # Remover padrões de parcelas: (02/03), (1/12), (04/04), etc.
    text = re.sub(r'\([0-9/]+\)', '', text)

    # Remover prefixos comuns: Evo*, Bkg*, Htm*, Ifd*, etc.
    text = re.sub(r'^\w+\*', '', text)

    # Remover "Hyundai " e "Hb - " para normalizar
    text = re.sub(r'^Hyundai\s+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^Hb\s*-\s*', '', text, flags=re.IGNORECASE)

    # Remover palavras genéricas: pagamento, compra, anuidade, debito, credito, pix
    text = re.sub(r'\b(pagamento|compra|anuidade|debito|credito|pix)\b', '', text, flags=re.IGNORECASE)

    # Remover hífens e espaços extras
    text = re.sub(r'^[\s-]+|[\s-]+$', '', text)
    text = re.sub(r'\s+', ' ', text)

    # Remover parênteses vazios e outros caracteres especiais residuais
    text = re.sub(r'[()]+', '', text)

    return text.lower().strip()
