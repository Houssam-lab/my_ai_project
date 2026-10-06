"""القرار الاقتصادي — اختناقٌ واحد، وفعلٌ بشريٌّ واحد، وجملٌ لا تتجاوز دليلها (D-314 · الطبقتان 2 و4).

**لماذا هذه الوحدة موجودة.** ``economic_truth`` يقول ما الحقيقة؛ هذه تقول **ماذا يُفعل بها**:
أين تنقطع السلسلة أوّلاً، وما أصغر فعلٍ قانونيٍّ قابلٍ للتراجع يُنتج الدليل الناقص، وكيف يُقال
كلّ ذلك بجملٍ يحمل كلٌّ منها صنفها ودليلها.

**العقد.**

- **فعلٌ أساسيٌّ واحد بالضبط** من جدولٍ ثابت (``ACTIONS``) — يُختار بقاعدةٍ معجمية مُعلَنة:
  قانونيٌّ الآن ← قابلٌ للتراجع ← يُنتج الدليل الناقص التالي ← أقلّ وقتاً من المالك. ⛔ لا أرقام
  «درجات» مُخترَعة: صيغةٌ ضربيةٌ بلا قياسٍ دقّةٌ زائفة.
- إن تعذّر فعلٌ قانوني (سجلٌّ لا يُقرأ · شرط قتلٍ أُطلق) ⇒ ``NO_LAWFUL_DECISION_AVAILABLE`` بالسبب.
- **كلّ جملةٍ مُصنَّفة** ``FACT|HYPOTHESIS|UNKNOWN|ACTION|REFUSAL``، و``FACT`` بلا مُعرِّف دليلٍ
  مرفوضة، ومُعرِّفٌ غير موجود مرفوض (``sentence_problems``). العقد نفسه يحكم أيّ مولِّد لغةٍ لاحق.
- **لا كتابة:** معاينة النتيجة (``preview_outcome``) تُرجِع السطر و«ماذا يتغيّر» و``written: false`` —
  المالك يلتزم السطر عبر git، وgit هو سجلّ التدقيق.

⛔ صفر تبعياتٍ خارج المكتبة القياسية؛ لا ``app`` ولا ``tools`` (مُدقِّق الصياغة يُحقَن)؛ لا نموذج لغوي.
"""

from __future__ import annotations

import csv
import io
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from shared.research.contact_ledger import (
    CALL_MADE,
    CLOSED_DECLINED,
    COLUMNS,
    DEPOSIT_RECEIVED,
    EMAIL_SENT,
    LEDGER_REL,
    PAYMENT_SETTLED,
    QUOTE_SENT,
    REPLY_RECEIVED,
    SAMPLE_DELIVERED,
    SCORECARD_REL,
    LedgerError,
    parse_ledger,
    row_problems,
)
from shared.research.economic_truth import (
    ACTIVE_THESIS_DECISION,
    ACTIVE_THESIS_ID,
    FIRED,
    NOT_SUPPORTED,
    SCORECARD_ID,
    SUPPORTED,
    UNKNOWN,
    VALUE_CHAIN_ID,
    WordingLinter,
    build_snapshot,
)
from shared.research.value_chain import (
    CATALOG_REQUIRES,
    FORBIDDEN_TERMS,
    VALUE_CHAIN_REL,
    route_of,
    route_table,
)

__all__ = [
    "ACTIONS",
    "BOTTLENECKS",
    "DECISION_AVAILABLE",
    "NO_LAWFUL_DECISION",
    "QUESTIONS",
    "SENTENCE_CLASSES",
    "Action",
    "TextClassifier",
    "build_brief",
    "cross_examine",
    "preview_outcome",
    "render_sentences",
    "sentence_problems",
]

DECISION_AVAILABLE = "DECISION_AVAILABLE"
NO_LAWFUL_DECISION = "NO_LAWFUL_DECISION_AVAILABLE"

#: مجموعةٌ مغلقة — اختناقٌ خارجها لا يُسمّى.
BOTTLENECKS: tuple[str, ...] = (
    "technical",
    "buyer_trust",
    "legal",
    "payment",
    "data_access",
    "delivery_cost",
    "founder_capacity",
    "evidence",
    "channel",
    "pricing",
    "unknown",
)

FACT = "FACT"
HYPOTHESIS = "HYPOTHESIS"
ACTION = "ACTION"
REFUSAL = "REFUSAL"
SENTENCE_CLASSES: tuple[str, ...] = (FACT, HYPOTHESIS, UNKNOWN, ACTION, REFUSAL)

#: أسئلة الاستجواب المغلقة — لا محادثة حرّة.
QUESTIONS: tuple[str, ...] = ("ready", "build", "why_no_money", "say_to_buyer")

#: مُصنِّف نصّ المشتري يُحقَن (``tools.hard_currency_engine.buyer_claims.classify``):
#: النصّ ⇒ (الحكم، السبب، [(القاعدة، المقتطف)]).
TextClassifier = Callable[[str], tuple[str, str, Sequence[tuple[str, str]]]]

_TARGETS_HINT = "الهدف التالي غير المتّصَل به في ملفّ الأهداف المسمّاة"
_REGENERATE = (
    "python3 scripts/research/hard_currency_scorecard.py && python3 scripts/research/value_chain.py"
)


