"""الحقيقة الاقتصادية — أقصى ما يُقال، وأوّل دليلٍ ناقص، وما لا يُعرَف (D-314 · الطبقة 1).

**لماذا هذه الوحدة موجودة.** للمستودع سلسلة قيمةٍ من ثماني حلقات (``value_chain``) وسجلُّ اتصالٍ
بمجموعة أفعالٍ مغلقة (``contact_ledger``) ولوحةٌ مُشتقّة — وكلٌّ منها يجيب عن سؤاله. لكنّ سؤال
المدير واحد: **ما أقصى ما يحقّ لنا قوله اليوم، وما الدليل الأوّل الناقص، وما الذي لا نعرفه؟**
وكان الجواب يُجمَع بيدٍ من خمسة ملفّات، فيُقرأ «قدرةٌ تعمل» كأنها «عرضٌ جاهز».

**العقد.**

- **لا سُلَّم ثالث:** السقف يُشتقّ من الحلقات المتّصلة نفسها (``value_chain.LINKS``)، وحالات
  التسوية **عرضٌ** فوق أفعال السجلّ المغلقة لا أسماءٌ جديدة. ما ليس له فعلٌ في السجلّ يُعلَن
  «غير قابلٍ للملاحظة» — إضافتُه قرارُ مالك.
- **ثلاث حالاتٍ للادّعاء:** ``SUPPORTED`` (دليلٌ مسجَّل) · ``NOT_SUPPORTED`` (للدليل موطنٌ في
  المستودع وهو يُظهر غيابه) · ``UNKNOWN`` (لا موطن لتسجيله أصلاً — الغياب لا يُثبت شيئاً).
- **شرط القتل يمتنع قبل مقامه:** دون العتبة ``NOT_YET_EVALUABLE`` لا صفرٌ يُقرأ نجاحاً (D-212).
- **كلّ جملةٍ تُبنى على دليلٍ له مُعرِّف** (``evidence``)، والمُعرِّف يشير إلى مسارٍ يجب أن يوجد.

⛔ صفر تبعياتٍ خارج المكتبة القياسية؛ لا استيراد من ``app`` ولا من ``tools``؛ لا نموذج لغوي؛
لا ساعة نظام (``today`` مُدخَل)؛ ولا كتابة — الوحدة تقرأ وتحسب فقط.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import TypedDict

from shared.research.contact_ledger import (
    CALL_MADE,
    CLOSED_DECLINED,
    CLOSED_NO_REPLY,
    DEPOSIT_RECEIVED,
    EMAIL_SENT,
    FORM_SUBMITTED,
    INBOUND,
    LEDGER_REL,
    LINKEDIN_SENT,
    MONEY,
    OUTBOUND,
    PAYMENT_SETTLED,
    QUOTE_SENT,
    REPLY_RECEIVED,
    SAMPLE_DELIVERED,
    SCORECARD_REL,
    LedgerError,
    LedgerRow,
    ledger_sha256,
    parse_ledger,
)
from shared.research.value_chain import (
    CATALOG_REL,
    LINKS,
    REACHED,
    VALUE_CHAIN_REL,
    classify,
    compute_derived,
    problems,
    route_of,
)

__all__ = [
    "ACTIVE_THESIS_DECISION",
    "ACTIVE_THESIS_ID",
    "CLAIMS",
    "CLAIM_STATUSES",
    "DECISIONS_REL",
    "FIRED",
    "HOLDING",
    "KILL_CONDITIONS",
    "NOT_RECORDABLE",
    "NOT_SUPPORTED",
    "NOT_YET_EVALUABLE",
    "SCORECARD_ID",
    "SETTLEMENT_VIEW",
    "SUPPORTED",
    "UNKNOWN",
    "VALUE_CHAIN_ID",
    "Claim",
    "Inputs",
    "KillCondition",
    "SettlementState",
    "WordingLinter",
    "build_snapshot",
    "load_inputs",
]

#: الأطروحة النشطة الوحيدة — موطنها هنا وحده؛ القرار المكتوب في ``DECISIONS_REL`` (D-300).
ACTIVE_THESIS_ID = "fr-be-einvoicing-referential-cleansing"
ACTIVE_THESIS_DECISION = "D-300"
DECISIONS_REL = ".memory/decisions.md"

#: مُعرِّفا دليلٍ ثابتان في السجلّ — كلّ جملةٍ تستشهد بهما تستورد الاسم.
SCORECARD_ID = "SCORECARD"
VALUE_CHAIN_ID = "VALUE_CHAIN"

SUPPORTED = "SUPPORTED"
NOT_SUPPORTED = "NOT_SUPPORTED"
UNKNOWN = "UNKNOWN"
CLAIM_STATUSES: tuple[str, ...] = (SUPPORTED, NOT_SUPPORTED, UNKNOWN)

#: مُدقِّق الصياغة يُحقَن (``tools.hard_currency_engine.buyer_claims``) — ``shared`` لا يستورد
#: ``tools``. يُرجِع لكلّ نصٍّ قائمة ``(rule, verdict, excerpt)``.
WordingLinter = Callable[[str], Sequence[tuple[str, str, str]]]

_BLOCKING_VERDICTS = frozenset({"FORBIDDEN", "UNSUPPORTED"})
#: ما يصف ما يتسلّمه المشتري ومشكلته. ``hard_currency_route_ar`` خارجها عمداً: نطاقاته
#: أسعارُ سوقٍ منشورة يُستشهَد بها (مصادر) لا سعرنا — كما يقرّر اختبار D-304.
_CATALOG_WORDING_FIELDS: tuple[str, ...] = ("offer_outcome_ar", "paid_problem_ar")


# ── الادّعاءات ───────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Claim:
    """ادّعاءٌ تجاري واحد بما يتطلّبه وما يُسقطه وما يُغري باختصاره.

    ``basis`` يقول كيف يُحكَم: ``link`` (حلقةٌ متّصلة ≥ ``ref``) · ``action`` (فعلٌ في السجلّ
    من المجموعة ``ref``) · ``repeat`` (كيانٌ دفع مرّتين) · ``absent`` (للدليل موطنٌ يُظهر
    غيابه — ``ref`` يسمّيه) · ``unrecorded`` (لا موطن لتسجيله — ``UNKNOWN`` دائماً).
    """

    claim_id: str
    basis: str
    ref: str
    statement_ar: str
    requires_ar: str
    external_actor_ar: str
    disconfirming_ar: str
    forbidden_shortcut_ar: str
    decision_affected_ar: str
    expiry_ar: str


def _link_claim(number: int, statement: str, actor: str, disconfirm: str, shortcut: str) -> Claim:
    link = LINKS[number - 1]
    return Claim(
        claim_id=f"C-L{number}",
        basis="link",
        ref=str(number),
        statement_ar=statement,
        requires_ar=f"الحلقة {number} متّصلة: {link.title_ar}",
        external_actor_ar=actor,
        disconfirming_ar=disconfirm,
        forbidden_shortcut_ar=shortcut,
        decision_affected_ar="سقف ما يُقال للمشتري وحالة الكتالوج المسموحة",
        expiry_ar="يسقط حين تُعلَن الحلقة NOT_REACHED أو يُحذَف دليلها",
    )


CLAIMS: tuple[Claim, ...] = (
    _link_claim(
        1,
        "للمشكلة موعدٌ قانونيٌّ مؤرَّخ بمصدر",
        "المشرّع (نصٌّ منشور)",
        "تأجيلٌ رسميٌّ للموعد أو إلغاؤه",
        "الاستشهاد بمقالٍ ثانويٍّ بدل النصّ",
    ),
    _link_claim(
        2,
        "معرّفٌ غير صالحٍ أو مشطوب أو مكرَّر يمنع توجيه الفاتورة (آليةٌ لا نسبة)",
        "منصّات التوجيه (PDP/Peppol)",
        "منصّةٌ تقبل المعرّف المشطوب",
        "تحويل الآلية إلى نسبة رفضٍ لم تُقَس",
    ),
    _link_claim(
        3,
        "عيّنةُ عرضٍ بلا بيانات عميلٍ موجودة",
        "لا أحد — مُصنَّعة",
        "اكتشاف بياناتٍ حقيقية في العيّنة",
        "تقديم العيّنة المُصنَّعة كأنها ملفّ عميل",
    ),
    _link_claim(
        4,
        "أداة التحقّق FR/BE تعمل حتمياً وقابلةً لإعادة الإنتاج على عيّناتٍ مُصنَّعة",
        "لا أحد — اختبارٌ داخلي",
        "اختبارٌ أحمر أو نتيجةٌ تتغيّر بين تشغيلين",
        "قول «تعمل على ملفّاتكم» قبل أيّ ملفٍّ حقيقي",
    ),
    _link_claim(
        5,
        "الأداة أنتجت نتيجةً مفيدة على ملفّ أطرافٍ ثالثة حقيقي",
        "مكتب محاسبةٍ يملك الملفّ",
        "الملفّ الحقيقي بلا أخطاء تلتقطها الأداة ويفوتها برنامج المكتب",
        "إعادة تشغيل الأداة على ملفّات العرض المُصنَّعة",
    ),
    _link_claim(
        6,
        "مشترٍ مسمّى اتّخذ قراراً مربوطاً بتلك النتيجة",
        "المشتري",
        "رفضٌ بعد العيّنة",
        "عدّ مجاملةٍ أو «مثير للاهتمام» قراراً",
    ),
    _link_claim(
        7,
        "طرفٌ خارجيٌّ ردّ (اهتمامٌ مُسجَّل)",
        "المشتري",
        "CLOSED_NO_REPLY أو CLOSED_DECLINED",
        "عدّ رسالةٍ مُرسَلة اهتماماً",
    ),
    _link_claim(
        8,
        "مالٌ تحرّك (عربونٌ أو دفعةٌ مسوّاة)",
        "المشتري والبنك",
        "استرجاعٌ أو رفض البنك",
        "عدّ وعدٍ بالدفع أو فاتورةٍ صادرة مالاً",
    ),
    Claim(
        "C-PAID",
        "action",
        PAYMENT_SETTLED,
        "دفعةٌ مسوّاة بالعملة الصعبة (GATE_C)",
        "صفّ PAYMENT_SETTLED بمبلغٍ وكشفٍ بنكي",
        "المشتري والبنك",
        "استرجاع الدفعة",
        "عربونٌ أو فاتورةٌ أو تحويلٌ «في الطريق»",
        "بقاء الأطروحة أمام شرط القتل (14 يوماً)",
        "يسقط بصفّ استرجاعٍ لا فعل له في السجلّ بعد — قرار مالك",
    ),
    Claim(
        "C-REPEAT",
        "repeat",
        PAYMENT_SETTLED,
        "عميلٌ دفع مرّتين",
        "صفّا PAYMENT_SETTLED للكيان نفسه",
        "العميل نفسه",
        "عدم تجديدٍ بعد الدفعة الأولى",
        "عدّ عميلَين مختلفَين تكراراً",
        "هل هي خدمةٌ متكرّرة أم مهمّةٌ لمرّة",
        "لا يسقط — لكنه لا يُثبت الاحتفاظ دون فترتَي فوترة",
    ),
    Claim(
        "C-RATE",
        "absent",
        f"{VALUE_CHAIN_REL}#OPP-01.links.5",
        "نسبة الأخطاء في ملفّات الأطراف الثالثة الحقيقية معروفة",
        "قياسٌ على ملفّاتٍ حقيقية من عدّة مكاتب",
        "عدّة مكاتب محاسبة",
        "—",
        "الاستقراء من ملفَّي العرض المُصنَّعَين",
        "صياغة العرض ونطاق السعر",
        "—",
    ),
    Claim(
        "C-MARGIN",
        "absent",
        f"{SCORECARD_REL}#gross_margin",
        "الخدمة رابحةٌ لكلّ مهمّة",
        "سجلّ ساعاتٍ وكلفةٍ لأوّل مهمّة",
        "المالك (ساعاته)",
        "مهمّةٌ تستهلك ساعاتٍ أكثر من ثمنها",
        "اعتبار «كلفة النموذج صفر» ربحاً",
        "السعر الواحد 290 €",
        "—",
    ),
    Claim(
        "C-RAIL",
        "unrecorded",
        "activation_gate",
        "مسار قبض اليورو (Malt/SWIFT ← حساب العملة الصعبة) مُجرَّب",
        "جوابٌ مصرفيٌّ مكتوب ودفعةٌ تجريبية",
        "البنك وMalt",
        "رفض البنك أو Malt بلا بديل (شرط قتل)",
        "افتراض أنّ Malt يُحوِّل إلى الجزائر",
        "إرسال عرض سعرٍ مدفوع",
        "—",
    ),
    Claim(
        "C-LEGAL",
        "unrecorded",
        "activation_gate",
        "التسجيل القانوني (بطاقة ANAE) منجز",
        "بطاقة ANAE",
        "ANAE",
        "رفض التسجيل",
        "البيع قبل التسجيل",
        "قانونية الفاتورة الأولى",
        "—",
    ),
    Claim(
        "C-DPA",
        "unrecorded",
        "activation_gate",
        "قالب DPA مُراجَعٌ قانونياً",
        "مراجعة محامٍ مكتوبة",
        "محامٍ",
        "ملاحظاتٌ قانونية تمنع المعالجة",
        "عدّ وجود القالب مراجعةً له",
        "طلب ملفٍّ حقيقي من مكتب",
        "—",
    ),
)
_CLAIMS_BY_ID: dict[str, Claim] = {claim.claim_id: claim for claim in CLAIMS}


# ── شروط القتل (D-300 — الدوسييه §12 حرفياً) ────────────────────────────────────


@dataclass(frozen=True)
class KillCondition:
    """شرط قتلٍ واحد. ``source_quote`` يوجد حرفياً في D-300 — تحرسه الاختبارات.

    ``measure`` يقول كيف يُقاس من صفوف الأطروحة:
    ``ratio:<المقام>:<عتبته>:<البسط>:<حدّه>`` — يُطلَق حين يبلغ المقامُ عتبتَه والبسطُ دون حدّه ·
    ``days_after_first:<الفعل>:<الأيام>`` — يُطلَق حين تمضي الأيام بلا دفعةٍ مسوّاة ·
    ``unrecorded`` — لا فعل في السجلّ يقيسه.
    """

    kill_id: str
    source_quote: str
    rule_ar: str
    measure: str
    proxy_ar: str | None


KILL_CONDITIONS: tuple[KillCondition, ...] = (
    KillCondition(
        "K1",
        "30 اتصالاً مؤهَّلاً ⇒ أقلّ من 3 محادثات",
        "بعد 30 كياناً اتُّصل به: أقلّ من 3 ردّت",
        "ratio:entities_contacted:30:entities_replied:3",
        "«محادثة» = كيانٌ له REPLY_RECEIVED؛ و«مؤهَّل» = كيانٌ في ملفّ الأهداف المسمّاة",
    ),
    KillCondition(
        "K2",
        "10 محادثات ⇒ صفر طلب عرض",
        "بعد 10 كياناتٍ ردّت: صفر عرض سعر",
        "ratio:entities_replied:10:entities_quoted:1",
        "«طلب عرض» = كيانٌ أُرسل إليه QUOTE_SENT (يُرسَل بطلب)",
    ),
    KillCondition(
        "K3",
        "5 عروض ⇒ صفر عربون",
        "بعد 5 عروض: صفر مال",
        "ratio:entities_quoted:5:entities_paid_any:1",
        None,
    ),
    KillCondition(
        "K4",
        "رفض البنك/Malt بلا بديل",
        "رفض البنك أو Malt بلا بديل",
        "unrecorded",
        "لا فعلَ في السجلّ يسجّل جواب البنك — غير قابلٍ للتقييم من الأدلّة",
    ),
    KillCondition(
        "K5",
        "لا دفعة خلال 14 يوماً من جدّيةٍ كاملة",
        "لا دفعة خلال 14 يوماً من أوّل عرض سعر",
        "days_after_first:QUOTE_SENT:14",
        "«الجدّية الكاملة» = أوّل QUOTE_SENT",
    ),
)

#: آخر حلقةٍ تُعلَن في VALUE_CHAIN.json — ما بعدها يُشتقّ من السجلّ وحده.
_LAST_DECLARED_LINK = max(link.number for link in LINKS if link.source == "declared")

FIRED = "FIRED"
HOLDING = "HOLDING"
NOT_YET_EVALUABLE = "NOT_YET_EVALUABLE"
NOT_RECORDABLE = "NOT_RECORDABLE"


# ── عرض التسوية (لا سُلَّم: كلّ حالةٍ فعلٌ في السجلّ أو تُعلَن غير قابلةٍ للملاحظة) ─────


@dataclass(frozen=True)
class SettlementState:
    state: str
    observed_by: str | None
    required_proof_ar: str
    authority_ar: str
    reversible: bool
    permitted_claim_ar: str
    forbidden_claim_ar: str


_OWNER = "المالك وحده يسجّل الصفّ"
SETTLEMENT_VIEW: tuple[SettlementState, ...] = (
    SettlementState(
        "TARGET",
        "targets_file",
        "صفٌّ في ملفّ الأهداف المسمّاة",
        _OWNER,
        True,
        "كيانٌ مسمّى مستهدَف",
        "أنّه مهتمّ",
    ),
    SettlementState(
        "CONTACTED",
        "OUTBOUND",
        "صفّ رسالة/مكالمة/نموذج",
        _OWNER,
        False,
        "تواصلنا معه",
        "أنّه قرأ أو يعاني المشكلة",
    ),
    SettlementState(
        "REPLIED",
        REPLY_RECEIVED,
        "صفّ ردّ",
        _OWNER,
        False,
        "ردّ",
        "أنّه سيدفع",
    ),
    SettlementState(
        "DISCOVERY", None, "مكالمة اكتشاف", _OWNER, False, "—", "كلّ ادّعاءٍ عنها — لا فعل لها"
    ),
    SettlementState(
        "SAMPLE_REQUESTED", None, "طلب عيّنة", _OWNER, False, "—", "كلّ ادّعاءٍ عنه — لا فعل له"
    ),
    SettlementState(
        SAMPLE_DELIVERED,
        SAMPLE_DELIVERED,
        "صفّ عيّنة",
        _OWNER,
        False,
        "سلّمنا عيّنة",
        "أنّها كانت مفيدة",
    ),
    SettlementState(
        "BUYER_DECISION",
        "value_chain_link_6",
        "الحلقة 6 مُعلَنة بدليل",
        "المالك يعلن الحلقة بدليل",
        True,
        "قرارٌ مربوطٌ بنتيجة",
        "قرارٌ بلا نتيجةٍ مستقلّة",
    ),
    SettlementState(
        "PROPOSAL",
        QUOTE_SENT,
        "صفّ عرضٍ بمبلغ",
        _OWNER,
        False,
        "اقترحنا سعراً",
        "أنّه قُبل",
    ),
    SettlementState(
        "DEPOSIT",
        DEPOSIT_RECEIVED,
        "صفّ عربونٍ بمبلغٍ وإيصال",
        _OWNER,
        False,
        "مالٌ تحرّك",
        "أنّ التسليم قُبل",
    ),
    SettlementState(
        "DELIVERY_ACCEPTED", None, "قبول التسليم", _OWNER, False, "—", "كلّ ادّعاءٍ عنه — لا فعل له"
    ),
    SettlementState(
        "INVOICE", None, "فاتورةٌ صادرة", _OWNER, False, "—", "عدّ الفاتورة مالاً — ولا فعل لها"
    ),
    SettlementState(
        PAYMENT_SETTLED,
        PAYMENT_SETTLED,
        "صفّ دفعةٍ بمبلغٍ وكشفٍ بنكي",
        _OWNER,
        False,
        "دفعةٌ مسوّاة",
        "التكرار أو الهامش",
    ),
    SettlementState(
        "REPEAT_PAYMENT",
        "derived:2×PAYMENT_SETTLED",
        "صفّا دفعٍ للكيان نفسه",
        "مُشتقّ",
        False,
        "عميلٌ دفع مرّتين",
        "الاحتفاظ",
    ),
    SettlementState(
        "RETAINED_CUSTOMER",
        f"derived:{SCORECARD_REL}#customer_retention",
        "فترتا فوترة لكيانٍ واحد",
        "مُشتقّ",
        False,
        "عميلٌ محتفَظٌ به",
        "قبل فترتَي فوترة",
    ),
)


# ── أدوات صغيرة ──────────────────────────────────────────────────────────────────


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _items(value: object) -> list[object]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _strs(value: object) -> list[str]:
    return [str(item) for item in _items(value)]


def _thesis_paths(chain_doc: Mapping[str, object]) -> list[Mapping[str, object]]:
    return [
        entry
        for entry in _items(chain_doc.get("paths"))
        if isinstance(entry, Mapping) and entry.get("catalog_id") == ACTIVE_THESIS_ID
    ]


def _thesis_offer(catalog: Mapping[str, object]) -> Mapping[str, object]:
    for offer in _items(catalog.get("offers")):
        if isinstance(offer, Mapping) and offer.get("id") == ACTIVE_THESIS_ID:
            return offer
    return {}


_ACTION_PROOF: dict[str, tuple[str, str]] = {
    EMAIL_SENT: ("تواصلنا معه", "أنّ الرسالة قُرئت أو أنّ المشكلة محسوسة"),
    CALL_MADE: ("تواصلنا معه", "أنّ المكالمة أجيبت أو أنّ المشكلة محسوسة"),
    LINKEDIN_SENT: ("تواصلنا معه", "أنّ الرسالة قُرئت"),
    FORM_SUBMITTED: ("تواصلنا معه", "أنّ النموذج قُرئ"),
    REPLY_RECEIVED: ("ردّ", "نيّة الدفع"),
    SAMPLE_DELIVERED: ("سلّمنا عيّنة", "أنّها كانت مفيدة أو مقبولة"),
    QUOTE_SENT: ("اقترحنا سعراً", "أنّه قُبل"),
    DEPOSIT_RECEIVED: ("مالٌ تحرّك", "قبول التسليم أو التسوية"),
    PAYMENT_SETTLED: ("دفعةٌ مسوّاة", "التكرار أو الهامش"),
    CLOSED_NO_REPLY: ("أُغلق الملفّ بلا ردّ", "لماذا"),
    CLOSED_DECLINED: ("أُغلق الملفّ برفض", "لماذا"),
}


# ── الاشتقاق ─────────────────────────────────────────────────────────────────────


def _evidence(
    thesis: Sequence[Mapping[str, object]],
    rows: Sequence[LedgerRow],
    root: Path,
) -> list[dict[str, object]]:
    def exists(rel: str) -> bool:
        return (root / rel.split("#", 1)[0].split(":", 1)[0]).exists()

    found: list[dict[str, object]] = []
    for entry in thesis:
        pid = str(entry.get("id"))
        declared = _mapping(entry.get("links"))
        for link in LINKS:
            if link.source != "declared":
                continue
            raw = _mapping(declared.get(str(link.number)))
            if raw.get("status") == REACHED:
                paths = _strs(raw.get("evidence"))
                following = LINKS[link.number] if link.number < len(LINKS) else None
                found.append(
                    {
                        "id": f"{pid}.L{link.number}",
                        "kind": "chain",
                        "paths": paths,
                        "exists": bool(paths) and all(exists(p) for p in paths),
                        "proves_ar": link.title_ar,
                        "cannot_prove_ar": following.title_ar if following else "—",
                        "as_of": None,
                    }
                )
            else:
                found.append(
                    {
                        "id": f"{pid}.L{link.number}",
                        "kind": "chain_gap",
                        "paths": [VALUE_CHAIN_REL],
                        "exists": exists(VALUE_CHAIN_REL),
                        "proves_ar": f"الحلقة {link.number} غير مبلوغة: {raw.get('reason_ar') or '—'}",
                        "cannot_prove_ar": "أنّ الفجوة دائمة",
                        "as_of": None,
                    }
                )
    for row in rows:
        proves, cannot = _ACTION_PROOF.get(row.action, ("صفٌّ في السجلّ", "—"))
        amount = f" ({row.amount_eur:g} €)" if row.amount_eur is not None else ""
        found.append(
            {
                "id": f"LEDGER:{row.line_no}",
                "kind": "ledger",
                "paths": [f"{LEDGER_REL}:{row.line_no}"],
                "exists": exists(LEDGER_REL),
                "proves_ar": f"{row.action} — {row.entity} ({row.country}) · {proves}{amount}",
                "cannot_prove_ar": cannot,
                "as_of": row.date.isoformat(),
            }
        )
    for eid, rel, proves in (
        (SCORECARD_ID, SCORECARD_REL, "اللوحة المُشتقّة من السجلّ (GATE_C)"),
        (VALUE_CHAIN_ID, VALUE_CHAIN_REL, "سلسلة القيمة: الحلقات المُعلَنة لكلّ مسار"),
        (f"CATALOG:{ACTIVE_THESIS_ID}", CATALOG_REL, "حالة العرض في الكتالوج وما يُمنَع ادّعاؤه"),
        (ACTIVE_THESIS_DECISION, DECISIONS_REL, "الأطروحة النشطة الوحيدة وشروط قتلها"),
        ("D-304", DECISIONS_REL, "السعر الواحد وقواعد نصّ المشتري"),
        ("D-305", DECISIONS_REL, "حدود مركز العملة الصعبة"),
    ):
        found.append(
            {
                "id": eid,
                "kind": "decision" if eid.startswith("D-") else eid.split(":", 1)[0].lower(),
                "paths": [rel],
                "exists": exists(rel),
                "proves_ar": proves,
                "cannot_prove_ar": "—",
                "as_of": None,
            }
        )
    return found


def _thesis_rows(
    thesis: Sequence[Mapping[str, object]], rows: Sequence[LedgerRow]
) -> list[LedgerRow]:
    routes = {route for entry in thesis for route in _strs(entry.get("ledger_routes"))}
    return [row for row in rows if route_of(row.target_ref) in routes]


def _entities(rows: Sequence[LedgerRow]) -> list[dict[str, object]]:
    grouped: dict[str, list[LedgerRow]] = {}
    for row in sorted(rows, key=lambda r: (r.date, r.line_no)):
        grouped.setdefault(row.entity, []).append(row)
    return [
        {
            "entity": name,
            "country": items[-1].country,
            "target_ref": items[-1].target_ref,
            "actions": [row.action for row in items],
            "outbound": sum(1 for row in items if row.action in OUTBOUND),
            "replied": any(row.action in INBOUND for row in items),
            "last_action": items[-1].action,
            "last_date": items[-1].date.isoformat(),
            "first_date": items[0].date.isoformat(),
            "evidence_ids": [f"LEDGER:{row.line_no}" for row in items],
        }
        for name, items in grouped.items()
    ]


def _entities_with(rows: Sequence[LedgerRow], actions: Iterable[str]) -> set[str]:
    wanted = set(actions)
    return {row.entity for row in rows if row.action in wanted}


def _funnel(rows: Sequence[LedgerRow]) -> dict[str, int]:
    return {
        "contacts_sent": sum(1 for row in rows if row.action in OUTBOUND),
        "entities_contacted": len(_entities_with(rows, OUTBOUND)),
        "entities_replied": len(_entities_with(rows, INBOUND)),
        "samples_delivered": sum(1 for row in rows if row.action == SAMPLE_DELIVERED),
        "entities_quoted": len(_entities_with(rows, {QUOTE_SENT})),
        "entities_paid_any": len(_entities_with(rows, MONEY)),
        "payments_settled": sum(1 for row in rows if row.action == PAYMENT_SETTLED),
    }


def _kill_status(
    kill: KillCondition, funnel: Mapping[str, int], rows: Sequence[LedgerRow], today: date
) -> dict[str, object]:
    kind, _, spec = kill.measure.partition(":")
    status, progress = NOT_RECORDABLE, kill.proxy_ar or "—"
    if kind == "ratio":
        denom_key, threshold, num_key, floor = spec.split(":")
        denom, num = funnel[denom_key], funnel[num_key]
        progress = f"{denom_key}={denom}/{threshold} · {num_key}={num}"
        if denom < int(threshold):
            status = NOT_YET_EVALUABLE
        else:
            status = FIRED if num < int(floor) else HOLDING
    elif kind == "days_after_first":
        action, days = spec.split(":")
        firsts = sorted(row.date for row in rows if row.action == action)
        if not firsts:
            status, progress = NOT_YET_EVALUABLE, f"لا {action} بعد"
        elif funnel["payments_settled"] > 0:
            status, progress = HOLDING, "دفعةٌ مسوّاة مسجّلة"
        else:
            elapsed = (today - firsts[0]).days
            status = FIRED if elapsed > int(days) else NOT_YET_EVALUABLE
            progress = f"{elapsed}/{days} يوماً منذ أوّل {action}"
    return {**asdict(kill), "status": status, "progress": progress}


def _claim_status(
    claim: Claim,
    *,
    best_reached: int,
    best_path: str | None,
    rows: Sequence[LedgerRow],
) -> dict[str, object]:
    status, evidence = UNKNOWN, [SCORECARD_ID]
    basis = "لا موطن في المستودع لتسجيل هذا الدليل — الغياب لا يُثبت شيئاً"
    if claim.basis == "link" and int(claim.ref) <= _LAST_DECLARED_LINK:
        number = int(claim.ref)
        status = SUPPORTED if best_reached >= number else NOT_SUPPORTED
        evidence = (
            [f"{best_path}.L{n}" for n in range(1, number + 1)]
            if status == SUPPORTED
            else [f"{best_path}.L{number}"]
        )
        basis = f"أعلى حلقةٍ متّصلة لمسارات الأطروحة: {best_reached}"
    elif claim.basis == "link":
        # الحلقتان 7–8 تُقرآن من السجلّ: الصفّ حقيقة وإن كان فوق فجوة — لكنه لا يرفع السقف.
        number = int(claim.ref)
        wanted = INBOUND if number == 7 else MONEY
        matching = [row for row in rows if row.action in wanted]
        status = SUPPORTED if matching else NOT_SUPPORTED
        evidence = [f"LEDGER:{row.line_no}" for row in matching] or [SCORECARD_ID]
        above_gap = matching and best_reached < number - 1
        basis = f"صفوف {sorted(wanted)} في السجلّ: {len(matching)}" + (
            " — فوق فجوة: مُسجَّل ولا يرفع السقف" if above_gap else ""
        )
    elif claim.basis == "action":
        matching = [row for row in rows if row.action == claim.ref]
        status = SUPPORTED if matching else NOT_SUPPORTED
        evidence = [f"LEDGER:{row.line_no}" for row in matching] or [SCORECARD_ID]
        basis = f"صفوف {claim.ref} في السجلّ: {len(matching)}"
    elif claim.basis == "repeat":
        counts: dict[str, int] = {}
        for row in rows:
            if row.action == PAYMENT_SETTLED:
                counts[row.entity] = counts.get(row.entity, 0) + 1
        status = SUPPORTED if any(n >= 2 for n in counts.values()) else NOT_SUPPORTED
        evidence = [SCORECARD_ID]
        basis = f"أكثر دفعاتٍ لكيانٍ واحد: {max(counts.values(), default=0)}"
    elif claim.basis == "absent":
        status = NOT_SUPPORTED
        evidence = [SCORECARD_ID] if SCORECARD_REL in claim.ref else [f"{best_path}.L5"]
        basis = f"موطن الدليل يُظهر غيابه: {claim.ref}"
    return {**asdict(claim), "status": status, "evidence_ids": evidence, "basis_ar": basis}


def build_snapshot(
    *,
    chain_doc: Mapping[str, object],
    ledger_text: str,
    catalog: Mapping[str, object],
    scorecard: Mapping[str, object],
    root: Path,
    today: date,
    wording: WordingLinter | None = None,
) -> dict[str, object]:
    """``EconomicTruthSnapshot`` كاملاً — حتميٌّ لنفس المُدخَلات (لا ساعة، لا شبكة، لا كتابة)."""
    ledger_problems: list[str] = []
    try:
        rows = parse_ledger(ledger_text, today=today)
    except LedgerError as exc:
        rows = []
        ledger_problems = [line for line in str(exc).splitlines() if line.strip()]

    thesis = _thesis_paths(chain_doc)
    derived = compute_derived(chain_doc, rows)
    derived_by_id = {
        str(item.get("id")): item
        for item in _items(derived.get("paths"))
        if isinstance(item, Mapping)
    }
    thesis_view: list[dict[str, object]] = []
    for entry in thesis:
        item = _mapping(derived_by_id.get(str(entry.get("id"))))
        reached = item.get("reached")
        thesis_view.append(
            {
                "id": entry.get("id"),
                "title_ar": entry.get("title_ar"),
                "reached": reached if isinstance(reached, int) else 0,
                "classification": item.get("classification"),
                "next_link": item.get("next_link"),
                "next_link_title_ar": item.get("next_link_title_ar"),
                "next_actor": item.get("next_actor"),
                "ledger_routes": _strs(entry.get("ledger_routes")),
            }
        )
    best = max(thesis_view, key=lambda p: int(str(p["reached"])), default=None)
    best_reached = int(str(best["reached"])) if best else 0
    best_path = str(best["id"]) if best else None

    rows_in_thesis = _thesis_rows(thesis, rows)
    funnel = _funnel(rows_in_thesis)
    claims = [
        _claim_status(claim, best_reached=best_reached, best_path=best_path, rows=rows_in_thesis)
        for claim in CLAIMS
    ]
    ceiling_claim = _CLAIMS_BY_ID.get(f"C-L{best_reached}") if best_reached else None
    ceiling = {
        "claim_id": ceiling_claim.claim_id if ceiling_claim else None,
        "statement_ar": ceiling_claim.statement_ar if ceiling_claim else "لا ادّعاء — لا حلقة متّصلة",
        "classification": classify(best_reached),
        "link": best_reached,
        "path_id": best_path,
        "evidence_ids": [
            f"{best_path}.L{n}" for n in range(1, min(best_reached, _LAST_DECLARED_LINK) + 1)
        ]
        if best_path
        else [],
    }

    first_missing: dict[str, object] | None = None
    if best is not None and best["next_link"] is not None:
        number = int(str(best["next_link"]))
        entry = next(e for e in thesis if e.get("id") == best_path)
        declared = _mapping(_mapping(entry.get("links")).get(str(number)))
        link = LINKS[number - 1]
        first_missing = {
            "path_id": best_path,
            "link": number,
            "title_ar": link.title_ar,
            "reason_ar": declared.get("reason_ar")
            or ("لا صفّ في CONTACT_LEDGER.csv" if link.source == "ledger" else None),
            "actor": link.actor,
            "why_not_code_ar": (
                "مالك الحلقة إنسان: ما يسدّها بياناتٌ أو نظامٌ أو قرارٌ لم نكتبه، والكود لا يخترعه"
                if link.actor == "human"
                else "الحلقة برمجية: مُسبارٌ أو اختبارٌ يستطيع الكود إنتاجه"
            ),
            "evidence_ids": (
                [f"{best_path}.L{number}"] if number <= _LAST_DECLARED_LINK else [SCORECARD_ID]
            ),
        }

    last = max(rows, key=lambda r: (r.date, r.line_no), default=None)
    offer = _thesis_offer(catalog)

    contradictions: list[dict[str, object]] = []
    actual_sha = ledger_sha256(ledger_text)
    if scorecard.get("source_sha256") != actual_sha:
        contradictions.append(
            {
                "kind": "stale_scorecard",
                "detail_ar": "اللوحة مُشتقّةٌ من نسخةٍ أخرى من السجلّ — شغّل scripts/research/hard_currency_scorecard.py",
                "evidence_ids": [SCORECARD_ID],
            }
        )
    for problem in problems(chain_doc, root=root, ledger_rows=rows, catalog=catalog):
        contradictions.append(
            {"kind": "value_chain", "detail_ar": problem, "evidence_ids": [VALUE_CHAIN_ID]}
        )
    if wording is not None:
        for field in _CATALOG_WORDING_FIELDS:
            for rule, verdict, excerpt in wording(str(offer.get(field) or "")):
                if verdict in _BLOCKING_VERDICTS:
                    contradictions.append(
                        {
                            "kind": "catalog_wording",
                            "detail_ar": (
                                f"الكتالوج ({field}) يقول «{excerpt}» — {verdict} ({rule}) "
                                "ويناقض claims_forbidden_ar"
                            ),
                            "evidence_ids": [f"CATALOG:{ACTIVE_THESIS_ID}"],
                        }
                    )

    blind_spots: list[dict[str, object]] = [
        {
            "kind": "unrouted_path",
            "detail_ar": f"{p['id']} بلا ledger_routes — اتصالٌ له لا يُسجَّل (البوّابة تحمرّ على صفٍّ غير موجَّه)",
        }
        for p in thesis_view
        if not p["ledger_routes"]
    ]
    blind_spots.extend(
        {
            "kind": "unobservable_state",
            "detail_ar": f"{state.state}: لا فعل في السجلّ — إضافته قرار مالك",
        }
        for state in SETTLEMENT_VIEW
        if state.observed_by is None
    )
    blind_spots.extend(
        {
            "kind": "unrecorded_claim",
            "detail_ar": f"{claim['claim_id']}: {claim['statement_ar']} — لا موطن لتسجيله",
        }
        for claim in claims
        if claim["status"] == UNKNOWN
    )

    metrics = _mapping(scorecard.get("hard_currency_scorecard"))
    missing_denominators = [
        {"metric": name, "basis": _mapping(value).get("basis")}
        for name, value in metrics.items()
        if _mapping(value).get("value") is None
    ]

    return {
        "today": today.isoformat(),
        "thesis": {
            "id": ACTIVE_THESIS_ID,
            "decision": ACTIVE_THESIS_DECISION,
            "catalog_status": offer.get("status"),
            "paths": thesis_view,
        },
        "ledger_valid": not ledger_problems,
        "ledger_problems": ledger_problems,
        "gate_c": scorecard.get("gate_c"),
        "funnel": funnel,
        "ceiling": ceiling,
        "first_missing_proof": first_missing,
        "last_event": (
            {
                "date": last.date.isoformat(),
                "action": last.action,
                "entity": last.entity,
                "evidence_ids": [f"LEDGER:{last.line_no}"],
            }
            if last
            else None
        ),
        "days_since_last_event": (today - last.date).days if last else None,
        "claims": claims,
        "kill_conditions": [
            _kill_status(k, funnel, rows_in_thesis, today) for k in KILL_CONDITIONS
        ],
        "entities": _entities(rows_in_thesis),
        "settlement_view": [asdict(state) for state in SETTLEMENT_VIEW],
        "missing_denominators": missing_denominators,
        "contradictions": contradictions,
        "blind_spots": blind_spots,
        "wording_checked": wording is not None,
        "claims_forbidden_ar": offer.get("claims_forbidden_ar"),
        "evidence": _evidence(thesis, rows_in_thesis, root),
    }


class Inputs(TypedDict):
    """مُدخَلات ``build_snapshot`` من المستودع — مفتاحاً بمفتاح."""

    chain_doc: dict[str, object]
    ledger_text: str
    catalog: dict[str, object]
    scorecard: dict[str, object]


def load_inputs(root: Path) -> Inputs:
    """المُدخَلات من المستودع — للسكربتات والاختبارات؛ الخادم يقرأها عبر مصادره المحقونة."""

    def read_json(rel: str) -> dict[str, object]:
        payload: object = json.loads((root / rel).read_text(encoding="utf-8"))
        return dict(payload) if isinstance(payload, Mapping) else {}

    return {
        "chain_doc": read_json(VALUE_CHAIN_REL),
        "ledger_text": (root / LEDGER_REL).read_text(encoding="utf-8"),
        "catalog": read_json(CATALOG_REL),
        "scorecard": read_json(SCORECARD_REL),
    }
