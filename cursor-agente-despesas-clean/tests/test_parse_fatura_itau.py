from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

from services.pdf.itau_cartao_parser import parse_itau_fatura

PDF_PATH = Path("fatura_cartao_3.pdf")
EXPECTED_PATH = Path("tests/expected_fatura_itau.json")


@pytest.fixture(scope="session")
def parsed_fatura() -> dict:
    return parse_itau_fatura(str(PDF_PATH))


@pytest.fixture(scope="session")
def expected_snapshot() -> dict:
    return json.loads(EXPECTED_PATH.read_text(encoding="utf-8"))


def test_parse_matches_snapshot(parsed_fatura: dict, expected_snapshot: dict) -> None:
    assert parsed_fatura == expected_snapshot


def test_credit_entries_detection(parsed_fatura: dict) -> None:
    entradas = {
        (item["description"], item["amount"], item["last4"])
        for item in parsed_fatura["items"]
        if item["flux"] == "Entrada"
    }
    expected = {
        ("BRUNA CUTAIT", "0.18", "Final 9826 - ALINE I DE SOUSA"),
        ("PG *SHOPGEORGIA", "159.60", "Final 7430 - ALINE I DE SOUSA"),
        ("PG *AMARO", "209.93", "Final 7430 - ALINE I DE SOUSA"),
        ("PG *ONE WAY STORE COME", "68.23", "Final 7430 - ALINE I DE SOUSA"),
        ("niini", "0.02", "Final 7430 - ALINE I DE SOUSA"),
        ("niini", "0.04", "Final 7430 - ALINE I DE SOUSA"),
        ("TRELA*Pedido Trela", "0.01", "Final 7430 - ALINE I DE SOUSA"),
    }
    assert expected.issubset(entradas)


def test_installments_extracted(parsed_fatura: dict) -> None:
    lookup = {
        (item["description"], item["amount"]): (
            item["numero_parcela"],
            item["parcelas"],
        )
        for item in parsed_fatura["items"]
    }
    expected = {
        ("CLINICA ADRIANA VI", "2048.50"): (4, 10),
        ("ZARA BRASIL LTDA", "143.50"): (4, 5),
        ("PASSARO AZUL COMER", "266.35"): (3, 6),
        ("GALLERIST COM IMP", "125.82"): (3, 5),
        ("SEPHORA CIDJARDIN", "83.00"): (3, 5),
        ("LIVRARIA DA TRAVESSA", "439.50"): (2, 2),
    }
    for key, expected_tuple in expected.items():
        assert key in lookup, f"Missing transaction {key}"
        assert lookup[key] == expected_tuple


def test_seguro_entry_has_no_card(parsed_fatura: dict) -> None:
    seg_entry = next(
        item for item in parsed_fatura["items"] if item["description"] == "SEG CARTAO PROTEGIDO"
    )
    assert seg_entry["last4"] is None


def _pt_br_to_decimal(value: str) -> Decimal:
    return Decimal(value.replace(".", "").replace(",", "."))


def test_stats_aggregations(parsed_fatura: dict) -> None:
    stats = parsed_fatura["stats"]
    items = parsed_fatura["items"]

    assert stats["matched"] == len(items)

    sum_saida = _pt_br_to_decimal(stats["sum_saida"])
    sum_entrada = _pt_br_to_decimal(stats["sum_entrada"])
    sum_abs = _pt_br_to_decimal(stats["sum_abs_values"])
    assert sum_abs == (sum_saida - sum_entrada).quantize(Decimal("0.01"))

    by_card = stats["by_card"]

    assert by_card["9826"]["control_total"] == "9.139,39"
    assert by_card["7430"]["control_total"] == "6.329,45"
    assert by_card["1899"]["control_total"] == "135,30"
    assert by_card["unknown"]["control_total"] == "10,19"

    for card in ("9826", "7430", "1899"):
        control_decimal = _pt_br_to_decimal(by_card[card]["control_total"])
        calculated_decimal = _pt_br_to_decimal(by_card[card]["calculated_total"])
        delta_decimal = _pt_br_to_decimal(by_card[card]["delta"])
        expected_delta = (control_decimal - calculated_decimal).quantize(Decimal("0.01"))
        assert delta_decimal == expected_delta

    unknown_delta = _pt_br_to_decimal(by_card["unknown"]["delta"])
    assert unknown_delta == Decimal("0.00")

