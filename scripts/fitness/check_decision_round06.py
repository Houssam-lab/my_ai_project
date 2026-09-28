#!/usr/bin/env python3
"""بوّابة جولة القرار 06 — FIV: التحقق عبر الفاتورة الأولى (الدفعة العاشرة).

**ما تحرسه هذه البوّابة — ولماذا لا تحرسه بوّابةٌ سابقة:**

1. **مطابقةُ الأرقام**: 21 رقماً في §4 تُطابَق بمسارٍ مُسمّى وصيغةِ عرضٍ معلَنةٍ ضدّ
   `FIV_MEASUREMENTS.json` — فرقمٌ مكتوبٌ باليد بينما الملفّ يقول غيرَه ⇒ أحمر.
   (ملاحظةُ أمانة: الأرقامُ الأحادية تُطابَق وجوداً وقيمةً، والقوّةُ الإثباتية في
   متعدّدةِ الخانات التي يستحيل تواطؤُها صدفةً مع إعادة حسابٍ حتمية.)
2. **منعُ الاسم الميّت**: `prime-environments` خارجَ سياقِ البطلان (STALE) ⇒ أحمر —
   فالاسمُ ميّتٌ منذ 2026-03-29 (S129/C3).
3. **منعُ نقل الرسم**: أيُّ صافي tasksets/bounty محسوبٍ من جدول الـcodebases ⇒ أحمر
   (C2/H76) — كوداً (الملفّ) ونصّاً.
4. **انضباطُ الاقتباس**: كلُّ `$`+رقمٍ في وثيقة المعرفة بلا سند `[S1xx]` ⇒ أحمر،
   وكلُّ رقمٍ محسوبٍ (1.98 · 15.71 · 800.00 · 0.80) بلا وسمِ `⟨ح⟩` ⇒ أحمر.
5. **انضباطُ المستوى**: E1 واحدةٌ فقط (H71) — أيُّ مستوى فوق E1 أو E1 ثانية ⇒ أحمر.

Exit 0 = نظيف · 1 = انتهاك. وتُشغَّل ضمن وظيفة `guardrails`.
"""

from __future__ import annotations

import ast
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "studies" / "algeria-hard-currency"
LEDGER = STUDY / "decision_ledger_round06.csv"
EVIDENCE = STUDY / "evidence_round06.csv"
ROUND = STUDY / "DECISION-ROUND-06.md"
KNOWLEDGE = ROOT / "docs" / "research" / "HARD_CURRENCY_NEW_KNOWLEDGE_FIV.md"
ARTIFACT = ROOT / "docs" / "research" / "FIV_MEASUREMENTS.json"
CATALOG = ROOT / "docs" / "commercial" / "OFFER_CATALOG.json"
MEASURE = ROOT / "scripts" / "research" / "measure_first_invoice.py"
TOOL = ROOT / "shared" / "research" / "first_invoice.py"

EXPECTED_LEDGER_FIRST = "H70"
EXPECTED_LEDGER_LAST = "H79"
EXPECTED_EVIDENCE = 14
EXPECTED_EVIDENCE_RANGE = ("S127", "S140")
EXPECTED_E1_ID = "H71"

WANT_LEDGER_COLS = [
    "id",
    "hypothesis_ar",
    "counterparty",
    "binding_gate",
    "gate_state",
    "decision",
    "max_level",
    "key_claim",
    "key_test",
    "shared_dependency",
]
WANT_EVIDENCE_COLS = [
    "id",
    "claim_summary_ar",
    "source",
    "url",
    "as_of",
    "status",
    "independence_note",
    "reverification_trigger",
]

