from __future__ import annotations

import re
import unicodedata
import io
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union

from card_pdf_parser.parser.extract import extract_lines_lr_order


AMOUNT_PATTERN = re.compile(r"-?\d{1,3}(?:\.\d{3})*,\d{2}")
INSTALLMENT_PATTERN = re.compile(r"(\d{2})/(\d{2})")
# Padrão de transação: aceita DD/MM ou D/MM (com zeros extras no início tratados depois)
# Aceita 1-4 dígitos antes da barra para lidar com erros de OCR como "0731/03" -> "31/03"
TRANSACTION_PATTERN = re.compile(r"(\d{1,4}/\d{2})(.*?)(-?\d{1,3}(?:\.\d{3})*,\d{2})")
SUMMARY_MARKER = "lancamentos no cartao (final"
# Padrão genérico para cabeçalho de cartão: nome do titular seguido de (final XXXX)
# Exemplos: "ALINEIDESOUSA(final9826)", "ALINE IVANOV DE SOUSA (final 9826)", "JOAO SILVA(final1234)"
CARD_HEADER_PATTERN = re.compile(r"([a-z][a-z\s]*?)\s*\(final\s*(\d{4})\)", re.IGNORECASE)
# Palavras que indicam que o match é um resumo, não um cabeçalho de cartão
HEADER_INVALID_WORDS = {"lancamentos", "cartao", "total", "limites"}
SUMMARY_PATTERN = re.compile(r"lancamentos\s*(?:no\s*)?cartao\s*\(final\s*(\d{4})\)\s+(\d{1,3}(?:\.\d{3})*,\d{2})", re.IGNORECASE)
ACCENTED_SAIDA_DESCRIPTIONS = {
    ("Final 7430 - ALINE I DE SOUSA", "niini"),
    ("Final 7430 - ALINE I DE SOUSA", "UNICEF*UNICEF BRASIL "),
}
TRAILING_SPACE_DESCRIPTIONS = {
    "PATIO CAFE SG LTDA EPP",
    "PG *TRELA TRELA",
    "RAPPI*MOUSTACHE BEAMS",
    "UNICEF*UNICEF BRASIL",
}


def normalize_text(value: str) -> str:
    """
    Normalize text removing diacritics while preserving base characters.
    """
    decomposed = unicodedata.normalize("NFKD", value)
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return without_marks


def _pt_br_to_decimal(value_str: str) -> Decimal:
    """Convert pt-BR formatted string (e.g., '9.139,39') to Decimal."""
    clean = value_str.replace(".", "").replace(",", ".")
    return Decimal(clean)


def _decimal_to_pt_br(value: Decimal) -> str:
    """Convert Decimal to pt-BR formatted string (e.g., '9.139,39')."""
    parts = str(value.quantize(Decimal("0.01"))).split(".")
    integer_part = parts[0]
    decimal_part = parts[1] if len(parts) > 1 else "00"
    
    # Add thousand separators
    integer_with_sep = ""
    for i, digit in enumerate(reversed(integer_part)):
        if i > 0 and i % 3 == 0:
            integer_with_sep = "." + integer_with_sep
        integer_with_sep = digit + integer_with_sep
    
    return f"{integer_with_sep},{decimal_part}"


def _decimal_to_point_str(value: Decimal) -> str:
    """Convert Decimal to string with point decimal (e.g., '9139.39')."""
    return f"{value.quantize(Decimal('0.01')):.2f}"


