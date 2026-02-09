"""
FastAPI router for PDF parsing endpoint
"""

import os
import re
import sys
from pathlib import Path
from typing import List
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from decimal import Decimal

# Adicionar o diretório raiz ao path para importar services
ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.pdf.itau_cartao_parser import parse_itau_fatura
from .parser.model import ParseResponse, ParsedItem, ParseStats, CardStats, RejectedLine

router = APIRouter(prefix="", tags=["PDF Parsing"])


def _convert_to_parsed_items(items: List[dict]) -> List[ParsedItem]:
    """Converte items do formato dict para ParsedItem."""
    parsed_items = []
    for item in items:
        # Converter amount de string para Decimal
        amount_str = item.get("amount", "0")
        # O parser retorna amount no formato "123.45" (ponto decimal)
        # Mas pode haver casos com vírgula (pt-BR), então tratamos ambos
        if "," in amount_str:
            # Formato pt-BR: remover pontos de milhar e substituir vírgula por ponto
            amount_clean = amount_str.replace(".", "").replace(",", ".")
        else:
            # Formato já com ponto decimal
            amount_clean = amount_str
        amount_decimal = Decimal(amount_clean)
        
        parsed_item = ParsedItem(
            date=item.get("date", ""),
            description=item.get("description", ""),
            amount=amount_decimal,
            last4=item.get("last4"),
            flux=item.get("flux", "Saida"),
            source=item.get("source"),
            parcelas=item.get("parcelas"),
            numero_parcela=item.get("numero_parcela")
        )
        parsed_items.append(parsed_item)
    return parsed_items


def _convert_to_card_stats(by_card_dict: dict) -> dict:
    """Converte by_card do formato dict para CardStats."""
    card_stats = {}
    for card_key, card_data in by_card_dict.items():
        # Converter valores de string pt-BR para Decimal
        control_total_str = card_data.get("control_total", "0")
        calculated_total_str = card_data.get("calculated_total", "0")
        delta_str = card_data.get("delta", "0")
        
        # Converter formato pt-BR (9.139,39) para Decimal
        def _pt_br_to_decimal(value_str: str) -> Decimal:
            if value_str == "0" or not value_str:
                return Decimal("0")
            # Remover pontos de milhar e substituir vírgula por ponto
            clean = value_str.replace(".", "").replace(",", ".")
            return Decimal(clean)
        
        card_stats[card_key] = CardStats(
            control_total=_pt_br_to_decimal(control_total_str),
            calculated_total=_pt_br_to_decimal(calculated_total_str),
            delta=_pt_br_to_decimal(delta_str)
        )
    return card_stats


def _convert_to_parse_stats(stats_dict: dict, total_lines: int, rejected: int) -> ParseStats:
    """Converte stats do formato dict para ParseStats."""
    # Converter valores de string pt-BR para Decimal
    def _pt_br_to_decimal(value_str: str) -> Decimal:
        if value_str == "0" or not value_str:
            return Decimal("0")
        # Remover pontos de milhar e substituir vírgula por ponto
        clean = value_str.replace(".", "").replace(",", ".")
        return Decimal(clean)
    
    return ParseStats(
        total_lines=total_lines,
        matched=stats_dict.get("matched", 0),
        rejected=rejected,
        sum_abs_values=_pt_br_to_decimal(stats_dict.get("sum_abs_values", "0")),
        sum_saida=_pt_br_to_decimal(stats_dict.get("sum_saida", "0")),
        sum_entrada=_pt_br_to_decimal(stats_dict.get("sum_entrada", "0")),
        by_card=_convert_to_card_stats(stats_dict.get("by_card", {}))
    )


@router.post("/parse_itau")
async def parse_itau_pdf(file: UploadFile = File(...)) -> ParseResponse:
    """
    🧾 **Parse Itaú PDF Invoice**
    
    Extrai transações de uma fatura de cartão Itaú em PDF usando o parser centralizado
    em `services/pdf/itau_cartao_parser.py`.
    
    ### 📋 Regras de Parsing
    
    - Leitura página por página, da coluna esquerda para direita (L→R)
    - Detecção automática do ano da fatura
    - Extração de valores em valor absoluto
    - Atribuição de `last4` baseado em cabeçalhos de seção (ex: "final 9826")
    - Detecção de parcelas (formato NN/MM)
    - Identificação de flux (Entrada/Saida) baseado em sinal e contexto
    - Validação usando subtotais do PDF com cálculo de delta por cartão
    
    ### 📤 Requisição
    
    - **file**: Arquivo PDF (multipart/form-data)
    
    ### 📥 Resposta
    
    - **items**: Lista de transações extraídas
    - **stats**: Estatísticas do parsing
      - `total_lines`: Total de linhas processadas
      - `matched`: Número de transações extraídas
      - `rejected`: Número de linhas rejeitadas
      - `sum_abs_values`: Soma dos valores absolutos
      - `by_card`: Estatísticas por cartão (control_total, calculated_total, delta)
    - **rejects**: Linhas rejeitadas com motivos
    """
    # Validar tipo de arquivo
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Arquivo deve ser um PDF (.pdf)"
        )

    # Validar MIME type
    if file.content_type and file.content_type not in ['application/pdf', 'application/x-pdf']:
        raise HTTPException(
            status_code=400,
            detail=f"MIME type inválido: {file.content_type}. Esperado: application/pdf"
        )

    try:
        # Ler bytes do arquivo
        file_bytes = await file.read()

        # Validar tamanho (máximo 10MB)
        MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Arquivo muito grande. Tamanho máximo: 10MB"
            )

        # Validar magic bytes (PDF deve começar com %PDF)
        if not file_bytes.startswith(b'%PDF'):
            raise HTTPException(
                status_code=400,
                detail="Arquivo não é um PDF válido (magic bytes incorretos)"
            )
        
        # Extrair linhas uma vez para contar total_lines
        from card_pdf_parser.parser.extract import extract_lines_lr_order
        import io
        pdf_io = io.BytesIO(file_bytes)
        lines = extract_lines_lr_order(pdf_io)
        total_lines = len(lines)
        
        # Processar PDF com o novo parser (reutilizar bytes)
        result = parse_itau_fatura(file_bytes)
        
        # Converter items para ParsedItem
        parsed_items = _convert_to_parsed_items(result.get("items", []))
        
        # Converter stats para ParseStats
        # O parser não retorna rejects, então vamos usar lista vazia
        rejected = 0  # O novo parser não rastreia linhas rejeitadas
        parse_stats = _convert_to_parse_stats(
            result.get("stats", {}),
            total_lines=total_lines,
            rejected=rejected
        )
        
        # Preparar resposta
        response = ParseResponse(
            items=parsed_items,
            stats=parse_stats,
            rejects=[]  # O novo parser não rastreia linhas rejeitadas
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Arquivo inválido ou layout não reconhecido: {str(e)}"
        )
    except Exception as e:
        # Log do erro para debug (sem vazar stack trace para o cliente)
        import logging
        logging.error(f"Erro ao processar PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=422,
            detail="Arquivo inválido ou layout não reconhecido"
        )
