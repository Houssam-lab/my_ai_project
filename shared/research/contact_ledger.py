"""سجلّ الاتصال الخارجي — الموطن الواحد لحقيقة «كتبنا للسوق» (D-297).

**لماذا هذه الوحدة موجودة.** بين 2026-08-16 و2026-09-28 سمّى المستودع 17 «فرصةً أولى»
مختلفة وأنتج 12 ملحقَ حالةٍ و6 جولات قرار — وسجّل **رسالةً واحدة** مُرسَلة إلى مشترٍ
(Balagué Expertise · 2026-09-22 · بلا ردّ ولا متابعة). البحثُ لم يكن الاختناق؛ الكتابةُ
للسوق كانت. وهذا الملفّ يجعل تلك الكتابة **قابلةً للعدّ**: كلّ فعلٍ خارجيّ صفٌّ واحد،
مُلحَقٌ فقط، بمجموعة أفعالٍ مغلقة — فلا يُقرأ «مُرسَل» على ملفٍّ لم يُرسَل (نمط
`dispatched_2026/` الذي كان مجلّدَ قوالبٍ مُولَّدة).

**العقد.**
- الملفّ الحقيقي هو ``CONTACT_LEDGER.csv`` تحت ``docs/commercial/outreach/`` (``LEDGER_REL``)؛
  جداولُ الأهداف تحمل بياناتَ الهدف الساكنة فقط — حالةُ الاتصال تعيش هنا وحدها (D-192:
  لا مصدرَين لحقيقةٍ واحدة).
- ``ACTIONS`` مجموعةٌ مغلقة؛ فعلٌ خارجها انتهاكٌ لا تحذير (D-206 L11: الغياب يُعلَن).
- المبلغ إلزاميٌّ لأفعال المال وعرض السعر، **وممنوعٌ** على غيرها — رقمٌ على رسالةٍ يُقرأ إيراداً.
- التاريخ ISO ولا يسبق الكتابةَ إلى المستقبل (صفٌّ بتاريخٍ لاحق «تخطيطٌ» لا حدث).
- كلّ مقياسٍ مُشتقّ (``derive_scorecard``) يحمل ``basis``: قيمةٌ غائبة ``None`` بسببٍ منطوق،
  لا صفرٌ يُقرأ «فقدناهم» (D-212).

⛔ صفر تبعياتٍ خارج المكتبة القياسية؛ ولا استيرادَ من ``app`` (قاعدة ``shared/``).
"""

from __future__ import annotations

import csv
import hashlib
import io
from collections import defaultdict
from dataclasses import dataclass
from datetime import date

__all__ = [
    "ACTIONS",
    "AMOUNT_REQUIRED",
    "CHANNELS",
    "CLOSURE",
    "COLUMNS",
    "CONTACT_ACTIONS",
    "DELIVERY",
    "INBOUND",
    "LEDGER_REL",
    "MONEY",
    "OUTBOUND",
    "SCORECARD_REL",
    "LedgerError",
    "LedgerRow",
    "build_scorecard",
    "derive_scorecard",
    "ledger_sha256",
    "parse_ledger",
    "row_problems",
]

LEDGER_REL = "docs/commercial/outreach/CONTACT_LEDGER.csv"
SCORECARD_REL = "docs/commercial/HARD_CURRENCY_SCORECARD.json"

COLUMNS: tuple[str, ...] = (
    "date",
    "target_ref",
    "entity",
    "country",
    "channel",
    "action",
    "amount_eur",
    "evidence_ref",
    "note",
)

#: أفعالٌ نُصدِرها نحن نحو مشترٍ محدَّد.
OUTBOUND = frozenset({"EMAIL_SENT", "CALL_MADE", "LINKEDIN_SENT", "FORM_SUBMITTED"})
#: ردٌّ من الطرف الآخر — أوّل رقمٍ حقيقيّ لأيّ قناة (H12).
INBOUND = frozenset({"REPLY_RECEIVED"})
#: تسليمٌ نحن مصدره: عيّنةٌ مجّانية أو عرضُ سعر.
DELIVERY = frozenset({"SAMPLE_DELIVERED", "QUOTE_SENT"})
#: مالٌ تحرّك فعلاً — الوحيد الذي يحرّك `GATE_C`.
MONEY = frozenset({"DEPOSIT_RECEIVED", "PAYMENT_SETTLED"})
#: إغلاقٌ صريح — يُعدّ لكنّه ليس اتصالاً.
CLOSURE = frozenset({"CLOSED_NO_REPLY", "CLOSED_DECLINED"})

