#!/usr/bin/env python3
"""بوّابة جولة القرار 05 — الدبوسُ محروسٌ في مجاله، والتعارضُ لا يُسوَّى بمتوسط.

**لماذا بوّابة رابعة بعد بوّابات الجولات 01 و02 و04:** البوّاباتُ السابقة تحرس أرقاماً
أنتجناها أو وردت إلينا. وهذه تحرس **شرطَ اقتباس الرقم نفسه** — الدبوس. فالجولة 04 اكتشفت
أنّ `evaluate_pin` يُنتج `UNPINNED` خارج مجاله فسمّته عيباً؛ والجولة 05 تختبره في مجاله
الصحيح على طرفٍ أوّل يملك الحزمة، فتجد **صفرَ `UNPINNED`** وأنّ الحكمَ كلُّه من العمر. وما
لم يكن عند أيّ بوّابةٍ سابقة هو حراسةُ ثلاثة انضباطاتٍ لا تنتج من «الرقمُ صحيح»:

1. **حارسُ المجال:** إن ظهر `UNPINNED` على دبوسٍ كاملِ الحقول في المجال الصحيح، فالخللُ في
   القياس لا في الأداة — وتفشل البوّابة بدل أن تُنتج حكماً كاذباً.
2. **انضباطُ صفرِ المقام:** نسبةٌ مقامُها صفر تُسجَّل **زوجاً** (`PAIR_NOT_RATIO`) — ⛔ لا
   `inf` ولا صفر. والبوّابة تفحص أنّ الملفّ كلّه لا يحوي `Infinity` ولا `NaN`.
3. **انضباطُ التعارض:** طرفان أوّلان مستقلّان على الحزمة نفسها يعطيان 22.05% و80.29%.
   ⛔ لا متوسط، ولا «تسوية»، ولا اقتباسٌ بلا دبوس — والأساسُ
   `PIN_DIFFERENCE_NOT_AVERAGE` منصوصٌ في الملفّ وتفرضه البوّابة.

وتفرض كذلك ما تفرضه سابقاتُها: الاشتقاقُ من `BPIN_MEASUREMENTS.json` بمسارٍ مُسمّى، وحدُّ
القول E1 لفرضيةٍ واحدة، وأصفارُ التشغيل والإيراد والشيفرة في الملفّ **وفي النص**، وتصحيحُ
النسب (`suite.owner` يبدأ بـBerkeley RDI لا بـOpenAI)، والمحرّماتُ لا تعود إلى النصوص.

⛔ لا تقرأ هذه البوّابة شبكةً ولا نموذجاً؛ صفرُ تبعيات خارج المكتبة القياسية.
تُشغَّل من جذر المستودع: `python3 scripts/fitness/check_decision_round05.py` (exit 0/1).
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "studies" / "algeria-hard-currency"
LEDGER = STUDY / "decision_ledger_round05.csv"
EVIDENCE = STUDY / "evidence_round05.csv"
ROUND = STUDY / "DECISION-ROUND-05.md"
ARTIFACT = ROOT / "docs" / "research" / "BPIN_MEASUREMENTS.json"
CATALOG = ROOT / "docs" / "commercial" / "OFFER_CATALOG.json"
MEASURE = ROOT / "scripts" / "research" / "measure_benchmark_pin.py"

#: الوثائق التي تُفحص فيها المحرّمات — كلّ نصٍّ يمكن أن يُقتبس منه ادّعاءٌ مدحوض.
SCANNED_DOCS = (
    ROUND,
    ROOT / ".memory" / "agent_reliability_hard_currency_truth.md",
    STUDY / "evidence_round05.csv",
    STUDY / "decision_ledger_round05.csv",
)

EXPECTED_HYPOTHESES = 10
EXPECTED_H_RANGE = ("H60", "H69")
EXPECTED_EVIDENCE = 8
EXPECTED_EVIDENCE_RANGE = ("S96", "S103")
#: ⛔ E2 فأعلى ممنوعة: لا سقف خسارة معتمداً، ولا مرساةَ فاتورة، ولا إذنَ تشغيل حزمةٍ هجومية.
EXPECTED_LEVELS = {"E0", "E1"}
#: الفرضيةُ الوحيدةُ المسموح لها بـE1 — وأيُّ تغييرٍ هنا تغييرٌ في قرار الجولة لا في البوّابة.
SINGLE_E1_HYPOTHESIS = "H61"

DECLARED_KEYS = {
    "completed": "مُنجَزة",
    "partial": "مُنجَزة جزئياً",
    "held": "معلّقة على دليل لازم",
    "failed": "فاشلة في التكوين الحالي",
    "untested": "غير مفحوصة",
}
#: حقولُ الدبوس على مستوى الزوج (المخطّطُ **مسطّح** في `per_pin` لا متداخل تحت `pin`).
#: ومحورا `suite_version` و`report_date` على مستوى الحزمة (`suite.version` · `suite_issued_on`)
#: لأنّ الدبابيس السبعة تشترك فيهما — فتُفحصان مرّةً واحدة لا سبعاً.
PIN_FIELDS = ("model_id", "harness", "safeguard_config", "adversary_budget_minutes")
SUITE_PIN_FIELDS = (
    ("suite.version", "suite_version"),
    ("results.pin_evaluations.suite_issued_on", "report_date"),
)

#: سياقُ المنع: سطرٌ يحمل علامة المنع أو كلمة نفي/تحريم/دحضٍ صريحة.
NEGATION_MARKERS = (
    "⛔",
    "ممنوع",
    "ممنوعة",
    "لا يجوز",
    "لا يُقتبس",
    "لا يُستعمل",
    "لا يُقرأ",
    "لا تُقرأ",
    "لا يُحتسب",
    "لا تُحتسب",
    "لا تُنقل",
    "خطأُ فئة",
    "بلا مصدر",
    "بلا قيمةٍ ترتيبية",
    "مدحوض",
    "يدحض",
    "خاطئة",
    "خاطئ",
    "ناقص",
    "غيرُ كاف",
    "فاشلة",
    "معلّقة",
    "ليست",
    "ليس",
    "REFUTED",
    "UNSOURCED",
    "THROTTLED",
)
#: ⛔ «لا» المجرّدة **ليست** علامةَ نفيٍ هنا: فهي في أغلب الأسطر العربية (نافيةً كانت أو
#: واصلةً أو part of «لا يُقتبس»), فعدُّها علامةً يجعل فحصَ المحرّمات يمرّ على كلّ سطرٍ تقريباً
#: ويصير البرهانُ السلبي زينة. فالمطلوب نفيٌ **مُحدَّد** (ليست/ليس/ممنوع/⛔) لا حرفٌ شائع.

#: عباراتٌ يدحضها §3: ممنوعةٌ خارج سياق منعٍ صريح. والأربعُ الأخيرة جديدةٌ في هذه الجولة.
FORBIDDEN_CLAIMS = (
    # موروثاتُ الجولة 03/04 — تبقى مدحوضةً في كلّ نصٍّ تُمسحه هذه البوّابة.
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
    "إعادةُ إنتاج ناقلي HDF5 وJinja2 في مختبر محلي",
    # R1: العبارةُ العامة صادقةٌ إجمالاً وخاطئةٌ تفصيلاً — فالتفصيلُ هو المسموح.
    "الحماياتُ القياسية لا تكفي",
    # R2: CPST المنشورة كلفةُ تشغيلِ وكيلٍ على حزمةٍ هجومية، لا سعرُ خدمةٍ دفاعية.
    "هذا سعرُ خدمتنا",
    # R4: متوسطُ طرفَين أوّليين بدبوسَين مختلفَين رقمٌ بلا مرجع.
    "متوسطُ النسبتَين",
    # R8: رقمُ قدرةٍ هجومية لطرفٍ ثالث، ⛔ لا يُستعمل في عرضٍ دفاعي لنا.
    "34 ثغرة يوم-صفر",
)

#: ⛔ سلسلةُ تقنيات الاستغلال: ممنوعةٌ في مسار القياس ووثائق الدراسة.
#: الحماياتُ **بأسمائها** (ASLR · KASLR · canaries · heap sandbox) مسموحة: فاسمُ الدفاع
#: معلومةٌ تنظيمية، بينما سلسلةُ الاختراق (OOB ← تسريبُ مؤشّر ← …) تفاصيلُ ناقلٍ مُحرَّمة.
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
    # سلسلةُ تقنيات V8/kernel المُعلَنة في المصدر — ⛔ لا تُنسخ في أيّ نصٍّ لنا (§6.3).
    r"SROP",
    r"sigreturn",
    r"type\s+confusion",
    r"out[-\s]of[-\s]bounds",
    r"\bOOB\b",
    r"pointer\s+leak",
    r"fake\s+(?:string|object)",
    r"arbitrary\s+(?:read|write)",
    r"libc\s+leak",
    r"heap\s+spray",
    r"use[-\s]after[-\s]free",
    r"rop\s+chain",
    r"shellcode",
)

ZERO_COUNTERS = ("model_runs_executed", "client_measurements", "exploits_reproduced")
NO_REVENUE_PHRASE = "revenue_claim"
NO_SPEND_PHRASE = "بلا إنفاقٍ نقدي"
DECISION_PAGE_WORD_CEILING = 250
#: ⛔ صفرُ المقام لا يُلاعَن ولا يُصفَّر: الملفّ كلّه يجب أن يخلو من هاتَين الصيغتَين.
FORBIDDEN_JSON_TOKENS = ("Infinity", "NaN")
CARD_RANGE = (55, 64)

#: (مسار JSON · صيغةُ العرض · القيمةُ المُصيَّرة المتوقَّعة · النصّ الذي يجب أن يحويه المستند).
#: الصيغةُ **عقدُ عرض**: إن غيّرت تنسيقَ رقمٍ في الوثيقة، فغيّر الصيغة هنا — لا العكس.
DERIVED_FIGURES: tuple[tuple[str, str, str, str], ...] = (
    ("suite.name", "str", "ExploitGym", "ExploitGym"),
    ("suite.instances", "int", "898", "**898**"),
    ("suite.domains.USERSPACE", "int", "520", "520 userspace"),
    ("suite.domains.BROWSER_V8", "int", "185", "185 V8"),
    ("suite.domains.KERNEL", "int", "193", "193 kernel"),
    ("suite.issued_on", "str", "2026-05-13", "2026-05-13"),
    ("suite.owner", "prefix", "Berkeley RDI", "Berkeley RDI"),
    ("as_of", "str", "2026-09-12", "2026-09-12"),
    # --- الدبابيس: حسمُ H59 بالاستعمال لا بالحجّة
    ("results.pin_evaluations.pins_evaluated", "int", "7", "**7**"),
    ("results.pin_evaluations.unpinned_count", "int", "0", "**`UNPINNED` = 0**"),
    ("results.pin_evaluations.report_age_days", "f1", "122.0", "**122.0**"),
    ("results.pin_evaluations.max_report_age_days", "int", "90", "سقف 90"),
    ("results.pin_evaluations.fresh_days_threshold", "f1", "14.0", "`fresh_days_threshold = 14.0`"),
    (
        "results.pin_evaluations.age_governs_not_missingness",
        "boolj",
        "true",
        "`age_governs_not_missingness = true`",
    ),
    ("results.pin_evaluations.all_stale_by_age", "boolj", "true", "`STALE` بالإجماع"),
    (
        "results.pin_evaluations.h59_verdict",
        "str",
        "CONFIRMED_IN_DOMAIN",
        "**`CONFIRMED_IN_DOMAIN`**",
    ),
    # --- أثرُ الحمايات: «لا تكفي» صادقةٌ إجمالاً خاطئةٌ تفصيلاً
    ("results.mitigation_effect.successes_mitigations_off", "int", "369", "**369 ← 69**"),
    ("results.mitigation_effect.successes_mitigations_on", "int", "69", "**369 ← 69**"),
    ("results.mitigation_reduction_factor", "f4", "5.3478", "**5.3478×**"),
    ("results.mitigation_residual_share", "f6s", "0.186992", "**0.186992 = 18.70%**"),
    ("results.pairs_zeroed_by_mitigations", "int", "4", "**4 من 7**"),
    (
        "results.mitigation_effect.residual_top_pair",
        "str",
        "claude-mythos-preview",
        "`claude-mythos-preview`",
    ),
    ("results.residual_top_share", "f6s", "0.652174", "**0.652174 = 65.22%**"),
    # --- CPST: أوّلُ مرساةٍ مُلتزمة بـL7
    ("results.cpst_band_usd.0", "f2", "3.75", "**[3.75، 22.99]**"),
    ("results.cpst_band_usd.1", "f2", "22.99", "**[3.75، 22.99]**"),
    ("results.cpst_spread_factor", "f4", "6.1307", "**6.1307×**"),
    ("results.cpst_band.median_usd", "f1", "8.6", "وسيطٌ **8.6**"),
    ("results.cpst_band.n_disclosed", "int", "6", "على 6 أزواج"),
    ("results.cpst_undisclosed_count", "int", "1", "**1** (`claude-mythos-preview`)"),
    ("results.cpst_band.unit", "str", "USD_PER_SUCCESSFUL_TASK", "`USD_PER_SUCCESSFUL_TASK`"),
    ("results.cpst_band.undisclosed_imputed", "boolj", "false", "⛔ `undisclosed_imputed = false`"),
    # --- التباعدُ عن الهدف: أطروحةٌ صارت مُسندةً من طرفَين أوّليين
    ("results.off_target_rate.pairs_measured", "int", "2", "**2**"),
    ("results.off_target_rate.per_pair.0.flags_captured", "int", "210", "210 أعلاماً"),
    (
        "results.off_target_rate.per_pair.0.successes_on_intended",
        "int",
        "120",
        "← 120 على المقصودة",
    ),
    ("results.max_off_target_share", "f6s", "0.428571", "**0.428571 = 42.86%**"),
    ("results.off_target_rate.per_pair.1.flags_captured", "int", "226", "226 ← 157"),
    ("results.off_target_rate.per_pair.1.successes_on_intended", "int", "157", "226 ← 157"),
    (
        "results.off_target_rate.per_pair.1.off_target_share",
        "f6s",
        "0.30531",
        "**0.30531 = 30.53%**",
    ),
    # --- تعارضُ الطرفَين الأوّليين: ⛔ لا متوسط
    ("results.unsolved_conflict.openai_never_solved", "int", "198", "198/898"),
    (
        "results.unsolved_conflict.openai_never_solved_share",
        "f6s",
        "0.22049",
        "**0.22049 = 22.05%**",
    ),
    ("results.unsolved_conflict.berkeley_union_solved", "int", "177", "177"),
    (
        "results.unsolved_conflict.berkeley_unsolved_share",
        "f6s",
        "0.802895",
        "**0.802895 = 80.29%**",
    ),
    ("results.unsolved_share_spread_factor", "f4", "3.6414", "**3.6414×**"),
    ("results.unsolved_reconciled", "boolj", "false", "`reconciled = false`"),
    (
        "results.unsolved_conflict.reconciliation_basis",
        "str",
        "PIN_DIFFERENCE_NOT_AVERAGE",
        "`PIN_DIFFERENCE_NOT_AVERAGE`",
    ),
    ("results.unsolved_conflict.pin_axes_that_differ", "len", "4", "**4** محاور مختلفة"),
    ("results.unsolved_conflict.suite_instances", "int", "898", "**898**"),
    # --- الميزانيةُ محورٌ مُنحازٌ للأسفل بغير تناظر
    ("results.budget_sensitivity.successes_at_120min", "int", "127", "127 ← 204"),
    ("results.budget_sensitivity.successes_at_360min", "int", "204", "127 ← 204"),
    ("results.budget_growth_share", "f6s", "0.606299", "**0.606299 = +60.63%**"),
    ("results.budget_sensitivity.plateau_declared", "boolj", "false", "`plateau_declared = false`"),
    (
        "results.budget_sensitivity.self_declared_undercount",
        "boolj",
        "true",
        "`self_declared_undercount = true`",
    ),
    ("results.budget_sensitivity.weaker_pair.plateau_minutes", "int", "30", "**30** دقيقة"),
    ("results.budget_sensitivity.weaker_pair.plateau_value", "int", "15", "عند **15**"),
    # --- محورُ الحماية: صفرُ مقامٍ يُسجَّل زوجاً
    ("results.safeguard_pair.successes_default_filters", "int", "0", "**0 ← 120**"),
    ("results.safeguard_pair.successes_filters_disabled", "int", "120", "**0 ← 120**"),
    ("results.safeguard_ratio", "none", "None", "`ratio = None`"),
    (
        "results.safeguard_pair.recorded_as",
        "str",
        "PAIR_NOT_RATIO",
        "`recorded_as = PAIR_NOT_RATIO`",
    ),
    (
        "results.safeguard_pair.ratio_undefined_reason",
        "prefix",
        "ZERO_DENOMINATOR",
        "`ZERO_DENOMINATOR`",
    ),
    # --- التناقضُ الداخلي وحدودُ الحقول
    ("results.self_contradiction_count", "int", "1", "**D1**"),
    ("results.self_contradictions.0.delta", "int", "30", "الفرقُ **30**"),
    ("results.self_contradictions.0.resolved", "boolj", "false", "`resolved = false`"),
    ("results.pin_field_limitations", "len", "2", "**2**"),
    # --- الأصفار: في الملفّ وفي النصّ معاً
    ("model_runs_executed", "int", "0", "`model_runs_executed = 0`"),
    ("client_measurements", "int", "0", "`client_measurements = 0`"),
    ("exploits_reproduced", "int", "0", "`exploits_reproduced = 0`"),
    ("exploit_code_present", "bool", "False", "`exploit_code_present = False`"),
    ("revenue_claim", "prefix", "NONE", "`revenue_claim = NONE"),
)


def squash(text: str) -> str:
    """يُسوّي تتابعات البياض إلى مسافةٍ واحدة.

    **لماذا:** التفافُ السطر في Markdown اختياريٌّ وعرضه 80 عموداً اصطلاحٌ لا قيد. فبوّابةٌ
    تبحث عن عبارةٍ لازمة («بلا إنفاقٍ نقدي») بمطابقةٍ حرفية تسقط حين يفصل الالتفافُ كلمتَيها —
    وتفشل على نصٍّ سليم. فالمطابقةُ تُجرى على النصّ المُسوّى، لا على التفافه.
    """
    return re.sub(r"\s+", " ", text)


def load_csv(path: Path) -> list[dict[str, str]]:
    """يقرأ سجلاً CSV — والفشلُ صريحٌ لا قائمةٌ فارغة تُقرأ نجاحاً."""
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def field(row: dict, key: str) -> str:
    """يُعيد قيمةَ عمودٍ نصّاً — و⛔ لا `None` يصل إلى `re` فيُسقط البوّابة.

    **لماذا لازم:** `csv.DictReader` على صفٍّ أقصرَ من الترويسة يُعطي `None` للأعمدة الناقصة
    (لا `""`، لأنّ المفتاح **موجود** بقيمته الفارغة). و`re.fullmatch(pattern, None)` يرفع
    `TypeError` — فتسقط البوّابةُ استثناءً بدل أن تُبلِّغ انتهاكاً. وسجلٌّ مشوَّهٌ انتهاكٌ
    يجب أن يُفشل، لا عطلٌ يجب أن يُسقِط: فالفرقُ بينهما أنّ الأوّل يُقرأ في CI أحمرَ
    مُسمّى، والثاني يُقرأ «البوّابةُ مكسورة» ويُتجاوَز.
    """
    value = row.get(key)
    return value if isinstance(value, str) else ""


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


def _render_boolj(value: object) -> str:
    #: صيغةُ JSON لا صيغةُ Python: الوثيقةُ تكتب `= false` لأنّ الملفّ JSON.
    if value is True:
        return "true"
    if value is False:
        return "false"
    return f"⛔ ليس bool: {value!r}"


def _render_none(value: object) -> str:
    return "None" if value is None else f"⛔ القيمة ليست None: {value!r}"


def _render_len(value: object) -> str:
    return str(len(value))  # type: ignore[arg-type]


def _render_int(value: object) -> str:
    return str(int(value))  # type: ignore[arg-type]


def _render_f1(value: object) -> str:
    return f"{float(value):.1f}"  # type: ignore[arg-type]


def _render_f2(value: object) -> str:
    return f"{float(value):.2f}"  # type: ignore[arg-type]


def _render_f4(value: object) -> str:
    return f"{float(value):.4f}"  # type: ignore[arg-type]


def _render_f6s(value: object) -> str:
    #: ستّ خاناتٍ ثمّ تجريدُ الأصفار الذيلية: 0.305310 → 0.30531، و0.186992 كما هي.
    #: فالملفّ يحفظ `round(x, 6)` الذي يُسقط الأصفار، والمطابقةُ الحرفية تتطلب الشكل نفسه.
    return f"{float(value):.6f}".rstrip("0").rstrip(".")  # type: ignore[arg-type]


#: جدولُ التوزيع: الصيغةُ مفتاحٌ لا سلسلةُ فروع — فإضافةُ صيغةٍ الثانيةَ عشرةَ لا ترفع
#: عدّادَ الفروع في `render` (PLR0911/PLR0912)، و`ValueError` على المجهولة باقٍ عقداً.
#: بلا تعليقٍ نوعيٍّ عمداً: سطحُ استيرادِ البوّابةِ خمسُ وحداتٍ لا أكثر (يفرضه
#: `test_gate_module_is_stdlib_only` في شقيقتها)، و`collections.abc` سادسةٌ لا يبرّرها شيء.
_RENDERERS = {
    "str": str,
    "prefix": str,
    "bool": _render_bool,
    "boolj": _render_boolj,
    "none": _render_none,
    "len": _render_len,
    "int": _render_int,
    "f1": _render_f1,
    "f2": _render_f2,
    "f4": _render_f4,
    "f6s": _render_f6s,
}


def render(value: object, spec: str) -> str:
    """يُصيّر قيمة JSON إلى نصّها في الوثيقة — والصيغةُ جزءٌ من العقد لا تفصيلٌ تجميلي."""
    try:
        renderer = _RENDERERS[spec]
    except KeyError:
        raise ValueError(f"صيغةُ تنسيقٍ غير معروفة: {spec!r}") from None
    return renderer(value)


def bucket_state(state: str) -> str:
    """تصنيفُ حالة البوابة — المصدرُ `gate_state` لا نصٌّ يدوي في الوثيقة.

    ⚠️ الترتيبُ عقديٌّ: «مُنجَزة جزئياً» تُفحص **قبل** «مُنجَزة»، وإلا ابتلع التصنيفُ الأعمّ
    الجزئيَّ وصارت `H62` مُنجَزةً وهي ليست كذلك.
    """
    if state.startswith("فاشلة"):
        return "failed"
    if state.startswith("مُنجَزة جزئياً") or state.startswith("منجزة جزئياً"):
        return "partial"
    if state.startswith("مُنجَزة") or state.startswith("منجزة"):
        return "completed"
    if state.startswith("غير مفحوصة"):
        return "untested"
    if "معلّقة" in state or "معلقة" in state:
        return "held"
    return "other"


def _check_ledger_identity(ledger: list[dict[str, str]], failures: list[str]) -> None:
    """صفّيةُ السجل وتفريدُ معرّفاته واتصالُها — ثلاثةُ فروعٍ لا أكثر."""
    if len(ledger) != EXPECTED_HYPOTHESES:
        failures.append(f"سجلّ الجولة 05 يحوي {len(ledger)} صفاً، والمتوقّع {EXPECTED_HYPOTHESES}")
    ids = [field(row, "id") for row in ledger]
    if len(set(ids)) != len(ids):
        failures.append("معرّفات الفرضيات غير فريدة")
    want = [f"H{n}" for n in range(int(EXPECTED_H_RANGE[0][1:]), int(EXPECTED_H_RANGE[1][1:]) + 1)]
    if ids != want:
        failures.append(f"معرّفات الفرضيات {ids}، والمتوقّع اتّصالاً {want}")


def _check_ledger_levels(ledger: list[dict[str, str]], failures: list[str]) -> None:
    """سقوفُ الالتزام: ⛔ ولا مستوى فوق E1، وE1 واحدةٌ فقط لا تكتمل قبل القبول."""
    levels = {field(row, "max_level") for row in ledger}
    if not levels <= EXPECTED_LEVELS:
        failures.append(
            f"مستويات التزام خارج E0/E1 معلَنة في السجل: {sorted(levels - EXPECTED_LEVELS)} — "
            f"⛔ {NO_SPEND_PHRASE} ولا سقف خسارة معتمداً، فلا E2 في هذه الجولة (محرك §5)"
        )
    e1_rows = [row for row in ledger if field(row, "max_level") == "E1"]
    if len(e1_rows) != 1:
        failures.append(
            f"{len(e1_rows)} فرضيةً عند E1، والمتوقّع واحدةً ({SINGLE_E1_HYPOTHESIS}) — "
            "⛔ رفعُ سقفِ أكثرَ من فرضيةٍ واحدة في جولةٍ بصفرِ مقابلة تضخيمٌ لا قياس"
        )
    elif field(e1_rows[0], "id") != SINGLE_E1_HYPOTHESIS:
        failures.append(
            f"فرضيةُ E1 هي {field(e1_rows[0], 'id')} والمتوقّع {SINGLE_E1_HYPOTHESIS} — "
            "⛔ القرارُ المعلَن في §1/§6.1 يقول غير ذلك"
        )
    elif bucket_state(field(e1_rows[0], "gate_state")) == "completed":
        failures.append(
            f"{SINGLE_E1_HYPOTHESIS} عند E1 وحالتُها «مُنجَزة» — ⛔ تناقض: فما أُنجِز لا ينتظر "
            "قبولاً، وما ينتظر قبولاً لم يُنجَز"
        )


def _check_ledger_row(row: dict[str, str], counts: dict[str, int], failures: list[str]) -> None:
    """صفٌّ واحد: اكتمالُ الحقول وحصيلتُه وصيغةُ ترقيمه — والمنطقُ حرفيٌّ كما كان."""
    rid = field(row, "id") or "؟"
    state = field(row, "gate_state")
    key = bucket_state(state)
    if key in counts:
        counts[key] += 1
    if not (field(row, "hypothesis_ar") and field(row, "counterparty")):
        failures.append(f"{rid}: صفٌّ بلا فرضيةٍ أو بلا طرفٍ مقابل")
    if not (field(row, "binding_gate") and state and field(row, "decision")):
        failures.append(f"{rid}: صفٌّ بلا بوّابة حاكمة أو حالة أو قرار")
    if not field(row, "shared_dependency"):
        failures.append(f"{rid}: صفٌّ بلا اعتماد مشترك — «محفظة متنوّعة» بلا فحص العُقد")
    if key == "other":
        failures.append(
            f"{rid}: حالةُ بوّابةٍ لا تُصنَّف ({state[:40]}…) — "
            "⛔ الحالةُ المعلَنة يجب أن تبدأ بأحد التصريحات الخمسة في §6.1"
        )
    #: ⚠️ `name` لا `field`: فالاسمُ الأخير دالةُ الوحدة، وتظليلُه هنا يجعله متغيّراً حرّاً
    #: في الفهمَين التاليَين ⇒ `NameError` على مدخلٍ **سليم** (سقطت عشرةُ اختباراتٍ بهذا).
    for name in ("key_claim", "key_test"):
        value = field(row, name)
        if value != "-" and not re.fullmatch(r"[CT]\d\d( [CT]\d\d)*", value):
            failures.append(f"{rid}: {name}={value!r} خارج الصيغة [CT]nn")


def _check_ledger_numbering(ledger: list[dict[str, str]], failures: list[str]) -> None:
    """اتصالُ الترقيم مع الجولة 04 (C47–C56 · T45–T54): ⛔ لا إعادةُ استعمالٍ ولا قفز."""
    claims = {int(m) for row in ledger for m in re.findall(r"C(\d+)", field(row, "key_claim"))}
    tests = {int(m) for row in ledger for m in re.findall(r"T(\d+)", field(row, "key_test"))}
    if claims:
        if min(claims) <= 56:
            failures.append(
                f"أرقامُ ادّعاءاتٍ معادٌ استعمالها من الجولة 04: {sorted(c for c in claims if c <= 56)}"
            )
        if sorted(claims) != list(range(min(claims), max(claims) + 1)):
            failures.append(f"أرقامُ الادّعاءات غيرُ متّصلة: {sorted(claims)}")
    if tests:
        if min(tests) <= 54:
            failures.append(
                f"أرقامُ بطاقاتٍ معادٌ استعمالها من الجولة 04: {sorted(t for t in tests if t <= 54)}"
            )
        if sorted(tests) != list(range(min(tests), max(tests) + 1)):
            failures.append(f"أرقامُ البطاقات غيرُ متّصلة: {sorted(tests)}")


def check_ledger(ledger: list[dict[str, str]], failures: list[str]) -> dict[str, int]:
    """بنيةُ السجل: صفّية، تفريد، اتصالُ الترقيم، ⛔ ولا مستوى فوق E1، وE1 واحدةٌ فقط."""
    counts = dict.fromkeys(DECLARED_KEYS, 0)
    _check_ledger_identity(ledger, failures)
    _check_ledger_levels(ledger, failures)
    for row in ledger:
        _check_ledger_row(row, counts, failures)
    _check_ledger_numbering(ledger, failures)
    return counts


def check_declared_counts(round_text: str, counts: dict[str, int], failures: list[str]) -> None:
    """جدولُ المسح في §6.1 يجب أن يساوي ما يشتقّه الفارض من السجل — لا ما يذكره الكاتب."""
    for key, label in DECLARED_KEYS.items():
        want = counts[key]
        #: «مُنجَزة جزئياً» تُطابق قبل «مُنجَزة» — وإلا التقط الصفُّ الأوّلُ الثانيَ.
        if key == "completed":
            row = re.search(
                rf"\|\s*(?:\*\*)?{re.escape(label)}(?! جزئياً)[^\n|]*\|\s*(?:\*\*)?(\d+)(?:\*\*)?\s*\|",
                round_text,
            )
        else:
            row = re.search(
                rf"\|\s*(?:\*\*)?{re.escape(label)}[^\n|]*\|\s*(?:\*\*)?(\d+)(?:\*\*)?\s*\|",
                round_text,
            )
        if not row:
            failures.append(f"§6.1: لا صفَّ معلن لـ«{label}» في جدول المسح")
            continue
        if int(row.group(1)) != want:
            failures.append(
                f"§6.1: «{label}» معلَنة {row.group(1)} بينما السجلّ يشتقّ {want} — "
                "⛔ الرقمُ المكتوب يدوياً ليس اشتقاقاً"
            )
    total = sum(counts.values())
    if total != EXPECTED_HYPOTHESES:
        failures.append(f"§6.1: مجموعُ حصائل المسح {total}، والمتوقّع {EXPECTED_HYPOTHESES}")


def check_levels_declared(
    round_text: str, ledger: list[dict[str, str]], failures: list[str]
) -> None:
    """عددا E1 وE0 في §6.1 يجب أن يطابقا السجلّ."""
    n_e1 = sum(1 for row in ledger if field(row, "max_level") == "E1")
    n_e0 = sum(1 for row in ledger if field(row, "max_level") == "E0")
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
    if re.search(
        r"\|\s*(?:\*\*)?مؤهَّلة نظرياً لـE2[^\n|]*\|\s*(?:\*\*)?(\d+)(?:\*\*)?\s*\|", round_text
    ):
        n_e2 = int(
            re.search(
                r"\|\s*(?:\*\*)?مؤهَّلة نظرياً لـE2[^\n|]*\|\s*(?:\*\*)?(\d+)(?:\*\*)?\s*\|",
                round_text,
            ).group(1)
        )  # type: ignore[union-attr]
        if n_e2 != 0:
            failures.append(
                f"§6.1: {n_e2} فرضيةً معلَنةً مؤهَّلةً لـE2، والمتوقّع 0 — "
                "⛔ لا سقف خسارة معتمداً ولا مرساةَ فاتورة ⇒ ولا واحدةَ تبلغ E2"
            )


def check_evidence(evidence: list[dict[str, str]], failures: list[str]) -> None:
    """سجلّ الأدلة: عدٌّ، اتصالُ نطاق S96–S103، تاريخٌ لكلّ صفّ، ودرجةُ مصدرٍ صالحة."""
    if len(evidence) != EXPECTED_EVIDENCE:
        failures.append(
            f"سجلّ أدلّة الجولة 05 يحوي {len(evidence)} سنداً، والمتوقّع {EXPECTED_EVIDENCE}"
        )
    ids = [field(row, "id") for row in evidence]
    want = [
        f"S{n}"
        for n in range(int(EXPECTED_EVIDENCE_RANGE[0][1:]), int(EXPECTED_EVIDENCE_RANGE[1][1:]) + 1)
    ]
    if ids != want:
        failures.append(f"معرّفات الأدلّة {ids}, والمتوقّع اتّصالاً {want[0]}–{want[-1]}")
    #: عُرفُ الأعمدة موروثٌ من الجولتين 02/04 — ⛔ لا اختراعَ مخطّطٍ جديد في الجولة 05.
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
            f"أعمدةُ سجلّ الأدلّة {list(evidence[0].keys())}، والمتوقّع عُرفَ الجولتين 02/04: {want_cols}"
        )
    grade = re.compile(r"^(?:P|M|L)(?:-[HM])?\s+—")
    for row in evidence:
        sid = field(row, "id") or "؟"
        as_of = field(row, "as_of")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", as_of):
            failures.append(f"{sid}: `as_of` غائبٌ أو غير صالح ({as_of!r}) — T43 يلزم تاريخاً لكلّ صفّ")
        status = field(row, "status")
        if not (grade.match(status) or status.startswith("UNSTATED")):
            failures.append(
                f"{sid}: درجةُ مصدرٍ خارج العُرف (P/M/L ± H/M أو UNSTATED): {status[:30]!r}"
            )
        url = field(row, "url")
        if not url and not status.startswith("UNSTATED"):
            failures.append(f"{sid}: سندٌ بلا رابطٍ ولا وسم UNSTATED")
        if url and not url.startswith("http") and not status.startswith("UNSTATED"):
            failures.append(
                f"{sid}: `url` ليس رابطاً ({url[:28]!r}) والصفُّ ليس UNSTATED — "
                "⛔ حاشيةٌ مكان الرابط تُقرأ إسناداً"
            )
        if status.startswith("UNSTATED") and url.startswith("http"):
            failures.append(f"{sid}: صفٌّ موسومٌ UNSTATED ومع ذلك يحمل رابطاً — ⛔ الوسمُ يناقض السند")
        if not field(row, "independence_note"):
            failures.append(f"{sid}: سندٌ بلا ملاحظةِ استقلال — ومحورُ التحكيم الأوّل هو الاستقلال")
        if not field(row, "reverification_trigger"):
            failures.append(f"{sid}: سندٌ بلا محفّزِ إعادة تحقّق — فالدليلُ بلا تاريخِ انتهاء")


def check_demand_signal(
    evidence: list[dict[str, str]], ledger: list[dict[str, str]], failures: list[str]
) -> None:
    """`H69`: إشارةُ الطلب من ممارس **ليست** تحقّقَ سوق — تُفرض في السند وفي السجلّ معاً.

    ⛔ هذا أخطرُ إغراءٍ في الجولة: تعليقٌ واحد يبدو «إثباتَ طلب»، ولو قُبل كذلك لصار أساسَ
    رفعِ مستوى التزامٍ بلا مشترٍ. فالبوّابة تفرض الدرجةَ L والنفيَ الصريح وبقاءَ `H69` عند E0.
    """
    row = next((r for r in evidence if field(r, "id") == "S102"), None)
    if row is None:
        failures.append("S102 (إشارةُ الطلب من ممارس) غائبةٌ عن سجلّ الأدلّة")
        return
    status = field(row, "status")
    if not status.startswith("L"):
        failures.append(
            f"S102: درجتُه {status[:20]!r} والمتوقّع L — ⛔ تعليقُ مدوّنةٍ ليس طرفاً أوّلاً، "
            "ورفعُ درجته يرفع مستوى التزامٍ بلا دليل"
        )
    note = squash(field(row, "independence_note"))
    if not any(word in note for word in ("n=1", "ليست", "لا يُقرأ", "لا يُحتسب", "⛔")):
        failures.append(
            "S102: ملاحظةُ الاستقلال لا تحمل نفياً صريحاً لقراءته تحقّقَ سوق — "
            "⛔ إشارةُ طلبٍ بلا نفيٍ تُقرأ دليلاً"
        )
    h69 = next((r for r in ledger if field(r, "id") == "H69"), None)
    if h69 is None:
        failures.append("H69 غائبةٌ عن سجلّ القرار")
        return
    if field(h69, "max_level") != "E0":
        failures.append(
            f"H69 عند {field(h69, 'max_level')!r} والمتوقّع E0 — ⛔ إشارةُ طلبٍ واحدة لا ترفع التزاماً"
        )
    if bucket_state(field(h69, "gate_state")) != "completed":
        failures.append("H69: حالتُها يجب أن تكون «مُنجَزة» (فالمنعُ نفسه هو المُنجَز، لا قبولُ السوق)")
    decision = squash(field(h69, "decision"))
    if "لا تُحتسب" not in decision and "لا يُحتسب" not in decision:
        failures.append(
            "H69: قرارُها لا يعلن صراحةً أنّ الإشارة لا تُحتسب في `T47` (خمسُ مقابلات) — "
            "⛔ الصمتُ هنا يُقرأ ضمّاً"
        )


def check_measurements(round_text: str, failures: list[str]) -> dict:
    """كلّ رقمٍ في §4 مطابَقٌ بملفّ القياس بمسارٍ مُسمّى، وبصيغةِ عرضٍ معلَنة."""
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    flat = squash(round_text)
    matched = 0
    for dotted, spec, want_render, doc_token in DERIVED_FIGURES:
        try:
            value = dig(artifact, dotted)
        except KeyError as exc:
            failures.append(str(exc))
            continue
        got = render(value, spec)
        if spec == "prefix":
            if not got.startswith(want_render):
                failures.append(
                    f"{dotted}: الملفّ يقول {value!r} ولا يبدأ بـ{want_render!r} — "
                    "⛔ العقدُ بادئةٌ لا مساواة"
                )
                continue
        elif got != want_render:
            failures.append(
                f"{dotted}: الملفّ يقول {value!r} ⇒ يُصيَّر {got!r}، وعقدُ العرض يتوقّع {want_render!r} — "
                "⛔ غيّر الصيغة في الفارض إن كان التنسيق هو المقصود، لا الرقمَ في الوثيقة"
            )
            continue
        if doc_token not in flat:
            failures.append(
                f"الرمزُ المشتقّ {doc_token!r} ({dotted}) غائبٌ عن وثيقة الجولة — "
                "⛔ رقمٌ في الملفّ بلا مقابلٍ في النصّ هو رقمٌ لا يُقرأ"
            )
            continue
        matched += 1
    return {"artifact": artifact, "matched": matched}


def _check_h59_pin(pin: dict, failures: list[str]) -> None:
    """دبوسٌ واحد: اكتمالُ الحقول واتساقُ حُكمِ AHW مع العدّ — والمنطقُ حرفيٌّ كما كان."""
    label = str(pin.get("model_id", "?"))
    missing = [f for f in PIN_FIELDS if pin.get(f) in (None, "")]
    if missing:
        failures.append(f"الدبوس {label}: حقولٌ ناقصة {missing} — ⛔ `UNPINNED` هنا عادلٌ لا كاذب")
    if pin.get("missing_fields"):
        failures.append(
            f"الدبوس {label}: AHW تُعلن حقولاً ناقصة {pin['missing_fields']} — "
            "⛔ تناقضٌ مع `unpinned_count = 0`"
        )
    if pin.get("pin_state") not in ("FRESH", "THROTTLED", "STALE"):
        failures.append(
            f"الدبوس {label}: حالةٌ {pin.get('pin_state')!r} خارج المُدرَّج (FRESH/THROTTLED/STALE)"
        )
    #: ⛔ STALE ⇒ غيرُ قابلٍ للاقتباس دليلاً على قدرةٍ قائمة. فلو صار `quotable = True`
    #: لدبوسٍ منتهي الصلاحية لكان الحارسُ مُزيَّناً لا حارساً.
    if pin.get("pin_state") == "STALE" and pin.get("quotable") is not False:
        failures.append(
            f"الدبوس {label}: `quotable` = {pin.get('quotable')!r} مع حالةٍ STALE — "
            "⛔ منتهيُ الصلاحية لا يُقتبس دليلاً على قدرةٍ قائمة"
        )


def _check_h59_suite_axes(artifact: dict, failures: list[str]) -> None:
    """محورا الدبوس على مستوى الحزمة: الإصدارُ وتاريخُ الإصدار — يُفحصان مرّةً واحدة."""
    for dotted, label in SUITE_PIN_FIELDS:
        try:
            value = dig(artifact, dotted)
        except KeyError:
            failures.append(f"محورُ الدبوس على مستوى الحزمة غائب: {dotted} ({label})")
            continue
        if value in (None, ""):
            failures.append(f"محورُ الدبوس {label} = {value!r} — ⛔ دبوسٌ بلا إصدارٍ أو تاريخٍ ناقص")


def check_h59_domain_guard(artifact: dict, round_text: str, failures: list[str]) -> None:
    """حارسُ المجال: صفرُ `UNPINNED` على دبابيسَ كاملةِ الحقول، والعمرُ هو الحاكم.

    ⚠️ هذه ليست ملاحظةً بل حارسٌ مُنفَّذ: لو ظهر `UNPINNED` في المجال الصحيح لكان معنى ذلك
    أنّ القياس نفسه (لا الأداة) مُعيب — و`H60` تنقلب من مُنجَزةٍ إلى فاشلة. فالبوّابة تفشل
    بدل أن تُنتج حكماً كاذباً يُقتبس.
    """
    pe = artifact.get("results", {}).get("pin_evaluations", {})
    per_pin = pe.get("per_pin", [])
    if not per_pin:
        failures.append("results.pin_evaluations.per_pin فارغة — ⛔ لا حكمَ بلا دبابيس")
        return
    if pe.get("unpinned_count") != 0:
        failures.append(
            f"`unpinned_count` = {pe.get('unpinned_count')!r} على {len(per_pin)} دبابيس في المجال "
            "الصحيح، والمتوقّع 0 — ⛔ H60 فاشلة: فإمّا دبوسٌ ناقصُ الحقول أو قياسٌ مُعيب"
        )
    #: كلّ دبوسٍ يجب أن تكون حقولُه حاضرةً غيرَ فارغة — وإلا فـ`UNPINNED` عادلٌ لا كاذب.
    #: و`missing_fields` هو **حُكمُ AHW نفسه** لا إعادةُ حسابٍ منّا: فالبوّابة لا تُصدّر منطقاً ثانياً.
    for pin in per_pin:
        _check_h59_pin(pin, failures)
    #: ومحورا الحزمة يُفحصان مرّةً واحدة (المخطّطُ مسطّح، فلا تكرارَ لفحصٍ مشترك).
    _check_h59_suite_axes(artifact, failures)
    if pe.get("age_governs_not_missingness") is not True:
        failures.append(
            "`age_governs_not_missingness` ليس True — ⛔ إن حكم النقصُ لا العمرُ فالحكمُ عن "
            "اكتمال الدبوس لا عن صلاحية الاقتباس"
        )
    if pe.get("all_stale_by_age") is not True:
        failures.append("`all_stale_by_age` ليس True بينما العمر 122 يوماً > سقف 90")
    if pe.get("h59_verdict") != "CONFIRMED_IN_DOMAIN":
        failures.append(
            f"`h59_verdict` = {pe.get('h59_verdict')!r} والمتوقّع CONFIRMED_IN_DOMAIN — "
            "⛔ H59 لا تُحسم بالحجّة بل بالقياس في المجال"
        )
    #: والحكمُ المُنجَز لا يجوز أن يُقرأ إذناً باقتباس الأرقام دليلاً على القدرة الحالية.
    if not pe.get("purpose_qualifier"):
        failures.append(
            "`purpose_qualifier` غائب — ⛔ STALE قد يُقرأ تكذيباً للرقم لا انتهاءً لصلاحية اقتباسه"
        )
    flat = squash(round_text)
    if "لا يُقتبس أيُّ رقمٍ هنا دليلاً على القدرة الحالية" not in flat:
        failures.append(
            "§7: قيدُ `STALE` غيرُ مُعلَن في وثيقة الجولة — ⛔ 122 يوماً > سقف 90 ⇒ الأرقامُ "
            "سجلٌّ تاريخي لتكوينٍ مُقاس، لا دليلٌ على قدرةٍ قائمة"
        )


def check_zero_denominator(artifact: dict, failures: list[str]) -> None:
    """انضباطُ صفرِ المقام: `PAIR_NOT_RATIO` في النتيجة، و⛔ لا `Infinity` ولا `NaN` في الملفّ.

    **لماذا يُفحص الملفّ كلّه لا الحقلُ وحده:** قاعدةُ D-212 ليست «لا تقس على صفر» بل
    «الغيابُ لا يُصفَّر ولا يُلاعَن». فـ`json.dump` يكتب `Infinity` و`NaN` بلا خطأ (ليسا JSON
    صالحاً)، ولو تسرّبا لقُرئا قيماً. فالمسحُ النصّي هو الحارسُ الوحيد الذي يمسكهما.
    """
    raw = ARTIFACT.read_text(encoding="utf-8")
    for token in FORBIDDEN_JSON_TOKENS:
        if token in raw:
            failures.append(
                f"ملفّ القياس يحوي {token!r} — ⛔ D-212: الغيابُ يُسجَّل `None`/زوجاً، لا `inf` ولا `NaN`"
            )
    sp = artifact.get("results", {}).get("safeguard_pair", {})
    if sp.get("ratio") is not None:
        failures.append(
            f"results.safeguard_pair.ratio = {sp.get('ratio')!r} والمتوقّع None — "
            "⛔ المقامُ صفر (0 ← 120) فالنسبةُ غيرُ معرَّفة"
        )
    if not str(sp.get("ratio_undefined_reason", "")).startswith("ZERO_DENOMINATOR"):
        failures.append(
            "`ratio_undefined_reason` لا يعلن ZERO_DENOMINATOR — ⛔ `None` بلا سببٍ منطوق "
            "يُقرأ خطأً لا غياباً"
        )
    if sp.get("recorded_as") != "PAIR_NOT_RATIO":
        failures.append(
            f"`recorded_as` = {sp.get('recorded_as')!r} والمتوقّع PAIR_NOT_RATIO — "
            "⛔ صفرُ المقام يُسجَّل زوجاً (0 · 120) لا رقماً"
        )
    if sp.get("successes_default_filters") != 0:
        failures.append(
            f"`successes_default_filters` = {sp.get('successes_default_filters')!r} والمتوقّع 0 — "
            "⛔ إن تغيّر فالمقامُ لم يعد صفراً ويجب حسابُ النسبة لا تسجيلُها زوجاً"
        )


def check_no_averaging(artifact: dict, round_text: str, failures: list[str]) -> None:
    """انضباطُ التعارض: طرفان أوّلان مستقلّان على الحزمة نفسها ⛔ لا يُسوَّيان بمتوسط.

    **لماذا هذه أخطرُ بوّابةٍ في الجولة:** متوسطُ 22.05% و80.29% يبدو «تسويةً معقولة» ويُسكت
    التعارض. لكنّه رقمٌ **بلا مرجع**: لا يُعرف أيَّ تكوينٍ يصف، لأنّ المحاورَ الأربعة تختلف
    وثلاثةٌ منها غيرُ منشورة. فالسكوتُ هنا ينتج رقماً جديداً مختلَقاً من رقمَين صادقين.
    """
    uc = artifact.get("results", {}).get("unsolved_conflict", {})
    if uc.get("reconciled") is not False:
        failures.append(
            f"`unsolved_conflict.reconciled` = {uc.get('reconciled')!r} والمتوقّع False — "
            "⛔ تعارضُ طرفَين أوّليين بدبوسَين مختلفَين لا يُحسم بجمع"
        )
    if uc.get("reconciliation_basis") != "PIN_DIFFERENCE_NOT_AVERAGE":
        failures.append(
            f"`reconciliation_basis` = {uc.get('reconciliation_basis')!r} والمتوقّع "
            "PIN_DIFFERENCE_NOT_AVERAGE — ⛔ الأساسُ يجب أن يكون منصوصاً لا ضمنيّاً"
        )
    axes = uc.get("pin_axes_that_differ", [])
    if len(axes) < 4:
        failures.append(
            f"{len(axes)} محاورَ مختلفةً مُعلَنة، والمتوقّع ≥4 — ⛔ تعارضٌ بلا تسميةِ محاوره "
            "يُقرأ غموضاً لا فرقَ دبوس"
        )
    if uc.get("domain_sum_matches_instances") is not True:
        failures.append(
            "`domain_sum_matches_instances` ليس True — ⛔ 520+185+193 يجب أن تساوي 898 وإلا "
            "فالنسبتان مقسومتان على مقامَين مختلفَين"
        )
    share_a = uc.get("openai_never_solved_share")
    share_b = uc.get("berkeley_unsolved_share")
    spread = uc.get("share_spread_factor")
    if None in (share_a, share_b, spread):
        failures.append("نسبُ التعارض أو انتشارُه غائبة من الملفّ")
    #: إعادةُ حساب الانتشار من النسبتَين — فالبوّابة لا تثق بالملفّ ثقةً عمياء.
    elif abs(share_b / share_a - spread) > 5e-5:
        failures.append(
            f"`share_spread_factor` = {spread} بينما {share_b}/{share_a} = {share_b / share_a:.6f}"
        )
    flat = squash(round_text)
    for needle in ("متوسطُ طرفَين أوّليين بدبوسَين مختلفَين", "رقمٌ **بلا مرجع**"):
        if needle not in flat and needle.replace("**", "") not in flat:
            failures.append(
                f"§3.2 R4: تعليلُ منعِ المتوسط ({needle!r}) غائبٌ عن وثيقة الجولة — "
                "⛔ المنعُ بلا تعليلٍ يُقرأ تحفّظاً لا قاعدة"
            )


def check_cpst_doctrine(artifact: dict, failures: list[str]) -> None:
    """مرساةُ CPST مُلتزمةٌ بـD-290 L7: الوحدةُ صريحة، والغائبةُ ⛔ لم تُستكمل."""
    cb = artifact.get("results", {}).get("cpst_band", {})
    if cb.get("unit") != "USD_PER_SUCCESSFUL_TASK":
        failures.append(
            f"`cpst_band.unit` = {cb.get('unit')!r} والمتوقّع USD_PER_SUCCESSFUL_TASK — "
            "⛔ L7: مقارنةُ الكلفة بـCPST لا بأجرٍ ساعيّ، والوحدةُ شرطُ المقارنة"
        )
    if not str(cb.get("doctrine_compliance", "")).startswith("D-290 L7"):
        failures.append(
            "`doctrine_compliance` لا يُسند إلى D-290 L7 — ⛔ رقمٌ بلا حكمٍ مذهبي يُقرأ "
            "ملاحظةً لا التزاماً"
        )
    if cb.get("undisclosed_imputed") is not False:
        failures.append(
            f"`undisclosed_imputed` = {cb.get('undisclosed_imputed')!r} والمتوقّع False — "
            "⛔ استكمالُ الغائبة بمتوسط الباقي يُزيح النطاقَ للأسفل (والأقوى أداءً هو الغائب)"
        )
    band = cb.get("band_usd") or []
    if len(band) != 2 or not band[0] < band[1]:
        failures.append(f"`band_usd` = {band!r} والمتوقّع [min, max] بـmin < max")
    else:
        #: ⛔ وصولٌ خامّ إلى مفتاحٍ غائب يُسقط البوّابة `KeyError`؛ فغيابُ المفتاح انتهاكٌ
        #: يُبلَّغ في `check_measurements`، وهنا تُجرى المصالحةُ فقط إن حضر الطرفان.
        declared = artifact.get("results", {}).get("cpst_spread_factor")
        if (
            cb.get("n_disclosed")
            and isinstance(declared, (int, float))
            and abs(band[1] / band[0] - float(declared)) > 5e-5
        ):
            failures.append(
                f"`cpst_spread_factor` = {declared} بينما max/min = {band[1] / band[0]:.6f}"
            )
    #: ⛔ الانتشارُ هنا بين بدائل (كلٌّ كلفتُه الحقيقية)، لا تشتّتٌ في تقدير بديلٍ واحد.
    #: والإبرةُ هي **النفيُ** الحاملُ للمعنى: فقولُ «بين بدائل» وحده لا يمنع الخلط، بينما
    #: «لا بين تقديراتٍ للكمية نفسها» يستبعد القراءةَ الخاطئة صراحةً.
    if "لا بين تقديراتٍ للكمية نفسها" not in squash(cb.get("reading", "")):
        failures.append(
            "`cpst_band.reading` لا يميّز الانتشارَ بين بدائل عن التشتّت في تقديرٍ واحد — "
            "⛔ خلطُهما يُنتج ترتيباً من ضجيج"
        )


def check_attribution_correction(artifact: dict, round_text: str, failures: list[str]) -> None:
    """تصحيحُ النسب (`H67`): الحزمةُ لـBerkeley RDI، ⛔ لا لـOpenAI.

    **لماذا تُفرض بالبوّابة لا بالتوثيق وحده:** الخطأُ كان في نصٍّ مُثبَّت (الجولة 04 §5.4)
    وصار قابلاً للاقتباس. فالتصحيحُ في وثيقةٍ جديدة لا يمنع عودةَ الصيغة القديمة؛ والحارسُ
    الذي يفحص `suite.owner` يمنع أن يُسجَّل طرفٌ أوّلٌ باسمٍ خاطئ في أيّ قياسٍ لاحق.
    """
    suite = artifact.get("suite", {})
    owner = str(suite.get("owner", ""))
    if not owner.startswith("Berkeley RDI"):
        failures.append(
            f"`suite.owner` = {owner[:40]!r} والمتوقّع أن يبدأ بـ«Berkeley RDI» — "
            "⛔ H67: مالكُ الحزمة أكاديميٌّ مستقلّ، والشركاءُ الصناعيون وفّروا الوصول فقط"
        )
    if owner.startswith("OpenAI"):
        failures.append("`suite.owner` يبدأ بـOpenAI — ⛔ هذا هو خطأُ الجولة 04 بعينه (C1)")
    note = str(suite.get("attribution_note", ""))
    if not note or "ليست" not in note:
        failures.append(
            "`suite.attribution_note` غائبٌ أو لا يحمل نفيَ النسب الخاطئ — "
            "⛔ تصحيحٌ بلا نفيٍ صريح يُقرأ إضافةً لا تصحيحاً"
        )
    flat = squash(round_text)
    for needle in ("ExploitGym ليست حزامَ OpenAI", "مالكِ الحزمة"):
        if needle not in flat:
            failures.append(
                f"§3.1 C1: تصحيحُ النسب ({needle!r}) غائبٌ عن وثيقة الجولة — "
                "⛔ خطأٌ في نصٍّ مُثبَّت لا يُغلقه الصمت"
            )
    if "يرفع" not in flat or "قيمة الدليل" not in flat:
        failures.append(
            "§3.1 C1: لم يُعلَن أنّ التصحيح **يرفع** قيمة الدليل — ⛔ استقلالُ القياس عمّن "
            "يملك النموذجَ المقاس معلومةٌ لا تفصيل"
        )


def check_self_contradiction(artifact: dict, failures: list[str]) -> None:
    """D1: تناقضُ طرفٍ أوّل مع نفسه يُسجَّل **بلا حلٍّ** — وحلُّه بلا نصٍّ اختلاق."""
    cases = artifact.get("results", {}).get("self_contradictions", [])
    if not cases:
        failures.append("`self_contradictions` فارغة بينما الجدول 1 (157) يخالف الشكل 5 (127)")
        return
    for case in cases:
        cid = str(case.get("id", "?"))
        if case.get("resolved") is not False:
            failures.append(
                f"{cid}: `resolved` = {case.get('resolved')!r} والمتوقّع False — ⛔ لم يُقرأ نصُّ "
                "arXiv الكامل، فالحسمُ اختلاقٌ لا استنتاج"
            )
        if not case.get("why_unresolved"):
            failures.append(f"{cid}: بلا `why_unresolved` — ⛔ تعليقٌ بلا سببٍ منطوق يُقرأ إهمالاً")
        if not case.get("handling"):
            failures.append(f"{cid}: بلا `handling` — ⛔ التناقضُ المسجَّل بلا معالجةٍ معلَنة يُقتبس")
        values = case.get("values") or {}
        if len(values) != 2:
            failures.append(f"{cid}: {len(values)} قيمتَين والمتوقّع اثنتَين")


def check_zero_counters(artifact: dict, round_text: str, failures: list[str]) -> None:
    """صفرُ تشغيلٍ وصفرُ إيرادٍ في الملفّ **وفي النص** — L9: لا استعارةَ دليلِ الغير دليلاً لنا."""
    flat = squash(round_text)
    for name in ZERO_COUNTERS:
        value = artifact.get(name, "MISSING")
        if value != 0:
            failures.append(f"{name} = {value!r} في ملفّ القياس، والمتوقّع 0")
        if f"{name} = 0" not in flat:
            failures.append(f"العدّاد {name} = 0 غيرُ مُعلَن في وثيقة الجولة")
    if artifact.get("exploit_code_present") is not False:
        failures.append(
            f"exploit_code_present = {artifact.get('exploit_code_present')!r} والمتوقّع False"
        )
    revenue = str(artifact.get(NO_REVENUE_PHRASE, "MISSING"))
    if not revenue.startswith("NONE"):
        failures.append(f"{NO_REVENUE_PHRASE} = {revenue!r}، والمتوقّع بادئةُ 'NONE'")
    if NO_SPEND_PHRASE not in flat:
        failures.append(f"§1/§2: عبارةُ «{NO_SPEND_PHRASE}» غائبة — ⛔ لا توصيةَ بإنفاقٍ بلا سقف")
    for needle in ("⛔ لا تسعيرَ ولا رقمَ إيراد", "⛔ لا خطَّ ثامن"):
        if needle not in flat:
            failures.append(f"§6.3: الحدّ {needle!r} غيرُ مُعلَن (L6 · L3)")


def check_no_exploit_code(failures: list[str]) -> None:
    """لا شيفرةَ استغلالٍ ولا سلسلةَ تقنياتٍ في مسار القياس ولا في وثائق الدراسة.

    ⚔️ الحدُّ الأخلاقيّ: تُقاس المُجمّعاتُ التنظيمية والاقتصادية والدفاعية فقط. والحماياتُ
    **بأسمائها** مسموحة (اسمُ الدفاع معلومةٌ تنظيمية)، أمّا سلسلةُ الاختراق فمُحرَّمة.
    """
    for path in (MEASURE, ARTIFACT, ROUND, EVIDENCE, LEDGER):
        text = path.read_text(encoding="utf-8")
        for pattern in EXPLOIT_PATTERNS:
            if re.search(pattern, text):
                failures.append(
                    f"{path.name}: نمطُ استغلالٍ {pattern!r} موجودٌ في مسار القياس — "
                    "⛔ إعادةُ إنتاج نواقل الحادثة وسلاسلُ التقنيات ممنوعةٌ في التكوين الحالي"
                )
    #: والحقلُّ نفسه يجب أن يبقى صادقاً: صفرُ استغلالٍ مُستنسخ.
    artifact = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    if (
        artifact.get("exploits_reproduced") != 0
        or artifact.get("exploit_code_present") is not False
    ):
        failures.append(
            "⛔ الحقلّان (exploits_reproduced / exploit_code_present) يناقضان الفحصَ النصّي"
        )


def check_forbidden_claims(failures: list[str]) -> None:
    """الادّعاءاتُ المدحوضة لا تعود إلى نصوصنا خارج سياق منعٍ صريح."""
    for path in SCANNED_DOCS:
        if not path.exists():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            #: أسطرُ الحكم المُثبت (`**مُثبتة**`) وصفوفُ السجلّ المُشتقّ ليست ادّعاءات.
            if "**مُثبتة**" in line:
                continue
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
            "⛔ شغّل `python3 scripts/research/measure_benchmark_pin.py` قبل الاعتماد على أيّ رقم"
        )
    if on_disk.get("suite") != rebuilt.get("suite"):
        failures.append("ملفّ القياس: `suite` على القرص لا يُعاد بناؤه حرفياً")


def check_measure_is_stdlib_only(failures: list[str]) -> None:
    """مسارُ القياس stdlib فقط وبلا شبكة — ⛔ بوّابةٌ تستورد ما تقيسه يجب أن تثق بمدخلاته."""
    import ast

    source = MEASURE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    allowed = {
        "__future__",  # جزءٌ من اللغة (تأجيلُ تقييم الإشارات)، ⛔ ليس حزمةً خارجية
        "json",
        "math",
        "statistics",
        "datetime",
        "dataclasses",
        "typing",
        "argparse",
        "sys",
        "pathlib",
        "hashlib",
        "collections",
        "itertools",
        "functools",
        "re",
        "textwrap",
        "unicodedata",
        "decimal",
        "fractions",
        "csv",
        "shared",  # وحدةُ المستودع نفسها — وإعادةُ استعمال `evaluate_pin` هي **جوهرُ H60**
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root_name = alias.name.split(".")[0]
                if root_name not in allowed:
                    failures.append(
                        f"measure_benchmark_pin.py: استيرادٌ خارج المكتبة القياسية: {alias.name}"
                    )
        elif isinstance(node, ast.ImportFrom):
            root_name = (node.module or "").split(".")[0]
            if root_name and root_name not in allowed:
                failures.append(
                    f"measure_benchmark_pin.py: استيرادٌ خارج المكتبة القياسية: {node.module}"
                )
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {"eval", "exec", "compile", "__import__"}
        ):
            failures.append(
                f"measure_benchmark_pin.py:{node.lineno}: نداءُ {node.func.id} — ⛔ تنفيذٌ ديناميكي"
            )
    for banned in ("urllib", "requests", "socket", "http.client", "subprocess"):
        if banned in source:
            failures.append(
                f"measure_benchmark_pin.py: ذكرُ {banned!r} — ⛔ القياسُ لا يقرأ شبكةً ولا يُنفّذ"
            )


def check_doc_structure(round_text: str, failures: list[str]) -> None:
    """أقسامٌ إلزامية: صفحةُ قرار، عقدُ D05، جدولُ تصحيحٍ ودحض، بطاقات، حدود."""
    required = (
        "## 1. صفحة القرار",
        "## 2. عقد القرار D05",
        "## 3. ما صُحِّح ودُحض في هذه الجولة",
        "### 3.1 تصحيحاتٌ في عملنا نحن",
        "### 3.2 ما دُحض أو حُجِب من الإغراءات المتاحة",
        "## 4. الأرقام المستعملة",
        "## 5. المعرفة الجديدة",
        "## 6. الفصلُ الثلاثي والبوابات غيرُ التعويضية",
        "## 7. حدودُ هذه الجولة",
        "## 8. البطاقات التالية",
    )
    flat = squash(round_text)
    for section in required:
        if section not in flat:
            failures.append(f"وثيقة الجولة 05: قسمٌ إلزامي غائب: {section!r}")
    #: صفحةُ القرار محكومةٌ بطولٍ (المحرك §3): ≤250 كلمة بين عنوانها والعقد.
    body = round_text.split("## 1. صفحة القرار", 1)[-1].split("## 2. عقد القرار", 1)[0]
    words = len(re.findall(r"[\w\u0600-\u06FF]+", re.sub(r"[*`>|#_⛔]", " ", body)))
    if words > DECISION_PAGE_WORD_CEILING:
        failures.append(
            f"صفحةُ القرار {words} كلمة، والسقفُ {DECISION_PAGE_WORD_CEILING} (محرك §3) — "
            "⛔ القرارُ الذي لا يُقرأ لا يُتَّخذ"
        )
    #: كلّ بطاقةٍ يجب أن تكون معيارَ خروجٍ لا عنوانَ نيّة — ⛔ البطاقاتُ عناوينُ أسطر، لا تُسوّى.
    for card in range(CARD_RANGE[0], CARD_RANGE[1] + 1):
        if f"**T{card}**" not in round_text:
            failures.append(f"§8: البطاقة T{card} غائبة عن جدول الخطوات التالية")
    #: عقدُ القرار يجب أن يسمّي البديلَين المُثبَّتَين، لا المختارَ وحده (محرك §4).
    for needle in ("عدمُ التنفيذ", "أفضلُ استخدامٍ بديلٌ للموارد"):
        if needle not in flat:
            failures.append(f"§2: البديلُ المُثبَّت {needle!r} غائبٌ — ⛔ قرارٌ بلا بدائله ليس قراراً")
    #: ومعيارُ نهاية الجولة يجب أن يجعل الصمتَ نتيجةً لا فراغاً.
    if "صمتٌ موثَّق" not in flat:
        failures.append("§8: معيارُ نهاية الجولة لا يعامل الصمتَ نتيجةً موثّقة")


def main() -> int:
    for path in (LEDGER, EVIDENCE, ROUND, ARTIFACT, CATALOG, MEASURE):
        if not path.exists():
            print(f"❌ check_decision_round05: ملفٌّ لازمٌ غائب: {path}")
            return 1
    failures: list[str] = []
    ledger = load_csv(LEDGER)
    evidence = load_csv(EVIDENCE)
    round_text = ROUND.read_text(encoding="utf-8")

    counts = check_ledger(ledger, failures)
    check_declared_counts(round_text, counts, failures)
    check_levels_declared(round_text, ledger, failures)
    check_evidence(evidence, failures)
    check_demand_signal(evidence, ledger, failures)
    measured = check_measurements(round_text, failures)
    if "artifact" in measured:
        artifact = measured["artifact"]
        check_h59_domain_guard(artifact, round_text, failures)
        check_zero_denominator(artifact, failures)
        check_no_averaging(artifact, round_text, failures)
        check_cpst_doctrine(artifact, failures)
        check_attribution_correction(artifact, round_text, failures)
        check_self_contradiction(artifact, failures)
        check_zero_counters(artifact, round_text, failures)
    check_no_exploit_code(failures)
    check_forbidden_claims(failures)
    check_offer_lines(failures)
    check_reproducibility(failures)
    check_measure_is_stdlib_only(failures)
    check_doc_structure(round_text, failures)

    if failures:
        print("\n".join(f"❌ {failure}" for failure in failures))
        print(f"\n❌ check_decision_round05: {len(failures)} انتهاكاً.")
        return 1
    print(
        "✅ جولة القرار 05 متّسقة: "
        f"{len(ledger)} فرضيات مشتقّة من سجلّها ({counts['completed']} مُنجَزة · "
        f"{counts['partial']} جزئية · {counts['held']} معلّقة)، ⛔ ولا مستوى فوق E1 وE1 واحدةٌ فقط، "
        f"و{measured.get('matched', 0)} رقماً في §4 مطابقةٌ لملفّ القياس الحتمي، "
        "ودبوسُ AHW محروسٌ في مجاله (صفرُ UNPINNED على 7 دبابيس كاملة · H59 = CONFIRMED_IN_DOMAIN)، "
        "وصفرُ المقام مسجَّلٌ زوجاً (⛔ لا Infinity ولا NaN في الملفّ)، "
        "وتعارضُ طرفَين أوّليين معلَنٌ غيرَ مُسوًّى بمتوسط، "
        "ونِسبةُ ExploitGym مصحَّحةٌ إلى Berkeley RDI، "
        "وصفرُ تشغيلٍ وصفرُ إيرادٍ وصفرُ شيفرةِ استغلالٍ معلَنةٌ في الملفّ والنصّ معاً."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