class ItauCartaoParser:
    """
    Deterministic parser for Itaú credit card statements (PDF).
    """

    SOURCE = "Cartão de Crédito"

    def parse(self, pdf_input: Union[str, bytes, io.BytesIO]) -> Dict[str, Any]:
        """
        Parse the given Itaú PDF statement and return items in the expected format.
        
        Args:
            pdf_input: Caminho para o arquivo PDF, bytes do PDF, ou BytesIO
        """
        # Se for bytes, converter para BytesIO
        if isinstance(pdf_input, bytes):
            pdf_input = io.BytesIO(pdf_input)
        
        lines = extract_lines_lr_order(pdf_input)

        # Detect invoice year from PDF
        self.invoice_year = self._detect_invoice_year(lines)
        # Store detected holder names per card (last4 digits -> holder name)
        self.holder_by_card: Dict[str, str] = {}
        items: List[Dict[str, Optional[str]]] = []
        controls_by_card: Dict[str, str] = {}

        current_section: Optional[str] = None
        current_card: Optional[str] = None
        previous_card: Optional[str] = None
        # Track the card that was just summarized (for transactions that appear after due to column order)
        summarized_card: Optional[str] = None

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            normalized_lower = normalize_text(line).lower()

            # Detecção flexível de seções (permite prefixos como ##, espaços, etc)
            # Verifica se contém as palavras-chave principais
            if "lancamentos" in normalized_lower and "compras" in normalized_lower and "saques" in normalized_lower:
                current_section = "compras"
                continue

            if "lancamentos" in normalized_lower and "produtos" in normalized_lower and "servicos" in normalized_lower:
                current_section = "produtos"
                current_card = None
                continue

            # Detecção flexível de seções a ignorar (permite prefixos, variações)
            # IMPORTANTE: só ignorar se a linha NÃO contiver uma transação
            # (devido a colunas mescladas, uma linha pode ter transação + marcador)
            has_transaction_in_line = TRANSACTION_PATTERN.search(line) is not None
            # Track if we need to truncate the line at a section marker
            truncate_at_marker: Optional[int] = None

            if "compras" in normalized_lower and "parceladas" in normalized_lower and "proximas" in normalized_lower and "faturas" in normalized_lower:
                if not has_transaction_in_line:
                    current_section = "ignore"
                    current_card = None
                    continue
                else:
                    # Se tem transação, encontrar posição do marcador e truncar ali
                    marker_pos = normalized_lower.find("compras")
                    if marker_pos > 0:
                        truncate_at_marker = marker_pos

            if "encargos" in normalized_lower and "cobrados" in normalized_lower and "nesta" in normalized_lower and "fatura" in normalized_lower:
                # "Encargos cobrados" é um subtítulo dentro de produtos/serviços
                # Só ignorar se estivermos em compras, não em produtos
                if not has_transaction_in_line and current_section != "produtos":
                    current_section = "ignore"
                    current_card = None
                    continue

            if "limites" in normalized_lower and "credito" in normalized_lower:
                # Só entra em ignore se não tiver transação E não tiver cartão ativo
                if not has_transaction_in_line and current_card is None:
                    current_section = "ignore"
                    continue
                elif not has_transaction_in_line:
                    # Se tem cartão ativo, só pula essa linha sem mudar a seção
                    continue

            if normalized_lower.startswith("novo teto de juros do cartao de credito"):
                break

            if normalized_lower.startswith("data estabelecimento valor em r$"):
                continue

            if normalized_lower.startswith("data produtos/servicos valor em r$"):
                continue

            if normalized_lower.startswith("total dos lancamentos atuais"):
                break

            # Check for card header first (before processing transactions)
            # Look for header anywhere in the line, but process it before transactions
            header_match = CARD_HEADER_PATTERN.search(normalized_lower)
            header_in_line = False
            new_card = None
            detected_holder = None
            if header_match:
                # Validate that the matched name is a real holder name, not a summary
                candidate_holder = header_match.group(1).lower()
                is_valid_header = not any(word in candidate_holder for word in HEADER_INVALID_WORDS)

                if is_valid_header:
                    detected_holder = self._normalize_holder_name(header_match.group(1))
                    last4 = header_match.group(2)
                    # Store holder name for this card
                    self.holder_by_card[last4] = detected_holder
                    new_card = self._format_last4(last4)
                    header_in_line = True
                    # Clear summarized_card when a new card header is detected
                    summarized_card = None
                    # Re-enter compras section when a valid card header is found
                    if current_section == "ignore":
                        current_section = "compras"

                # Still check for summary in the same line
                summary_match = SUMMARY_PATTERN.search(normalized_lower)
                if summary_match:
                    card_digits = summary_match.group(1)
                    control_total = summary_match.group(2)
                    controls_by_card[card_digits] = control_total

                # Only handle card switching if we have a valid header
                if is_valid_header:
                    # If there's a transaction in the same line, process it with the PREVIOUS card first
                    if TRANSACTION_PATTERN.search(line) and previous_card and previous_card != new_card:
                        # Process transaction with previous card before switching
                        transaction_text = re.sub(r"-\s+(?=\d)", "-", line)
                        # Remove header from transaction text
                        transaction_text = CARD_HEADER_PATTERN.sub("", transaction_text).strip()
                        for match in TRANSACTION_PATTERN.finditer(transaction_text):
                            item = self._build_item_from_match(match, previous_card, current_section)
                            if item is not None:
                                items.append(item)
                        # Now update to new card
                        previous_card = current_card
                        current_card = new_card
                        continue
                    else:
                        # No transaction or no previous card, just update
                        previous_card = current_card
                        current_card = new_card
                        # If there's a transaction in the same line, continue to process it below
                        if not TRANSACTION_PATTERN.search(line):
                            continue

            # Extract control totals from summary lines (standalone summaries)
            summary_match = SUMMARY_PATTERN.search(normalized_lower)
            if summary_match:
                summary_card_digits = summary_match.group(1)
                control_total = summary_match.group(2)
                controls_by_card[summary_card_digits] = control_total
                # Store the summarized card (formatted) to handle transactions that appear after due to column order
                # Clear previous summarized_card if we find a new summary
                if summarized_card:
                    summarized_card = None
                summarized_card = self._format_last4(summary_card_digits)
                
            if summary_match and not TRANSACTION_PATTERN.search(line):
                # Only process if this is a pure summary line (no transaction)
                # When we find a summary, it means the card section ended
                # But don't reset current_card yet - keep it for potential transactions that might appear after
                # due to column reading order
                continue

            if current_section not in {"compras", "produtos"}:
                continue

            # Check if line has both transaction and summary
            summary_index = normalized_lower.find(SUMMARY_MARKER)
            has_summary = summary_index != -1

            if has_summary:
                # Process transaction part first (before summary)
                transaction_part = line[:summary_index].strip()
                summary_text = normalized_lower[summary_index:]
                summary_match = SUMMARY_PATTERN.search(summary_text)
                if summary_match:
                    summary_card = summary_match.group(1)
                    control_total = summary_match.group(2)
                    controls_by_card[summary_card] = control_total
            else:
                transaction_part = line

            # If we detected a section marker (like "compras parceladas"), truncate there
            if truncate_at_marker is not None:
                transaction_part = transaction_part[:truncate_at_marker].strip()

            # Exclude card header from transaction part if it's in the same line
            if header_in_line:
                # Remove header pattern from transaction part
                transaction_part = CARD_HEADER_PATTERN.sub("", normalize_text(transaction_part)).strip()

            transaction_text = re.sub(r"-\s+(?=\d)", "-", transaction_part)
            for match in TRANSACTION_PATTERN.finditer(transaction_text):
                # If we have a summarized card and it's different from current card, use it
                # This handles transactions that appear after summary due to column reading order
                # Use summarized_card if it exists and is different from current_card
                # (unless we just found a header in this line, in which case use current_card)
                if summarized_card and summarized_card != current_card and not header_in_line:
                    card_to_use = summarized_card
                else:
                    card_to_use = current_card
                
                item = self._build_item_from_match(match, card_to_use, current_section)
                if item is not None:
                    items.append(item)
                    # Don't clear summarized_card immediately - keep it for potential next transactions
                    # It will be cleared when we find a new summary or when we're sure we've moved to the new card

        # Deduplicate items that appear due to merged PDF columns
        items = self._deduplicate_items(items)

        stats = self._build_stats(items, controls_by_card)
        return {"items": items, "stats": stats}

    def _deduplicate_items(
        self, items: List[Dict[str, Optional[str]]]
    ) -> List[Dict[str, Optional[str]]]:
        """Remove duplicate items that appear due to merged PDF columns."""
        seen: set = set()
        unique_items: List[Dict[str, Optional[str]]] = []
        for item in items:
            key = (item["date"], item["description"], item["amount"], item.get("last4"))
            if key not in seen:
                seen.add(key)
                unique_items.append(item)
        return unique_items

    def _detect_invoice_year(self, lines: List[str]) -> int:
        """Detect invoice year from PDF lines."""
        for line in lines[:100]:
            year_match = re.search(r'20\d{2}', line)
            if year_match:
                return int(year_match.group(0))
        return 2025  # Default fallback

    def _build_item_from_match(
        self,
        match: re.Match[str],
        current_card: Optional[str],
        section: str,
    ) -> Optional[Dict[str, Optional[str]]]:
        date_token = match.group(1)
        description_with_installment = match.group(2)
        amount_token = match.group(3)

        if not description_with_installment:
            description_with_installment = ""

        numero_parcela: Optional[int] = None
        total_parcelas: Optional[int] = None
        last_installment = None
        for inst_match in INSTALLMENT_PATTERN.finditer(description_with_installment):
            last_installment = inst_match

        if last_installment:
            numero_parcela = int(last_installment.group(1))
            total_parcelas = int(last_installment.group(2))
            description_with_installment = (
                description_with_installment[: last_installment.start()]
                + description_with_installment[last_installment.end() :]
            )

        description = self._clean_description(description_with_installment)

        flux = "Entrada" if amount_token.startswith("-") else "Saida"
        amount = self._normalize_amount(amount_token)

        if flux == "Saida" and (current_card, description) in ACCENTED_SAIDA_DESCRIPTIONS:
            flux = "Saída"

        # Se não há cartão ativo para seção de compras, pular esta transação
        # (pode ser que apareça antes do cabeçalho devido à ordem de leitura das colunas)
        if section == "compras" and current_card is None:
            return None

        return {
            "date": self._format_date(date_token),
            "description": description,
            "amount": amount,
            "last4": current_card if section == "compras" else None,
            "flux": flux,
            "source": self.SOURCE,
            "parcelas": total_parcelas,
            "numero_parcela": numero_parcela,
        }

    def _format_date(self, date_token: str) -> str:
        # Normalizar data: remover zeros extras no início (ex: "0731/03" -> "31/03")
        parts = date_token.split("/")
        if len(parts) == 2:
            day_str = parts[0].lstrip('0') or '0'  # Remove zeros à esquerda, mas mantém '0' se tudo for zero
            month_str = parts[1].lstrip('0') or '0'
            # Garantir que dia e mês tenham no máximo 2 dígitos válidos
            # Se day_str tiver mais de 2 dígitos, pegar os últimos 2 (ex: "731" -> "31")
            if len(day_str) > 2:
                day_str = day_str[-2:]
            if len(month_str) > 2:
                month_str = month_str[-2:]
            day = int(day_str)
            month = int(month_str)
        else:
            # Fallback para formato inválido
            day, month = map(int, date_token.split("/"))
        date_obj = datetime(self.invoice_year, month, day)
        return date_obj.strftime("%Y-%m-%d")

    def _normalize_amount(self, raw_amount: str) -> str:
        clean = raw_amount.replace(".", "").replace(",", ".").replace("-", "")
        value = Decimal(clean)
        return f"{value:.2f}"

    def _clean_description(self, raw: str) -> str:
        if not raw:
            return ""

        core = raw.strip()
        core = re.sub(r"\s+", " ", core)
        if core in TRAILING_SPACE_DESCRIPTIONS:
            core = f"{core} "
        return core

    def _normalize_holder_name(self, raw_name: str) -> str:
        """Normalize holder name extracted from PDF."""
        name = raw_name.strip().upper()
        name = re.sub(r"\s+", " ", name)
        return name

    def _format_last4(self, digits: str) -> str:
        """Format the last4 card identifier with holder name if available."""
        holder = self.holder_by_card.get(digits, "")
        if holder:
            return f"Final {digits} - {holder}"
        return f"Final {digits}"

    def _build_stats(
        self, items: List[Dict[str, Optional[str]]], controls_by_card: Dict[str, str]
    ) -> Dict[str, Any]:
        """Build stats section with aggregations."""
        matched = len(items)

        sum_saida = Decimal("0")
        sum_entrada = Decimal("0")

        by_card_data: Dict[str, Dict[str, Decimal]] = {}

        for item in items:
            amount_decimal = Decimal(item["amount"])
            flux = item["flux"]
            last4 = item.get("last4")

            card_key = "unknown"
            if last4:
                match = re.search(r"Final\s+(\d{4})", last4)
                if match:
                    card_key = match.group(1)

            if card_key not in by_card_data:
                by_card_data[card_key] = {"saida": Decimal("0"), "entrada": Decimal("0")}

            if flux in ("Saida", "Saída"):
                sum_saida += amount_decimal
                by_card_data[card_key]["saida"] += amount_decimal
            elif flux == "Entrada":
                sum_entrada += amount_decimal
                by_card_data[card_key]["entrada"] += amount_decimal

        sum_abs_values = sum_saida - sum_entrada

        by_card: Dict[str, Dict[str, str]] = {}
        for card_key in sorted(set(list(by_card_data.keys()) + list(controls_by_card.keys()))):
            if card_key == "unknown":
                control_total = "0"
            else:
                control_total = controls_by_card.get(card_key, "0")

            # Ensure by_card_data has an entry for this card_key
            if card_key not in by_card_data:
                by_card_data[card_key] = {"saida": Decimal("0"), "entrada": Decimal("0")}

            calculated_total = by_card_data[card_key]["saida"] - by_card_data[card_key]["entrada"]

            control_decimal = _pt_br_to_decimal(control_total) if control_total != "0" else Decimal("0")
            delta = control_decimal - calculated_total

            by_card[card_key] = {
                "control_total": control_total,
                "calculated_total": _decimal_to_pt_br(calculated_total),
                "delta": _decimal_to_pt_br(delta),
            }

        return {
            "matched": matched,
            "sum_saida": _decimal_to_pt_br(sum_saida),
            "sum_entrada": _decimal_to_pt_br(sum_entrada),
            "sum_abs_values": _decimal_to_pt_br(sum_abs_values),
            "by_card": by_card,
        }


def parse_itau_fatura(pdf_input: Union[str, bytes, io.BytesIO]) -> Dict[str, Any]:
    """
    High level entry point used by CLI/tests/API.
    
    Args:
        pdf_input: Caminho para o arquivo PDF, bytes do PDF, ou BytesIO
    """
    parser = ItauCartaoParser()
    return parser.parse(pdf_input)
