#!/usr/bin/env python3
"""سلسلة القيمة — يولّد الكتلة ``derived`` في ``VALUE_CHAIN.json`` ولا يمسّ ما أُعلن (D-305).

الحلقات 1–6 يكتبها إنسانٌ بدليل؛ الحلقتان 7–8 والتصنيف والحلقة التالية تُشتقّ هنا من
``CONTACT_LEDGER.csv`` — فلا يرتفع مسارٌ في الخريطة إلّا حين يتحرّك السجلّ.

    python3 scripts/research/value_chain.py          # يكتب derived
    python3 scripts/research/value_chain.py --check  # يفشل إن انحرفت أو انكسر عقدٌ

البوّابة الحاجبة في CI هي ``scripts/fitness/check_value_chain.py``؛ ``--check`` هنا مرآتها المحلّية.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.research.contact_ledger import LEDGER_REL, LedgerError, parse_ledger
from shared.research.value_chain import (
    CATALOG_REL,
    VALUE_CHAIN_REL,
    ValueChainError,
    compute_derived,
    load_json,
    problems,
)


def _load(root: Path) -> tuple[dict[str, object], list, dict[str, object]]:
    doc = load_json(root / VALUE_CHAIN_REL)
    ledger_text = (root / LEDGER_REL).read_text(encoding="utf-8")
    rows = parse_ledger(ledger_text, today=date.today())
    catalog = load_json(root / CATALOG_REL)
    return doc, rows, catalog


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument("--check", action="store_true", help="يفشل عند الانحراف أو أيّ مشكلة")
    args = parser.parse_args()

    try:
        doc, rows, catalog = _load(ROOT)
    except (ValueChainError, LedgerError, FileNotFoundError) as exc:
        print(f"❌ {exc}")
        return 1

    if args.check:
        found = problems(doc, root=ROOT, ledger_rows=rows, catalog=catalog)
        for item in found:
            print(f"❌ {item}")
        if found:
            return 1
        print("value_chain --check: PASS")
        return 0

    doc["derived"] = compute_derived(doc, rows)
    path = ROOT / VALUE_CHAIN_REL
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    counts = doc["derived"]["by_classification"]  # type: ignore[index]
    print(f"✅ {VALUE_CHAIN_REL} — derived كُتب: {json.dumps(counts, ensure_ascii=False)}")
    leftovers = problems(doc, root=ROOT, ledger_rows=rows, catalog=catalog)
    for item in leftovers:
        print(f"⚠️ {item}")
    return 1 if leftovers else 0


if __name__ == "__main__":
    sys.exit(main())