#: (المسارُ المُسمّى في الملفّ · صيغةُ العرض) — 21 رقماً في §4.
MATCHES: tuple[tuple[str, str], ...] = (
    ("results.listing_band.count", "int"),
    ("results.listing_band.price_lo_usd", "int"),
    ("results.listing_band.price_hi_usd", "int"),
    ("results.listing_band.unit_lo_usd", "f2"),
    ("results.listing_band.unit_hi_usd", "f2"),
    ("results.net_probe.CH5_datavendor_codebase.net_usd", "f2"),
    ("results.net_probe_summary.gross_usd", "int"),
    ("results.net_probe_summary.quotable", "int"),
    ("results.net_probe_summary.unquotable", "int"),
    ("results.settle.stated", "int"),
    ("results.settle.unstated", "int"),
    ("results.contradictions.total", "int"),
    ("results.kill_switches", "len"),
    ("results.channels_ranked", "len"),
    ("inputs.policy.max_spend_usd", "int"),
    ("inputs.policy.max_effort_days", "int"),
    ("results.fee_schedule.codebase.seller_share", "f2"),
    ("results.naming.current_name", "raw"),
    ("results.audit_band.anchors", "int"),
    ("results.audit_band.engagement_floor_usd", "int"),
    ("results.audit_band.highest_stated_hi_usd", "int"),
)

#: الأرقامُ المحسوبة التي تلزم وسمَ ⟨ح⟩ في وثيقة المعرفة.
COMPUTED_FIGURES = ("1.98", "15.71", "800.00", "0.80")

#: عباراتٌ ممنوعةٌ مطلقاً في ملفّات الجولة الجديدة — بلا سياقِ استثناء.
FORBIDDEN_ABSOLUTE = ("مضمون", "guaranteed", "صفر أخطاء", "إيراد مؤكد", "عقد مؤكد")

_DIACRITICS = re.compile("[\u064b-\u0652\u0670]")


def strip_diacritics(text: str) -> str:
    """يُسقِط الحركاتِ قبل المطابقة — فالحركاتُ رسمٌ لا معنى هنا."""
    return _DIACRITICS.sub("", text)


def field(row: dict, key: str) -> str:
    """يُعيد قيمةَ عمودٍ نصّاً — و⛔ لا `None` يصل إلى `re` فيُسقط البوّابة."""
    value = row.get(key)
    return value if isinstance(value, str) else ""


def load_csv(path: Path) -> list[dict[str, str]]:
    """يقرأ سجلاً CSV — والفشلُ صريحٌ لا قائمةٌ فارغة تُقرأ نجاحاً."""
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def dig(artifact: dict, dotted: str) -> object:
    """يغوص في الملفّ بمسارٍ مُسمّى — والمسارُ المفقودُ انتهاكٌ لا استثناء."""
    node: object = artifact
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise KeyError(dotted)
        node = node[part]
    return node


def render(value: object, spec: str) -> str:
    """يُخرِج القيمةَ بصيغةِ العرض المعلَنة — نفسُ الصيغة في النصّ والملفّ."""
    if spec == "int":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(spec)
        return str(int(value))
    if spec == "f2":
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(spec)
        return f"{float(value):.2f}"
    if spec == "len":
        if not isinstance(value, (list, tuple)):
            raise TypeError(spec)
        return str(len(value))
    if spec == "raw":
        return str(value)
    raise ValueError(spec)


def section(text: str, start: str, end: str) -> str:
    """يقتطع مقطعاً بين عنوانَين — والمقطعُ الغائبُ نصٌّ فارغٌ يُفشِل المطابقة."""
    head = text.find(start)
    if head < 0:
        return ""
    tail = text.find(end, head + len(start))
    return text[head:] if tail < 0 else text[head:tail]