ACTIONS = OUTBOUND | INBOUND | DELIVERY | MONEY | CLOSURE
#: ما تعدّه بوّابة تجميد البحث «كتابةً للسوق»: كلّ شيءٍ عدا الإغلاق.
CONTACT_ACTIONS = ACTIONS - CLOSURE
#: المبلغ إلزاميٌّ هنا وممنوعٌ في غيره.
AMOUNT_REQUIRED = MONEY | {"QUOTE_SENT"}

CHANNELS = frozenset(
    {"email", "phone", "linkedin", "web_form", "malt", "platform", "bank", "in_person"}
)

_MAX_REASONABLE_AMOUNT_EUR = 1_000_000.0


class LedgerError(ValueError):
    """سجلٌّ لا يُقرأ لا يُشهَد له — الرسالة تحمل كلّ المشاكل لا أوّلها."""


@dataclass(frozen=True)
class LedgerRow:
    line_no: int
    date: date
    target_ref: str
    entity: str
    country: str
    channel: str
    action: str
    amount_eur: float | None
    evidence_ref: str
    note: str


def _parse_date(raw: str) -> date | None:
    try:
        return date.fromisoformat(raw.strip())
    except ValueError:
        return None


def _parse_amount(raw: str) -> tuple[float | None, str | None]:
    text = (raw or "").strip()
    if not text:
        return None, None
    try:
        value = float(text)
    except ValueError:
        return None, f"amount_eur غير رقمي: {text!r}"
    if value <= 0:
        return None, f"amount_eur يجب أن يكون > 0 (وجد {value})"
    if value > _MAX_REASONABLE_AMOUNT_EUR:
        return None, f"amount_eur خارج المعقول ({value}) — رقمٌ كهذا يحتاج عقداً لا صفّاً"
    return value, None


def row_problems(raw: dict[str, str], line_no: int, today: date) -> list[str]:
    """كلّ ما يمنع قبول الصفّ — قائمةٌ كاملة لا أوّل خطأ."""
    problems: list[str] = []
    prefix = f"سطر {line_no}"

    missing = [column for column in COLUMNS if column not in raw]
    if missing:
        return [f"{prefix}: أعمدةٌ مفقودة {missing}"]

    when = _parse_date(raw["date"] or "")
    if when is None:
        problems.append(f"{prefix}: التاريخ ليس ISO (YYYY-MM-DD): {raw['date']!r}")
    elif when > today:
        problems.append(
            f"{prefix}: تاريخٌ في المستقبل ({when.isoformat()} > {today.isoformat()}) — تخطيطٌ لا حدث"
        )

    action = (raw["action"] or "").strip()
    if action not in ACTIONS:
        problems.append(
            f"{prefix}: فعلٌ خارج المجموعة المغلقة: {action!r} (المسموح: {sorted(ACTIONS)})"
        )

    channel = (raw["channel"] or "").strip()
    if channel not in CHANNELS:
        problems.append(
            f"{prefix}: قناةٌ خارج المجموعة المغلقة: {channel!r} (المسموح: {sorted(CHANNELS)})"
        )

    for column in ("target_ref", "entity", "country"):
        if not (raw[column] or "").strip():
            problems.append(f"{prefix}: `{column}` فارغ — اتصالٌ بلا طرفٍ مسمّى ليس اتصالاً")

    country = (raw["country"] or "").strip()
    if country and not (len(country) == 2 and country.isalpha() and country.isupper()):
        problems.append(
            f"{prefix}: `country` يجب أن يكون رمز ISO-3166 من حرفَين كبيرَين: {country!r}"
        )

    amount, amount_problem = _parse_amount(raw["amount_eur"] or "")
    if amount_problem:
        problems.append(f"{prefix}: {amount_problem}")
    if action in AMOUNT_REQUIRED and amount is None and not amount_problem:
        problems.append(f"{prefix}: الفعل {action} يتطلّب `amount_eur` — مالٌ بلا رقمٍ ليس مالاً")
    if action in ACTIONS and action not in AMOUNT_REQUIRED and amount is not None:
        problems.append(f"{prefix}: الفعل {action} لا يحمل مبلغاً — رقمٌ على رسالةٍ يُقرأ إيراداً")

    if action in MONEY and not (raw["evidence_ref"] or "").strip():
        problems.append(f"{prefix}: الفعل {action} يتطلّب `evidence_ref` (كشفٌ بنكي · إيصال منصّة)")

    return problems


