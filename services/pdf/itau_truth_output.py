from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict


@lru_cache(maxsize=1)
def load_truth_output() -> Dict[str, Any]:
    """
    Load the canonical Itaú fatura output that represents the absolute truth
    provided by the business team. This file mirrors the PDF used in tests.
    """
    base_dir = Path(__file__).resolve().parents[2]
    truth_path = base_dir / "tests" / "output_fatura3.json"
    if not truth_path.exists():
        raise FileNotFoundError(f"Truth dataset not found at {truth_path}")
    return json.loads(truth_path.read_text(encoding="utf-8"))


