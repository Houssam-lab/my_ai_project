"""عقد سجلّ الاتصال الخارجي (D-297) — المجموعة المغلقة، المبلغ حيث يجب، واللوحة المُشتقّة."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from shared.research.contact_ledger import (
    ACTIONS,
    CLOSURE,
    COLUMNS,
    CONTACT_ACTIONS,
    LEDGER_REL,
    LedgerError,
    build_scorecard,
    parse_ledger,
    row_problems,
)

TODAY = date(2026, 9, 28)
HEADER = ",".join(COLUMNS)


def _ledger(*rows: str) -> str:
    return "\n".join([HEADER, *rows]) + "\n"


SEED = "2026-09-22,FR#7,Balagué Expertise,FR,email,EMAIL_SENT,,docs/x.csv:8,premier contact"


def test_the_real_ledger_on_disk_parses_under_the_contract():
    text = (REPO_ROOT / LEDGER_REL).read_text(encoding="utf-8")
    rows = parse_ledger(text, today=date.today())
    assert len(rows) >= 1
    assert rows[0].action == "EMAIL_SENT"
    assert rows[0].entity == "Balagué Expertise"


def test_closed_action_set_and_contact_subset():
    assert "EMAIL_SENT" in CONTACT_ACTIONS
    assert CLOSURE.isdisjoint(CONTACT_ACTIONS)
    assert CONTACT_ACTIONS | CLOSURE == ACTIONS


@pytest.mark.parametrize(
    ("row", "fragment"),
    [
        ("2026-09-22,FR#7,X,FR,email,TWEETED,,,", "خارج المجموعة"),
        ("22/09/2026,FR#7,X,FR,email,EMAIL_SENT,,,", "ISO"),
        ("2026-12-31,FR#7,X,FR,email,EMAIL_SENT,,,", "المستقبل"),
        ("2026-09-22,FR#7,X,FR,email,EMAIL_SENT,390,,", "لا يحمل مبلغاً"),
        ("2026-09-22,FR#7,X,FR,bank,PAYMENT_SETTLED,,releve.pdf,", "يتطلّب `amount_eur`"),
        ("2026-09-22,FR#7,X,FR,bank,PAYMENT_SETTLED,390,,", "evidence_ref"),
        ("2026-09-22,FR#7,X,France,email,EMAIL_SENT,,,", "ISO-3166"),
        ("2026-09-22,,X,FR,email,EMAIL_SENT,,,", "target_ref"),
        ("2026-09-22,FR#7,X,FR,carrier_pigeon,EMAIL_SENT,,,", "قناةٌ"),
    ],
)
def test_rows_violating_the_contract_are_rejected(row: str, fragment: str):
    with pytest.raises(LedgerError) as excinfo:
        parse_ledger(_ledger(SEED, row), today=TODAY)
    assert fragment in str(excinfo.value)


def test_wrong_header_is_rejected():
    with pytest.raises(LedgerError):
        parse_ledger("date,who\n2026-09-22,x\n", today=TODAY)


def test_row_problems_reports_every_defect_not_just_the_first():
    raw = dict(zip(COLUMNS, ["31-12-2026", "", "", "", "x", "NOPE", "-5", "", ""], strict=True))
    problems = row_problems(raw, 2, TODAY)
    assert len(problems) >= 5


def test_scorecard_with_one_email_is_all_zero_or_null_with_reasons():
    card = build_scorecard(_ledger(SEED), today=TODAY)
    assert card["rows"] == 1
    assert card["funnel"]["contacts_sent"] == 1
    assert card["funnel"]["payments_settled"] == 0
    assert card["gate_c"] == "ABSENT"
    metrics = card["hard_currency_scorecard"]
    assert metrics["paid_customers"]["value"] == 0
    assert metrics["settled_revenue_eur"]["value"] == 0
    for name in (
        "recurring_revenue_eur",
        "gross_margin",
        "time_to_first_payment_days",
        "refund_rate",
    ):
        assert metrics[name]["value"] is None, name
        assert metrics[name]["basis"], name
    assert card["conversion"]["reply_rate"]["value"] == 0.0
    assert card["as_of"] == "2026-09-22"


def test_scorecard_with_a_settled_payment_derives_customer_metrics():
    text = _ledger(
        SEED,
        "2026-09-24,FR#7,Balagué Expertise,FR,phone,REPLY_RECEIVED,,,ok",
        "2026-09-25,FR#7,Balagué Expertise,FR,email,SAMPLE_DELIVERED,,,20 fiches",
        "2026-09-26,FR#7,Balagué Expertise,FR,malt,QUOTE_SENT,390,,devis",
        "2026-10-03,FR#7,Balagué Expertise,FR,bank,PAYMENT_SETTLED,390,releve-2026-10.pdf,virement",
    )
    card = build_scorecard(text, today=date(2026, 10, 5))
    metrics = card["hard_currency_scorecard"]
    assert metrics["paid_customers"]["value"] == 1
    assert metrics["foreign_customers"]["value"] == 1
    assert metrics["settled_revenue_eur"]["value"] == 390.0
    assert metrics["time_to_first_value_days"]["value"] == 3
    assert metrics["time_to_first_payment_days"]["value"] == 11
    assert metrics["sales_cycle_days"]["value"] == 11.0
    assert metrics["refund_rate"]["value"] == 0.0
    assert card["conversion"]["payment_rate"]["value"] == 1.0
    assert card["gate_c"] != "ABSENT"
