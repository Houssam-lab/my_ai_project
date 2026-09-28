"""البرهان السلبي لبوّابة تجميد البحث — D-297 · D-270 L4.

⛔ «اختبارٌ يستدعي البوّابة ويتوقّع نجاحها» يُثبِت أنّها تعمل لا أنّها تحجب. كلّ فحصٍ هنا
يُدخل وثيقةَ بحثٍ بلا صفّ اتصالٍ ويؤكّد أنّ ``check_outbound_before_research`` يخرج بـ1،
ثمّ يضيف الصفّ ويؤكّد الصفر.
"""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "fitness"))
sys.path.insert(0, str(REPO_ROOT))

import check_outbound_before_research as gate

from shared.research.contact_ledger import (
    COLUMNS,
    LEDGER_REL,
    SCORECARD_REL,
    build_scorecard,
)

TODAY = date(2026, 9, 28)
HEADER = ",".join(COLUMNS)
SEED = (
    "2026-09-22,FR#7,Balagué Expertise,FR,email,EMAIL_SENT,,"
    "docs/commercial/FR_EINVOICING_TARGETS_2026-09-21.csv:8,premier contact"
)


def _row(**overrides: str) -> dict[str, str]:
    row = {
        "date": "2026-09-27",
        "target_ref": "FR#9",
        "entity": "Cabinet Test",
        "country": "FR",
        "channel": "email",
        "action": "EMAIL_SENT",
        "amount_eur": "",
        "evidence_ref": "",
        "note": "",
    }
    row.update(overrides)
    return row


# ---------------------------------------------------------------- pure decision


def test_research_doc_without_contact_row_is_blocked():
    failures = gate.evaluate(["docs/research/HARD_CURRENCY_NEW_KNOWLEDGE_XYZ.md"], [], TODAY)
    assert len(failures) >= 1
    assert LEDGER_REL in failures[0]


def test_research_doc_with_valid_contact_row_passes():
    assert gate.evaluate(["docs/research/x.md"], [_row()], TODAY) == []


def test_closure_row_does_not_count_as_writing_to_the_market():
    failures = gate.evaluate(
        ["studies/new-round/README.md"], [_row(action="CLOSED_NO_REPLY")], TODAY
    )
    assert len(failures) >= 1


def test_future_dated_row_is_planning_not_a_contact():
    tomorrow = (TODAY + timedelta(days=1)).isoformat()
    failures = gate.evaluate(["docs/reconstitution/13-new.md"], [_row(date=tomorrow)], TODAY)
    assert len(failures) >= 1
    assert any("المستقبل" in f for f in failures)


def test_unknown_action_is_rejected_not_ignored():
    failures = gate.evaluate(["docs/commercial/NEW_OFFER.md"], [_row(action="TWEETED")], TODAY)
    assert len(failures) >= 1


def test_root_arabic_markdown_counts_as_research():
    assert gate.is_research_path("تقرير-صيد-الفرص-المدفوعة.md") is True
    assert gate.is_research_path("README.md") is False


def test_outreach_folder_and_catalog_are_exempt():
    exempt = [
        "docs/commercial/outreach/CONTACT_LEDGER.csv",
        "docs/commercial/outreach/drafts_2026/01_X.txt",
        "docs/commercial/outreach/templates/DPA_NDA_TEMPLATE_FR.md",
        "docs/commercial/HARD_CURRENCY_SCORECARD.json",
        "docs/commercial/OFFER_CATALOG.json",
        "docs/commercial/FR_EINVOICING_TARGETS_2026-09-21.csv",
        "app/main.py",
        ".memory/decisions.md",
    ]
    assert [p for p in exempt if gate.is_research_path(p)] == []
    assert gate.evaluate(exempt, [], TODAY) == []


# ---------------------------------------------------------------- end to end (temp git repo)


def _git(root: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )


def _write_ledger_and_scorecard(root: Path, rows: list[str]) -> None:
    text = "\n".join([HEADER, *rows]) + "\n"
    (root / LEDGER_REL).parent.mkdir(parents=True, exist_ok=True)
    (root / LEDGER_REL).write_text(text, encoding="utf-8")
    (root / SCORECARD_REL).write_text(
        json.dumps(build_scorecard(text, today=TODAY), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _run_gate(root: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[int, str]:
    monkeypatch.setattr(gate, "REPO_ROOT", root)
    monkeypatch.delenv(gate.BASE_ENV, raising=False)
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        code = gate.main()
    return code, buffer.getvalue()


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _write_ledger_and_scorecard(tmp_path, [SEED])
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "seed")
    return tmp_path


def test_e2e_research_commit_without_new_ledger_row_exits_1(
    repo: Path, monkeypatch: pytest.MonkeyPatch
):
    (repo / "docs" / "research").mkdir(parents=True)
    (repo / "docs" / "research" / "BATCH_13.md").write_text("# more research\n", encoding="utf-8")
    code, out = _run_gate(repo, monkeypatch)
    assert code == 1, out
    assert "BATCH_13.md" in out


def test_e2e_same_diff_with_a_new_contact_row_exits_0(repo: Path, monkeypatch: pytest.MonkeyPatch):
    (repo / "docs" / "research").mkdir(parents=True)
    (repo / "docs" / "research" / "BATCH_13.md").write_text("# research\n", encoding="utf-8")
    _write_ledger_and_scorecard(
        repo, [SEED, "2026-09-28,FR#9,Cabinet Test,FR,phone,CALL_MADE,,,appel de suivi"]
    )
    code, out = _run_gate(repo, monkeypatch)
    assert code == 0, out


def test_e2e_hand_edited_scorecard_is_rejected(repo: Path, monkeypatch: pytest.MonkeyPatch):
    scorecard = json.loads((repo / SCORECARD_REL).read_text(encoding="utf-8"))
    scorecard["funnel"]["contacts_sent"] = 30
    (repo / SCORECARD_REL).write_text(
        json.dumps(scorecard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    code, out = _run_gate(repo, monkeypatch)
    assert code == 1, out
    assert "D-192" in out


def test_e2e_malformed_ledger_is_rejected(repo: Path, monkeypatch: pytest.MonkeyPatch):
    (repo / LEDGER_REL).write_text(
        HEADER + "\n2026-09-22,FR#7,Balagué,FR,email,SENT_MAYBE,,,x\n", encoding="utf-8"
    )
    code, out = _run_gate(repo, monkeypatch)
    assert code == 1, out


def test_e2e_clean_repo_passes(repo: Path, monkeypatch: pytest.MonkeyPatch):
    code, out = _run_gate(repo, monkeypatch)
    assert code == 0, out