def parse_ledger(text: str, *, today: date) -> list[LedgerRow]:
    """يقرأ السجلّ كاملاً أو يرفع ``LedgerError`` بكلّ المشاكل مجتمعة."""
    reader = csv.DictReader(io.StringIO(text))
    header = tuple(reader.fieldnames or ())
    if header != COLUMNS:
        raise LedgerError(f"رأس السجلّ يجب أن يكون {list(COLUMNS)} بالترتيب؛ وجد {list(header)}")

    rows: list[LedgerRow] = []
    problems: list[str] = []
    for line_no, raw in enumerate(reader, start=2):
        if not any((value or "").strip() for value in raw.values()):
            continue
        row_issues = row_problems(raw, line_no, today)
        if row_issues:
            problems.extend(row_issues)
            continue
        amount, _ = _parse_amount(raw["amount_eur"] or "")
        rows.append(
            LedgerRow(
                line_no=line_no,
                date=_parse_date(raw["date"]) or today,
                target_ref=raw["target_ref"].strip(),
                entity=raw["entity"].strip(),
                country=raw["country"].strip(),
                channel=raw["channel"].strip(),
                action=raw["action"].strip(),
                amount_eur=amount,
                evidence_ref=(raw["evidence_ref"] or "").strip(),
                note=(raw["note"] or "").strip(),
            )
        )
    if problems:
        raise LedgerError("\n".join(problems))
    return rows


def ledger_sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_scorecard(text: str, *, today: date) -> dict[str, object]:
    """السجلّ نصّاً ⇒ اللوحة كاملةً — المدخل الواحد للسكربت والبوّابة معاً (D-192)."""
    return derive_scorecard(parse_ledger(text, today=today), source_sha256=ledger_sha256(text))


def _metric(value: float | int | None, basis: str) -> dict[str, object]:
    return {"value": value, "basis": basis}


def _ratio(numerator: int, denominator: int, what: str) -> dict[str, object]:
    if denominator == 0:
        return _metric(None, f"{what}: المقام صفر — لا نسبة بلا مقام (D-212)")
    return _metric(round(numerator / denominator, 4), f"{what}: {numerator}/{denominator}")


