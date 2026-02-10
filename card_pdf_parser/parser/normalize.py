"""
Text normalization functions
"""

import unicodedata
import re


def normalize_text(text: str) -> str:
    """
    Normaliza texto removendo acentos e caracteres especiais.
    
    Args:
        text: Texto a normalizar
        
    Returns:
        Texto normalizado
    """
    # Remove acentos
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    # Remove múltiplos espaços
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()


def clean_line(line: str) -> str:
    """
    Limpa linha de texto removendo caracteres de controle.
    
    Args:
        line: Linha a limpar
        
    Returns:
        Linha limpa
    """
    # Remove caracteres de controle exceto quebras de linha
    line = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]', '', line)
    
    # Remove espaços no início e fim
    line = line.strip()
    
    return line

