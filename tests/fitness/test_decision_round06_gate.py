"""البرهان السلبي لبوّابة جولة القرار 06 — `check_decision_round06.py` · D-270 L4.

**لماذا هذا الملفّ:** بوّابةٌ لا تُحجَب حين يُخرَق قانونها زينةٌ تُقرأ حماية. فكلّ فحصٍ هنا
**يكسر مُدخلاً** ويؤكّد رمز خروج ≠ 0 على شجرةٍ مؤقتة، ثمّ يُثبت أنّ الشجرة الحقيقية تمرّ.
الأفكار الخمس الجديدة في هذه الجولة لها برهانٌ سلبيٌّ خاص:

1. رقمٌ في §4 ≠ ملفّ القياس ⇒ أحمر (لا «15.71» باليد بينما الملفّ يقول 15.72).
2. الاسمُ الميّت `prime-environments` خارجَ سياقِ البطلان ⇒ أحمر.
3. صافيٌّ مُقتبَسٌ بلا جدولِ رسمٍ مُعلَن (نقلُ 80/20) ⇒ أحمر — كوداً ونصّاً.
4. `$`+رقمٌ بلا سندٍ، أو رقمٌ محسوبٌ بلا وسمِ ⟨ح⟩، أو بصمةٌ وهمية ⇒ أحمر.
5. E1 ثانيةٌ أو مستوى فوق E1 ⇒ أحمر.

⚠️ لا تُلمَس شجرة المستودع: كلّ كسرٍ يُكتب في `tmp_path` ويُشار إليه بإبدال ثوابت
الوحدة المستورَدة (`LEDGER` · `EVIDENCE` · `ROUND` · `KNOWLEDGE` · `ARTIFACT` · `CATALOG`).
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "fitness"))

import check_decision_round06 as gate

STUDY = REPO_ROOT / "studies" / "algeria-hard-currency"
RESEARCH = REPO_ROOT / "docs" / "research"


def _run(**overrides) -> tuple[int, str]:
    """يشغّل `main()` تحت مسارات بديلة ويُعيد (رمز الخروج، المخرَج)."""
    saved = {name: getattr(gate, name) for name in overrides}
    for name, value in overrides.items():
        setattr(gate, name, value)
    buffer = io.StringIO()
    try:
        with contextlib.redirect_stdout(buffer):
            code = gate.main()
    finally:
        for name, value in saved.items():
            setattr(gate, name, value)
    return code, buffer.getvalue()


def _tree(tmp_path: Path) -> dict[str, object]:
    """نسخةٌ صالحة من كلّ مُدخلات البوّابة إلى `tmp_path`."""
    shutil.copy(STUDY / "decision_ledger_round06.csv", tmp_path / "decision_ledger_round06.csv")
    shutil.copy(STUDY / "evidence_round06.csv", tmp_path / "evidence_round06.csv")
    shutil.copy(STUDY / "DECISION-ROUND-06.md", tmp_path / "DECISION-ROUND-06.md")
    shutil.copy(RESEARCH / "HARD_CURRENCY_NEW_KNOWLEDGE_FIV.md", tmp_path / "KNOWLEDGE_FIV.md")
    shutil.copy(RESEARCH / "FIV_MEASUREMENTS.json", tmp_path / "FIV_MEASUREMENTS.json")
    shutil.copy(
        REPO_ROOT / "docs" / "commercial" / "OFFER_CATALOG.json", tmp_path / "OFFER_CATALOG.json"
    )
    return {
        "LEDGER": tmp_path / "decision_ledger_round06.csv",
        "EVIDENCE": tmp_path / "evidence_round06.csv",
        "ROUND": tmp_path / "DECISION-ROUND-06.md",
        "KNOWLEDGE": tmp_path / "KNOWLEDGE_FIV.md",
        "ARTIFACT": tmp_path / "FIV_MEASUREMENTS.json",
        "CATALOG": tmp_path / "OFFER_CATALOG.json",
    }


def test_real_tree_passes() -> None:
    code, output = _run()
    assert code == 0, output
    assert "21 رقماً" in output


def test_dropped_hypothesis_row_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    ledger = paths["LEDGER"]
    lines = Path(str(ledger)).read_text(encoding="utf-8").splitlines()
    Path(str(ledger)).write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    code, _ = _run(**paths)
    assert code == 1


def test_second_e1_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    ledger = Path(str(paths["LEDGER"]))
    text = ledger.read_text(encoding="utf-8")
    head, sep, tail = text.partition("H71,")
    assert sep
    broken = head.replace(",E0,N1,T71,", ",E1,N1,T71,", 1) + sep + tail
    assert broken != text
    ledger.write_text(broken, encoding="utf-8")
    code, _ = _run(**paths)
    assert code == 1


def test_level_above_e1_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    ledger = Path(str(paths["LEDGER"]))
    text = ledger.read_text(encoding="utf-8")
    broken = text.replace(",E0,N3,T72,", ",E2,N3,T72,", 1)
    assert broken != text
    ledger.write_text(broken, encoding="utf-8")
    code, _ = _run(**paths)
    assert code == 1


def test_declared_counts_mismatch_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    round_doc = Path(str(paths["ROUND"]))
    text = round_doc.read_text(encoding="utf-8")
    broken = text.replace("8 مُنجَزة", "7 مُنجَزة", 1)
    assert broken != text
    round_doc.write_text(broken, encoding="utf-8")
    code, _ = _run(**paths)
    assert code == 1


def test_dropped_evidence_row_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    evidence = Path(str(paths["EVIDENCE"]))
    lines = evidence.read_text(encoding="utf-8").splitlines()
    evidence.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
    code, _ = _run(**paths)
    assert code == 1


def test_invalid_evidence_grade_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    evidence = Path(str(paths["EVIDENCE"]))
    text = evidence.read_text(encoding="utf-8")
    broken = text.replace("L — منخفضةٌ", "X — مجهولةٌ", 1)
    assert broken != text
    evidence.write_text(broken, encoding="utf-8")
    code, _ = _run(**paths)
    assert code == 1


def test_tampered_artifact_number_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    artifact = Path(str(paths["ARTIFACT"]))
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["results"]["listing_band"]["unit_hi_usd"] = 15.72
    artifact.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    code, _ = _run(**paths)
    assert code == 1


def test_bare_stale_name_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    round_doc = Path(str(paths["ROUND"]))
    with round_doc.open("a", encoding="utf-8") as handle:
        handle.write("\nسطرٌ يذكر prime-environments وحده بلا سياق\n")
    code, _ = _run(**paths)
    assert code == 1


def test_gate_c_without_absent_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    round_doc = Path(str(paths["ROUND"]))
    with round_doc.open("a", encoding="utf-8") as handle:
        handle.write("\nسطرٌ يقول GATE_C تغيّرت هذا الأسبوع\n")
    code, _ = _run(**paths)
    assert code == 1


def test_forbidden_phrase_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    round_doc = Path(str(paths["ROUND"]))
    with round_doc.open("a", encoding="utf-8") as handle:
        handle.write("\nهذا العائد مضمون الربح\n")
    code, _ = _run(**paths)
    assert code == 1


def test_fee_transfer_in_artifact_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    artifact = Path(str(paths["ARTIFACT"]))
    payload = json.loads(artifact.read_text(encoding="utf-8"))
    payload["results"]["fee_schedule"]["taskset"]["seller_share"] = 0.8
    artifact.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    code, _ = _run(**paths)
    assert code == 1


def test_duplicate_offer_id_fails(tmp_path: Path) -> None:
    """بعد D-296 لا حصرَ عددياً (D-297) — لكنّ مُعرِّفاً مكرَّراً يُحجب."""
    paths = _tree(tmp_path)
    catalog = Path(str(paths["CATALOG"]))
    payload = json.loads(catalog.read_text(encoding="utf-8"))
    payload["offers"].append({"id": payload["offers"][0]["id"], "status": "PROPOSED"})
    catalog.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    code, _ = _run(**paths)
    assert code == 1


def test_missing_section_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    round_doc = Path(str(paths["ROUND"]))
    text = round_doc.read_text(encoding="utf-8")
    broken = text.replace("## 8.", "## ثمانية.", 1)
    assert broken != text
    round_doc.write_text(broken, encoding="utf-8")
    code, _ = _run(**paths)
    assert code == 1


def test_infinity_in_artifact_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    artifact = Path(str(paths["ARTIFACT"]))
    text = artifact.read_text(encoding="utf-8")
    broken = text.replace("15.714285714285714", "Infinity", 1)
    assert broken != text
    artifact.write_text(broken, encoding="utf-8")
    code, _ = _run(**paths)
    assert code == 1


def test_fake_fingerprint_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    knowledge = Path(str(paths["KNOWLEDGE"]))
    text = knowledge.read_text(encoding="utf-8")
    broken = re_sub_fingerprint(text)
    assert broken != text
    knowledge.write_text(broken, encoding="utf-8")
    code, _ = _run(**paths)
    assert code == 1


def re_sub_fingerprint(text: str) -> str:
    import re

    return re.sub(r"sha256 = [0-9a-f]{64}", "sha256 = " + "0" * 64, text, count=1)


def test_dollar_without_citation_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    knowledge = Path(str(paths["KNOWLEDGE"]))
    with knowledge.open("a", encoding="utf-8") as handle:
        handle.write("\nسعر $999 بلا سندٍ على السطر\n")
    code, _ = _run(**paths)
    assert code == 1


def test_computed_figure_without_pin_fails(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    knowledge = Path(str(paths["KNOWLEDGE"]))
    with knowledge.open("a", encoding="utf-8") as handle:
        handle.write("\nالقيمة 1.98 هنا بلا وسم\n")
    code, _ = _run(**paths)
    assert code == 1
