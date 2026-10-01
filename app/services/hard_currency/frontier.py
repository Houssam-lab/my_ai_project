"""خريطة الجبهة — كلّ مسارٍ بموقعه الحقيقي على السلسلة، مُشتقّاً لحظة الطلب (D-305).

الاشتقاق يُعاد هنا من ``CONTACT_LEDGER.csv`` لا يُقرأ من الكتلة المُلتزَمة: صفُّ ردٍّ أُضيف
للتوّ يرفع المسار فوراً، وانحرافُ الكتلة المُلتزَمة يُعلَن (``committed_snapshot_current``)
ولا يُخفى.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import date

from app.services.hard_currency.sources import HardCurrencySources, SourceUnavailableError
from shared.research.contact_ledger import (
    LEDGER_REL,
    SCORECARD_REL,
    LedgerError,
    parse_ledger,
)
from shared.research.value_chain import (
    CATALOG_REL,
    LINKS,
    MAP_REL,
    NOT_REACHED,
    REACHED,
    VALUE_CHAIN_REL,
    compute_derived,
    map_decisions,
)


def _declared_links(entry: Mapping[str, object]) -> list[dict[str, object]]:
    declared = entry.get("links") or {}
    out: list[dict[str, object]] = []
    for link in LINKS:
        if link.source != "declared":
            continue
        raw = declared.get(str(link.number)) or {}  # type: ignore[union-attr]
        out.append(
            {
                "number": link.number,
                "status": raw.get("status"),
                "evidence": list(raw.get("evidence") or []),
                "note_ar": raw.get("note_ar"),
                "reason_ar": raw.get("reason_ar"),
            }
        )
    return out


def _ledger_links(derived_path: Mapping[str, object]) -> list[dict[str, object]]:
    raw = set(derived_path.get("raw_links") or [])  # type: ignore[arg-type]
    return [
        {
            "number": link.number,
            "status": REACHED if link.number in raw else NOT_REACHED,
            "evidence": [LEDGER_REL] if link.number in raw else [],
            "note_ar": None,
            "reason_ar": None if link.number in raw else "لا صفّ في CONTACT_LEDGER.csv",
        }
        for link in LINKS
        if link.source == "ledger"
    ]


def build_frontier(sources: HardCurrencySources, *, today: date | None = None) -> dict[str, object]:
    """الخريطة كاملةً: القمع الحقيقي في الأعلى، ثمّ كلّ مسارٍ بحلقاته وتصنيفه وفاعله التالي."""
    doc = sources.read_json(VALUE_CHAIN_REL)
    try:
        rows = parse_ledger(sources.read_text(LEDGER_REL), today=today or date.today())
    except LedgerError as exc:
        raise SourceUnavailableError(f"سجلّ الاتصال غير مقبول: {exc}") from exc
    scorecard = sources.read_json(SCORECARD_REL)
    catalog = sources.read_json(CATALOG_REL)
    decisions = map_decisions(sources.read_text(MAP_REL))

    derived = compute_derived(doc, rows)
    derived_by_id = {str(item["id"]): item for item in derived["paths"]}  # type: ignore[index]
    catalog_status = {
        str(offer.get("id")): offer.get("status")
        for offer in catalog.get("offers", []) or []  # type: ignore[union-attr]
        if isinstance(offer, dict)
    }

    paths: list[dict[str, object]] = []
    for entry in doc.get("paths", []) or []:  # type: ignore[union-attr]
        pid = str(entry.get("id"))
        item = derived_by_id[pid]
        catalog_id = entry.get("catalog_id")
        paths.append(
            {
                "id": pid,
                "title_ar": entry.get("title_ar"),
                "source": entry.get("source"),
                "owner_decision": decisions.get(pid),
                "catalog_id": catalog_id,
                "catalog_status": catalog_status.get(str(catalog_id)) if catalog_id else None,
                "withdrawn": bool(entry.get("withdrawn")),
                "workbench": entry.get("workbench"),
                "classification": item["classification"],
                "reached": item["reached"],
                "next_link": item["next_link"],
                "next_link_title_ar": item["next_link_title_ar"],
                "next_actor": item["next_actor"],
                "links": _declared_links(entry) + _ledger_links(item),
                "ledger": item["ledger"],
                "reused_assets": list(entry.get("reused_assets") or []),
                "locked_extensions": list(entry.get("locked_extensions") or []),
            }
        )

    return {
        "as_of": derived["as_of"],
        "gate_c": scorecard.get("gate_c"),
        "funnel": scorecard.get("funnel"),
        "by_classification": derived["by_classification"],
        "next_actor_human": derived["next_actor_human"],
        "next_actor_code": derived["next_actor_code"],
        "committed_snapshot_current": doc.get("derived") == derived,
        "links": [
            {
                "number": link.number,
                "title_ar": link.title_ar,
                "actor": link.actor,
                "source": link.source,
            }
            for link in LINKS
        ],
        "paths": paths,
    }
