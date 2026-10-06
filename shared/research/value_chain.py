"""سلسلة القيمة — من الحادثة إلى الدفعة، والتصنيف يُشتقّ ولا يُكتب (D-305).

**لماذا هذه الوحدة موجودة.** للمستودع 19 مساراً للعملة الصعبة في
``REVENUE_OPPORTUNITY_MAP_2026-09-29.csv`` وستّة عروضٍ خارج الكتالوج، ولكلٍّ قرارٌ مكتوب —
ولا شيء يربط أيّاً منها بدليل. فكان كلّ مسارٍ يُوصَف بما يتمنّاه كاتبه: «قدرة» و«عرض» و«منتج»
بلا فرقٍ يُقاس. قاعدة المالك (2026-10-01): كلّ مخرَجٍ يُختبَر على سلسلةٍ واحدة من ثماني حلقات،
وما يتوقّف عند المراحل الداخلية يُصنَّف **أصلاً بحثياً** أو **قدرةً هندسية** — لا منتجاً
ثورياً ولا دليلاً على العملة الصعبة.

**العقد.**

- الحلقات الثماني تُعرَّف هنا **وحدها** (``LINKS``) — لا نسخة في JSON ولا في الواجهة (D-192).
- الحلقات 1–6 تُعلَن في ``VALUE_CHAIN.json`` بدليلٍ (مساراتٌ يجب أن توجد) أو بسببٍ منطوق.
- الحلقتان 7–8 **لا تُعلَنان أبداً**: تُشتقّان من ``CONTACT_LEDGER.csv`` وحده — ردٌّ مُسجَّل
  أو مالٌ تحرّك. اهتمامٌ يُكتب بيدٍ هو بالضبط ما يُقرأ إيراداً بعد أسبوعين.
- **الاتّصال:** أعلى حلقةٍ مُحتسَبة هي آخر حلقةٍ قبل أوّل فجوة. ما فوق الفجوة يُسجَّل ولا
  يرفع التصنيف — اهتمامٌ خارجيٌّ بلا نتيجةٍ على نظامٍ مستقلّ اهتمامٌ لا دليل.
- **لا سُلَّم ثانٍ:** السلسلة طبقةُ أدلّةٍ **تحت** ``readiness_states`` في الكتالوج. لا تُسمّي
  حالة نضج؛ تمنع فقط أن تتجاوز حالةُ الكتالوج ما تسنده الأدلّة.

⛔ صفر تبعياتٍ خارج المكتبة القياسية؛ ولا استيرادَ من ``app`` (قاعدة ``shared/``).
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from shared.research.contact_ledger import INBOUND, MONEY, OUTBOUND, PAYMENT_SETTLED, LedgerRow

__all__ = [
    "CATALOG_REL",
    "CATALOG_REQUIRES",
    "CLASSIFICATIONS",
    "FORBIDDEN_TERMS",
    "LINKS",
    "MAP_REL",
    "NOT_REACHED",
    "REACHED",
    "VALUE_CHAIN_REL",
    "Link",
    "ValueChainError",
    "classify",
    "compute_derived",
    "load_json",
    "map_decisions",
    "problems",
    "route_of",
    "route_table",
]

VALUE_CHAIN_REL = "docs/commercial/VALUE_CHAIN.json"
CATALOG_REL = "docs/commercial/OFFER_CATALOG.json"
MAP_REL = "docs/commercial/REVENUE_OPPORTUNITY_MAP_2026-09-29.csv"

REACHED = "REACHED"
NOT_REACHED = "NOT_REACHED"
_STATUSES = frozenset({REACHED, NOT_REACHED})


class ValueChainError(ValueError):
    """مدخلٌ لا يُقرأ لا يُشهَد له — الرسالة تحمل السبب لا رمزاً."""


@dataclass(frozen=True)
class Link:
    number: int
    key: str
    title_ar: str
    actor: str
    source: str


#: المصدر الوحيد لتعريف الحلقات. ``actor``: من يملك سدّ الحلقة حين تكون التالية الناقصة.
#: الحلقة 5 بشرية لأنّ ما يسدّها بياناتٌ أو نظامٌ لم نكتبه — والكود لا يخترعه.
LINKS: tuple[Link, ...] = (
    Link(1, "observation", "حادثةٌ أو ملاحظةٌ مؤرَّخة بمصدر", "human", "declared"),
    Link(2, "pattern", "نمطٌ قابلٌ للتعميم بلا تفاصيل حالةٍ بعينها", "human", "declared"),
    Link(
        3, "privacy_preserving_probe", "مسبارٌ أو عيّنةٌ بلا بيانات عميلٍ أو مستخدم", "code", "declared"
    ),
    Link(4, "reliable_test", "اختبارٌ حتميٌّ قابلٌ لإعادة الإنتاج", "code", "declared"),
    Link(5, "independent_result", "نتيجةٌ مفيدة على نظامٍ أو بياناتٍ لم نكتبها", "human", "declared"),
    Link(6, "buyer_decision", "قرارٌ واضحٌ للمشتري مربوطٌ بنتيجة الحلقة 5", "human", "declared"),
    Link(7, "external_interest", "اهتمامٌ خارجيٌّ مُسجَّل (ردٌّ في السجلّ)", "human", "ledger"),
    Link(8, "paid_commitment", "تجربةٌ مدفوعة أو التزامٌ تجاري (مالٌ في السجلّ)", "human", "ledger"),
)
_BY_NUMBER: dict[int, Link] = {link.number: link for link in LINKS}
_DECLARED: tuple[int, ...] = tuple(link.number for link in LINKS if link.source == "declared")
_LEDGER: tuple[int, ...] = tuple(link.number for link in LINKS if link.source == "ledger")

#: الترتيب مهمّ: كلّ تصنيفٍ أعلى يتطلّب كلّ ما تحته.
CLASSIFICATIONS: tuple[str, ...] = (
    "unevidenced_hypothesis",
    "research_asset",
    "engineering_capability",
    "validated_capability",
    "commercial_evidence",
)

#: حالةُ الكتالوج ⇐ الحلقات الخامّ التي يجب أن تُبلَغ (بلا شرط الاتّصال: السُّلَّم يقيس ما
#: يقيسه، والسلسلة تمنعه فقط من تجاوز الدليل).
CATALOG_REQUIRES: dict[str, tuple[int, ...]] = {
    "DISCOVERY": (7,),
    "OFFER_READY": (6, 7),
    "PILOT": (8,),
    "PAID_PROOF": (8,),
    "REPEATABLE": (8,),
}
_PAYMENT_STATUSES = frozenset({"PAID_PROOF", "REPEATABLE"})

#: وصفٌ ممنوع ما دام المسار دون ``commercial_evidence`` (قاعدة المالك 2026-10-01 · D-227).
#: سطرٌ يحمل ⛔ مُستثنى: القانون يجب أن يستطيع تسمية ما يحظره (D-208 §7).
FORBIDDEN_TERMS: tuple[str, ...] = (
    "ثوري",
    "ثورية",
    "revolutionary",
    "révolutionnaire",
    "guaranteed",
    "garanti",
    "مضمون",
)


def classify(reached: int) -> str:
    """عدد الحلقات المتّصلة ⇒ التصنيف. ⛔ لا يُكتب التصنيف بيدٍ في أيّ مكان."""
    if not 0 <= reached <= len(LINKS):
        raise ValueChainError(f"عدد حلقاتٍ خارج المجال: {reached}")
    if reached == 0:
        return "unevidenced_hypothesis"
    if reached <= 3:
        return "research_asset"
    if reached == 4:
        return "engineering_capability"
    if reached <= 6:
        return "validated_capability"
    return "commercial_evidence"


def route_of(target_ref: str) -> str:
    """مفتاح التوجيه: ملفّ الأهداف قبل ``#`` — ``FR_…csv#id=7`` ⇒ ``FR_…csv``."""
    return target_ref.split("#", 1)[0].strip()


