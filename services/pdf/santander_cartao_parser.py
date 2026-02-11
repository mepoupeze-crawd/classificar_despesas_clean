"""Santander credit card PDF parser (MVP).

Goal: extract a reasonable first-pass list of transactions from common Santander
invoice PDFs so the classification pipeline can run end-to-end.

This is intentionally heuristic and conservative:
- prefers returning fewer rows over inventing rows
- focuses on lines that look like: DD/MM <description> <value>

If your PDF layout differs, we will iterate with real samples.
"""

from __future__ import annotations

import io
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

import pdfplumber


_DATE_RE = re.compile(r"\b(\d{2})/(\d{2})\b")
# value like 1.234,56 or 123,45 or 123.45
_VALUE_RE = re.compile(r"(-?\d{1,3}(?:\.\d{3})*,\d{2}|-?\d+\.\d{2}|-?\d+,\d{2})\b")
_INSTALLMENTS_RE = re.compile(r"\b(\d{1,2})/(\d{1,2})\b")


def _to_float(value: str) -> float:
    v = value.strip()
    if "," in v and "." in v:
        # pt-BR thousands + decimal comma
        v = v.replace(".", "").replace(",", ".")
    elif "," in v:
        v = v.replace(",", ".")
    return float(v)


def _guess_year(text: str) -> int:
    # try to find a 4-digit year in the PDF text
    m = re.search(r"\b(20\d{2})\b", text)
    if m:
        return int(m.group(1))
    return datetime.utcnow().year


def parse_santander_fatura(file_bytes: bytes) -> Dict[str, Any]:
    """Parse Santander PDF bytes and return {items, stats}."""
    if not file_bytes.startswith(b"%PDF"):
        raise ValueError("not a PDF")

    pdf_io = io.BytesIO(file_bytes)
    items: List[Dict[str, Any]] = []
    all_text_parts: List[str] = []
    raw_lines_sample: List[str] = []

    with pdfplumber.open(pdf_io) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            all_text_parts.append(text)
            for raw_line in text.splitlines():
                line = " ".join(raw_line.strip().split())
                if not line:
                    continue
                if len(raw_lines_sample) < 60:
                    raw_lines_sample.append(line)

                # must have a date and a value
                dm = _DATE_RE.search(line)
                vm = None
                # find last value on the line
                for m in _VALUE_RE.finditer(line):
                    vm = m
                if not dm or not vm:
                    continue

                day, month = int(dm.group(1)), int(dm.group(2))
                value_str = vm.group(1)
                try:
                    amount = abs(_to_float(value_str))
                except Exception:
                    continue

                # description = between date and value
                desc = line[dm.end(): vm.start()].strip(" -")
                if not desc or len(desc) < 3:
                    continue

                parcelas = None
                numero_parcela = None
                im = _INSTALLMENTS_RE.search(desc)
                if im:
                    try:
                        numero_parcela = int(im.group(1))
                        parcelas = int(im.group(2))
                    except Exception:
                        parcelas = None
                        numero_parcela = None

                items.append({
                    "date": f"{day:02d}/{month:02d}",
                    "description": desc,
                    "amount": f"{amount:.2f}",
                    "last4": None,
                    "flux": "Saida",
                    "source": "santander",
                    "parcelas": parcelas,
                    "numero_parcela": numero_parcela,
                })

    full_text = "\n".join(all_text_parts)
    year = _guess_year(full_text)

    stats = {
        "matched": len(items),
        "year": year,
        "source": "santander",
        "raw_lines_sample": raw_lines_sample,
    }

    return {"items": items, "stats": stats}