def _check_ledger_row(
    row: dict[str, str],
    e1_ids: list[str],
    counts: dict[str, int],
    failures: list[str],
) -> None:
    """يفحص بطاقةً واحدة: E0/E1 حصراً، والحالةُ تُحصى لا تُخمَّن."""
    hid = field(row, "id") or "؟"
    level = field(row, "max_level").strip()
    if level not in ("E0", "E1"):
        failures.append(f"{hid}: مستوى خارج المجموعة المغلقة {{E0,E1}}: {level!r}")
    if re.search(r"E[2-9]", level):
        failures.append(f"{hid}: مستوى فوق E1 ممنوع: {level!r}")
    if level == "E1":
        e1_ids.append(hid)
    state = strip_diacritics(field(row, "gate_state"))
    if "منجزة" in state:
        counts["completed"] += 1
    elif "جزئية" in state:
        counts["partial"] += 1
    elif "معلقة" in state:
        counts["held"] += 1
    else:
        failures.append(f"{hid}: حالةٌ خارج المجموعة المغلقة (مُنجَزة/جزئية/معلّقة)")
    for key in ("hypothesis_ar", "counterparty", "binding_gate", "decision", "key_test"):
        if not field(row, key):
            failures.append(f"{hid}: عمودٌ فارغ: {key} — الخانةُ الفارغة تُقرأ نجاحاً")


def check_ledger(ledger: list[dict[str, str]], failures: list[str]) -> dict[str, int]:
    """سجلّ الفرضيات: 10 صفوف · اتّصالُ H70–H79 · E1 واحدة (H71) · لا مستوى فوق E1."""
    counts = {"completed": 0, "partial": 0, "held": 0}
    if len(ledger) != 10:
        failures.append(f"سجلّ الجولة 06 يحوي {len(ledger)} فرضيات، والمتوقّع 10")
    want_ids = [f"H{n}" for n in range(70, 80)]
    ids = [field(row, "id") for row in ledger]
    if ids != want_ids:
        failures.append(f"معرّفاتُ السجلّ {ids}، والمتوقّع اتّصالاً H70–H79")
    if ledger and list(ledger[0].keys()) != WANT_LEDGER_COLS:
        failures.append(f"أعمدةُ السجلّ خارجَ عُرف الجولات: {list(ledger[0].keys())}")
    e1_ids: list[str] = []
    for row in ledger:
        _check_ledger_row(row, e1_ids, counts, failures)
    if e1_ids != [EXPECTED_E1_ID]:
        failures.append(f"E1 المتوقّعة [{EXPECTED_E1_ID}] وحده، والموجودة {e1_ids}")
    return counts


def check_declared_counts(round_text: str, counts: dict[str, int], failures: list[str]) -> None:
    """الأعدادُ المعلَنة في §6.1 تُشتَق من السجلّ — لا تُكتَب باليد مستقلّةً عنه."""
    plain = strip_diacritics(round_text)
    match = re.search(r"(\d+)\s+منجزة\s+·\s+(\d+)\s+جزئية\s+·\s+(\d+)\s+معلقة", plain)
    if not match:
        failures.append("§6.1 بلا سطرِ أعدادٍ مُشتَقّ (مُنجَزة · جزئية · معلّقة)")
        return
    declared = tuple(int(group) for group in match.groups())
    actual = (counts["completed"], counts["partial"], counts["held"])
    if declared != actual:
        failures.append(f"أعدادُ §6.1 المعلَنة {declared} ≠ المُشتقّة من السجلّ {actual}")
    if "E1 لفرضيةٍ واحدة (H71)" not in round_text:
        failures.append("§6.1 لا يُعلِن E1 الواحدة (H71) بنصّها الصريح")
    if "وE0 للتسع" not in round_text:
        failures.append("§6.1 لا يُعلِن E0 للتسع بنصّه الصريح")