def _mapping(value: object) -> Mapping[str, object]:
    """تضييق قيمة JSON إلى كائن — وغير الكائن يُقرأ فارغاً لا يُفترَض شكله."""
    return value if isinstance(value, Mapping) else {}


def _items(value: object) -> list[object]:
    return list(value) if isinstance(value, (list, tuple)) else []


def _paths(doc: Mapping[str, object]) -> list[Mapping[str, object]]:
    return [entry for entry in _items(doc.get("paths")) if isinstance(entry, Mapping)]


def route_table(paths: Sequence[Mapping[str, object]]) -> dict[str, list[str]]:
    """مفتاح التوجيه ⇒ المسارات التي تملكه — صفّ سجلٍّ يُحتسَب لمسارٍ واحدٍ فقط."""
    table: dict[str, list[str]] = {}
    for entry in paths:
        for route in _items(entry.get("ledger_routes")):
            table.setdefault(str(route), []).append(str(entry.get("id")))
    return table


def _rows_by_path(
    paths: Sequence[Mapping[str, object]], ledger_rows: Iterable[LedgerRow]
) -> dict[str, list[LedgerRow]]:
    table = route_table(paths)
    grouped: dict[str, list[LedgerRow]] = {str(entry.get("id")): [] for entry in paths}
    for row in ledger_rows:
        owners = table.get(route_of(row.target_ref), [])
        if len(owners) == 1:
            grouped[owners[0]].append(row)
    return grouped


