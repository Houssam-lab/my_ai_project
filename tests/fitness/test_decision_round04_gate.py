"""البرهان السلبي لبوّابة جولة القرار 04 — `check_decision_round04.py` · D-207/D-266 L4.

**لماذا هذا الملفّ:** بوّابةٌ لا تُحجَب حين يُخرَق قانونها زينةٌ تُقرأ حماية. فكلّ فحصٍ هنا
**يكسر مُدخلاً** ويؤكّد رمز خروج ≠ 0 على شجرةٍ مؤقتة، ثمّ يُثبت أنّ الشجرة الحقيقية تمرّ.

والجولة 04 تُدخل ثلاثة أصنافٍ من الادّعاء لم تكن في الجولتين 01/02، ولكلٍّ منها برهانٌ سلبي
خاصّ لأنّ كلاً منها يفشل بطريقةٍ مختلفة:

1. **رقمٌ واردٌ من الخارج** (لا رقمُنا ولا رقمُ أداتنا): يجب أن يبقى محكوماً، وكلُّ ممنوعٍ
   يجب أن يحمل بديلاً مُقتبَساً — فالمنعُ بلا بديلٍ يصير منعاً للكلام لا تصحيحاً له.
2. **اسمُ حقلٍ يَعِد بكميةٍ ويُسَلِّم أخرى**: المطابقةُ بمسارٍ مُسمّى وصيغةِ عرضٍ معلَنة هي
   ما كشف `decision_to_detection_ratio` وهو يحسب تنظيمي÷تقني؛ فحذفُ المسار أو تليينُ الصيغة
   يُعيد العيب.
3. **شيفرةُ استغلال**: الجولةُ تقيس الأثرَ التنظيمي لا الناقل، فوجودُ نمطِ استغلالٍ في مسار
   القياس كسرٌ للموضوع لا للأناقة.

⚠️ لا تُلمَس شجرة المستودع: كلّ كسرٍ يُكتب في `tmp_path` ويُشار إليه بإبدال ثوابت الوحدة
المستورَدة، كما في `test_decision_round02_gate.py`.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts" / "fitness"))

import check_decision_round04 as gate

STUDY = REPO_ROOT / "studies" / "algeria-hard-currency"
GATE_SCRIPT = REPO_ROOT / "scripts" / "fitness" / "check_decision_round04.py"
ARTIFACT = REPO_ROOT / "docs" / "research" / "DLY_MEASUREMENTS.json"
CATALOG = REPO_ROOT / "docs" / "commercial" / "OFFER_CATALOG.json"
KNOWLEDGE_DLY = REPO_ROOT / "docs" / "research" / "HARD_CURRENCY_NEW_KNOWLEDGE_DLY.md"
KNOWLEDGE_CND = REPO_ROOT / "docs" / "research" / "HARD_CURRENCY_NEW_KNOWLEDGE_CND.md"
TRUTH_DOC = REPO_ROOT / ".memory" / "agent_reliability_hard_currency_truth.md"
OS_DOC = REPO_ROOT / "docs" / "commercial" / "FOREIGN_CURRENCY_OPERATING_SYSTEM.md"


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
    shutil.copy(STUDY / "decision_ledger_round04.csv", tmp_path / "decision_ledger_round04.csv")
    shutil.copy(STUDY / "evidence_round04.csv", tmp_path / "evidence_round04.csv")
    shutil.copy(STUDY / "DECISION-ROUND-04.md", tmp_path / "DECISION-ROUND-04.md")
    shutil.copy(ARTIFACT, tmp_path / "DLY_MEASUREMENTS.json")
    shutil.copy(CATALOG, tmp_path / "OFFER_CATALOG.json")
    return {
        "LEDGER": tmp_path / "decision_ledger_round04.csv",
        "EVIDENCE": tmp_path / "evidence_round04.csv",
        "ROUND": tmp_path / "DECISION-ROUND-04.md",
        "ARTIFACT": tmp_path / "DLY_MEASUREMENTS.json",
        "CATALOG": tmp_path / "OFFER_CATALOG.json",
        #: ⛔ `MEASURE` يبقى الحقيقي: البوّابةُ تستورده لتُعيد بناء الملفّ، ونسخُه إلى
        #: `tmp_path` تُدخل وحدةً ثانية بالاسم نفسه في `sys.modules` فتتسرّب بين الاختبارات.
        "SCANNED_DOCS": (
            tmp_path / "DECISION-ROUND-04.md",
            KNOWLEDGE_DLY,
            KNOWLEDGE_CND,
            TRUTH_DOC,
            OS_DOC,
        ),
    }


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _rewrite_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _patch_artifact(path: Path, mutate) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutate(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _edit_doc(path: Path, pattern: str, repl: str, *, count: int = 0) -> None:
    """يستبدل بنمطٍ **متسامح مع البياض** — فالتفافُ السطر في Markdown اختياري."""
    text = path.read_text(encoding="utf-8")
    new, n = re.subn(pattern, repl, text, count=count)
    assert n > 0, f"النمط لم يُطابَق: {pattern!r}"
    path.write_text(new, encoding="utf-8")


def _append_doc(path: Path, text: str) -> None:
    path.write_text(path.read_text(encoding="utf-8") + text, encoding="utf-8")


# --------------------------------------------------------------------------- #
# 0) المرجع — بلا هذا لا معنى لأيّ كسرٍ لاحق
# --------------------------------------------------------------------------- #
def test_valid_copy_passes(tmp_path: Path) -> None:
    code, output = _run(**_tree(tmp_path))
    assert code == 0, output


def test_real_repository_tree_passes() -> None:
    """الشجرة الحقيقية — بالعملية الفرعية كما في CI، لا بإبدال ثوابت."""
    result = subprocess.run(
        [sys.executable, str(GATE_SCRIPT)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "جولة القرار 04 متّسقة" in result.stdout


def test_gate_reports_the_count_of_derived_figures(tmp_path: Path) -> None:
    """المخرَجُ يذكر عددَ الأرقام المطابَقة — فبوّابةٌ لا تُبلِّغ حجمَ فحصها غيرُ قابلةٍ للتدقيق."""
    code, output = _run(**_tree(tmp_path))
    assert code == 0
    assert f"{len(gate.DERIVED_FIGURES)} رقماً" in output


# --------------------------------------------------------------------------- #
# 1) الاشتقاق: رقمُ §4 مقابل ملفّ القياس
# --------------------------------------------------------------------------- #
def test_hand_written_number_drifting_from_artifact_is_blocked(tmp_path: Path) -> None:
    """⛔ «211,814» باليد بينما الملفّ يقول 211,813.6 — تدويرٌ يبدو بريئاً وهو كسرُ اشتقاق."""
    paths = _tree(tmp_path)
    _edit_doc(Path(paths["ROUND"]), r"211,813\.6", "211,814")
    code, output = _run(**paths)
    assert code == 1
    assert "tempo_ratio_actions_per_human_decision" in output


def test_artifact_number_drifting_from_document_is_blocked(tmp_path: Path) -> None:
    """الاتجاهُ الآخر: الملفّ يُعدَّل والوثيقةُ تبقى ⇒ أحمر (لا يكفي أن يكون أحدهما صحيحاً)."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"].__setitem__("controls_held_share", 0.5),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "controls_held_share" in output