def _check_evidence_row(
    row: dict[str, str],
    grade: re.Pattern[str],
    grades: dict[str, int],
    failures: list[str],
) -> None:
    """يفحص سنداً واحداً: التاريخُ والدرجةُ والرابطُ والاستقلالُ والمحفّز."""
    sid = field(row, "id") or "؟"
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", field(row, "as_of")):
        failures.append(f"{sid}: `as_of` غائبٌ أو غير صالح — التاريخُ إلزاميٌّ لكلّ صفّ")
    status = field(row, "status")
    if status.startswith("UNSTATED"):
        grades["UNSTATED"] += 1
    elif grade.match(status):
        grades[status[0]] += 1
    else:
        failures.append(f"{sid}: درجةٌ خارج العُرف (P/M/L أو UNSTATED): {status[:30]!r}")
    url = field(row, "url")
    if not url and not status.startswith("UNSTATED"):
        failures.append(f"{sid}: سندٌ بلا رابطٍ ولا وسم UNSTATED")
    if url and not url.startswith("http") and not status.startswith("UNSTATED"):
        failures.append(f"{sid}: `url` ليس رابطاً والصفُّ ليس UNSTATED")
    if status.startswith("UNSTATED") and url.startswith("http"):
        failures.append(f"{sid}: صفٌّ موسومٌ UNSTATED ومع ذلك يحمل رابطاً")
    if not field(row, "independence_note"):
        failures.append(f"{sid}: سندٌ بلا ملاحظةِ استقلال")
    if not field(row, "reverification_trigger"):
        failures.append(f"{sid}: سندٌ بلا محفّزِ إعادة تحقّق")


def check_evidence(evidence: list[dict[str, str]], round_text: str, failures: list[str]) -> None:
    """سجلّ الأدلة: 14 سنداً · اتّصالُ S127–S140 · درجةٌ وتاريخٌ ورابطٌ لكلّ صفّ."""
    if len(evidence) != EXPECTED_EVIDENCE:
        failures.append(f"سجلّ أدلّة الجولة 06 يحوي {len(evidence)} سنداً، والمتوقّع 14")
    want = [f"S{n}" for n in range(127, 141)]
    ids = [field(row, "id") for row in evidence]
    if ids != want:
        failures.append(f"معرّفاتُ الأدلّة {ids}، والمتوقّع اتّصالاً S127–S140")
    if evidence and list(evidence[0].keys()) != WANT_EVIDENCE_COLS:
        failures.append(f"أعمدةُ الأدلّة خارجَ عُرف الجولات: {list(evidence[0].keys())}")
    grade = re.compile(r"^(?:P|M|L)(?:-[HM])?\s+—")
    grades = {"P": 0, "M": 0, "L": 0, "UNSTATED": 0}
    for row in evidence:
        _check_evidence_row(row, grade, grades, failures)
    plain = strip_diacritics(round_text)
    match = re.search(
        r"(\d+)\s+سندا\s+\(S127–S140\):\s*\**(\d+)\s+أولية\s+·\s+(\d+)\s+ثانوية\s+·\s+"
        r"(\d+)\s+منخفضة\s+·\s+(\d+)\s+غير\s+ملتقطة",
        plain,
    )
    if not match:
        failures.append("§6.1 بلا سطرِ توزيعِ الدرجات (أوّلية · ثانوية · منخفضة · غيرُ ملتقطة)")
        return
    declared = tuple(int(group) for group in match.groups())
    actual = (
        len(evidence),
        grades["P"],
        grades["M"],
        grades["L"],
        grades["UNSTATED"],
    )
    if declared != actual:
        failures.append(f"توزيعُ §6.1 المعلَن {declared} ≠ المُشتَقّ من السجلّ {actual}")


def check_measurements(round_text: str, failures: list[str]) -> dict:
    """21 رقماً في §4 — كلٌّ بمسارٍ مُسمّى وصيغةِ عرضٍ معلَنةٍ ضدّ الملفّ الحتمي."""
    measured: dict = {"matched": 0}
    try:
        artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"ملفّ القياس لا يُقرأ: {exc}")
        return measured
    if artifact.get("batch") != "FIV-10" or artifact.get("as_of") != "2026-09-15":
        failures.append("رأسُ الملفّ خارج الدفعة (batch/as_of)")
    want_zeros = {
        "model_runs_executed": 0,
        "client_measurements": 0,
        "invoices_issued": 0,
        "settled_contracts": 0,
        "exploit_code_present": False,
        "revenue_claim": "NONE",
    }
    if artifact.get("declared_zeros") != want_zeros:
        failures.append(f"الأصفارُ المعلَنة في الملفّ {artifact.get('declared_zeros')}")
    body = section(round_text, "## 4.", "## 5.")
    if not body:
        failures.append("§4 مفقودٌ من وثيقة الجولة")
        return measured
    for dotted, spec in MATCHES:
        try:
            rendered = render(dig(artifact, dotted), spec)
        except (KeyError, TypeError, ValueError):
            failures.append(f"مسارٌ مفقودٌ أو صيغةٌ خاطئة: {dotted} [{spec}]")
            continue
        if rendered not in body:
            failures.append(f"§4 بلا `{rendered}` — المسارُ `{dotted}` [{spec}] غيرُ مُقتبَس")
            continue
        measured["matched"] += 1
    measured["artifact"] = artifact
    return measured


