#!/usr/bin/env python3
"""بوّابة سلسلة القيمة — التصنيف يُشتقّ من الأدلّة ولا يُكتب بيد (D-305).

**لماذا هذه البوّابة موجودة:** للمستودع 25 مساراً للعملة الصعبة (19 في خريطة المسارات + 6
عروضٍ خارج الكتالوج)، ولم يكن شيءٌ يربط أيّاً منها بدليل. فقاعدة المالك (2026-10-01):
**حادثة ← نمط ← مسبارٌ يحفظ الخصوصية ← اختبارٌ موثوق ← نتيجةٌ على نظامٍ مستقلّ ← قرارٌ
للمشتري ← اهتمامٌ خارجي ← التزامٌ مدفوع**، وما يتوقّف عند المراحل الداخلية أصلٌ بحثيٌّ أو
قدرةٌ هندسية — لا منتجٌ ثوريٌّ ولا دليلُ عملةٍ صعبة.

**ما تفرضه** (كلّه في ``shared/research/value_chain.py:problems`` — مصدرٌ واحد للقاعدة):

1. كلّ مسارٍ يُعلن الحلقات 1–6 بحالةٍ مغلقة: دليلٌ **موجود** أو سببٌ منطوق (D-206 L11).
2. الحلقتان 7–8 لا تُعلَنان يدوياً؛ وكلّ صفٍّ في ``CONTACT_LEDGER.csv`` موجَّهٌ إلى مسارٍ واحد.
3. الحلقة 3 تُصرّح ``contains_user_data: false`` — لا تُفترَض الخصوصية.
4. ``derived`` يساوي الاشتقاق — التصنيف لا يُكتب بيد.
5. حالةُ الكتالوج لا تتجاوز الحلقات المبلوغة (طبقةُ أدلّةٍ تحت السُّلَّم الوحيد، لا سُلَّمٌ ثانٍ).
6. لا «ثوري/revolutionary/مضمون» في مسارٍ دون ``commercial_evidence``.

⛔ لا إعفاءٌ بمتغيّر بيئة. تُشغَّل ضمن وظيفة ``guardrails``. Exit 0 = نظيف · 1 = انتهاك.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.research.contact_ledger import LEDGER_REL, LedgerError, parse_ledger
from shared.research.value_chain import (
    CATALOG_REL,
    VALUE_CHAIN_REL,
    ValueChainError,
    load_json,
    problems,
)


def run(root: Path = REPO_ROOT, *, today: date | None = None) -> list[str]:
    """قائمة الانتهاكات — فارغةٌ تعني نظيف. مدخلٌ لا يُقرأ يُبلَّغ انتهاكاً (D-208 §6)."""
    try:
        doc = load_json(root / VALUE_CHAIN_REL)
        catalog = load_json(root / CATALOG_REL)
        ledger_text = (root / LEDGER_REL).read_text(encoding="utf-8")
        rows = parse_ledger(ledger_text, today=today or date.today())
    except (ValueChainError, LedgerError, OSError) as exc:
        return [f"تعذّرت قراءة المدخلات: {exc}"]
    return problems(doc, root=root, ledger_rows=rows, catalog=catalog)


def main() -> int:
    failures = run()
    for failure in failures:
        print(f"❌ {failure}")
    if failures:
        print(f"\n❌ سلسلة القيمة (D-305): {len(failures)} انتهاكاً")
        return 1
    print("✅ سلسلة القيمة (D-305): كلّ مسارٍ بأدلّةٍ موجودة، والتصنيف مُشتقّ")
    return 0


if __name__ == "__main__":
    sys.exit(main())