@dataclass(frozen=True)
class Action:
    """فعلٌ بشريٌّ واحد بكلّ ما يحتاجه المالك ليقرّر وينفّذ ويسجّل.

    ``time_rank`` ترتيبٌ لا قياس: «مكالمةٌ لكيانٍ اتّصلنا به أقلّ من إيجاد هدفٍ جديد والكتابة إليه».
    """

    action_id: str
    bottleneck: str
    title_ar: str
    steps_ar: tuple[str, ...]
    produces: tuple[str, ...]
    reversible: bool
    time_rank: int
    time_cap_ar: str
    hypothesis_ar: str
    mechanism_ar: str
    success_ar: str
    failure_ar: str
    decision_change_ar: str
    risk_ar: str
    row_channel: str
    row_action: str
    kill_id: str | None
    requires_supported: tuple[str, ...] = ()


ACTIONS: tuple[Action, ...] = (
    Action(
        "FOLLOW_UP_CALL",
        "channel",
        "اتّصل هاتفياً بـ{entity} — رسالةٌ واحدة في {date} بلا ردٍّ ولا متابعةٍ مسجّلة",
        (
            "افتح صفّه في ملفّ الأهداف وتحقّق من flag_opposition قبل الاتصال",
            "مكالمةٌ واحدة: هل وصلت الرسالة؟ هل يُدار تنظيف المرجعيات داخلياً أم لا؟",
            "اعرض عيّنة 20 سجلّاً مجّاناً — لا نسبة ولا ضمان (D-304)",
            "سجّل CALL_MADE، وREPLY_RECEIVED إن أجاب، أو CLOSED_DECLINED إن رفض",
        ),
        (CALL_MADE, REPLY_RECEIVED, CLOSED_DECLINED),
        True,
        1,
        "محاولة اتصالٍ واحدة ورسالةٌ صوتية واحدة، ثمّ توقّف",
        "لم يردّ {entity} لأنّ الرسالة لم تُرَ، لا لأنّ المشكلة غائبة",
        "رسالةٌ باردة واحدة تضيع؛ المكالمة تكشف إن كانت المشكلة محسوسة",
        "ردٌّ مسجّل (الحلقة 7) أو طلب عيّنة",
        "رفضٌ صريح أو لا جواب بعد المحاولة",
        "ردٌّ ⇒ طلب ملفٍّ حقيقي (الحلقة 5)؛ رفضٌ أو صمت ⇒ الهدف التالي",
        "إزعاجُ مكتبٍ اعترض على الاستقبال التجاري — لذلك فحص flag_opposition أوّلاً",
        "phone",
        CALL_MADE,
        "K1",
    ),
    Action(
        "NEXT_CONTACT",
        "channel",
        "راسل " + _TARGETS_HINT,
        (
            "اختر أوّل هدفٍ لا صفّ له في CONTACT_LEDGER.csv وflag_opposition عنده لا يمنع",
            "انسخ الرسالة من ready_to_send/01_MAILS_CABINETS_PRETS.md بلا تعديل الأرقام",
            "سجّل EMAIL_SENT بعد الإرسال لا قبله",
        ),
        (EMAIL_SENT,),
        True,
        2,
        "رسالةٌ واحدة؛ كرِّر حتى 30 كياناً (شرط القتل K1)",
        "مكاتب المحاسبة تردّ على عرض عيّنةٍ مجّانية",
        "الحجم: شرط القتل K1 لا يُقيَّم قبل 30 كياناً",
        "ردٌّ مسجّل",
        "30 كياناً بأقلّ من 3 ردود (K1 يُطلَق)",
        "يقرّب K1 من مقامه — حتى 30 لا حكم",
        "إرسال إلى مكتبٍ معترِض",
        "email",
        EMAIL_SENT,
        "K1",
    ),
    Action(
        "REQUEST_REAL_FILE",
        "data_access",
        "اطلب من {entity} ملفّ أطرافٍ ثالثة حقيقياً بموجب قالب DPA",
        (
            "أرسل قالب DPA_NDA_TEMPLATE_FR.md قبل استلام أيّ ملفّ",
            "عالج الملفّ بالأداة الحتمية محلّياً — لا تخزين، لا نموذج لغوي، لا مشاركة",
            "سلّم التقرير والملفّ المنظَّف ثمّ سجّل SAMPLE_DELIVERED",
        ),
        (SAMPLE_DELIVERED,),
        True,
        1,
        "ملفٌّ واحد حتى 20 سجلّاً",
        "ملفّ {entity} الحقيقي يحمل أخطاءً تلتقطها الأداة",
        "الحلقة 5 لا تُسدّ ببيانات مُصنَّعة",
        "تقريرٌ بأخطاءٍ حقيقية يُعلَن دليلاً للحلقة 5",
        "ملفٌّ نظيفٌ أصلاً أو رفض المشاركة",
        "نتيجةٌ مفيدة ⇒ عرض سعر؛ لا نتيجة ⇒ إعادة النظر في الأطروحة",
        "قالب DPA غير مُراجَع قانونياً (C-DPA مجهول)",
        "email",
        SAMPLE_DELIVERED,
        "K2",
    ),
    Action(
        "DECLARE_LINK_5",
        "evidence",
        "أعلِن الحلقة 5 في VALUE_CHAIN.json بتقرير العيّنة دليلاً",
        (
            "أضف مسار التقرير (بلا بيانات العميل) دليلاً للحلقة 5",
            "شغّل " + _REGENERATE,
        ),
        (),
        True,
        1,
        "تعديلٌ واحد",
        "العيّنة المُسلَّمة نتيجةٌ على بياناتٍ لم نكتبها",
        "التصنيف يُشتقّ من الحلقات المُعلَنة لا من السجلّ",
        "الحلقة 5 REACHED والبوّابة خضراء",
        "لا تقرير يصلح دليلاً دون كشف بيانات العميل",
        "يرفع السقف إلى validated_capability",
        "تسريب بيانات العميل في المستودع",
        "",
        "",
        None,
    ),
    Action(
        "ASK_BANK_IN_WRITING",
        "payment",
        "اطلب من البنك جواباً مكتوباً عن استقبال EUR على حساب العملة الصعبة",
        (
            "رسالةٌ مكتوبة إلى البنك: استقبال تحويلٍ لخدمةٍ مُصدَّرة، والآجال (النظام 26-02)",
            "احفظ الجواب خارج المستودع — لا فعل في السجلّ يسجّله بعد (قرار مالك)",
        ),
        (),
        True,
        2,
        "رسالةٌ واحدة",
        "البنك يقبل استقبال اليورو لخدمةٍ مُصدَّرة",
        "D-304: لا طلبَ مدفوع قبل جواب البنك وANAE وDPA",
        "جوابٌ مكتوبٌ إيجابي",
        "رفضٌ بلا بديل (شرط القتل K4)",
        "يفتح عرض السعر الأوّل",
        "لا أثر على المشتري",
        "bank",
        "",
        "K4",
    ),
    Action(
        "SEND_QUOTE",
        "pricing",
        "أرسل إلى {entity} عرض 290 € HT حتى 200 سجلّ",
        ("سعرٌ واحد (D-304)", "سجّل QUOTE_SENT بالمبلغ"),
        (QUOTE_SENT,),
        True,
        1,
        "عرضٌ واحد",
        "{entity} يدفع 290 € لملفٍّ نظيف",
        "PRICING HYPOTHESIS — لا دليل سعرٍ بعد",
        "عربونٌ أو قبول",
        "رفضٌ على السعر",
        "يقرّب K3 وK5",
        "عرضٌ قبل جاهزية القبض",
        "email",
        QUOTE_SENT,
        "K3",
        ("C-RAIL", "C-LEGAL"),
    ),
    Action(
        "FOLLOW_UP_QUOTE",
        "buyer_trust",
        "تابِع عرض السعر مع {entity}",
        ("مكالمةٌ واحدة", "سجّل الجواب: DEPOSIT_RECEIVED أو CLOSED_DECLINED"),
        (DEPOSIT_RECEIVED, PAYMENT_SETTLED, CLOSED_DECLINED),
        True,
        1,
        "متابعةٌ واحدة",
        "العرض لم يُقرَّر بعد لا مرفوض",
        "الصمت بعد العرض ليس رفضاً حتى يُسأل",
        "عربون",
        "رفض",
        "مال ⇒ تسليم؛ رفض ⇒ الهدف التالي",
        "ضغطٌ يُفقد الثقة",
        "phone",
        CALL_MADE,
        "K5",
    ),
    Action(
        "SETTLE",
        "payment",
        "سلّم لـ{entity} وأصدر الفاتورة وسجّل الدفعة حين تُسوّى",
        ("سلّم الملفّ المنظَّف", "سجّل PAYMENT_SETTLED بكشف بنكي فقط"),
        (PAYMENT_SETTLED,),
        False,
        1,
        "مهمّةٌ واحدة",
        "التسليم يُقبَل والدفعة تُسوّى",
        "العربون ليس تسوية",
        PAYMENT_SETTLED,
        "استرجاع أو رفض التسليم",
        "GATE_C",
        "تسليمٌ قبل جاهزية القبض",
        "bank",
        PAYMENT_SETTLED,
        "K5",
    ),
    Action(
        "RECORD_COST",
        "delivery_cost",
        "سجّل ساعات المهمّة الأولى وكلفتها",
        ("ساعاتٌ فعلية لا تقدير",),
        (),
        True,
        1,
        "سجلٌّ واحد",
        "290 € تغطّي ساعات المهمّة",
        "الهامش مجهولٌ بلا سجلّ كلفة",
        "هامشٌ موجب",
        "هامشٌ سالب",
        "يقرّر السعر",
        "لا أثر خارجي",
        "email",
        "",
        None,
    ),
    Action(
        "ASK_NEXT_FILE",
        "buyer_trust",
        "اطلب من {entity} الملفّ التالي",
        ("سجّل الجواب",),
        (QUOTE_SENT, PAYMENT_SETTLED),
        True,
        1,
        "طلبٌ واحد",
        "العميل يعود",
        "التكرار يفرّق الخدمة عن المهمّة",
        "دفعةٌ ثانية",
        "لا عودة",
        "خدمةٌ متكرّرة أم مهمّةٌ لمرّة",
        "لا أثر",
        "email",
        "",
        None,
    ),
)
_ACTIONS_BY_ID: dict[str, Action] = {action.action_id: action for action in ACTIONS}