def check_fee_nontransfer(artifact: dict, failures: list[str]) -> None:
    """C2/H76: جدولُ الـcodebases لا يُسعِّر غيرَها — كوداً (الملفّ) لا نثراً."""
    try:
        schedule = artifact["results"]["fee_schedule"]
        probes = artifact["results"]["net_probe"]
    except (KeyError, TypeError):
        failures.append("مسارا الرسم/المسبار مفقودان من الملفّ")
        return
    if schedule.get("codebase", {}).get("seller_share") != 0.8:
        failures.append("حصّةُ الـcodebases في الجدول ≠ 0.8 — الجدولُ المُعلَن وحدَه يُحفَظ")
    for asset in ("taskset", "bounty"):
        if schedule.get(asset, {}).get("seller_share") is not None:
            failures.append(f"⛔ رسمٌ مُخترَعٌ لفئة {asset} — الغائبُ غائبٌ بسببٍ لا رقماً")
    if probes.get("CH5_datavendor_codebase", {}).get("net_usd") != 800.0:
        failures.append("صافي CH5 ≠ 800.00 — المسبارُ الوحيد القابل للاقتباس")
    for channel in (
        "CH1_prime_open",
        "CH2_prime_app",
        "CH3_prime_sprint",
        "CH4_datavendor_listing",
    ):
        probe = probes.get(channel, {})
        if probe.get("net_usd") is not None or probe.get("state") != "UNQUOTABLE":
            failures.append(f"⛔ صافيٌّ مُقتبَسٌ بلا جدولٍ مُعلَن: {channel}")
        if not probe.get("reason"):
            failures.append(f"{channel}: `None` بلا سببٍ منطوق")


def check_naming_guard(files: list[Path], failures: list[str]) -> None:
    """H75/C3: الاسمُ الميّت `prime-environments` لا يرد إلّا في سياقِ البطلان."""
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            failures.append(f"ملفٌّ لا يُقرأ: {path}")
            continue
        for lineno, line in enumerate(lines, 1):
            if (
                "prime-environments" in line
                and "community-environments" not in line
                and "STALE" not in line
            ):
                failures.append(f"{path.name}:{lineno}: اسمٌ ميّتٌ خارجَ سياقِ البطلان")


def check_gate_c(files: list[Path], failures: list[str]) -> None:
    """كلُّ سطرٍ يذكر `GATE_C` يُلزَم `ABSENT` على السطر نفسه — بلا استثناء."""
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for lineno, line in enumerate(lines, 1):
            if "GATE_C" in line and "ABSENT" not in line:
                failures.append(f"{path.name}:{lineno}: سطرُ GATE_C بلا ABSENT")


def check_forbidden(files: list[Path], failures: list[str]) -> None:
    """عباراتٌ مطلقةُ المنع في ملفّات الجولة — الوعدُ المُطلَق كذبٌ مُقنَّع."""
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for phrase in FORBIDDEN_ABSOLUTE:
            if phrase in text:
                failures.append(f"{path.name}: عبارةٌ ممنوعةٌ مطلقاً: {phrase!r}")


