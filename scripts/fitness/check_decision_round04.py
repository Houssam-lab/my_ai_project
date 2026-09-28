#!/usr/bin/env python3
"""بوّابة جولة القرار 04 — أرقامُ الجولة مشتقّة، والمدخلُ المفحوص لا يعود إلى النصوص.

**لماذا بوّابة ثالثة بعد `check_decision_round01.py` و`check_decision_round02.py`:**
الجولة 04 تُدخل صنفاً جديداً من الادّعاء لم يكن في الجولتين السابقتين — **رقمٌ واردٌ من
الخارج بلا إسناد**. فبوّابتا 01 و02 تحرسان أرقاماً أنتجناها نحن (سوق، أداة)؛ وهذه تحرس
أرقاماً **أرسلها طرفٌ آخر** وصارت، بمجرّد ورودها، قابلةً للتسرّب إلى نصوصنا كأنّها مسلّمات
(«4.8 مليار» · «CAGR 42%» · «143 دولار/ساعة» · «10 ملايين دولار أرصدة»). والرقمُ الوارد
بلا تاريخٍ أخطرُ من رقمِنا بلا قياس: فهو يحمل سلطةَ قائله لا سلطةَ دليله.

ف تفرض هذه البوّابة أربعة أشياء لا تقبل التأويل:

1. **الاشتقاق:** كلّ رقمٍ في §4 من الجولة يُطابَق مع `docs/research/DLY_MEASUREMENTS.json`
   بمسارٍ مُسمّى وصيغةِ تنسيقٍ مُعلنة — فكتابة «211,813 إجراء» باليد بينما الملفّ يقول
   211,813.6 صارت فشلاً لا رأياً.
2. **التحكيم:** الادّعاءاتُ الواردة الستّة يجب أن تبقى محكومةً في `adjudication_cases`،
   وكلُّ ممنوعٍ يجب أن يحمل بديلاً مُقتبَساً (`rescoped_quotable_claim`) — فالمنعُ بلا
   بديلٍ يصير منعاً للكلام لا تصحيحاً له.
3. **حدُّ القول:** `max_level` لا يتجاوز E1؛ و`exploits_reproduced` و`model_runs_executed`
   و`client_measurements` أصفارٌ في الملفّ **وفي النص**؛ ولا إيرادَ مُدَّعىً.
4. **المحرّمات:** اثنتا عشرة عبارةً يدحضها §3 ممنوعةٌ خارج سياق منعٍ صريح، في وثائق
   القرار والمعرفة والحالة — والعبارةُ المدحوضة تعود إلى النصوص بسهولةٍ أكبر ممّا تعود
   إلى الأرقام.

⛔ لا تقرأ هذه البوّابة شبكةً ولا نموذجاً؛ صفرُ تبعيات خارج المكتبة القياسية.
تُشغَّل من جذر المستودع: `python3 scripts/fitness/check_decision_round04.py` (exit 0/1).
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "studies" / "algeria-hard-currency"
LEDGER = STUDY / "decision_ledger_round04.csv"
EVIDENCE = STUDY / "evidence_round04.csv"
ROUND = STUDY / "DECISION-ROUND-04.md"
ARTIFACT = ROOT / "docs" / "research" / "DLY_MEASUREMENTS.json"
CATALOG = ROOT / "docs" / "commercial" / "OFFER_CATALOG.json"
MEASURE = ROOT / "scripts" / "research" / "measure_decision_latency.py"

#: الوثائق التي تُفحص فيها المحرّمات — كلّ نصٍّ يمكن أن يُقتبس منه ادّعاءٌ واردٌ مدحوض.
SCANNED_DOCS = (
    ROUND,
    ROOT / "docs" / "research" / "HARD_CURRENCY_NEW_KNOWLEDGE_DLY.md",
    ROOT / "docs" / "research" / "HARD_CURRENCY_NEW_KNOWLEDGE_CND.md",
    ROOT / ".memory" / "agent_reliability_hard_currency_truth.md",
    ROOT / "docs" / "commercial" / "FOREIGN_CURRENCY_OPERATING_SYSTEM.md",
)

EXPECTED_HYPOTHESES = 10
EXPECTED_H_RANGE = ("H50", "H59")
EXPECTED_EVIDENCE = 22
EXPECTED_EVIDENCE_RANGE = ("S74", "S95")
#: ⛔ E2 فأعلى ممنوعة في هذه الجولة: لا سقف خسارة معتمداً ولا إذن تشغيل نموذج (محرك §5).
EXPECTED_LEVELS = {"E0", "E1"}
DECLARED_KEYS = {
    "failed": "فاشلة في التكوين الحالي",
    "held": "معلّقة على دليل لازم",
    "partial": "مُنجَزة جزئياً",
    "untested": "غير مفحوصة",
}

#: سياقُ المنع: سطرٌ يحمل علامة المنع أو كلمة نفي/تحريم/دحضٍ صريحة.
NEGATION_MARKERS = (
    "⛔",
    "ممنوع",
    "ممنوعة",
    "لا يجوز",
    "لا يُقتبس",
    "لا يُستعمل",
    "خطأُ فئة",
    "بلا مصدر",
    "بلا قيمةٍ ترتيبية",
    "مدحوض",
    "يدحض",
    "ناقص",
    "خلطُ تعريفَين",
    "غيرُ كاف",
    "فاشلة",
    "معلّقة",
    "تُستبدل",
    "يُستبدل",
    "REFUTED",
    "UNSOURCED",
    "THROTTLED",
)

#: عباراتٌ واردةٌ يدحضها §3: ممنوعةٌ خارج سياق منعٍ صريح.
FORBIDDEN_CLAIMS = (
    "13.5 مليار",
    "CAGR ~42%",
    "~42% إلى",
    "143 دولار/ساعة",
    "10 ملايين دولار أرصدة",
    "$10M أرصدة",
    "14 من 16 نشراً",
    "4.5 يوم داخل بنية",
    "سوقُ تأمين الوكلاء المستقلين بـ",
    "نضمن الامتثال",
    "اكتشفنا ثغرة",
    "إعادةُ إنتاج ناقلي HDF5 وJinja2 في مختبر محلي\n",
)

#: شيفرةُ استغلالٍ ممنوعةٌ في مسار القياس والدراسة — الجولة تقيس الأثرَ التنظيمي لا الشيفرة.
EXPLOIT_PATTERNS = (
    r"169\.254\.169\.254",
    r"h5py\.File\(",
    r"__reduce__",
    r"jinja2\.Environment\(",
    r"Template\(\s*.*\)\.render",
    r"subprocess\.(run|Popen|call)\(\s*[^)]*shell\s*=\s*True",
    r"os\.system\(",
    r"curl\s+-[^ ]*\s+http://169\.",
    r"base64\s+-d\s*\|",
    r"reverse_shell",
    r"bind_shell",
)

#: صفرُ التشغيل وصفرُ الإيراد — تُفرض في الملفّ **وفي النص**.
ZERO_COUNTERS = ("model_runs_executed", "client_measurements", "exploits_reproduced")
NO_REVENUE_PHRASE = "revenue_claim"
NO_SPEND_PHRASE = "لا سقف خسارة معتمداً"
#: سقفُ صفحة القرار (محرك الالتزام §3) — يُجرَّد الترميزُ قبل العدّ.
DECISION_PAGE_WORD_CEILING = 250

#: (مسار JSON · صيغةُ العرض · القيمةُ المُصيَّرة المتوقَّعة · النصّ الذي يجب أن يحويه §4).
#: الصيغةُ **عقدُ عرض**: إن غيّرت تنسيقَ رقمٍ في الوثيقة، فغيّر الصيغة هنا — لا العكس.
#: والفصلُ بين `render` و`doc_token` مقصود: الملفّ يقول 30.0 والوثيقةُ تقول «30.0 دقيقة».
DERIVED_FIGURES: tuple[tuple[str, str, str, str], ...] = (
    ("results.binding_layer", "str", "DECISION", "`DECISION`"),
    ("results.operator_binding_layer", "str", "DECISION", "DECISION"),
    ("results.defender_binding_layer", "str", "UNMEASURED", "`UNMEASURED`"),
    ("results.open_gaps", "int", "2", "`results.open_gaps` = 2"),
    ("results.layer_totals_days.DETECTION", "int", "28", "DETECTION 28"),
    ("results.layer_totals_days.CORRELATION", "int", "0", "CORRELATION 0"),
    ("results.layer_totals_days.DECISION", "int", "45", "DECISION 45"),
    ("results.layer_totals_days.AUTHORITY", "int", "3", "AUTHORITY 3"),
    ("results.decision_to_detection_ratio", "f4", "1.6071", "**45 / 28 = 1.6071**"),
    ("results.technical_days", "f1", "14.0", "62 / 14"),
    ("results.organizational_days", "f1", "62.0", "62 / 14"),
    ("results.organizational_to_technical_ratio", "f4", "4.4286", "**4.4286**"),
    ("results.operator_technical_days", "f1", "10.0", "59 / 10"),
    ("results.operator_organizational_days", "f1", "59.0", "59 / 10"),
    ("results.machine_actions_per_day", "f2c", "3,922.47", "3,922.47"),
    ("results.machine_actions_per_hour", "f2c", "163.44", "163.44"),
    ("results.measurement_window_days", "f4", "4.4903", "4.4903"),
    ("results.tempo_ratio_actions_per_human_decision", "f1c", "211,813.6", "211,813.6"),
    ("results.projected_volume_outside_measurement_window", "none", "None", "`None` **بالقصد**"),
    ("results.transcript_trust_ceiling", "f2", "0.93", "0.93"),
    ("results.transcript_bound_direction", "str", "UPPER_BOUND_ON_TRUST", "`UPPER_BOUND_ON_TRUST`"),
    ("results.requires_out_of_band_evidence", "bool", "True", "`True` · والخصمُ هو المراقَب"),
    ("results.adversary_is_the_monitored", "bool", "True", "والخصمُ هو المراقَب"),
    ("results.harness_delta_at_least", "int", "100", "≥ **100×**"),
    ("results.harness_pair_stated", "bool", "True", "`results.harness_pair_stated`"),
    ("results.monitoring_lead_time_days_at_least", "f1", "1.0", "≥ **1.0 يوم**"),
    ("results.failsafe_policy.decide_within_minutes", "f1", "30.0", "30.0 دقيقة"),
    ("results.failsafe_policy.default_on_silence", "str", "PAUSE", "`PAUSE` عند الصمت"),
    ("results.failsafe_policy.failsafe", "bool", "True", "`failsafe = True`"),
    ("results.reward_wasted", "bool", "True", "**صفر** ⇒"),
    ("results.actions_per_unit_gain", "none", "None", "`actions_per_unit_gain = None`"),
    ("results.unsolvable_tasks.never_solved_by_any_model", "int", "198", "198/898"),
    ("results.unsolvable_tasks.suite_total", "int", "898", "198/898"),
    ("results.unsolvable_tasks.unsolvable_share", "f4", "0.2205", "0.2205"),
    ("results.unsolvable_tasks.chatter_share_from_unsolvable", "f2", "0.93", "→ 0.93 ⇒"),
    ("results.unsolvable_tasks.concentration_ratio", "f4", "4.2179", "**4.2179×**"),
    ("results.grader_divergent", "bool", "True", "`True` · شرطٌ شبحيٌّ واحد"),
    ("results.phantom_requirements", "int", "1", "شرطٌ شبحيٌّ واحد"),
    ("results.market_dispersion_ratio", "f4", "77.9778", "**77.9778×**"),
    ("results.market_number_is_decision_grade", "bool", "False", "قرارِيٌّ = `False`"),
    (
        "results.market_size_dispersion.verdict_flips_only_if_gap_exceeds",
        "f4",
        "77.9778",
        "> 77.9778 فقط",
    ),
    ("inputs.declared_decision_gap_ratio", "f1", "2.0", "`declared_decision_gap_ratio = 2.0`"),
    ("results.self_report_bias_factor", "f4", "2.4983", "**2.4983×**"),
    ("results.rate_bias.band_usd_per_hour.0", "f2", "57.64", "[57.64, 144.00]"),
    ("results.rate_bias.band_usd_per_hour.1", "f2", "144.00", "[57.64, 144.00]"),
    ("results.rate_bias.realized_anchor_present", "bool", "False", "`REALIZED` غائبة"),
    ("results.blocklist_yield_of_partial_block", "f1", "0.0", "**0.0**"),
    ("results.forensic_decode_yield_multiplier.value", "f1", "4.0", "**4.0×**"),
    ("results.sellable_unit", "str", "RESPONSE_COST_REDUCTION", "`RESPONSE_COST_REDUCTION`"),
    ("results.controls_held_share", "f4", "0.7273", "8/11 = **0.7273**"),
    ("results.loss_split.third_party_protected_asset_affected", "bool", "False", "`False`"),
    ("results.loss_split.counts.damage", "int", "3", "ضررٌ 3"),
    ("results.loss_split.counts.response", "int", "13", "استجابةٌ **13**"),
    ("results.loss_split.counts.held", "int", "8", "صمد 8"),
    ("inputs.input_omitted_actions_total", "int", "235", "235"),
)


def squash(text: str) -> str:
    """يُسوّي تتابعات البياض إلى مسافةٍ واحدة.

    **لماذا:** التفافُ السطر في Markdown اختياريٌّ وعرضه 80 عموداً اصطلاحٌ لا قيد. فبوّابةٌ
    تبحث عن عبارةٍ لازمةٍ («لا سقف خسارة معتمداً») بمطابقةٍ حرفية تسقط حين يفصل الالتفافُ
    كلمتَيها — وتفشل على نصٍّ سليم. فالمطابقةُ تُجرى على النصّ المُسوّى، لا على التفافه.
    """
    return re.sub(r"\s+", " ", text)


def load_csv(path: Path) -> list[dict[str, str]]:
    """يقرأ سجلاً CSV — والفشلُ صريحٌ لا قائمةٌ فارغة تُقرأ نجاحاً."""
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def dig(artifact: dict, dotted: str) -> object:
    """ينزل في مسارٍ مُنقَّط — وغيابُ المفتاح خطأٌ صريح لا `None` يُقرأ قيمةً."""
    node: object = artifact
    for part in dotted.split("."):
        if part.isdigit() and isinstance(node, list):
            if int(part) >= len(node):
                raise KeyError(f"دليلُ قائمةٍ خارج الحدود في {dotted} (توقّف عند {part!r})")
            node = node[int(part)]
            continue
        if not isinstance(node, dict) or part not in node:
            raise KeyError(f"مسارٌ غائب في ملفّ القياس: {dotted} (توقّف عند {part!r})")
        node = node[part]
    return node


def _render_bool(value: object) -> str:
    return "True" if value is True else "False"


def _render_none(value: object) -> str:
    return "None" if value is None else f"⛔ القيمة ليست None: {value!r}"


def _render_int(value: object) -> str:
    return str(int(value))  # type: ignore[arg-type]


def _render_f1(value: object) -> str:
    return f"{float(value):.1f}"  # type: ignore[arg-type]


def _render_f2(value: object) -> str:
    return f"{float(value):.2f}"  # type: ignore[arg-type]


def _render_f4(value: object) -> str:
    return f"{float(value):.4f}"  # type: ignore[arg-type]


def _render_f1c(value: object) -> str:
    return f"{float(value):,.1f}"  # type: ignore[arg-type]


def _render_f2c(value: object) -> str:
    return f"{float(value):,.2f}"  # type: ignore[arg-type]


#: جدولُ التوزيع: الصيغةُ مفتاحٌ لا سلسلةُ فروع — فإضافةُ صيغةٍ جديدة لا ترفع
#: عدّادَ الفروع في `render` (PLR0911/PLR0912)، و`ValueError` على المجهولة باقٍ عقداً.
#: بلا تعليقٍ نوعيٍّ عمداً: `test_gate_module_is_stdlib_only` يُبقي سطحَ استيرادِ
#: البوّابةِ خمسَ وحداتٍ لا أكثر، و`collections.abc` سادسةٌ لا يبرّرها شيء.
_RENDERERS = {
    "str": str,
    "bool": _render_bool,
    "none": _render_none,
    "int": _render_int,
    "f1": _render_f1,
    "f2": _render_f2,
    "f4": _render_f4,
    "f1c": _render_f1c,
    "f2c": _render_f2c,
}


def render(value: object, spec: str) -> str:
    """يُصيّر قيمة JSON إلى نصّها في الوثيقة — والصيغةُ جزءٌ من العقد لا تفصيلٌ تجميلي."""
    try:
        renderer = _RENDERERS[spec]
    except KeyError:
        raise ValueError(f"صيغةُ تنسيقٍ غير معروفة: {spec!r}") from None
    return renderer(value)


def bucket_state(state: str) -> str:
    """تصنيفُ حالة البوابة — المصدرُ `gate_state` لا نصٌّ يدوي في الوثيقة."""
    if state.startswith("فاشلة"):
        return "failed"
    if state.startswith("مُنجَزة") or state.startswith("منجزة"):
        return "partial"
    if state.startswith("غير مفحوصة"):
        return "untested"
    if "معلّقة" in state or "معلقة" in state:
        return "held"
    return "other"


def _check_ledger_identity(ledger: list[dict[str, str]], failures: list[str]) -> None:
    """صفّيةُ السجل وتفريدُ معرّفاته واتصالُها وسقوفُ التزامه — خمسةُ فروعٍ لا أكثر."""
    if len(ledger) != EXPECTED_HYPOTHESES:
        failures.append(f"سجلّ الجولة 04 يحوي {len(ledger)} صفاً، والمتوقّع {EXPECTED_HYPOTHESES}")
    ids = [row["id"] for row in ledger]
    if len(set(ids)) != len(ids):
        failures.append("معرّفات الفرضيات غير فريدة")
    want = [f"H{n}" for n in range(int(EXPECTED_H_RANGE[0][1:]), int(EXPECTED_H_RANGE[1][1:]) + 1)]
    if ids != want:
        failures.append(f"معرّفات الفرضيات {ids}، والمتوقّع اتّصالاً {want}")
    levels = {row["max_level"] for row in ledger}
    if not levels <= EXPECTED_LEVELS:
        failures.append(
            f"مستويات التزام خارج E0/E1 معلَنة في السجل: {sorted(levels - EXPECTED_LEVELS)} — "
            f"⛔ {NO_SPEND_PHRASE}، فلا E2 في هذه الجولة (محرك الالتزام §5)"
        )


def _check_ledger_row(row: dict[str, str], counts: dict[str, int], failures: list[str]) -> None:
    """صفٌّ واحد: اكتمالُ الحقول وحصيلتُه وصيغةُ ترقيمه — والمنطقُ حرفيٌّ كما كان."""
    key = bucket_state(row["gate_state"])
    if key in counts:
        counts[key] += 1
    if not (row["hypothesis_ar"] and row["counterparty"]):
        failures.append(f"{row['id']}: صفٌّ بلا فرضيةٍ أو بلا طرفٍ مقابل")
    if not (row["binding_gate"] and row["gate_state"] and row["decision"]):
        failures.append(f"{row['id']}: صفٌّ بلا بوّابة حاكمة أو حالة أو قرار")
    if not row["shared_dependency"]:
        failures.append(f"{row['id']}: صفٌّ بلا اعتماد مشترك — «محفظة متنوّعة» بلا فحص العُقد")
    if bucket_state(row["gate_state"]) == "other":
        failures.append(
            f"{row['id']}: حالةُ بوّابةٍ لا تُصنَّف ({row['gate_state'][:40]}…) — "
            "⛔ الحالةُ المعلَنة يجب أن تبدأ بأحد التصريحات الأربعة في §6.1"
        )
    for field in ("key_claim", "key_test"):
        value = row[field]
        if value != "-" and not re.fullmatch(r"[CT]\d\d( [CT]\d\d)*", value):
            failures.append(f"{row['id']}: {field}={value!r} خارج الصيغة [CT]nn")


def _check_ledger_numbering(ledger: list[dict[str, str]], failures: list[str]) -> None:
    """اتصالُ الترقيم مع الجولة 03 (C38–C46 · T37–T44): ⛔ لا إعادةُ استعمالٍ ولا قفز."""
    claims = {int(m) for row in ledger for m in re.findall(r"C(\d+)", row["key_claim"])}
    tests = {int(m) for row in ledger for m in re.findall(r"T(\d+)", row["key_test"])}
    if claims and min(claims) <= 46:
        failures.append(
            f"أرقامُ ادّعاءاتٍ معادٌ استعمالها من الجولة 03: {sorted(c for c in claims if c <= 46)}"
        )
    if tests and min(tests) <= 44:
        failures.append(
            f"أرقامُ بطاقاتٍ معادٌ استعمالها من الجولة 03: {sorted(t for t in tests if t <= 44)}"
        )


def check_ledger(ledger: list[dict[str, str]], failures: list[str]) -> dict[str, int]:
    """بنيةُ السجل: صفّية، تفريد، اتصالُ الترقيم، ⛔ ولا مستوى فوق E1."""
    counts = dict.fromkeys(DECLARED_KEYS, 0)
    _check_ledger_identity(ledger, failures)
    for row in ledger:
        _check_ledger_row(row, counts, failures)
    _check_ledger_numbering(ledger, failures)
    return counts


def check_declared_counts(round_text: str, counts: dict[str, int], failures: list[str]) -> None:
    """جدولُ المسح في §6.1 يجب أن يساوي ما يشتقّه الفارض من السجل — لا ما يذكره الكاتب."""
    for key, label in DECLARED_KEYS.items():
        want = counts[key]
        # الجدولُ يكتب «| **<label>** (…) | **N** |» أو «| <label> | N |».
        row = re.search(
            rf"\|\s*(?:\*\*)?{re.escape(label)}[^\n|]*\|\s*(?:\*\*)?(\d+)(?:\*\*)?\s*\|", round_text
        )
        if not row:
            failures.append(f"§6.1: لا صفَّ معلن لـ«{label}» في جدول المسح")
            continue
        if int(row.group(1)) != want:
            failures.append(
                f"§6.1: «{label}» معلَنة {row.group(1)} بينما السجلّ يشتقّ {want} — "
                "⛔ الرقمُ المكتوب يدوياً ليس اشتقاقاً"
            )


def check_levels_declared(
    round_text: str, ledger: list[dict[str, str]], failures: list[str]
) -> None:
    """عددا E1 وE0 في §6.1 يجب أن يطابقا السجلّ."""
    n_e1 = sum(1 for row in ledger if row["max_level"] == "E1")
    n_e0 = sum(1 for row in ledger if row["max_level"] == "E0")
    for label, want in (("E1", n_e1), ("E0", n_e0)):
        row = re.search(
            rf"\|\s*(?:\*\*)?سقفٌ أقصى مسموح = {label}[^\n|]*\|\s*(?:\*\*)?(\d+)(?:\*\*)?\s*\|",
            round_text,
        )
        if not row:
            row = re.search(
                rf"\|\s*(?:\*\*)?الباقي عند {label}[^\n|]*\|\s*(?:\*\*)?(\d+)(?:\*\*)?\s*\|",
                round_text,
            )
        if not row:
            failures.append(f"§6.1: لا صفَّ معلن لعدد {label}")
            continue
        if int(row.group(1)) != want:
            failures.append(f"§6.1: عددُ {label} معلَن {row.group(1)} بينما السجلّ يشتقّ {want}")


def check_evidence(evidence: list[dict[str, str]], failures: list[str]) -> None:
    """سجلّ الأدلة: عدٌّ، اتصالُ نطاق S74–S95، تاريخُ استرجاعٍ لكلّ صفّ، وحالةُ مصدرٍ صالحة."""
    if len(evidence) != EXPECTED_EVIDENCE:
        failures.append(
            f"سجلّ أدلّة الجولة 04 يحوي {len(evidence)} سنداً، والمتوقّع {EXPECTED_EVIDENCE}"
        )
    ids = [row["id"] for row in evidence]
    want = [
        f"S{n}"
        for n in range(int(EXPECTED_EVIDENCE_RANGE[0][1:]), int(EXPECTED_EVIDENCE_RANGE[1][1:]) + 1)
    ]
    if ids != want:
        failures.append(f"معرّفات الأدلّة {ids[:3]}…{ids[-2:]}, والمتوقّع اتّصالاً {want[0]}–{want[-1]}")
    #: عُرفُ الأعمدة موروثٌ من الجولتين 02/03 — ⛔ لا اختراعَ مخطّطٍ جديد في الجولة 04.
    want_cols = [
        "id",
        "claim_summary_ar",
        "source",
        "url",
        "as_of",
        "status",
        "independence_note",
        "reverification_trigger",
    ]
    if evidence and list(evidence[0].keys()) != want_cols:
        failures.append(
            f"أعمدةُ سجلّ الأدلّة {list(evidence[0].keys())}، والمتوقّع عُرفَ الجولتين 02/03: {want_cols}"
        )
    #: درجاتُ المصدر المعتمدة في السجلّ: P (أوّل) · M (ثانوي) · L (منخفض) + لاحقتا H/M، وUNSTATED.
    grade = re.compile(r"^(?:P|M|L)(?:-[HM])?\s+—")
    for row in evidence:
        sid = row.get("id", "?")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.get("as_of", "")):
            failures.append(
                f"{sid}: `as_of` غائبٌ أو غير صالح ({row.get('as_of', '')!r}) — T43 يلزم تاريخاً لكلّ صفّ"
            )
        status = row.get("status", "")
        if not (grade.match(status) or status.startswith("UNSTATED")):
            failures.append(
                f"{sid}: درجةُ مصدرٍ خارج العُرف (P/M/L ± H/M أو UNSTATED): {status[:30]!r}"
            )
        url = row.get("url", "")
        if not url and not status.startswith("UNSTATED"):
            failures.append(f"{sid}: سندٌ بلا رابطٍ ولا وسم UNSTATED")
        #: ⛔ حاشيةٌ مكان الرابط تُقرأ إسناداً: فإمّا `http…`، أو إعلانُ غيابٍ صريح في صفٍّ UNSTATED.
        if url and not url.startswith("http") and not status.startswith("UNSTATED"):
            failures.append(
                f"{sid}: `url` ليس رابطاً ({url[:28]!r}) والصفُّ ليس UNSTATED — "
                "⛔ حاشيةٌ مكان الرابط تُقرأ إسناداً"
            )
        if status.startswith("UNSTATED") and url.startswith("http"):
            failures.append(f"{sid}: صفٌّ موسومٌ UNSTATED ومع ذلك يحمل رابطاً — ⛔ الوسمُ يناقض السند")
        if not row.get("independence_note"):
            failures.append(f"{sid}: سندٌ بلا ملاحظةِ استقلال — ومحورُ التحكيم الأوّل هو الاستقلال")
        if not row.get("reverification_trigger"):
            failures.append(f"{sid}: سندٌ بلا محفّزِ إعادة تحقّق — فالدليلُ بلا تاريخِ انتهاء")


def check_measurements(round_text: str, failures: list[str]) -> dict:
    """كلّ رقمٍ في §4 مطابَقٌ بملفّ القياس بمسارٍ مُسمّى، وبصيغةِ عرضٍ معلَنة."""
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    matched = 0
    for dotted, spec, want_render, doc_token in DERIVED_FIGURES:
        try:
            value = dig(artifact, dotted)
        except KeyError as exc:
            failures.append(str(exc))
            continue
        got = render(value, spec)
        if got != want_render:
            failures.append(
                f"{dotted}: الملفّ يقول {value!r} ⇒ يُصيَّر {got!r}، وعقدُ العرض يتوقّع {want_render!r} — "
                "⛔ غيّر الصيغة في الفارض إن كان التنسيق هو المقصود، لا الرقمَ في الوثيقة"
            )
            continue
        if doc_token not in squash(round_text):
            failures.append(
                f"§4: الرمزُ المشتقّ {doc_token!r} ({dotted}) غائبٌ عن وثيقة الجولة — "
                "⛔ رقمٌ في الملفّ بلا مقابلٍ في النصّ هو رقمٌ لا يُقرأ"
            )
            continue
        matched += 1
    return {"artifact": artifact, "matched": matched}


def check_adjudication(artifact: dict, round_text: str, failures: list[str]) -> None:
    """التحكيم: 6 ادّعاءاتٍ، 5 ممنوعةٌ كما وردت، وكلُّ ممنوعٍ يحمل بديلاً مُقتبَساً."""
    cases = artifact.get("results", {}).get("adjudication_cases", [])
    if len(cases) != 6:
        failures.append(f"adjudication_cases يحوي {len(cases)} ادّعاءً، والمتوقّع 6")
        return
    quotable = [case for case in cases if case.get("quotable_as_cited") is True]
    if len(quotable) != 1:
        failures.append(
            f"{len(quotable)} ادّعاءً مقبولٌ كما ورد، والمتوقّع 1 (وقائعُ الحادث بتصحيحٍ واحد) — "
            "⛔ قبولُ ادّعاءٍ واردٍ بلا إسنادٍ هو بالضبط ما تمنعه هذه الجولة"
        )
    for case in cases:
        claim = str(case.get("claim_in_input", "?"))[:36]
        if not case.get("verdict"):
            failures.append(f"ادّعاءٌ بلا حكم: {claim}")
        if case.get("quotable_as_cited") is not True and not case.get("rescoped_quotable_claim"):
            failures.append(
                f"ادّعاءٌ ممنوعٌ بلا بديلٍ مُقتبَس (`rescoped_quotable_claim`): {claim} — "
                "⛔ المنعُ بلا بديلٍ يصير منعاً للكلام لا تصحيحاً له"
            )
        if case.get("claim_kind") == "BENCHMARK_SCORE" and case.get("pin_axis_applies") is not True:
            failures.append(f"درجةٌ معيارية بلا تطبيقٍ لمحور الدبوس: {claim}")
        if case.get("claim_kind") != "BENCHMARK_SCORE" and case.get("pin_axis_applies") is True:
            failures.append(
                f"محورُ الدبوس مُعلَن منطبقاً على {case.get('claim_kind')} — ⛔ H59: الدبوسُ محكومُ "
                f"المجال بدرجةٍ معيارية، وتطبيقُه على غيرها يُنتج UNPINNED كاذباً: {claim}"
            )
        if case.get("date_present_in_input") is False and case.get("age_days_at_as_of") is not None:
            failures.append(
                f"تاريخٌ غائبٌ في المدخل وعمرٌ محسوب مع ذلك: {claim} — ⛔ الغائبُ يُقرأ None لا طازجاً"
            )
    #: الحكمُ على المدخل كلّه يجب أن يبقى مذكوراً في الوثيقة.
    if "خمسةٌ ممنوعةُ الاقتباس كما وردت" not in squash(round_text):
        failures.append("§3/§5.6: حصيلةُ التحكيم (5 ممنوعة · 1 مقبولٌ بتصحيح) غائبةٌ عن وثيقة الجولة")


def check_zero_counters(artifact: dict, round_text: str, failures: list[str]) -> None:
    """صفرُ تشغيلٍ وصفرُ إيرادٍ في الملفّ **وفي النص** — L9: لا استعارةَ دليلِ الغير دليلاً لنا."""
    for name in ZERO_COUNTERS:
        value = artifact.get(name, "MISSING")
        if value != 0:
            failures.append(f"{name} = {value!r} في ملفّ القياس، والمتوقّع 0")
        if f"{name} = 0" not in squash(round_text):
            failures.append(f"§9: العدّاد {name} = 0 غيرُ مُعلَن في وثيقة الجولة")
    revenue = str(artifact.get(NO_REVENUE_PHRASE, "MISSING"))
    if not revenue.startswith("NONE"):
        failures.append(f"{NO_REVENUE_PHRASE} = {revenue!r}، والمتوقّع بادئةُ 'NONE'")
    if NO_SPEND_PHRASE not in squash(round_text):
        failures.append(f"§1: عبارةُ «{NO_SPEND_PHRASE}» غائبة — ⛔ لا توصيةَ بإنفاقٍ بلا سقف")
    if "لا يُسوَّى تعارضُ الدافع" not in squash(round_text):
        failures.append("§6.3: عدمُ تسويةِ تعارضِ الدافع بين الروايات الثلاث غيرُ مُعلَن (محرك §8)")


def check_no_exploit_code(failures: list[str]) -> None:
    """لا شيفرةَ استغلالٍ في مسار القياس ولا في وثائق الدراسة — الجولة تقيس الأثرَ لا الناقل."""
    for path in (MEASURE, ARTIFACT, ROUND, STUDY / "evidence_round04.csv", LEDGER):
        text = path.read_text(encoding="utf-8")
        for pattern in EXPLOIT_PATTERNS:
            if re.search(pattern, text):
                failures.append(
                    f"{path.name}: نمطُ استغلالٍ {pattern!r} موجودٌ في مسار القياس — "
                    "⛔ إعادةُ إنتاج نواقل الحادثة ممنوعةٌ في التكوين الحالي (§7 R6)"
                )


def check_forbidden_claims(failures: list[str]) -> None:
    """الادّعاءاتُ الواردة المدحوضة لا تعود إلى نصوصنا خارج سياق منعٍ صريح."""
    for path in SCANNED_DOCS:
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for claim in FORBIDDEN_CLAIMS:
                needle = claim.rstrip("\n")
                if needle in line and not any(marker in line for marker in NEGATION_MARKERS):
                    failures.append(
                        f"{path.name}:{lineno}: عبارةٌ يدحضها §3 ({needle!r}) خارج سياق منعٍ صريح"
                    )


def check_offer_lines(failures: list[str]) -> None:
    """قانون الكتالوج بعد D-296: عضويةٌ مفتوحة — لا حصرَ عددياً، لكن لا كتالوجَ فارغاً ولا مُعرِّفاً مكرَّراً.

    كان هنا حصرُ السبعة (L6 · D-273). ألغاه المالك كتابةً في D-296 (2026-09-19) وبقي هذا
    الفارضُ يعدّ — فارضٌ يناقض قانوناً حيّاً، وهو ما أصلحه D-297. الشرطُ الباقي بنيوي.
    """
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    lines = catalog.get("offer_lines") or catalog.get("offers") or []
    if not lines:
        failures.append("OFFER_CATALOG.json بلا خطوط — كتالوجٌ فارغ ليس عضويةً مفتوحة بل غياباً")
    ids = [str(line.get("id") or "") for line in lines]
    duplicates = sorted({identifier for identifier in ids if ids.count(identifier) > 1})
    if duplicates or "" in ids:
        failures.append(
            f"OFFER_CATALOG.json: مُعرِّفُ خطٍّ مكرَّر أو فارغ {duplicates or ['']} — خطٌّ واحد لكلّ مُعرِّف"
        )


def check_reproducibility(failures: list[str]) -> None:
    """ملفّ القياس يُعاد توليدُه من بنائه — ⛔ لا رقمَ في الجولة بلا مصدرٍ حتمي."""
    sys.path.insert(0, str(MEASURE.parent))
    try:
        module = __import__(MEASURE.stem)
        rebuilt = module.build()
        rebuilt["inputs_digest_sha256"] = module._canonical_digest(rebuilt)
    #: `BLE001` غيرُ مفعَّلةٍ في هذا المستودع — والتعليقُ يبقى توثيقاً لا توجيهاً:
    #: التقاطُ `Exception` هنا فشلٌ صريحٌ يُبلَّغ، لا تجاوزٌ صامت.
    except Exception as exc:
        failures.append(f"تعذّرت إعادةُ بناء ملفّ القياس: {type(exc).__name__}: {exc}")
        return
    on_disk = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    #: ⛔ `generated_at` طابعُ وقتٍ لا مدخل — مقارنتُه تجعل البوّابة تفشل كلّ ثانية.
    #: فالمقارنةُ على ما يقارنه `--check` نفسه: الهويةُ والتاريخُ وبصمةُ المدخلات والنتائج.
    for key in ("kind", "as_of", "inputs_digest_sha256"):
        if on_disk.get(key) != rebuilt.get(key):
            failures.append(
                f"ملفّ القياس: انحرافٌ في {key}: {on_disk.get(key)!r} ≠ المحسوب {rebuilt.get(key)!r}"
            )
    if on_disk.get("results") != rebuilt.get("results"):
        disk_keys = set(on_disk.get("results", {}))
        new_keys = set(rebuilt.get("results", {}))
        diff = sorted(disk_keys ^ new_keys) or [
            k
            for k in sorted(disk_keys & new_keys)
            if on_disk["results"][k] != rebuilt["results"][k]
        ]
        failures.append(
            f"ملفّ القياس: `results` على القرص لا تُعاد بناؤها حرفياً؛ المختلف: {diff[:6]} — "
            "⛔ شغّل `python3 scripts/research/measure_decision_latency.py` قبل الاعتماد على أيّ رقم"
        )


def check_doc_structure(round_text: str, failures: list[str]) -> None:
    """أقسامٌ إلزامية: صفحةُ قرار، عقدُ D04، جدولُ دحض، بطاقات، حدود، بوابةٌ أخلاقية."""
    required = (
        "## 1. صفحة القرار",
        "## 2. عقد القرار D04",
        "## 3. ما دُحض في هذه الجولة",
        "## 4. الأرقام المستعملة",
        "## 5. المعرفة الجديدة",
        "## 6. الفصل الثلاثي",
        "## 7. البوابة القانونية والأخلاقية",
        "## 8. البطاقات التالية",
        "## 9. حدودُ هذه الجولة",
    )
    flat = squash(round_text)
    for section in required:
        if section not in flat:
            failures.append(f"وثيقة الجولة 04: قسمٌ إلزامي غائب: {section!r}")
    #: صفحةُ القرار محكومةٌ بطولٍ (المحرك §3): ≤250 كلمة بين عنوانها والعقد.
    #: ⛔ الترميزُ يُجرَّد قبل العدّ، والسقفُ المطبَّق هو المعلن — لا سقفٌ أوسعُ في الكود
    #: ورسالةٌ تقول غيره؛ فبوّابةٌ تكذب عن حدّها أسوأُ من غيابها.
    body = round_text.split("## 1. صفحة القرار", 1)[-1].split("## 2. عقد القرار", 1)[0]
    words = len(re.findall(r"[\w\u0600-\u06FF]+", re.sub(r"[*`>|#_]", " ", body)))
    if words > DECISION_PAGE_WORD_CEILING:
        failures.append(
            f"صفحةُ القرار {words} كلمة، والسقفُ {DECISION_PAGE_WORD_CEILING} (محرك §3) — "
            "⛔ القرارُ الذي لا يُقرأ لا يُتَّخذ"
        )
    #: كلّ بطاقةٍ من T45 إلى T54 يجب أن تكون معيارَ خروجٍ لا عنوانَ نيّة.
    for card in range(45, 55):
        if f"**T{card}**" not in round_text:  # البطاقاتُ عناوينُ أسطر، لا تُسوّى
            failures.append(f"§8: البطاقة T{card} غائبة عن جدول الخطوات التالية")


def main() -> int:
    for path in (LEDGER, EVIDENCE, ROUND, ARTIFACT, CATALOG, MEASURE):
        if not path.exists():
            print(f"❌ check_decision_round04: ملفٌّ لازمٌ غائب: {path}")
            return 1
    failures: list[str] = []
    ledger = load_csv(LEDGER)
    round_text = ROUND.read_text(encoding="utf-8")

    counts = check_ledger(ledger, failures)
    check_declared_counts(round_text, counts, failures)
    check_levels_declared(round_text, ledger, failures)
    check_evidence(load_csv(EVIDENCE), failures)
    measured = check_measurements(round_text, failures)
    if "artifact" in measured:
        check_adjudication(measured["artifact"], round_text, failures)
        check_zero_counters(measured["artifact"], round_text, failures)
    check_no_exploit_code(failures)
    check_forbidden_claims(failures)
    check_offer_lines(failures)
    check_reproducibility(failures)
    check_doc_structure(round_text, failures)

    if failures:
        print("\n".join(f"❌ {failure}" for failure in failures))
        print(f"\n❌ check_decision_round04: {len(failures)} انتهاكاً.")
        return 1
    print(
        "✅ جولة القرار 04 متّسقة: "
        f"{len(ledger)} فرضيات مشتقّة من سجلّها، ⛔ لا مستوى فوق E1، "
        f"و{measured.get('matched', 0)} رقماً عن الأداة في §4 مطابقةٌ لملفّ القياس الحتمي، "
        "و6 ادّعاءاتٍ واردةٍ محكومة (5 ممنوعةٌ كما وردت وكلٌّ ببديلٍ مُقتبَس)، "
        "وصفرُ تشغيلٍ وصفرُ إيرادٍ وصفرُ شيفرةِ استغلالٍ معلَنةٌ في الملفّ والنصّ معاً."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