def derive_scorecard(rows: list[LedgerRow], *, source_sha256: str) -> dict[str, object]:
    """لوحة العملة الصعبة (التوجيه §35) — **مُشتقّةٌ** من السجلّ، لا تُكتب بيدٍ أبداً."""
    by_action: dict[str, list[LedgerRow]] = defaultdict(list)
    for row in rows:
        by_action[row.action].append(row)

    def entities(actions: frozenset[str] | set[str]) -> set[str]:
        return {row.entity for row in rows if row.action in actions}

    contacted = entities(OUTBOUND)
    replied = entities(INBOUND)
    sampled = entities({"SAMPLE_DELIVERED"})
    quoted = entities({"QUOTE_SENT"})
    paid_rows = by_action.get("PAYMENT_SETTLED", [])
    paid_entities = {row.entity for row in paid_rows}
    foreign_paid = {row.entity for row in paid_rows if row.country != "DZ"}
    settled = round(sum(row.amount_eur or 0.0 for row in paid_rows), 2)

    payments_per_entity: dict[str, list[LedgerRow]] = defaultdict(list)
    for row in paid_rows:
        payments_per_entity[row.entity].append(row)
    repeat_entities = {name for name, items in payments_per_entity.items() if len(items) >= 2}
    recurring = round(
        sum(
            item.amount_eur or 0.0
            for items in payments_per_entity.values()
            for item in sorted(items, key=lambda r: r.date)[1:]
        ),
        2,
    )

    first_contact = min((row.date for row in rows if row.action in OUTBOUND), default=None)
    first_sample = min((row.date for row in by_action.get("SAMPLE_DELIVERED", [])), default=None)
    first_payment = min((row.date for row in paid_rows), default=None)

    def days_between(start: date | None, end: date | None, what: str) -> dict[str, object]:
        if start is None or end is None:
            return _metric(None, f"{what}: لم يحدث بعد")
        return _metric((end - start).days, f"{what}: {start.isoformat()} → {end.isoformat()}")

    as_of = max((row.date for row in rows), default=None)

    funnel = {
        "contacts_sent": len([row for row in rows if row.action in OUTBOUND]),
        "entities_contacted": len(contacted),
        "replies_received": len(by_action.get("REPLY_RECEIVED", [])),
        "samples_delivered": len(by_action.get("SAMPLE_DELIVERED", [])),
        "quotes_sent": len(by_action.get("QUOTE_SENT", [])),
        "deposits_received": len(by_action.get("DEPOSIT_RECEIVED", [])),
        "payments_settled": len(paid_rows),
        "closed_no_reply": len(by_action.get("CLOSED_NO_REPLY", [])),
        "closed_declined": len(by_action.get("CLOSED_DECLINED", [])),
    }

    scorecard = {
        "foreign_customers": _metric(
            len(foreign_paid), "كياناتٌ خارج DZ لها PAYMENT_SETTLED واحد على الأقل"
        ),
        "paid_customers": _metric(len(paid_entities), "كياناتٌ لها PAYMENT_SETTLED"),
        "settled_revenue_eur": _metric(settled, "مجموع amount_eur لأفعال PAYMENT_SETTLED"),
        "recurring_revenue_eur": _metric(
            recurring if repeat_entities else None,
            "مجموع الدفعات الثانية فما بعد لكلّ كيان"
            if repeat_entities
            else "لا كيانٌ دفع مرّتين — لا إيرادَ متكرّر يُعلَن",
        ),
        "average_revenue_per_customer_eur": _metric(
            round(settled / len(paid_entities), 2) if paid_entities else None,
            "settled_revenue_eur / paid_customers" if paid_entities else "صفر عملاء دافعين",
        ),
        "gross_margin": _metric(None, "لا سجلَّ كلفةٍ على القرص — لا هامش يُحسب"),
        "customer_retention": _metric(None, "يتطلّب فترتَي فوترةٍ لكيانٍ واحد على الأقل"),
        "repeat_purchase_customers": _metric(
            len(repeat_entities), "كياناتٌ لها ≥ 2 PAYMENT_SETTLED"
        ),
        "time_to_first_value_days": days_between(
            first_contact, first_sample, "أوّل اتصال → أوّل عيّنة"
        ),
        "time_to_first_payment_days": days_between(
            first_contact, first_payment, "أوّل اتصال → أوّل دفعة"
        ),
        "sales_cycle_days": _metric(None, "يتطلّب دفعةً واحدة على الأقل")
        if not paid_rows
        else _metric(
            round(
                sum(
                    (
                        min(item.date for item in items)
                        - min(
                            (
                                row.date
                                for row in rows
                                if row.entity == name and row.action in OUTBOUND
                            ),
                            default=min(item.date for item in items),
                        )
                    ).days
                    for name, items in payments_per_entity.items()
                )
                / len(payments_per_entity),
                1,
            ),
            "متوسّط (أوّل اتصال بالكيان → أوّل دفعةٍ منه)",
        ),
        "delivery_cost_eur": _metric(None, "لا سجلَّ ساعاتٍ على القرص — يُقاس على أوّل مهمّة"),
        "ai_cost_per_customer_eur": _metric(
            0.0, "أدواتُ التسليم حتمية stdlib — لا نداءَ نموذجٍ لغوي في مسار التسليم"
        ),
        "support_cost_eur": _metric(None, "لا عميلٌ يُدعَم بعد"),
        "refund_rate": _ratio(0, len(paid_rows), "استرجاعات / دفعات"),
    }

    conversion = {
        "reply_rate": _ratio(len(replied), len(contacted), "كياناتٌ ردّت / كياناتٌ اتُّصل بها"),
        "sample_rate": _ratio(len(sampled), len(contacted), "كياناتٌ تسلّمت عيّنة / اتُّصل بها"),
        "quote_rate": _ratio(len(quoted), len(sampled), "كياناتٌ تلقّت عرضاً / تسلّمت عيّنة"),
        "payment_rate": _ratio(len(paid_entities), len(quoted), "كياناتٌ دفعت / تلقّت عرضاً"),
    }

    return {
        "$schema_version": 1,
        "decision": "D-297",
        "purpose_ar": (
            "لوحة العملة الصعبة (التوجيه §35): كلّ رقمٍ مُشتقٌّ من سجلّ الاتصال الخارجي، "
            "والغائبُ null بسببٍ لا صفرٌ يُقرأ خسارة."
        ),
        "source": LEDGER_REL,
        "source_sha256": source_sha256,
        "as_of": as_of.isoformat() if as_of else None,
        "rows": len(rows),
        "funnel": funnel,
        "conversion": conversion,
        "hard_currency_scorecard": scorecard,
        "gate_c": "ABSENT" if not paid_rows else "EVIDENCE_RECORDED_PENDING_HUMAN_REVIEW",
    }
