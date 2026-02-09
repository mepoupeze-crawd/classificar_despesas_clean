#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from services.pdf.itau_cartao_parser import parse_itau_fatura


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(data: Dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def build_diff(actual: Dict[str, Any], expected: Dict[str, Any]) -> str:
    import difflib

    actual_str = json.dumps(actual, ensure_ascii=False, indent=2).splitlines()
    expected_str = json.dumps(expected, ensure_ascii=False, indent=2).splitlines()
    diff = difflib.unified_diff(expected_str, actual_str, fromfile="expected", tofile="actual", lineterm="")
    return "\n".join(diff)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Parse Itaú credit card statement and optionally compare with expected JSON."
    )
    parser.add_argument("--pdf", required=True, type=Path, help="Path to the PDF statement.")
    parser.add_argument("--out", required=True, type=Path, help="Where to write the parsed JSON.")
    parser.add_argument(
        "--expected",
        type=Path,
        default=Path("tests/expected_fatura_itau.json"),
        help="Snapshot JSON to compare against (default: %(default)s).",
    )
    parser.add_argument(
        "--skip-compare",
        action="store_true",
        help="Skip comparison against the expected snapshot, even if it exists.",
    )
    args = parser.parse_args()

    if not args.pdf.exists():
        parser.error(f"PDF not found: {args.pdf}")

    result = parse_itau_fatura(str(args.pdf))
    save_json(result, args.out)
    print(f"Wrote {len(result.get('items', []))} items to {args.out}")

    if args.skip_compare or args.expected is None:
        return 0

    if not args.expected.exists():
        print(f"Expected snapshot not found at {args.expected}, skipping diff.", file=sys.stderr)
        return 0

    expected = load_json(args.expected)
    if result == expected:
        print(f"Output matches snapshot {args.expected}")
        return 0

    print("Output differs from expected snapshot.", file=sys.stderr)
    diff = build_diff(result, expected)
    if diff:
        print(diff, file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