_TEMPTING: dict[str, str] = {
    "channel": "كتابة دراسةٍ أخرى أو بناء ميزةٍ أو صفحة هبوط بدل الاتصال بالمشتري التالي (D-297)",
    "data_access": "إعادة تشغيل الأداة على ملفّات العرض المُصنَّعة وتقديم النتيجة كأنها ملفّ عميل",
    "evidence": "رفع الحالة في الكتالوج بيدٍ بدل إعلان الحلقة بدليل",
    "payment": "إرسال عرض سعرٍ مدفوع قبل جواب البنك وANAE وDPA (D-304)",
    "pricing": "نطاق أسعار بدل السعر الواحد",
    "buyer_trust": "عدّ «مثير للاهتمام» قراراً",
    "delivery_cost": "اعتبار «كلفة النموذج صفر» هامشاً",
}


# ── أدوات ────────────────────────────────────────────────────────────────────────


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _maps(value: object) -> list[Mapping[str, object]]:
    return [item for item in value if isinstance(item, Mapping)] if isinstance(value, list) else []


def _int(value: object) -> int:
    return value if isinstance(value, int) else 0


def _claim_status(snapshot: Mapping[str, object], claim_id: str) -> str:
    for claim in _maps(snapshot.get("claims")):
        if claim.get("claim_id") == claim_id:
            return str(claim.get("status"))
    return UNKNOWN