def check_knowledge_pins(knowledge_text: str, artifact: dict, failures: list[str]) -> None:
    """انضباطُ الاقتباس في وثيقة المعرفة: بصمةٌ · سندُ الدولار · وسمُ المحسوب."""
    fingerprint = artifact.get("inputs_fingerprint", "")
    match = re.search(r"sha256 = ([0-9a-f]{64})", knowledge_text)
    if not match:
        failures.append("وثيقةُ المعرفة بلا سطرِ بصمةٍ `sha256 = …`")
    elif match.group(1) != fingerprint:
        failures.append("بصمةُ الوثيقة ≠ بصمةَ المُدخَلات في الملفّ — ⛔ بصمةٌ وهمية")
    for lineno, line in enumerate(knowledge_text.splitlines(), 1):
        if re.search(r"\$\d", line) and "[S1" not in line:
            failures.append(f"المعرفة:{lineno}: `$`+رقمٌ بلا سندِ `[S1xx]` على السطر نفسه")
        for figure in COMPUTED_FIGURES:
            if figure in line and "⟨ح⟩" not in line:
                failures.append(f"المعرفة:{lineno}: رقمٌ محسوبٌ ({figure}) بلا وسمِ ⟨ح⟩")


def check_offer_lines(failures: list[str]) -> None:
    """الكتالوج بعد D-296: عضويةٌ مفتوحة (لا حصرَ عددياً) — وكلُّ خطٍّ `PROPOSED` حتى معاملةٍ مُسوّاة.

    حصرُ السبعة (L6 · D-273) ألغاه المالك في D-296 وبقي هنا يعدّ حتى D-297. الشرطان
    الباقيان: مُعرِّفٌ فريد لكلّ خطّ، ولا ترقيةَ فوق `PROPOSED` بلا معاملةٍ مُسوّاة.
    """
    try:
        catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"الكتالوج لا يُقرأ: {exc}")
        return
    offers = catalog.get("offers", [])
    if not offers:
        failures.append("الكتالوج بلا خطوط — كتالوجٌ فارغ ليس عضويةً مفتوحة بل غياباً")
    ids = [str(offer.get("id") or "") for offer in offers]
    duplicates = sorted({identifier for identifier in ids if ids.count(identifier) > 1})
    if duplicates or "" in ids:
        failures.append(f"الكتالوج: مُعرِّفُ خطٍّ مكرَّر أو فارغ {duplicates or ['']} — خطٌّ واحد لكلّ مُعرِّف")
    for offer in offers:
        if offer.get("status") != "PROPOSED":
            failures.append(f"خطُّ {offer.get('id')}: ترقيةٌ بلا معاملةٍ مُسوّاة")


def check_zero_declarations(round_text: str, knowledge_text: str, failures: list[str]) -> None:
    """الصفرُ التجاريُّ مُعلَنٌ في النصَّين معاً — فالغيابُ يُقال ولا يُفهَم."""
    if "صفرُ عقد" not in round_text:
        failures.append("وثيقةُ الجولة لا تُعلِن صفرَ العقد صراحةً")
    if "صفرُ عقد" not in knowledge_text:
        failures.append("وثيقةُ المعرفة لا تُعلِن صفرَ العقد صراحةً")


def check_no_infinity(failures: list[str]) -> None:
    """⛔ `json.dumps` يكتب `Infinity`/`NaN` بلا خطأ — فالمسحُ نصّيٌّ لا قيميّ."""
    try:
        text = ARTIFACT.read_text(encoding="utf-8")
    except OSError:
        failures.append("ملفّ القياس لا يُقرأ للمسح النصّي")
        return
    if "Infinity" in text or "NaN" in text:
        failures.append("⛔ `Infinity`/`NaN` في الملفّ — الغيابُ لا يُلاعَن (D-212)")