def test_missing_artifact_path_is_an_explicit_failure_not_a_silent_skip(tmp_path: Path) -> None:
    """مسارٌ غائب في الملفّ يجب أن يُسمّى — ⛔ لا `None` يُقرأ «لا انحراف»."""
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p["results"].pop("sellable_unit"))
    code, output = _run(**paths)
    assert code == 1
    assert "مسارٌ غائب" in output and "results.sellable_unit" in output


def test_deleting_the_derived_figure_from_the_document_is_blocked(tmp_path: Path) -> None:
    """رقمٌ في الملفّ بلا مقابلٍ في النصّ هو رقمٌ لا يُقرأ — فالمطابقةُ في الاتّجاهَين."""
    paths = _tree(tmp_path)
    _edit_doc(Path(paths["ROUND"]), r"\*\*4\.4286\*\*", "**4.43**")
    code, output = _run(**paths)
    assert code == 1
    assert "غائبٌ عن وثيقة الجولة" in output


def test_list_indexed_path_is_supported_and_validated(tmp_path: Path) -> None:
    """`band_usd_per_hour.0/.1` دليلُ قائمة — والخروجُ عن الحدود خطأٌ مُسمّى لا `IndexError`."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["rate_bias"].__setitem__("band_usd_per_hour", [57.64]),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "دليلُ قائمةٍ خارج الحدود" in output


def test_render_spec_is_part_of_the_contract_not_a_detail(tmp_path: Path) -> None:
    """صيغةُ العرض معلَنة: `f4` على 1.60714… ⇒ «1.6071». وتغييرُ القيمة يكسر العقد."""
    assert gate.render(1.6071428571428572, "f4") == "1.6071"
    assert gate.render(3922.474481905351, "f2c") == "3,922.47"
    assert gate.render(211813.62202288894, "f1c") == "211,813.6"
    assert gate.render(None, "none") == "None"
    assert gate.render(True, "bool") == "True"
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"].__setitem__("decision_to_detection_ratio", 4.4285714),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "decision_to_detection_ratio" in output


def test_the_two_ratios_are_distinct_fields_in_the_artifact(tmp_path: Path) -> None:
    """اسمٌ يَعِد بكميةٍ ويُسَلِّم أخرى: الحقلان موجودان ومختلفان، ⛔ ولا واحدٌ بديلُ الآخر."""
    payload = json.loads(Path(_tree(tmp_path)["ARTIFACT"]).read_text(encoding="utf-8"))
    results = payload["results"]
    assert results["organizational_to_technical_ratio"] == 62.0 / 14.0
    assert results["decision_to_detection_ratio"] == 45.0 / 28.0
    assert results["organizational_to_technical_ratio"] != results["decision_to_detection_ratio"]


def test_artifact_results_must_rebuild_byte_identically(tmp_path: Path) -> None:
    """⛔ لا رقمَ في الجولة بلا مصدرٍ حتمي: تعديلُ `results` على القرص يكسر إعادةَ البناء."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"].__setitem__("binding_layer", "DETECTION"),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "لا تُعاد بناؤها حرفياً" in output