def _funnel_at_least(key: str) -> Callable[[Mapping[str, object]], bool]:
    return lambda snapshot: _int(_mapping(snapshot.get("funnel")).get(key)) > 0


#: السلسلة بالترتيب — أوّل شرطٍ غير محقَّق يسمّي الاختناق. والدفعتان مرحلتان: مالٌ تحرّك
#: (عربون) ثمّ تسوية؛ وبعد التسوية الهامش، وبعده التكرار.
_STAGES: tuple[tuple[str, Callable[[Mapping[str, object]], bool]], ...] = (
    ("channel", _funnel_at_least("entities_replied")),
    ("data_access", _funnel_at_least("samples_delivered")),
    ("evidence", lambda s: _int(_mapping(s.get("ceiling")).get("link")) >= 5),
    ("payment", _funnel_at_least("entities_quoted")),
    ("buyer_trust", _funnel_at_least("entities_paid_any")),
    ("payment", _funnel_at_least("payments_settled")),
    ("delivery_cost", lambda s: _claim_status(s, "C-MARGIN") == SUPPORTED),
)


def _stage(snapshot: Mapping[str, object]) -> tuple[str, Mapping[str, object] | None]:
    """أين تنقطع السلسلة أوّلاً — الاختناق والكيان المعنيّ إن وُجد."""
    bottleneck = next((name for name, met in _STAGES if not met(snapshot)), "buyer_trust")
    entities = _maps(snapshot.get("entities"))
    open_entities = [e for e in entities if not str(e.get("last_action")).startswith("CLOSED")]
    if bottleneck == "channel":
        # المتابعة لكيانٍ راسلناه مرّةً واحدة ولم يردّ — لا لمن تابعناه من قبل.
        pool = [e for e in open_entities if _int(e.get("outbound")) == 1]
    else:
        pool = [e for e in open_entities if e.get("replied")]
    ordered = sorted(pool, key=lambda e: str(e.get("first_date")))
    return bottleneck, ordered[0] if ordered else None


def _candidates(bottleneck: str, snapshot: Mapping[str, object], entity: object) -> list[Action]:
    funnel = _mapping(snapshot.get("funnel"))
    if bottleneck == "channel":
        names = ["FOLLOW_UP_CALL"] if entity is not None else []
        if _int(funnel.get("entities_contacted")) < 30:
            names.append("NEXT_CONTACT")
    elif bottleneck == "payment" and _int(funnel.get("entities_quoted")) == 0:
        names = ["ASK_BANK_IN_WRITING", "SEND_QUOTE"]
    elif bottleneck == "payment":
        names = ["SETTLE"]
    elif bottleneck == "buyer_trust" and _int(funnel.get("payments_settled")) == 0:
        names = ["FOLLOW_UP_QUOTE"]
    else:
        names = {
            "data_access": ["REQUEST_REAL_FILE"],
            "evidence": ["DECLARE_LINK_5"],
            "delivery_cost": ["RECORD_COST"],
            "buyer_trust": ["ASK_NEXT_FILE"],
        }.get(bottleneck, [])
    return [_ACTIONS_BY_ID[name] for name in names]


def _lawful_now(action: Action, snapshot: Mapping[str, object]) -> bool:
    return all(_claim_status(snapshot, claim) == SUPPORTED for claim in action.requires_supported)


def _fill(text: str, entity: Mapping[str, object] | None) -> str:
    if entity is None:
        return text.replace("{entity}", _TARGETS_HINT).replace("{date}", "—")
    return text.replace("{entity}", str(entity.get("entity"))).replace(
        "{date}", str(entity.get("last_date"))
    )


def _row_template(action: Action, entity: Mapping[str, object] | None) -> dict[str, str] | None:
    if not action.row_action:
        return None
    return {
        "date": "<YYYY-MM-DD>",
        "target_ref": str(entity.get("target_ref")) if entity else "<ملفّ الأهداف>#id=<n>",
        "entity": str(entity.get("entity")) if entity else "<اسم الكيان>",
        "country": str(entity.get("country")) if entity else "FR",
        "channel": action.row_channel,
        "action": action.row_action,
        "amount_eur": "<مبلغ>" if action.row_action in {QUOTE_SENT, PAYMENT_SETTLED} else "",
        "evidence_ref": "<كشف بنكي>" if action.row_action == PAYMENT_SETTLED else "",
        "note": "",
    }


# ── الموجز ───────────────────────────────────────────────────────────────────────