def check_reproducibility(failures: list[str]) -> None:
    """الملفُّ المودَع يُعاد بناؤه بايتاً ببايت — فرقمٌ مُحرَّرٌ باليد مستحيل."""
    try:
        completed = subprocess.run(
            [sys.executable, str(MEASURE), "--check"],
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(ROOT),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        failures.append(f"إعادةُ الحساب تعذّرَت: {exc}")
        return
    if completed.returncode != 0:
        failures.append(f"المودَعُ ينحرف عن إعادة الحساب: {completed.stdout.strip()[:200]}")


def check_stdlib_only(failures: list[str]) -> None:
    """الأداةُ والمقياسُ stdlib خالصٌ (باستثناء `shared` و`__future__`) — بفحص AST."""
    allowed_roots = set(sys.stdlib_module_names) | {"shared", "__future__"}
    for path in (TOOL, MEASURE):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            failures.append(f"{path.name} لا يُحلَّل: {exc}")
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".")[0] not in allowed_roots:
                        failures.append(f"{path.name}: استيرادٌ خارج stdlib: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.level != 0:
                    failures.append(f"{path.name}: استيرادٌ نسبيٌّ ممنوع")
                elif (node.module or "").split(".")[0] not in allowed_roots:
                    failures.append(f"{path.name}: استيرادٌ خارج stdlib: {node.module}")


def check_doc_structure(round_text: str, knowledge_text: str, failures: list[str]) -> None:
    """البنيةُ المقطعية: §1–§8 للجولة و§0–§7 للمعرفة — فالمقطعُ الغائبُ حذفٌ صامت."""
    for number in range(1, 9):
        if f"## {number}" not in round_text:
            failures.append(f"وثيقةُ الجولة بلا مقطعٍ `## {number}`")
    for number in range(0, 8):
        if f"## {number}" not in knowledge_text:
            failures.append(f"وثيقةُ المعرفة بلا مقطعٍ `## {number}`")


def main() -> int:
    """يُشغِّل الفحوصَ الستّةَ عشر — ويُعيد 0 نظيفاً و1 عند أيّ انتهاك."""
    failures: list[str] = []
    try:
        ledger = load_csv(LEDGER)
    except OSError as exc:
        print(f"❌ سجلّ الفرضيات لا يُقرأ: {exc}")
        return 1
    try:
        evidence = load_csv(EVIDENCE)
    except OSError as exc:
        print(f"❌ سجلّ الأدلّة لا يُقرأ: {exc}")
        return 1
    try:
        round_text = ROUND.read_text(encoding="utf-8")
        knowledge_text = KNOWLEDGE.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"❌ وثيقةٌ لا تُقرأ: {exc}")
        return 1

    new_files = [ROUND, KNOWLEDGE, EVIDENCE, LEDGER]
    counts = check_ledger(ledger, failures)
    check_declared_counts(round_text, counts, failures)
    check_evidence(evidence, round_text, failures)
    measured = check_measurements(round_text, failures)
    if "artifact" in measured:
        check_fee_nontransfer(measured["artifact"], failures)
        check_knowledge_pins(knowledge_text, measured["artifact"], failures)
    check_naming_guard(new_files, failures)
    check_gate_c(new_files, failures)
    check_forbidden(new_files, failures)
    check_offer_lines(failures)
    check_zero_declarations(round_text, knowledge_text, failures)
    check_no_infinity(failures)
    check_reproducibility(failures)
    check_stdlib_only(failures)
    check_doc_structure(round_text, knowledge_text, failures)

    if failures:
        print("\n".join(f"❌ {failure}" for failure in failures))
        print(f"\n❌ check_decision_round06: {len(failures)} انتهاكاً.")
        return 1
    print(
        "✅ جولة القرار 06 متّسقة: "
        f"{len(ledger)} فرضيات مشتقّة من سجلّها ({counts['completed']} مُنجَزة · "
        f"{counts['partial']} جزئية · {counts['held']} معلّقة)، ⛔ ولا مستوى فوق E1 وE1 واحدةٌ فقط (H71)، "
        f"و{measured.get('matched', 0)} رقماً في §4 مطابقةٌ لملفّ القياس الحتمي، "
        "والاسمُ الميّت محروسٌ في سياقِ البطلان وحده، "
        "ونقلُ الرسم ممنوعٌ كوداً ونصّاً (صافيٌّ واحد قابلٌ للاقتباس)، "
        "وصفرُ تشغيلٍ وصفرُ عقدٍ وصفرُ إيرادٍ معلَنةٌ في الملفّ والنصَّين معاً."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