def test_volatile_timestamp_does_not_fail_the_rebuild_check(tmp_path: Path) -> None:
    """`generated_at` طابعُ وقتٍ لا مدخل — فمقارنتُه تُفشل البوّابة كلّ ثانية (اختبارُ هشاشة)."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p.__setitem__("generated_at", "1999-01-01T00:00:00Z"),
    )
    code, output = _run(**paths)
    assert code == 0, output


# --------------------------------------------------------------------------- #
# 2) تحكيمُ المدخل الوارد
# --------------------------------------------------------------------------- #
def test_forbidden_claim_without_a_rescoped_alternative_is_blocked(tmp_path: Path) -> None:
    """المنعُ بلا بديلٍ يصير منعاً للكلام لا تصحيحاً له."""
    paths = _tree(tmp_path)

    def mutate(payload: dict) -> None:
        for case in payload["results"]["adjudication_cases"]:
            if case["verdict"] == "REFUTED_DISPERSION":
                case["rescoped_quotable_claim"] = ""

    _patch_artifact(Path(paths["ARTIFACT"]), mutate)
    code, output = _run(**paths)
    assert code == 1
    assert "بلا بديلٍ مُقتبَس" in output


def test_accepting_a_second_incoming_claim_as_cited_is_blocked(tmp_path: Path) -> None:
    """⛔ قبولُ ادّعاءٍ واردٍ بلا إسناد هو بالضبط ما تمنعه هذه الجولة."""
    paths = _tree(tmp_path)

    def mutate(payload: dict) -> None:
        cases = payload["results"]["adjudication_cases"]
        cases[0]["quotable_as_cited"] = True

    _patch_artifact(Path(paths["ARTIFACT"]), mutate)
    code, output = _run(**paths)
    assert code == 1
    assert "مقبولٌ كما ورد" in output


def test_declaring_pin_axis_applicable_to_a_non_benchmark_claim_is_blocked(tmp_path: Path) -> None:
    """H59: الدبوسُ محكومُ المجال بدرجةٍ معيارية؛ وتطبيقُه على غيرها `UNPINNED` كاذب."""
    paths = _tree(tmp_path)

    def mutate(payload: dict) -> None:
        payload["results"]["adjudication_cases"][0]["pin_axis_applies"] = True

    _patch_artifact(Path(paths["ARTIFACT"]), mutate)
    code, output = _run(**paths)
    assert code == 1
    assert "UNPINNED كاذباً" in output


def test_computing_an_age_for_a_claim_with_no_date_in_input_is_blocked(tmp_path: Path) -> None:
    """⛔ الغائبُ يُقرأ `None` لا طازجاً — وإلا صار الادّعاءُ بلا تاريخ «حديثاً» بالافتراض."""
    paths = _tree(tmp_path)

    def mutate(payload: dict) -> None:
        for case in payload["results"]["adjudication_cases"]:
            if case["date_present_in_input"] is False:
                case["age_days_at_as_of"] = 1.0
                break

    _patch_artifact(Path(paths["ARTIFACT"]), mutate)
    code, output = _run(**paths)
    assert code == 1
    assert "عمرٌ محسوب مع ذلك" in output


def test_dropping_an_adjudication_case_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["adjudication_cases"].pop(),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "والمتوقّع 6" in output


def test_removing_the_adjudication_verdict_summary_from_the_document_is_blocked(
    tmp_path: Path,
) -> None:
    paths = _tree(tmp_path)
    _edit_doc(Path(paths["ROUND"]), r"خمسةٌ ممنوعةُ الاقتباس كما وردت", "بعضُ الادّعاءات ممنوعة")
    code, output = _run(**paths)
    assert code == 1
    assert "حصيلةُ التحكيم" in output


# --------------------------------------------------------------------------- #
# 3) الأصفار المعلَنة: صفرُ تشغيل · صفرُ إيراد · صفرُ استغلال
# --------------------------------------------------------------------------- #
def test_claiming_a_model_run_is_blocked(tmp_path: Path) -> None:
    """L9: لا استعارةَ دليلِ الغير دليلاً لنا — ولا ادّعاءَ تشغيلٍ لم يحدث."""
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p.__setitem__("model_runs_executed", 1))
    code, output = _run(**paths)
    assert code == 1
    assert "model_runs_executed" in output


def test_claiming_a_client_measurement_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p.__setitem__("client_measurements", 3))
    code, output = _run(**paths)
    assert code == 1
    assert "client_measurements" in output


def test_claiming_a_reproduced_exploit_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p.__setitem__("exploits_reproduced", 2))
    code, output = _run(**paths)
    assert code == 1
    assert "exploits_reproduced" in output


def test_zero_counters_must_also_be_declared_in_the_prose(tmp_path: Path) -> None:
    """العدّادُ في الملفّ وحده لا يكفي: النصُّ الذي يُقرأ يجب أن يحمل الصفرَ نفسه."""
    paths = _tree(tmp_path)
    _edit_doc(Path(paths["ROUND"]), r"`model_runs_executed = 0`", "«شُغِّلت نماذج»", count=0)
    code, output = _run(**paths)
    assert code == 1
    assert "غيرُ مُعلَن في وثيقة الجولة" in output


def test_claiming_revenue_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p.__setitem__("revenue_claim", "YES"))
    code, output = _run(**paths)
    assert code == 1
    assert "revenue_claim" in output


def test_revenue_claim_may_carry_an_arabic_explanation(tmp_path: Path) -> None:
    """البادئةُ `NONE` هي العقد — ⛔ لا مطابقةٌ حرفية تسقط على شرحٍ عربيٍّ مُلحق."""
    payload = json.loads(Path(_tree(tmp_path)["ARTIFACT"]).read_text(encoding="utf-8"))
    assert payload["revenue_claim"].startswith("NONE")
    assert payload["revenue_claim"] != "NONE"


def test_dropping_the_no_loss_ceiling_phrase_is_blocked(tmp_path: Path) -> None:
    """⛔ لا توصيةَ بإنفاقٍ بلا سقف — وغيابُ العبارة يعني أنّ الجولة صارت توصي بإنفاق."""
    paths = _tree(tmp_path)
    _edit_doc(Path(paths["ROUND"]), r"لا\s+سقف\s+خسارة\s+معتمداً", "سقفُ الخسارة لاحقاً")
    code, output = _run(**paths)
    assert code == 1
    assert "لا سقف خسارة معتمداً" in output


def test_dropping_the_no_motive_reconciliation_statement_is_blocked(tmp_path: Path) -> None:
    """محرك §8: تعارضُ الدافع يُفحص قبل الترجيح — وإعلانُ عدم التسوية جزءٌ من الحكم."""
    paths = _tree(tmp_path)
    _edit_doc(Path(paths["ROUND"]), r"لا يُسوَّى تعارضُ الدافع", "تعارضُ الدافع محسوم")
    code, output = _run(**paths)
    assert code == 1
    assert "تعارضِ الدافع" in output


def test_exploit_primitive_in_the_measurement_path_is_blocked(tmp_path: Path) -> None:
    """⛔ الجولةُ تقيس الأثرَ التنظيمي لا الناقل؛ وإعادةُ إنتاجه ممنوعةٌ في التكوين الحالي."""
    paths = _tree(tmp_path)
    _append_doc(Path(paths["ROUND"]), "\nعنوانُ metadata الرابط-المحلي 169.254.169.254\n")
    code, output = _run(**paths)
    assert code == 1
    assert "نمطُ استغلال" in output


def test_exploit_primitive_in_the_artifact_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["loss_split"].__setitem__("reading", "h5py.File( … )"),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "نمطُ استغلال" in output


# --------------------------------------------------------------------------- #
# 4) المحرّمات: الادّعاءاتُ الواردة المدحوضة لا تعود إلى نصوصنا
# --------------------------------------------------------------------------- #
def test_refuted_incoming_claim_outside_negation_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _append_doc(Path(paths["ROUND"]), "\nالسوقُ يبلغ 13.5 مليار دولار بحلول 2032.\n")
    code, output = _run(**paths)
    assert code == 1
    assert "خارج سياق منعٍ صريح" in output


def test_refuted_claim_inside_explicit_negation_is_allowed(tmp_path: Path) -> None:
    """وإلا صار الفحصُ منعاً للكلام **عن المنع** — والوثيقةُ تذكر المدحوض لتنفيه."""
    paths = _tree(tmp_path)
    _append_doc(Path(paths["ROUND"]), "\n⛔ ممنوعٌ اقتباسُ «13.5 مليار» بلا مصدر.\n")
    code, output = _run(**paths)
    assert code == 0, output


def test_refuted_rate_claim_outside_negation_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _append_doc(Path(paths["ROUND"]), "\nمتوسطُ الأجر 143 دولار/ساعة وهو معيارُ التسعير.\n")
    code, output = _run(**paths)
    assert code == 1, output


def test_refuted_window_conflation_outside_negation_is_blocked(tmp_path: Path) -> None:
    """R9: خلطُ نافذة الحملة بالبقاء داخل الضحية يغيّر وحدةَ القياس ⇒ يغيّر السعر."""
    paths = _tree(tmp_path)
    _append_doc(Path(paths["ROUND"]), "\nاختراقٌ كامل استمرّ 4.5 يوم داخل بنية الإنتاج.\n")
    code, output = _run(**paths)
    assert code == 1, output


def test_the_knowledge_document_is_scanned_too(tmp_path: Path) -> None:
    """وثيقةُ المعرفة قابلةٌ للاقتباس منها ⇒ تُفحص مثل وثيقة القرار تماماً."""
    assert KNOWLEDGE_DLY.exists(), "وثيقةُ المعرفة DLY غائبة"
    paths = _tree(tmp_path)
    shutil.copy(KNOWLEDGE_DLY, tmp_path / "HARD_CURRENCY_NEW_KNOWLEDGE_DLY.md")
    paths["SCANNED_DOCS"] = (tmp_path / "HARD_CURRENCY_NEW_KNOWLEDGE_DLY.md",)
    _append_doc(
        tmp_path / "HARD_CURRENCY_NEW_KNOWLEDGE_DLY.md",
        "\nيعتمد العرضُ على 14 من 16 نشراً بلا سجلّات تدقيق.\n",
    )
    code, output = _run(**paths)
    assert code == 1
    assert "HARD_CURRENCY_NEW_KNOWLEDGE_DLY.md" in output


# --------------------------------------------------------------------------- #
# 5) السجلّ: مستوى الالتزام والبوابة والترقيم
# --------------------------------------------------------------------------- #
def test_escalating_a_hypothesis_to_e2_is_blocked(tmp_path: Path) -> None:
    """⛔ لا E2 بلا سقف خسارة معتمد — ولا تُرقّى فرضيةٌ بحجّة قوّة الدليل الأوّلي."""
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["LEDGER"]))
    rows[0]["max_level"] = "E2"
    _rewrite_csv(Path(paths["LEDGER"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "خارج E0/E1" in output


def test_breaking_hypothesis_id_continuity_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["LEDGER"]))
    rows[-1]["id"] = "H60"
    _rewrite_csv(Path(paths["LEDGER"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "اتّصالاً" in output


def test_reusing_a_claim_id_from_round03_is_blocked(tmp_path: Path) -> None:
    """الترقيمُ متصلٌ مع الجولة 03 (C38–C46) — ⛔ لا إعادةُ استعمالٍ تُفسد التتبّع."""
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["LEDGER"]))
    rows[0]["key_claim"] = "C40"
    _rewrite_csv(Path(paths["LEDGER"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "معادٌ استعمالها" in output


def test_reusing_a_card_id_from_round03_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["LEDGER"]))
    rows[0]["key_test"] = "T41"
    _rewrite_csv(Path(paths["LEDGER"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "معادٌ استعمالها" in output


def test_malformed_claim_or_test_id_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["LEDGER"]))
    rows[0]["key_claim"] = "C47a"
    _rewrite_csv(Path(paths["LEDGER"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "خارج الصيغة [CT]nn" in output


def test_dropping_the_shared_dependency_is_blocked(tmp_path: Path) -> None:
    """«محفظة متنوّعة» بلا فحص العُقد ادّعاءٌ لا تحليل."""
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["LEDGER"]))
    rows[3]["shared_dependency"] = ""
    _rewrite_csv(Path(paths["LEDGER"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "بلا اعتماد مشترك" in output


def test_an_unclassifiable_gate_state_is_blocked(tmp_path: Path) -> None:
    """حالةُ البوابة يجب أن تكون أحد التصريحات الأربعة — ⛔ لا «قيد الدراسة» التي لا تُفحص."""
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["LEDGER"]))
    rows[0]["gate_state"] = "قيد الدراسة"
    _rewrite_csv(Path(paths["LEDGER"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "لا تُصنَّف" in output


def test_dropping_the_binding_gate_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["LEDGER"]))
    rows[0]["binding_gate"] = ""
    _rewrite_csv(Path(paths["LEDGER"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "بلا بوّابة حاكمة" in output


# --------------------------------------------------------------------------- #
# 6) الأعدادُ المعلَنة في §6.1 يجب أن تُشتقّ من السجلّ
# --------------------------------------------------------------------------- #
def test_published_survey_count_drift_is_blocked(tmp_path: Path) -> None:
    """⛔ عددٌ منسوخ في الجدول لا مشتقٌّ من CSV يصير ادّعاءً لا دليلاً."""
    paths = _tree(tmp_path)
    _edit_doc(
        Path(paths["ROUND"]),
        r"\| \*\*فاشلة في التكوين الحالي\*\* \(مانعٌ مسند\) \| \*\*2\*\* \|",
        "| **فاشلة في التكوين الحالي** (مانعٌ مسند) | **5** |",
    )
    code, output = _run(**paths)
    assert code == 1
    assert "بينما السجلّ يشتقّ" in output


def test_published_level_count_drift_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _edit_doc(
        Path(paths["ROUND"]),
        r"\| \*\*سقفٌ أقصى مسموح = E1\*\* \| \*\*6\*\* \|",
        "| **سقفٌ أقصى مسموح = E1** | **9** |",
    )
    code, output = _run(**paths)
    assert code == 1
    assert "عددُ E1" in output


def test_bucket_state_classification_matches_the_ledger_words(tmp_path: Path) -> None:
    """التصنيفُ يشتقّ من `gate_state` لا من نيّة الكاتب — فكلّ صيغةٍ معلَنة لها دلْو."""
    rows = _rows(Path(_tree(tmp_path)["LEDGER"]))
    buckets = {row["id"]: gate.bucket_state(row["gate_state"]) for row in rows}
    assert buckets["H55"] == "failed" and buckets["H56"] == "failed"
    assert buckets["H51"] == "held", "«معلّقة مشروطة» معلّقةٌ لا فاشلة"
    assert buckets["H53"] == "untested"
    assert buckets["H58"] == "partial" and buckets["H59"] == "partial"
    assert "other" not in buckets.values()


# --------------------------------------------------------------------------- #
# 7) سجلّ الأدلّة
# --------------------------------------------------------------------------- #
def test_evidence_row_without_a_date_is_blocked(tmp_path: Path) -> None:
    """T43: تاريخٌ لكلّ صفّ — فسندٌ بلا تاريخ لا يُعرَف إن كان قد تُوفّي."""
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["EVIDENCE"]))
    rows[0]["as_of"] = ""
    _rewrite_csv(Path(paths["EVIDENCE"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "`as_of` غائبٌ" in output


def test_evidence_grade_outside_the_inherited_convention_is_blocked(tmp_path: Path) -> None:
    """⛔ لا اختراعَ مخطّطِ درجاتٍ جديد في الجولة 04: P/M/L ± H/M أو UNSTATED."""
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["EVIDENCE"]))
    rows[0]["status"] = "PRIMARY"
    _rewrite_csv(Path(paths["EVIDENCE"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "درجةُ مصدرٍ خارج العُرف" in output


def test_evidence_without_independence_note_is_blocked(tmp_path: Path) -> None:
    """محورُ التحكيم الأوّل هو الاستقلال — فسندٌ بلا ملاحظةِ استقلالٍ غيرُ قابلٍ للتحكيم."""
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["EVIDENCE"]))
    rows[2]["independence_note"] = ""
    _rewrite_csv(Path(paths["EVIDENCE"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "بلا ملاحظةِ استقلال" in output


def test_evidence_without_reverification_trigger_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["EVIDENCE"]))
    rows[2]["reverification_trigger"] = ""
    _rewrite_csv(Path(paths["EVIDENCE"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "بلا محفّزِ إعادة تحقّق" in output


def test_breaking_the_evidence_id_range_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["EVIDENCE"]))
    rows[-1]["id"] = "S96"
    _rewrite_csv(Path(paths["EVIDENCE"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "اتّصالاً" in output


def test_renaming_the_evidence_schema_is_blocked(tmp_path: Path) -> None:
    """عمودٌ مُعاد تسميتُه يكسر قابليةَ المقارنة مع الجولتين 02/03."""
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["EVIDENCE"]))
    renamed = [{("as_of" if k == "as_of" else k): v for k, v in row.items()} for row in rows]
    for row in renamed:
        row["date"] = row.pop("as_of")
    with Path(paths["EVIDENCE"]).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(renamed[0].keys()))
        writer.writeheader()
        writer.writerows(renamed)
    code, output = _run(**paths)
    assert code == 1
    assert "أعمدةُ سجلّ الأدلّة" in output


def test_unstated_source_is_admitted_as_evidence_with_a_declared_absence(tmp_path: Path) -> None:
    """S94 هو المدخلُ المفحوص نفسه: وجودُه بلا إسنادٍ **هو** النتيجةُ القابلة للقياس.

    ⛔ والرابطُ **إعلانُ غيابٍ** («بلا رابط — مُدخلُ محادثة») لا حقلٌ فارغ: فالفارغُ يُقرأ
    نقصاً في التدوين، والمُعلَن يُقرأ صفةً في السند. وهذا فرقٌ له أثر: البوّابةُ تقبل الثاني
    وترفض الأول في صفٍّ غير UNSTATED.
    """
    rows = _rows(Path(_tree(tmp_path)["EVIDENCE"]))
    s94 = next(row for row in rows if row["id"] == "S94")
    assert s94["status"].startswith("UNSTATED")
    assert not s94["url"].startswith("http")
    assert "بلا رابط" in s94["url"]
    assert s94["as_of"] == "2026-09-12"


def test_a_non_http_url_on_a_resourced_row_is_blocked(tmp_path: Path) -> None:
    """⛔ حاشيةٌ مكان الرابط تُقرأ إسناداً — فصفٌّ مُسند بلا `http…` كسرٌ لا تفصيل."""
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["EVIDENCE"]))
    rows[0]["url"] = "(انظر المصدر أعلاه)"
    _rewrite_csv(Path(paths["EVIDENCE"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "حاشيةٌ مكان الرابط" in output


def test_an_unstated_row_carrying_a_link_is_blocked(tmp_path: Path) -> None:
    """الوسمُ يناقض السند: `UNSTATED` مع رابطٍ يعني أنّ الإسناد موجودٌ فلم الوسم؟"""
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["EVIDENCE"]))
    s94 = next(row for row in rows if row["id"] == "S94")
    s94["url"] = "https://example.org/the-input"
    _rewrite_csv(Path(paths["EVIDENCE"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "يناقض السند" in output


# --------------------------------------------------------------------------- #
# 8) الكتالوج وبنية الوثيقة
# --------------------------------------------------------------------------- #
def test_duplicate_offer_id_is_blocked(tmp_path: Path) -> None:
    """بعد D-296 لا حصرَ عددياً (D-297 أزال عدّ السبعة من هذا الفارض) — لكنّ مُعرِّفاً مكرَّراً يُحجب."""
    paths = _tree(tmp_path)
    catalog = json.loads(Path(paths["CATALOG"]).read_text(encoding="utf-8"))
    clone = dict(catalog["offers"][0])  # same id ⇒ two lines, one identifier
    catalog["offers"].append(clone)
    Path(paths["CATALOG"]).write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    code, output = _run(**paths)
    assert code == 1
    assert "مكرَّر" in output


def test_removing_the_legal_ethical_gate_section_is_blocked(tmp_path: Path) -> None:
    """§7 هي البوابةُ غيرُ التعويضية على خطة الـ90 يوماً الواردة — ⛔ لا تُحذف."""
    paths = _tree(tmp_path)
    _edit_doc(Path(paths["ROUND"]), r"## 7\. البوابة القانونية والأخلاقية", "## 7. ملاحظات")
    code, output = _run(**paths)
    assert code == 1
    assert "قسمٌ إلزامي غائب" in output


def test_dropping_a_next_step_card_is_blocked(tmp_path: Path) -> None:
    """بطاقةٌ بلا معيارِ خروج نيّةٌ لا التزام — فكلّ T45..T54 يجب أن تُذكر."""
    paths = _tree(tmp_path)
    _edit_doc(Path(paths["ROUND"]), r"\*\*T50\*\*", "**T50x**")
    code, output = _run(**paths)
    assert code == 1
    assert "T50" in output


def test_decision_page_over_the_word_ceiling_is_blocked(tmp_path: Path) -> None:
    """محرك §3: القرارُ الذي لا يُقرأ لا يُتَّخذ — والسقفُ 250 لا 300."""
    paths = _tree(tmp_path)
    _edit_doc(
        Path(paths["ROUND"]),
        r"\*\*التالي:\*\*",
        "**تمهيدٌ طويلٌ** " + "كلمةٌ " * 60 + "**التالي:**",
    )
    code, output = _run(**paths)
    assert code == 1
    assert "والسقفُ 250" in output


def test_decision_page_at_the_ceiling_passes(tmp_path: Path) -> None:
    """الحدُّ نفسه مقبولٌ — فبوّابةٌ ترفض 250 كلمةً وهي تعلن 250 تكذب عن حدّها."""
    paths = _tree(tmp_path)
    body = Path(paths["ROUND"]).read_text(encoding="utf-8")
    section = body.split("## 1. صفحة القرار", 1)[1].split("## 2. عقد القرار", 1)[0]
    words = len(re.findall(r"[\w\u0600-\u06FF]+", re.sub(r"[*`>|#_]", " ", section)))
    assert words == gate.DECISION_PAGE_WORD_CEILING


def test_missing_required_file_is_a_hard_failure_not_an_empty_pass(tmp_path: Path) -> None:
    """⛔ ملفٌّ غائب ⇒ خروج 1 من `main` مباشرة، لا بوّابةٌ خضراء على فراغ."""
    for missing in ("LEDGER", "EVIDENCE", "ROUND", "ARTIFACT", "CATALOG", "MEASURE"):
        sub = tmp_path / missing
        sub.mkdir(exist_ok=True)
        paths = _tree(sub)
        paths[missing] = sub / "definitely_absent.xyz"
        buffer = io.StringIO()
        saved = {name: getattr(gate, name) for name in paths}
        for name, value in paths.items():
            setattr(gate, name, value)
        try:
            with contextlib.redirect_stdout(buffer):
                code = gate.main()
        finally:
            for name, value in saved.items():
                setattr(gate, name, value)
        assert code == 1, f"{missing}: خروج {code} على ملفٍّ غائب"
        assert "لازمٌ غائب" in buffer.getvalue()


# --------------------------------------------------------------------------- #
# 9) حراسُ الفارض نفسه
# --------------------------------------------------------------------------- #
def test_gate_module_is_stdlib_only() -> None:
    """⛔ البوّابةُ لا تستورد شبكةً ولا طرفاً ثالثاً — وإلا صارت هي نفسها اعتماداً."""
    import ast

    tree = ast.parse(GATE_SCRIPT.read_text(encoding="utf-8"))
    allowed = {"__future__", "csv", "json", "re", "sys", "pathlib"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] in allowed, alias.name
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root in allowed, node.module


def test_gate_has_no_network_or_shell_escape() -> None:
    """⛔ الفحصُ بالـAST لا بالبحث النصي: `subprocess` يظهر في الفارض **نمطَ كشفٍ** لشيءٍ
    ممنوع، لا استدعاءً — فبوّابةٌ تُفتَّش بالنصّ تحظر نفسها بسبب ما تحرس منه."""
    import ast

    tree = ast.parse(GATE_SCRIPT.read_text(encoding="utf-8"))
    banned = {"urllib", "requests", "http", "socket", "subprocess", "os", "shutil", "tempfile"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned, alias.name
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned, node.module
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            assert not (node.value.id == "os" and node.attr == "system"), "os.system"
            assert node.value.id not in {"subprocess", "socket", "urllib"}, node.value.id


def test_every_derived_figure_path_resolves_in_the_real_artifact() -> None:
    """حارسٌ على الفارض نفسه: مسارٌ مُهملأ في `DERIVED_FIGURES` يُسقط فحصاً بصمت."""
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    for dotted, spec, want, doc_token in gate.DERIVED_FIGURES:
        value = gate.dig(payload, dotted)  # يرفع KeyError إن غاب
        assert gate.render(value, spec) == want, (
            f"{dotted}: {value!r} ⇒ {gate.render(value, spec)!r} ≠ {want!r}"
        )
        assert doc_token, f"{dotted}: رمزُ وثيقةٍ فارغ"


def test_every_derived_figure_token_is_in_the_round_document() -> None:
    text = gate.squash((STUDY / "DECISION-ROUND-04.md").read_text(encoding="utf-8"))
    missing = [token for _, _, _, token in gate.DERIVED_FIGURES if token not in text]
    assert not missing, missing


def test_negation_markers_cover_every_refutation_row() -> None:
    """كلُّ صفِّ **دحضٍ** في §3 يحمل علامةَ منع — وإلا صار الدحضُ سرداً للمدحوض.

    ⛔ ويُستثنى صفُّ «مُثبتة» صراحةً: فاشتراطُ علامةِ نفيٍ على ما ثبت صحّتُه يجبر النصَّ
    على إنكار الصحيح، وهو أسوأُ من قبول المدحوض. والجدولُ يجب أن يحوي واحداً كهذا على
    الأقلّ — وإلا صار دحضاً شاملاً يُقرأ تشكيكاً لا تحكيماً.
    """
    text = (STUDY / "DECISION-ROUND-04.md").read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if re.match(r"^\| R\d+ \|", line)]
    assert len(rows) >= 10, f"جدولُ الدحض ناقص: {len(rows)} صفوف"
    confirmed = [line for line in rows if "**مُثبتة**" in line]
    assert len(confirmed) == 1, f"صفوفُ «مُثبتة» = {len(confirmed)}، والمتوقّع 1 (R11)"
    for line in rows:
        if line in confirmed:
            continue
        assert any(marker in line for marker in gate.NEGATION_MARKERS), line[:70]


def test_forbidden_claims_present_in_the_round_document_are_all_negated() -> None:
    """ما ذُكر من المحرّمات في §3 يجب أن يكون **منفيّاً في السطر نفسه**.

    ⛔ ولا يُشترط أن تُذكر كلّها: فأربعةٌ منها حرسٌ لنصوصٍ **قادمة** («نضمن الامتثال» ·
    «اكتشفنا ثغرة» · صيغتان بديلتان لرقمٍ مدحوض)، وذكرُها في جدول الدحض حشو. لكنّ القائمةَ
    لا يجوز أن تصير زينةً كاملة ⇒ يُشترط أن يُذكر أكثرُ من نصفها.
    """
    text = (STUDY / "DECISION-ROUND-04.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    present = 0
    for claim in gate.FORBIDDEN_CLAIMS:
        needle = claim.rstrip("\n")
        hits = [line for line in lines if needle in line]
        if not hits:
            continue
        present += 1
        assert all(any(marker in line for marker in gate.NEGATION_MARKERS) for line in hits), (
            f"محرَّمٌ مذكورٌ خارج منع: {needle!r} → {hits[0][:80]}"
        )
    assert present * 2 > len(gate.FORBIDDEN_CLAIMS), (
        f"{present} من {len(gate.FORBIDDEN_CLAIMS)} محرَّماً مذكور — فالقائمةُ صارت زينة"
    )


def test_forward_looking_guards_are_declared_as_such() -> None:
    """الحرسُ المستقبليّ مُسمّى — ⛔ لا يُترك في القائمة بلا سببٍ فيُظنّ سهواً."""
    text = (STUDY / "DECISION-ROUND-04.md").read_text(encoding="utf-8")
    forward = [c for c in gate.FORBIDDEN_CLAIMS if c.rstrip("\n") not in text]
    assert set(forward) == {
        "10 ملايين دولار أرصدة",
        "سوقُ تأمين الوكلاء المستقلين بـ",
        "نضمن الامتثال",
        "اكتشفنا ثغرة",
    }, forward