def build_brief(snapshot: Mapping[str, object]) -> dict[str, object]:
    """``EconomicDecisionBrief`` — فعلٌ أساسيٌّ واحد أو امتناعٌ بسببه."""
    kills = _maps(snapshot.get("kill_conditions"))
    if not snapshot.get("ledger_valid"):
        return _no_decision(
            "evidence",
            "السجلّ لا يُقرأ — لا قرار على أدلّةٍ لا تُقرأ",
            _ids(snapshot.get("ledger_problems")),
        )
    if fired := [k for k in kills if k.get("status") == FIRED]:
        return _no_decision(
            None,
            "شرط قتلٍ أُطلق — الاستمرار أو القتل قرارُ مالكٍ مكتوب لا فعلٌ يُقترَح",
            [f"{k.get('kill_id')}: {k.get('source_quote')} ({k.get('progress')})" for k in fired],
        )

    bottleneck, entity = _stage(snapshot)
    candidates = _candidates(bottleneck, snapshot, entity)
    first_missing = _mapping(snapshot.get("first_missing_proof"))

    def key(action: Action) -> tuple[bool, bool, bool, int]:
        produces_next = bool(action.produces) or action.action_id == "DECLARE_LINK_5"
        return (
            not _lawful_now(action, snapshot),
            not action.reversible,
            not produces_next,
            action.time_rank,
        )

    ranked = sorted(candidates, key=key)
    lawful = [action for action in ranked if _lawful_now(action, snapshot)]
    considered = [
        {
            "action_id": action.action_id,
            "lawful_now": _lawful_now(action, snapshot),
            "reversible": action.reversible,
            "produces": list(action.produces),
            "time_rank": action.time_rank,
            "requires_supported": list(action.requires_supported),
            "chosen": bool(lawful) and action is lawful[0],
        }
        for action in ranked
    ]
    if not lawful:
        return _no_decision(
            bottleneck,
            "لا فعلَ قانونيٌّ الآن عند هذا الاختناق",
            [f"{a['action_id']} يتطلّب {a['requires_supported']}" for a in considered],
        )

    chosen = lawful[0]
    kill = next((k for k in kills if k.get("kill_id") == chosen.kill_id), None)
    return {
        "status": DECISION_AVAILABLE,
        "bottleneck": bottleneck,
        "reason_ar": _bottleneck_reason(bottleneck, snapshot),
        "selection_rule_ar": (
            "قاعدةٌ معجمية: قانونيٌّ الآن ← قابلٌ للتراجع ← يُنتج الدليل الناقص التالي ← "
            "أقلّ وقتاً من المالك (ترتيبٌ لا قياس)"
        ),
        "primary_action": {
            "action_id": chosen.action_id,
            "title_ar": _fill(chosen.title_ar, entity),
            "steps_ar": [_fill(step, entity) for step in chosen.steps_ar],
            "produces": list(chosen.produces),
            "owner_ar": "المالك — لا يُنفَّذ آلياً",
            "entity": entity.get("entity") if entity else None,
            "evidence_ids": _ids(entity.get("evidence_ids")) if entity else [],
        },
        "capsule": {
            "claim_ar": _fill(chosen.hypothesis_ar, entity),
            "mechanism_ar": chosen.mechanism_ar,
            "minimum_falsification_test_ar": _fill(chosen.title_ar, entity),
            "human_owner_ar": "المالك",
            "max_time_ar": chosen.time_cap_ar,
            "max_cost_ar": "0 € مباشرة",
            "risk_ar": chosen.risk_ar,
            "expected_decision_change_ar": chosen.decision_change_ar,
            "success_observation_ar": chosen.success_ar,
            "failure_observation_ar": chosen.failure_ar,
            "kill_condition": kill,
            "expiry_ar": "يسقط بأوّل صفٍّ جديدٍ في السجلّ لهذا الكيان — يُعاد الحساب",
            "status": "HYPOTHESIS",
        },
        "ledger_row_template": _row_template(chosen, entity),
        "candidates_considered": considered,
        "next_missing_link": first_missing.get("link"),
        "tempting_shortcut_ar": _TEMPTING.get(bottleneck, "—"),
        "regenerate_after_commit": _REGENERATE,
    }


def _no_decision(bottleneck: str | None, reason: str, details: list[str]) -> dict[str, object]:
    return {
        "status": NO_LAWFUL_DECISION,
        "bottleneck": bottleneck,
        "reason_ar": reason,
        "details": details,
        "primary_action": None,
        "capsule": None,
        "ledger_row_template": None,
        "candidates_considered": [],
        "tempting_shortcut_ar": "اختراع فعلٍ يملأ الفراغ",
    }


def _bottleneck_reason(bottleneck: str, snapshot: Mapping[str, object]) -> str:
    funnel = _mapping(snapshot.get("funnel"))
    if bottleneck == "channel":
        return (
            f"{funnel.get('entities_contacted')} كياناً اتُّصل به و{funnel.get('entities_replied')} "
            "ردّ: الحلقة 5 تحتاج ملفّاً حقيقياً، والملفّ يحتاج مشترياً يردّ أوّلاً"
        )
    return {
        "data_access": "مشترٍ ردّ ولا عيّنة على ملفٍّ حقيقي بعد",
        "evidence": "عيّنةٌ مُسلَّمة والحلقة 5 غير مُعلَنة",
        "payment": "لا مال بعد، وجاهزية القبض مجهولة أو المال لم يُسوَّ",
        "buyer_trust": "عرضٌ بلا قرار أو عميلٌ لم يعد",
        "delivery_cost": "دفعةٌ مسوّاة والهامش مجهول",
    }.get(bottleneck, "—")


# ── الجمل ────────────────────────────────────────────────────────────────────────


def _s(sentence: str, cls: str, evidence: Sequence[object] = ()) -> dict[str, object]:
    return {"sentence": sentence, "class": cls, "evidence_ids": [str(e) for e in evidence]}