def _raw_links(entry: Mapping[str, object], rows: Sequence[LedgerRow]) -> dict[int, bool]:
    declared = _mapping(entry.get("links"))
    raw = {
        number: _mapping(declared.get(str(number))).get("status") == REACHED for number in _DECLARED
    }
    actions = {row.action for row in rows}
    raw[7] = bool(actions & INBOUND)
    raw[8] = bool(actions & MONEY)
    return raw


def _contiguous(raw: Mapping[int, bool]) -> int:
    reached = 0
    for link in LINKS:
        if not raw.get(link.number):
            break
        reached = link.number
    return reached


def _derive_path(entry: Mapping[str, object], rows: Sequence[LedgerRow]) -> dict[str, object]:
    raw = _raw_links(entry, rows)
    reached = _contiguous(raw)
    next_link = _BY_NUMBER.get(reached + 1)
    return {
        "id": entry.get("id"),
        "reached": reached,
        "classification": classify(reached),
        "next_link": next_link.number if next_link else None,
        "next_link_title_ar": next_link.title_ar if next_link else None,
        "next_actor": next_link.actor if next_link else None,
        "raw_links": [number for number in sorted(raw) if raw[number]],
        "ledger": {
            "outbound": sum(1 for row in rows if row.action in OUTBOUND),
            "replies": sum(1 for row in rows if row.action in INBOUND),
            "money_events": sum(1 for row in rows if row.action in MONEY),
            "payments_settled": sum(1 for row in rows if row.action == PAYMENT_SETTLED),
        },
    }


def compute_derived(
    doc: Mapping[str, object], ledger_rows: Sequence[LedgerRow]
) -> dict[str, object]:
    """الكتلة ``derived`` كاملةً — لا تعتمد على الساعة ولا على وجود الملفّات (حتمية)."""
    paths = _paths(doc)
    grouped = _rows_by_path(paths, ledger_rows)
    derived_paths = [_derive_path(entry, grouped[str(entry.get("id"))]) for entry in paths]
    counts = dict.fromkeys(CLASSIFICATIONS, 0)
    for item in derived_paths:
        counts[str(item["classification"])] += 1
    as_of = max((row.date for row in ledger_rows), default=None)
    return {
        "as_of": as_of.isoformat() if as_of else None,
        "as_of_basis": "آخر تاريخٍ في CONTACT_LEDGER.csv — لا ساعة النظام",
        "paths_total": len(derived_paths),
        "by_classification": counts,
        "next_actor_human": sum(1 for item in derived_paths if item["next_actor"] == "human"),
        "next_actor_code": sum(1 for item in derived_paths if item["next_actor"] == "code"),
        "paths": derived_paths,
    }


# ── التحقّق ─────────────────────────────────────────────────────────────────────


def _strings(value: object) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, Mapping):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def _missing(root: Path, rel: object) -> bool:
    return not isinstance(rel, str) or not rel.strip() or not (root / rel).exists()


