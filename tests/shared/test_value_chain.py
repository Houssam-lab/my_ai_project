"""سلسلة القيمة (D-305) — الاشتقاق حتميّ، والاتّصال إلزامي، والسجلّ وحده يرفع الحلقتين 7–8."""

from __future__ import annotations

from datetime import date

import pytest

from shared.research.contact_ledger import LedgerRow
from shared.research.value_chain import (
    CLASSIFICATIONS,
    LINKS,
    ValueChainError,
    classify,
    compute_derived,
    route_of,
)


def _row(action: str, *, target: str = "TARGETS.csv#id=1", when: str = "2026-09-22") -> LedgerRow:
    return LedgerRow(
        line_no=2,
        date=date.fromisoformat(when),
        target_ref=target,
        entity="Firm",
        country="FR",
        channel="email",
        action=action,
        amount_eur=290.0 if action in {"DEPOSIT_RECEIVED", "PAYMENT_SETTLED"} else None,
        evidence_ref="x",
        note="",
    )


def _entry(reached: set[int], *, routes: list[str] | None = None) -> dict[str, object]:
    links = {
        str(n): {"status": "REACHED", "evidence": ["x"]}
        if n in reached
        else {"status": "NOT_REACHED", "reason_ar": "r"}
        for n in range(1, 7)
    }
    return {"id": "P-1", "links": links, "ledger_routes": routes or ["TARGETS.csv"]}


@pytest.mark.parametrize(
    ("reached", "expected"),
    [
        (0, "unevidenced_hypothesis"),
        (1, "research_asset"),
        (3, "research_asset"),
        (4, "engineering_capability"),
        (5, "validated_capability"),
        (6, "validated_capability"),
        (7, "commercial_evidence"),
        (8, "commercial_evidence"),
    ],
)
def test_classification_boundaries(reached: int, expected: str) -> None:
    assert classify(reached) == expected


@pytest.mark.parametrize("bad", [-1, 9])
def test_classification_rejects_out_of_range(bad: int) -> None:
    with pytest.raises(ValueChainError):
        classify(bad)


def test_links_are_eight_ordered_and_ledger_owns_seven_and_eight() -> None:
    assert [link.number for link in LINKS] == list(range(1, 9))
    assert [link.number for link in LINKS if link.source == "ledger"] == [7, 8]
    assert CLASSIFICATIONS[-1] == "commercial_evidence"


def test_gap_stops_the_chain_even_if_higher_links_are_declared() -> None:
    # 1,2,4,5 مبلوغة والثالثة ناقصة ⇒ اثنتان فقط تُحتسَبان.
    derived = compute_derived({"paths": [_entry({1, 2, 4, 5})]}, [])
    path = derived["paths"][0]
    assert path["reached"] == 2
    assert path["classification"] == "research_asset"
    assert path["next_link"] == 3 and path["next_actor"] == "code"
    assert path["raw_links"] == [1, 2, 4, 5]


def test_reply_raises_link_seven_only_after_a_contiguous_chain() -> None:
    reply = [_row("REPLY_RECEIVED")]
    partial = compute_derived({"paths": [_entry({1, 2, 3, 4})]}, reply)["paths"][0]
    assert 7 in partial["raw_links"]
    assert partial["reached"] == 4  # اهتمامٌ بلا نتيجةٍ على نظامٍ مستقلّ لا يرفع التصنيف

    full = compute_derived({"paths": [_entry({1, 2, 3, 4, 5, 6})]}, reply)["paths"][0]
    assert full["reached"] == 7
    assert full["classification"] == "commercial_evidence"


def test_money_raises_link_eight_and_is_counted() -> None:
    rows = [_row("REPLY_RECEIVED"), _row("PAYMENT_SETTLED")]
    path = compute_derived({"paths": [_entry({1, 2, 3, 4, 5, 6})]}, rows)["paths"][0]
    assert path["reached"] == 8
    assert path["next_link"] is None and path["next_actor"] is None
    assert path["ledger"]["payments_settled"] == 1


def test_unrouted_rows_do_not_count_for_any_path() -> None:
    rows = [_row("REPLY_RECEIVED", target="OTHER.csv#id=1")]
    path = compute_derived({"paths": [_entry({1, 2, 3, 4, 5, 6})]}, rows)["paths"][0]
    assert 7 not in path["raw_links"]


def test_as_of_comes_from_the_ledger_not_the_clock() -> None:
    rows = [_row("EMAIL_SENT", when="2026-09-01"), _row("EMAIL_SENT", when="2026-09-22")]
    assert compute_derived({"paths": [_entry(set())]}, rows)["as_of"] == "2026-09-22"
    assert compute_derived({"paths": [_entry(set())]}, [])["as_of"] is None


def test_route_of_strips_the_row_selector() -> None:
    assert (
        route_of("FR_EINVOICING_TARGETS_2026-09-21.csv#id=7")
        == "FR_EINVOICING_TARGETS_2026-09-21.csv"
    )
    assert route_of("plain.csv") == "plain.csv"


def test_derivation_is_deterministic() -> None:
    doc = {"paths": [_entry({1, 2, 3})]}
    rows = [_row("EMAIL_SENT")]
    assert compute_derived(doc, rows) == compute_derived(doc, rows)