def _ids(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def render_sentences(
    snapshot: Mapping[str, object], brief: Mapping[str, object]
) -> list[dict[str, object]]:
    """شاشة الغرفة الأولى جملاً — كلّ جملةٍ بصنفها ودليلها، بلا نموذجٍ لغوي."""
    ceiling = _mapping(snapshot.get("ceiling"))
    funnel = _mapping(snapshot.get("funnel"))
    missing = _mapping(snapshot.get("first_missing_proof"))
    last = _mapping(snapshot.get("last_event"))
    entities = _maps(snapshot.get("entities"))
    ledger_ids = [eid for e in entities for eid in _ids(e.get("evidence_ids"))]
    out = [
        _s(
            f"الأطروحة النشطة الوحيدة: {ACTIVE_THESIS_ID} ({ACTIVE_THESIS_DECISION}).",
            FACT,
            [ACTIVE_THESIS_DECISION, f"CATALOG:{ACTIVE_THESIS_ID}"],
        ),
        _s(
            f"أقصى ما يحقّ قوله اليوم: {ceiling.get('statement_ar')} — "
            f"{ceiling.get('classification')}، الحلقة {ceiling.get('link')} من 8.",
            FACT,
            _ids(ceiling.get("evidence_ids")),
        ),
        _s(
            f"السجلّ: {funnel.get('contacts_sent')} اتصالاً لـ{funnel.get('entities_contacted')} "
            f"كياناً، {funnel.get('entities_replied')} ردّ، {funnel.get('payments_settled')} "
            f"دفعة مسوّاة؛ GATE_C = {snapshot.get('gate_c')}.",
            FACT,
            [*ledger_ids, SCORECARD_ID],
        ),
    ]
    if missing:
        out.append(
            _s(
                f"أوّل دليلٍ ناقص: الحلقة {missing.get('link')} — {missing.get('title_ar')}. "
                f"{missing.get('reason_ar') or ''}".strip(),
                FACT,
                _ids(missing.get("evidence_ids")),
            )
        )
        out.append(_s(str(missing.get("why_not_code_ar")), FACT, _ids(missing.get("evidence_ids"))))
    if last:
        out.append(
            _s(
                f"آخر حدثٍ موثّق: {last.get('action')} لـ{last.get('entity')} في {last.get('date')} — "
                f"منذ {snapshot.get('days_since_last_event')} يوماً.",
                FACT,
                _ids(last.get("evidence_ids")),
            )
        )
    for kill in _maps(snapshot.get("kill_conditions")):
        if kill.get("kill_id") == "K1":
            out.append(
                _s(
                    f"شرط القتل الأقرب ({kill.get('kill_id')}): «{kill.get('source_quote')}» — "
                    f"{kill.get('status')} ({kill.get('progress')}).",
                    FACT,
                    [ACTIVE_THESIS_DECISION, SCORECARD_ID],
                )
            )
    for claim in _maps(snapshot.get("claims")):
        if claim.get("status") == UNKNOWN:
            out.append(
                _s(
                    f"مجهول: {claim.get('statement_ar')} — لا موطن لتسجيله.",
                    UNKNOWN,
                )
            )
    action = _mapping(brief.get("primary_action"))
    if action:
        out.append(
            _s(
                f"الفعل التالي (بشري): {action.get('title_ar')}.",
                ACTION,
                _ids(action.get("evidence_ids")),
            )
        )
        capsule = _mapping(brief.get("capsule"))
        out.append(_s(f"فرضية: {capsule.get('claim_ar')}.", HYPOTHESIS))
    else:
        out.append(_s(f"لا قرار قانونيٌّ متاح: {brief.get('reason_ar')}.", REFUSAL))
    for claim in _maps(snapshot.get("claims")):
        if (
            claim.get("claim_id") in {"C-L5", "C-RATE", "C-PAID"}
            and claim.get("status") != SUPPORTED
        ):
            out.append(_s(f"لا يُقال للمشتري: {claim.get('statement_ar')}.", REFUSAL))
    out.append(_s(f"الاختصار الأكثر إغراءً الآن: {brief.get('tempting_shortcut_ar')}.", REFUSAL))
    return out


#: عائلات المعنى الحسّاسة: جملة FACT تمسّها تحتاج دليلاً من صنفٍ يسندها. المطابقة على
#: **الكلمة** بعد نزع السوابق (و·ف·ب·ل·ك·ال) — «مالك» ليست «مال» (L4 من D-206).
_SENSITIVE: tuple[tuple[frozenset[str], frozenset[str]], ...] = (
    (
        frozenset(
            {"دفع", "دفعة", "دفعات", "إيراد", "إيرادات", "عميل", "عملاء", "مال", "€"}
            | {"payment", "revenue", "customer", "customers"}
        ),
        frozenset({"ledger", "scorecard"}),
    ),
    (
        frozenset({"قانون", "قانوني", "قانونية", "جاهز", "جاهزة", "مسموح", "ready", "legal"}),
        frozenset({"decision", "catalog"}),
    ),
)
_WORD = re.compile(r"[\w€]+")
_PREFIXES: tuple[str, ...] = ("وال", "بال", "فال", "كال", "لل", "ال", "و", "ف", "ب", "ل", "ك")


def _words(text: str) -> set[str]:
    words: set[str] = set()
    for word in _WORD.findall(text.lower()):
        words.add(word)
        words.update(word[len(prefix) :] for prefix in _PREFIXES if word.startswith(prefix))
    return words


def sentence_problems(
    sentences: Sequence[Mapping[str, object]], evidence: Sequence[Mapping[str, object]]
) -> list[str]:
    """كلّ ما يجعل جملةً تتجاوز دليلها — العقد الذي يحكم أيّ مولِّد لغة (حتميٍّ أو لاحق)."""
    kinds = {str(item.get("id")): str(item.get("kind")) for item in evidence}
    found: list[str] = []
    for index, item in enumerate(sentences):
        text = str(item.get("sentence") or "")
        cls = item.get("class")
        ids = _ids(item.get("evidence_ids"))
        where = f"جملة {index}"
        if cls not in SENTENCE_CLASSES:
            found.append(f"{where}: صنفٌ خارج المجموعة {cls!r}")
            continue
        if cls == FACT and not ids:
            found.append(f"{where}: FACT بلا مُعرِّف دليل — «{text[:60]}»")
        if unknown := [eid for eid in ids if eid not in kinds]:
            found.append(f"{where}: مُعرِّفات دليلٍ غير موجودة {unknown}")
        if cls != REFUSAL and (hits := [t for t in FORBIDDEN_TERMS if t.lower() in text.lower()]):
            found.append(f"{where}: وصفٌ ممنوع {hits}")
        if cls == FACT:
            present = _words(text)
            for family, needed in _SENSITIVE:
                if (hit := sorted(family & present)) and not ({kinds.get(e) for e in ids} & needed):
                    found.append(f"{where}: FACT يمسّ {hit} بلا دليلٍ من {sorted(needed)}")
    return found


# ── الاستجواب ────────────────────────────────────────────────────────────────────


def cross_examine(
    question: str,
    snapshot: Mapping[str, object],
    brief: Mapping[str, object],
    *,
    text: str | None = None,
    classify_text: TextClassifier | None = None,
) -> dict[str, object]:
    """سؤالٌ من مجموعةٍ مغلقة ⇒ جوابٌ بجملٍ مُصنَّفة. ⛔ لا تشجيع ولا سؤالٌ مفتوح."""
    if question not in QUESTIONS:
        raise ValueError(f"سؤالٌ خارج المجموعة المغلقة: {question!r}")
    if question == "ready":
        return {"question": question, "sentences": _ready(snapshot)}
    if question == "build":
        return {"question": question, "sentences": _build(snapshot, brief)}
    if question == "why_no_money":
        return {"question": question, "sentences": _why_no_money(snapshot)}
    if not text or not text.strip():
        raise ValueError("say_to_buyer يتطلّب نصّاً")
    if classify_text is None:
        raise ValueError("say_to_buyer يتطلّب مُصنِّف نصّ المشتري")
    verdict, reason, hits = classify_text(text)
    cls = REFUSAL if verdict in {"FORBIDDEN", "UNSUPPORTED"} else FACT
    sentences = [_s(f"الحكم: {verdict} — {reason}", cls, ["D-304"])]
    sentences.extend(_s(f"قاعدة {rule}: «{excerpt}»", REFUSAL) for rule, excerpt in hits)
    return {
        "question": question,
        "verdict": verdict,
        "findings": [{"rule": rule, "excerpt": excerpt} for rule, excerpt in hits],
        "sentences": sentences,
    }


def _raw_links(snapshot: Mapping[str, object]) -> set[int]:
    ceiling = _int(_mapping(snapshot.get("ceiling")).get("link"))
    funnel = _mapping(snapshot.get("funnel"))
    raw = set(range(1, ceiling + 1))
    if _int(funnel.get("entities_replied")):
        raw.add(7)
    if _int(funnel.get("entities_paid_any")):
        raw.add(8)
    return raw


def _ready(snapshot: Mapping[str, object]) -> list[dict[str, object]]:
    thesis = _mapping(snapshot.get("thesis"))
    ceiling = _mapping(snapshot.get("ceiling"))
    raw = _raw_links(snapshot)
    out = [
        _s(
            "جاهزون لماذا؟ لكلّ حالةٍ في الكتالوج حلقاتٌ يجب أن تُبلَغ:",
            FACT,
            [VALUE_CHAIN_ID, f"CATALOG:{ACTIVE_THESIS_ID}"],
        ),
        _s(
            f"حالة العرض اليوم في الكتالوج: {thesis.get('catalog_status')}.",
            FACT,
            [f"CATALOG:{ACTIVE_THESIS_ID}"],
        ),
    ]
    for status, links in CATALOG_REQUIRES.items():
        missing = [n for n in links if n not in raw]
        verdict = "مبلوغة" if not missing else f"ناقصة: الحلقات {missing}"
        out.append(
            _s(
                f"{status} يتطلّب الحلقات {list(links)} — {verdict}.",
                FACT,
                [f"CATALOG:{ACTIVE_THESIS_ID}", SCORECARD_ID],
            )
        )
    out.append(
        _s(
            f"المسموح قوله الآن: {ceiling.get('statement_ar')}.",
            FACT,
            [*_ids(ceiling.get("evidence_ids")), f"CATALOG:{ACTIVE_THESIS_ID}"],
        )
    )
    out.extend(
        _s(f"غير المسموح الآن: {claim.get('statement_ar')}.", REFUSAL)
        for claim in _maps(snapshot.get("claims"))
        if claim.get("status") == NOT_SUPPORTED
    )
    return out


def _build(snapshot: Mapping[str, object], brief: Mapping[str, object]) -> list[dict[str, object]]:
    paths = _maps(_mapping(snapshot.get("thesis")).get("paths"))
    code_paths = [p for p in paths if p.get("next_actor") == "code"]
    missing = _mapping(snapshot.get("first_missing_proof"))
    action = _mapping(brief.get("primary_action"))
    if code_paths:
        out = [
            _s(
                f"نعم، الكود هو الاختناق في {[p.get('id') for p in code_paths]}: الحلقة التالية برمجية.",
                FACT,
                [VALUE_CHAIN_ID],
            )
        ]
    else:
        out = [
            _s(
                "لا. الكود ليس الاختناق: الحلقة التالية لكلّ مسارات الأطروحة مالكها إنسان.",
                FACT,
                _ids(missing.get("evidence_ids")) or [VALUE_CHAIN_ID],
            ),
            _s(
                "بناءُ كودٍ الآن لا يُنتج الدليل الناقص — يُنتج قدرةً إضافية فوق فجوةٍ بشرية.",
                REFUSAL,
            ),
        ]
    if action:
        out.append(_s(f"أصغر تجربةٍ بلا كود: {action.get('title_ar')}.", ACTION))
    return out


def _why_no_money(snapshot: Mapping[str, object]) -> list[dict[str, object]]:
    funnel = _mapping(snapshot.get("funnel"))
    ceiling = _int(_mapping(snapshot.get("ceiling")).get("link"))
    rail = _claim_status(snapshot, "C-RAIL")
    legal = _claim_status(snapshot, "C-LEGAL")
    stages: list[tuple[str, bool | None]] = [
        ("اتصالٌ مسجّل", _int(funnel.get("entities_contacted")) > 0),
        ("ردٌّ من مشترٍ (الحلقة 7)", _int(funnel.get("entities_replied")) > 0),
        ("عيّنةٌ على ملفٍّ حقيقي", _int(funnel.get("samples_delivered")) > 0),
        ("نتيجةٌ على نظامٍ مستقلّ (الحلقة 5)", ceiling >= 5),
        ("جاهزية القبض (البنك/Malt)", None if rail == UNKNOWN else rail == SUPPORTED),
        ("التسجيل القانوني (ANAE)", None if legal == UNKNOWN else legal == SUPPORTED),
        ("عرض سعر", _int(funnel.get("entities_quoted")) > 0),
        ("مالٌ تحرّك", _int(funnel.get("entities_paid_any")) > 0),
    ]
    out: list[dict[str, object]] = []
    first_break: str | None = None
    for name, reached in stages:
        if reached is None:
            out.append(_s(f"{name}: مجهول — لا سجلّ.", UNKNOWN))
            continue
        out.append(
            _s(f"{name}: {'نعم' if reached else 'لا'}.", FACT, [SCORECARD_ID, VALUE_CHAIN_ID])
        )
        if not reached and first_break is None:
            first_break = name
    if first_break:
        out.append(
            _s(f"السلسلة تنقطع أوّلاً عند: {first_break}.", FACT, [SCORECARD_ID, VALUE_CHAIN_ID])
        )
    return out


# ── معاينة النتيجة (بلا كتابة) ───────────────────────────────────────────────────


def _csv_line(row: Mapping[str, str]) -> str:
    buffer = io.StringIO()
    csv.writer(buffer, lineterminator="\n").writerow([row.get(column, "") for column in COLUMNS])
    return buffer.getvalue()


def preview_outcome(
    *,
    row: Mapping[str, str],
    chain_doc: Mapping[str, object],
    ledger_text: str,
    catalog: Mapping[str, object],
    scorecard: Mapping[str, object],
    root: Path,
    today: date,
    wording: WordingLinter | None = None,
) -> dict[str, object]:
    """صفٌّ مقترَح ⇒ مقبولٌ أو مرفوضٌ بأسبابه، والسطر، وما يتغيّر. ⛔ لا يُكتب شيء."""
    line = _csv_line(row)
    base = ledger_text if ledger_text.endswith("\n") else ledger_text + "\n"
    candidate = base + line
    line_no = len(base.splitlines()) + 1
    found = row_problems({column: row.get(column, "") for column in COLUMNS}, line_no, today)
    if not found:
        try:
            parse_ledger(candidate, today=today)
        except LedgerError as exc:
            found = [p for p in str(exc).splitlines() if p.strip()]
    paths = _maps(chain_doc.get("paths"))
    if route_of(row.get("target_ref", "")) not in route_table(paths):
        found.append(
            f"`{route_of(row.get('target_ref', ''))}` غير موجَّه إلى أيّ مسار — "
            f"البوّابة تحمرّ على صفٍّ غير موجَّه ({VALUE_CHAIN_REL})"
        )
    result: dict[str, object] = {
        "accepted": not found,
        "problems": found,
        "csv_line": line,
        "written": False,
        "ledger": LEDGER_REL,
        "commit_hint_ar": (
            f"أضف السطر إلى {LEDGER_REL} ثمّ شغّل {_REGENERATE} والتزم — "
            "الالتزام هو التدقيق، والمركز لا يكتب"
        ),
    }
    if found:
        return result
    before, after = (
        build_snapshot(
            chain_doc=chain_doc,
            ledger_text=text,
            catalog=catalog,
            scorecard=scorecard,
            root=root,
            today=today,
            wording=wording,
        )
        for text in (ledger_text, candidate)
    )
    result["delta"] = {
        "ceiling": [
            _mapping(before["ceiling"]).get("link"),
            _mapping(after["ceiling"]).get("link"),
        ],
        "funnel": [before["funnel"], after["funnel"]],
        "primary_action": [
            _mapping(build_brief(before).get("primary_action")).get("action_id"),
            _mapping(build_brief(after).get("primary_action")).get("action_id"),
        ],
        "kill_conditions": [
            [k.get("status") for k in _maps(before["kill_conditions"])],
            [k.get("status") for k in _maps(after["kill_conditions"])],
        ],
        "scorecard_note_ar": f"{SCORECARD_REL} يُعاد توليده بعد الالتزام — المعاينة لا تلمسه",
    }
    return result
