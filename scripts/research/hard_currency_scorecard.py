#!/usr/bin/env python3
"""لوحة العملة الصعبة — مُشتقّةٌ من سجلّ الاتصال الخارجي، لا تُكتب بيدٍ أبداً (D-297).

التوجيه §35 يطلب لوحةً بـ15 مقياساً (عملاء أجانب · دافعون · إيراد مسوّى · متكرّر · متوسّط
لكلّ عميل · هامش · احتفاظ · إعادة شراء · زمن أوّل قيمة · زمن أوّل دفعة · دورة البيع · كلفة
التسليم · كلفة الذكاء الاصطناعي · كلفة الدعم · نسبة الاسترجاع). كلٌّ منها هنا **يُشتقّ**
من ``docs/commercial/outreach/CONTACT_LEDGER.csv`` وحده، والغائبُ ``null`` بسببٍ منطوق —
لا صفرٌ يُقرأ خسارة (D-212) ولا رقمٌ يُكتب في النثر (D-192).

    python3 scripts/research/hard_currency_scorecard.py          # يكتب اللوحة
    python3 scripts/research/hard_currency_scorecard.py --check  # يفشل إن انحرفت عن السجلّ

⛔ لا يقرأ الساعة إلّا لرفض تواريخ المستقبل في السجلّ؛ ``as_of`` هو آخر تاريخٍ في السجلّ.
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

from shared.research.contact_ledger import (
    LEDGER_REL,
    SCORECARD_REL,
    LedgerError,
    build_scorecard,
)

LEDGER = ROOT / LEDGER_REL
OUT = ROOT / SCORECARD_REL


def render(root: Path = ROOT, *, today: date | None = None) -> dict[str, object]:
    text = (root / LEDGER_REL).read_text(encoding="utf-8")
    return build_scorecard(text, today=today or date.today())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__ or "")
    parser.add_argument(
        "--check", action="store_true", help="يقارن المودَع بالمحسوب ويفشل عند الانحراف"
    )
    args = parser.parse_args()

    try:
        computed = render()
    except FileNotFoundError:
        print(f"❌ السجلّ غير موجود: {LEDGER_REL}")
        return 1
    except LedgerError as exc:
        print(f"❌ سجلّ الاتصال غير مقبول:\n{exc}")
        return 1

    serialized = json.dumps(computed, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if not OUT.exists():
            print(f"❌ اللوحة غير موجودة: {SCORECARD_REL} — شغّل السكربت بلا --check")
            return 1
        if OUT.read_text(encoding="utf-8") != serialized:
            print(f"❌ {SCORECARD_REL} لا تطابق ما يُشتقّ من {LEDGER_REL} — أعد التوليد بلا --check")
            return 1
        print("hard_currency_scorecard --check: PASS")
        return 0

    OUT.write_text(serialized, encoding="utf-8")
    funnel = computed["funnel"]
    print(
        f"✅ {SCORECARD_REL} كُتبت — صفوف={computed['rows']} · اتصالات={funnel['contacts_sent']} · دفعات={funnel['payments_settled']} · GATE_C={computed['gate_c']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
