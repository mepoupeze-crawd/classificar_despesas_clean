#!/usr/bin/env python3
"""
Regression test for fatura fevereiro.pdf parsing.

This test ensures the Itaú parser correctly handles PDFs with:
- Different cardholder name formats (concatenated like "ALINEIDESOUSA")
- Merged columns where transactions and section markers appear on the same line
- Multiple cards (9826, 7430) and produtos/serviços section
"""

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest
from decimal import Decimal

from services.pdf.itau_cartao_parser import parse_itau_fatura


PDF_PATH = Path("fatura fevereiro.pdf")


@pytest.fixture(scope="session")
def parsed_fatura() -> dict:
    if not PDF_PATH.exists():
        pytest.skip(f"PDF file not found: {PDF_PATH}")
    return parse_itau_fatura(str(PDF_PATH))


def test_minimum_items_extracted(parsed_fatura: dict) -> None:
    """Ensure at least 10 items are extracted from the PDF."""
    assert len(parsed_fatura["items"]) >= 10, (
        f"Expected at least 10 items, got {len(parsed_fatura['items'])}"
    )


def test_cards_detected(parsed_fatura: dict) -> None:
    """Ensure both expected cards (9826 and 7430) are detected."""
    cards = set()
    for item in parsed_fatura["items"]:
        last4 = item.get("last4")
        if last4 and "9826" in last4:
            cards.add("9826")
        elif last4 and "7430" in last4:
            cards.add("7430")

    assert "9826" in cards, "Card 9826 not found in parsed items"
    assert "7430" in cards, "Card 7430 not found in parsed items"


def test_control_totals_match(parsed_fatura: dict) -> None:
    """Ensure calculated totals match control totals (delta = 0)."""
    by_card = parsed_fatura["stats"]["by_card"]

    for card in ("9826", "7430"):
        if card in by_card:
            delta = by_card[card]["delta"]
            # Delta should be 0,00 (allowing for format variations)
            delta_decimal = Decimal(delta.replace(".", "").replace(",", "."))
            assert delta_decimal == Decimal("0"), (
                f"Card {card} has non-zero delta: {delta}"
            )


def test_produtos_servicos_item(parsed_fatura: dict) -> None:
    """Ensure the produtos/serviços item (SEG CARTAO PROTEGIDO) is extracted."""
    produtos_items = [
        item for item in parsed_fatura["items"]
        if item.get("last4") is None and "SEG" in item.get("description", "").upper()
    ]
    assert len(produtos_items) >= 1, "Produtos/serviços item not found"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