def _link_problems(pid: str, entry: Mapping[str, object], root: Path) -> list[str]:
    found: list[str] = []
    links = entry.get("links")
    if not isinstance(links, Mapping):
        return [f"{pid}: `links` مفقود — مسارٌ بلا حلقاتٍ مُعلَنة لا يُصنَّف"]
    extra = sorted(set(links) - {str(number) for number in _DECLARED})
    if manual := [key for key in extra if key in {str(number) for number in _LEDGER}]:
        found.append(f"{pid}: الحلقات {manual} مُعلَنة يدوياً — تُشتقّ من CONTACT_LEDGER.csv وحده")
    if unknown := [key for key in extra if key not in {str(number) for number in _LEDGER}]:
        found.append(f"{pid}: مفاتيح حلقاتٍ غير معروفة {unknown}")
    for number in _DECLARED:
        link = links.get(str(number))
        if not isinstance(link, Mapping):
            found.append(f"{pid}: الحلقة {number} غير مُعلَنة — الخانة الفارغة تُقرأ نجاحاً")
            continue
        status = link.get("status")
        if status not in _STATUSES:
            found.append(f"{pid}: الحلقة {number} بحالةٍ خارج المجموعة: {status!r}")
            continue
        if status == REACHED:
            evidence = _items(link.get("evidence"))
            if not evidence:
                found.append(f"{pid}: الحلقة {number} REACHED بلا دليل")
            for rel in evidence:
                if _missing(root, rel):
                    found.append(f"{pid}: الحلقة {number} تستشهد بمسارٍ غير موجود: {rel!r}")
            if number == 3 and link.get("contains_user_data") is not False:
                found.append(
                    f"{pid}: الحلقة 3 تتطلّب `contains_user_data: false` مُصرَّحاً — "
                    "مسبارٌ يحفظ الخصوصية يقول ذلك ولا يُفترَض"
                )
        elif not str(link.get("reason_ar") or "").strip():
            found.append(f"{pid}: الحلقة {number} NOT_REACHED بلا سببٍ منطوق")
    return found


def _entry_problems(entry: Mapping[str, object], root: Path) -> list[str]:
    pid = str(entry.get("id") or "").strip()
    if not pid:
        return ["مدخلٌ بلا `id`"]
    found: list[str] = []
    if not str(entry.get("title_ar") or "").strip():
        found.append(f"{pid}: `title_ar` فارغ")
    if _missing(root, entry.get("source")):
        found.append(f"{pid}: `source` غير موجود: {entry.get('source')!r}")
    for asset in _items(entry.get("reused_assets")):
        if not isinstance(asset, Mapping) or _missing(root, asset.get("path")):
            found.append(f"{pid}: أصلٌ مُعاد استعماله غير موجود: {asset!r}")
        elif not str(asset.get("role_ar") or "").strip():
            found.append(f"{pid}: أصلٌ مُعاد استعماله بلا دورٍ منطوق: {asset.get('path')!r}")
    found.extend(_link_problems(pid, entry, root))
    return found


def _ledger_route_problems(
    paths: Sequence[Mapping[str, object]], ledger_rows: Sequence[LedgerRow]
) -> list[str]:
    table = route_table(paths)
    found = [
        f"مفتاح توجيهٍ لأكثر من مسار: {route!r} ⇒ {owners}"
        for route, owners in sorted(table.items())
        if len(owners) > 1
    ]
    for row in ledger_rows:
        if route_of(row.target_ref) not in table:
            found.append(
                f"صفّ السجلّ {row.line_no} ({row.entity}) بلا مسار — `{route_of(row.target_ref)}` "
                "غير موجَّه؛ الإسقاط الصامت ممنوع"
            )
    return found


