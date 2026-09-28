#!/usr/bin/env python3
"""بوّابة تجميد البحث — لا وثيقةَ بحثٍ أو عرضٍ تدخل بلا كتابةٍ للسوق (D-297 · قرار المالك 2026-09-28).

**القياس الذي وُلدت منه.** بين 2026-08-16 و2026-09-28: 17 «فرصةً أولى» مختلفة · 12 ملحقَ
حالةٍ يعيد «GATE_C = ABSENT» · 6 جولات قرار · 62٪ من الأسطر المُضافة في أسبوعَين وثائقُ
بحث — و**رسالةٌ واحدة** مُرسَلة إلى مشترٍ، بلا ردٍّ ولا متابعة. الوثائق نفسها شخّصت العطب
(«الاختناق في الكتابة للسوق لا في القراءة عنه») ثمّ كتبت دراسةً أخرى. قانونٌ بلا فارضٍ
يُنسى في أوّل PR (D-207)؛ فهذه البوّابة تربط الاثنين آلياً.

**ما تفرضه (ثلاثة بنود):**
1. **السجلّ سليم دائماً:** ``docs/commercial/outreach/CONTACT_LEDGER.csv`` يُقرأ كاملاً بعقد
   ``shared/research/contact_ledger.py`` (مجموعة أفعالٍ مغلقة · تواريخ ISO لا مستقبلية ·
   المبلغ حيث يجب فقط) — سجلٌّ لا يُقرأ لا يُشهَد له.
2. **اللوحة مُشتقّة:** ``docs/commercial/HARD_CURRENCY_SCORECARD.json`` تساوي ما يُشتقّ من
   السجلّ بالبايت؛ رقمٌ مكتوب بيدٍ في اللوحة انتهاك (D-192).
3. **البحث مقرونٌ بالاتصال:** إذا أضاف الفارق (``base...HEAD`` أو شجرة العمل) ملفّاً تحت
   ``docs/research/`` · ``docs/reconstitution/`` · ``studies/`` · ``research/`` (md/json/csv)،
   أو ``*.md`` تحت ``docs/commercial/`` (عدا ``outreach/`` والكتالوج واللوحة)، أو ``*.md`` في
   الجذر باسمٍ عربيّ — وجب أن يضيف الفارقُ نفسه صفّاً واحداً على الأقل في السجلّ بفعلٍ من
   ``CONTACT_ACTIONS`` (رسالة · مكالمة · ردّ · عيّنة · عرض · دفعة). الإغلاق لا يُحتسب.

⛔ **لا إعفاءات بمتغيّر بيئة** — الإعفاء هو الثقب الذي يُنسى. تعطيلُ البوّابة قرارٌ مكتوب
في ``.memory/decisions.md`` (D-266 L9). ⛔ ولا تمنع البوّابة أيّ فعلٍ تجاري: الرسالة والفاتورة
تحدثان خارج المستودع؛ هي تمنع فقط أن يدخل **البحث** بلا **أثرِ سوق**.

تُشغَّل ضمن وظيفة ``guardrails`` في ``.github/workflows/ci.yml``. Exit 0 = نظيف · 1 = انتهاك.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.research.contact_ledger import (
    COLUMNS,
    CONTACT_ACTIONS,
    LEDGER_REL,
    SCORECARD_REL,
    LedgerError,
    build_scorecard,
    row_problems,
)

#: نفس المتغيّر الذي تقرأه ``check_code_acceptance.py`` في CI — مصدرٌ واحد لقاعدة الفارق.
BASE_ENV = "CODE_ACCEPTANCE_BASE_SHA"

RESEARCH_ROOTS: tuple[str, ...] = (
    "docs/research/",
    "docs/reconstitution/",
    "studies/",
    "research/",
)
RESEARCH_SUFFIXES: tuple[str, ...] = (".md", ".json", ".csv")
COMMERCIAL_ROOT = "docs/commercial/"
COMMERCIAL_EXEMPT: frozenset[str] = frozenset(
    {LEDGER_REL, SCORECARD_REL, "docs/commercial/OFFER_CATALOG.json"}
)
COMMERCIAL_EXEMPT_PREFIXES: tuple[str, ...] = ("docs/commercial/outreach/",)
_ARABIC = re.compile(r"[؀-ۿ]")

_FAILURES: list[str] = []


def _fail(message: str) -> None:
    _FAILURES.append(message)
    print(f"❌ {message}")


def is_research_path(path: str) -> bool:
    """هل يُعدّ هذا المسار «بحثاً/عرضاً» يجب أن يقترن بكتابةٍ للسوق؟"""
    if path in COMMERCIAL_EXEMPT or path.startswith(COMMERCIAL_EXEMPT_PREFIXES):
        return False
    if "/" not in path:
        return path.endswith(".md") and bool(_ARABIC.search(path))
    if path.startswith(RESEARCH_ROOTS):
        return path.endswith(RESEARCH_SUFFIXES)
    if path.startswith(COMMERCIAL_ROOT):
        return path.endswith(".md")
    return False


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "core.quotepath=false", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def changed_paths(root: Path, base: str | None) -> list[str]:
    """المسارات المُضافة/المُعدَّلة: ``base...HEAD`` في CI، وشجرة العمل (مع غير المتعقَّب) محلياً."""
    paths: set[str] = set()
    if base:
        out = _git(root, "diff", "--name-only", "--diff-filter=ACMR", f"{base}...HEAD")
        paths.update(line.strip() for line in out.splitlines() if line.strip())
        return sorted(paths)
    for args in (
        ("diff", "--name-only", "--diff-filter=ACMR"),
        ("diff", "--cached", "--name-only", "--diff-filter=ACMR"),
    ):
        paths.update(line.strip() for line in _git(root, *args).splitlines() if line.strip())
    for line in _git(root, "status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if line.startswith("?? "):
            paths.add(line[3:].strip())
    return sorted(paths)


def _is_tracked(root: Path, rel: str) -> bool:
    completed = subprocess.run(
        ["git", "ls-files", "--error-unmatch", rel],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    return completed.returncode == 0


def added_ledger_rows(root: Path, base: str | None) -> list[dict[str, str]]:
    """صفوف السجلّ التي **يضيفها الفارق** (لا كلّ السجلّ) — كلٌّ قاموساً بأعمدة العقد."""
    ledger = root / LEDGER_REL
    if not ledger.exists():
        return []
    if base:
        diff = _git(root, "diff", "--unified=0", f"{base}...HEAD", "--", LEDGER_REL)
    elif _is_tracked(root, LEDGER_REL):
        diff = _git(root, "diff", "--unified=0", "HEAD", "--", LEDGER_REL)
    else:
        diff = "\n".join(f"+{line}" for line in ledger.read_text(encoding="utf-8").splitlines())

    header = ",".join(COLUMNS)
    added_lines = [
        line[1:]
        for line in diff.splitlines()
        if line.startswith("+")
        and not line.startswith("+++")
        and line[1:].strip()
        and line[1:] != header
    ]
    if not added_lines:
        return []
    reader = csv.DictReader(io.StringIO("\n".join([header, *added_lines])))
    return [dict(row) for row in reader]


def evaluate(paths: list[str], added_rows: list[dict[str, str]], today: date) -> list[str]:
    """القرار الصرف: بحثٌ بلا صفّ اتصالٍ صالح ⇒ انتهاكات؛ غير ذلك ⇒ لا شيء."""
    research = sorted(path for path in paths if is_research_path(path))
    if not research:
        return []
    problems: list[str] = []
    contacts = 0
    for index, row in enumerate(added_rows, start=1):
        issues = row_problems(row, index, today)
        if issues:
            problems.extend(f"صفٌّ مُضاف {issue}" for issue in issues)
        elif (row.get("action") or "").strip() in CONTACT_ACTIONS:
            contacts += 1
    if contacts == 0:
        shown = research[:8] + (["…"] if len(research) > 8 else [])
        problems.insert(
            0,
            f"{len(research)} ملفّ بحثٍ/عرضٍ يدخل بلا صفّ اتصالٍ خارجيّ جديد في {LEDGER_REL}: {shown} — "
            "البحثُ لا يدخل المستودع إلّا مع كتابةٍ للسوق (رسالة · مكالمة · ردّ · عيّنة · عرض · دفعة). "
            "D-297: 17 فرصةً «أولى» ورسالةٌ واحدة كانت الثمن.",
        )
    return problems


def _check_ledger_and_scorecard(root: Path, today: date) -> None:
    ledger = root / LEDGER_REL
    if not ledger.exists():
        _fail(f"السجلّ غير موجود: {LEDGER_REL} — بلا سجلٍّ لا تُقاس كتابةٌ للسوق")
        return
    text = ledger.read_text(encoding="utf-8")
    try:
        computed = build_scorecard(text, today=today)
    except LedgerError as exc:
        _fail(f"سجلّ الاتصال غير مقبول:\n{exc}")
        return
    scorecard = root / SCORECARD_REL
    if not scorecard.exists():
        _fail(
            f"اللوحة غير موجودة: {SCORECARD_REL} — شغّل scripts/research/hard_currency_scorecard.py"
        )
        return
    expected = json.dumps(computed, ensure_ascii=False, indent=2) + "\n"
    if scorecard.read_text(encoding="utf-8") != expected:
        _fail(
            f"{SCORECARD_REL} لا تساوي ما يُشتقّ من {LEDGER_REL} — رقمٌ مكتوب بيد (D-192)؛ أعد التوليد"
        )


def main() -> int:
    _FAILURES.clear()
    today = date.today()
    base = os.environ.get(BASE_ENV, "").strip() or None

    _check_ledger_and_scorecard(REPO_ROOT, today)
    try:
        paths = changed_paths(REPO_ROOT, base)
        rows = added_ledger_rows(REPO_ROOT, base)
    except subprocess.CalledProcessError as exc:
        _fail(f"git غير قابل للقراءة ({exc}) — بوّابةٌ لا تقرأ الفارق لا تُبلِّغ أنّه نظيف (D-208 §6)")
        paths, rows = [], []
    for problem in evaluate(paths, rows, today):
        _fail(problem)

    if _FAILURES:
        print(f"\n❌ check_outbound_before_research: {len(_FAILURES)} انتهاك")
        return 1
    print("✅ check_outbound_before_research: السجلّ سليم، اللوحة مُشتقّة، ولا بحثٌ بلا كتابةٍ للسوق")
    return 0


if __name__ == "__main__":
    sys.exit(main())