def _catalog_problems(
    paths: Sequence[Mapping[str, object]],
    derived: Mapping[str, object],
    catalog: Mapping[str, object],
    ledger_rows: Sequence[LedgerRow],
) -> list[str]:
    offers = {
        str(offer.get("id")): offer
        for offer in _items(catalog.get("offers"))
        if isinstance(offer, Mapping)
    }
    by_id = {str(item.get("id")): item for item in _paths({"paths": derived.get("paths")})}
    grouped = _rows_by_path(paths, ledger_rows)
    found: list[str] = []
    for entry in paths:
        catalog_id = entry.get("catalog_id")
        if catalog_id is None:
            continue
        offer = offers.get(str(catalog_id))
        if offer is None:
            found.append(f"{entry.get('id')}: `catalog_id` غير موجود في الكتالوج: {catalog_id!r}")
            continue
        status = str(offer.get("status"))
        raw = set(_items(_mapping(by_id.get(str(entry.get("id")))).get("raw_links")))
        if missing := [n for n in CATALOG_REQUIRES.get(status, ()) if n not in raw]:
            found.append(
                f"{entry.get('id')}: الكتالوج يقول {status} والحلقات {missing} غير مبلوغة — "
                "حالةٌ تتجاوز دليلها"
            )
        rows = grouped[str(entry.get("id"))]
        if status in _PAYMENT_STATUSES and not any(r.action == PAYMENT_SETTLED for r in rows):
            found.append(f"{entry.get('id')}: {status} بلا PAYMENT_SETTLED في السجلّ")
    return found


def _wording_problems(
    paths: Sequence[Mapping[str, object]], derived: Mapping[str, object]
) -> list[str]:
    by_id = {str(item.get("id")): item for item in _paths({"paths": derived.get("paths")})}
    found: list[str] = []
    for entry in paths:
        pid = str(entry.get("id"))
        if _mapping(by_id.get(pid)).get("classification") == "commercial_evidence":
            continue
        for text in _strings(entry):
            for line in text.splitlines():
                if "⛔" in line:
                    continue
                lowered = line.lower()
                if hits := [term for term in FORBIDDEN_TERMS if term.lower() in lowered]:
                    found.append(
                        f"{pid}: وصفٌ ممنوع {hits} دون `commercial_evidence` — "
                        "ما يتوقّف عند المراحل الداخلية لا يُوصَف كذلك"
                    )
    return found


def problems(
    doc: Mapping[str, object],
    *,
    root: Path,
    ledger_rows: Sequence[LedgerRow],
    catalog: Mapping[str, object],
) -> list[str]:
    """كلّ ما يمنع قبول ``VALUE_CHAIN.json`` — قائمةٌ كاملة لا أوّل خطأ."""
    raw_paths = _items(doc.get("paths"))
    if not raw_paths:
        return ["`paths` فارغ أو مفقود — سلسلةٌ بلا مسارات لا تشهد لشيء"]
    paths = _paths(doc)
    found: list[str] = []
    if len(paths) != len(raw_paths):
        found.append("مدخلٌ في `paths` ليس كائناً — لا يُقرأ ولا يُشهَد له")
    ids = [str(entry.get("id")) for entry in paths]
    if duplicates := sorted({pid for pid in ids if ids.count(pid) > 1}):
        found.append(f"مُعرِّفات مكرَّرة: {duplicates}")
    for entry in paths:
        found.extend(_entry_problems(entry, root))
    found.extend(_ledger_route_problems(paths, ledger_rows))
    expected = compute_derived(doc, ledger_rows)
    if doc.get("derived") != expected:
        found.append(
            "الكتلة `derived` لا تساوي الاشتقاق — شغّل `python3 scripts/research/value_chain.py`"
        )
    found.extend(_catalog_problems(paths, expected, catalog, ledger_rows))
    found.extend(_wording_problems(paths, expected))
    return found


def map_decisions(text: str) -> dict[str, str]:
    """قرارات المالك من خريطة المسارات — تُقرأ ولا تُنسَخ إلى JSON (D-192)."""
    reader = csv.DictReader(io.StringIO(text))
    return {
        row["id"]: (row.get("decision_2026_09_29") or "").strip()
        for row in reader
        if (row.get("id") or "").strip()
    }


def load_json(path: Path) -> dict[str, object]:
    try:
        payload: object = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueChainError(f"ملفّ غير موجود: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueChainError(f"{path}: ليس JSON صالحاً ({exc})") from exc
    if not isinstance(payload, dict):
        raise ValueChainError(f"{path}: الجذر ليس كائناً")
    return payload
