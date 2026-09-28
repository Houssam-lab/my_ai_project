"""البرهان السلبي لبوّابة جولة القرار 05 — `check_decision_round05.py` · D-207/D-266 L4.

**لماذا هذا الملفّ:** بوّابةٌ لا تُحجَب حين يُخرَق قانونها زينةٌ تُقرأ حماية. فكلّ فحصٍ هنا
**يكسر مُدخلاً** ويؤكّد رمز خروج ≠ 0 على شجرةٍ مؤقتة، ثمّ يُثبت أنّ الشجرة الحقيقية تمرّ.

والجولة 05 تُدخل أربعة أصنافٍ من الحراسة لم تكن في بوّابات 01/02/04، ولكلٍّ برهانٌ سلبيٌّ
خاصّ لأنّ كلاً منها يفشل بطريقةٍ مختلفة:

1. **حارسُ المجال (`H59`/`H60`):** دبوسٌ كاملُ الحقول في المجال الصحيح يجب ألا يُنتج
   `UNPINNED`. فلو ظهر واحدٌ لكان القياسُ مُعيباً — والبوّابة تفشل بدل أن تُنتج حكماً كاذباً.
2. **انضباطُ صفرِ المقام:** نسبةٌ مقامُها صفر تُسجَّل **زوجاً** — ⛔ لا `Infinity` ولا `NaN`
   في الملفّ كلّه. والمسحُ النصّي هو الحارسُ الوحيد الذي يمسكهما، لأنّ `json.dumps` يكتبهما
   بلا خطأ.
3. **انضباطُ التعارض:** طرفان أوّلان مستقلّان يعطيان 22.05% و80.29% ⇒ ⛔ لا متوسط. ومتوسطُ
   رقمَين صادقين ينتج رقماً ثالثاً **مختلَقاً** لا مرجع له.
4. **أمانةُ النسب (`H67`):** مالكُ الحزمة يجب أن يبقى Berkeley RDI. فالخطأُ كان في نصٍّ
   مُثبَّت، والتوثيقُ وحده لا يمنع عودتَه في قياسٍ لاحق.

⚠️ لا تُلمَس شجرة المستودع: كلّ كسرٍ يُكتب في `tmp_path` ويُشار إليه بإبدال ثوابت الوحدة
المستورَدة، كما في `test_decision_round04_gate.py`.
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

import check_decision_round05 as gate

STUDY = REPO_ROOT / "studies" / "algeria-hard-currency"
GATE_SCRIPT = REPO_ROOT / "scripts" / "fitness" / "check_decision_round05.py"
ARTIFACT = REPO_ROOT / "docs" / "research" / "BPIN_MEASUREMENTS.json"
CATALOG = REPO_ROOT / "docs" / "commercial" / "OFFER_CATALOG.json"
MEASURE = REPO_ROOT / "scripts" / "research" / "measure_benchmark_pin.py"
TRUTH_DOC = REPO_ROOT / ".memory" / "agent_reliability_hard_currency_truth.md"


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
    shutil.copy(STUDY / "decision_ledger_round05.csv", tmp_path / "decision_ledger_round05.csv")
    shutil.copy(STUDY / "evidence_round05.csv", tmp_path / "evidence_round05.csv")
    shutil.copy(STUDY / "DECISION-ROUND-05.md", tmp_path / "DECISION-ROUND-05.md")
    shutil.copy(ARTIFACT, tmp_path / "BPIN_MEASUREMENTS.json")
    shutil.copy(CATALOG, tmp_path / "OFFER_CATALOG.json")
    return {
        "LEDGER": tmp_path / "decision_ledger_round05.csv",
        "EVIDENCE": tmp_path / "evidence_round05.csv",
        "ROUND": tmp_path / "DECISION-ROUND-05.md",
        "ARTIFACT": tmp_path / "BPIN_MEASUREMENTS.json",
        "CATALOG": tmp_path / "OFFER_CATALOG.json",
        #: ⛔ `MEASURE` يبقى الحقيقي: البوّابةُ تستورده لتُعيد بناء الملفّ، ونسخُه إلى
        #: `tmp_path` تُدخل وحدةً ثانية بالاسم نفسه في `sys.modules` فتتسرّب بين الاختبارات.
        "SCANNED_DOCS": (
            tmp_path / "DECISION-ROUND-05.md",
            TRUTH_DOC,
            tmp_path / "evidence_round05.csv",
            tmp_path / "decision_ledger_round05.csv",
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


def _set_ledger(path: Path, hid: str, field: str, value: str) -> None:
    rows = _rows(path)
    for row in rows:
        if row["id"] == hid:
            row[field] = value
    _rewrite_csv(path, rows)


def _set_evidence(path: Path, sid: str, field: str, value: str) -> None:
    rows = _rows(path)
    for row in rows:
        if row["id"] == sid:
            row[field] = value
    _rewrite_csv(path, rows)


def _patch_artifact(path: Path, mutate) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutate(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _write_raw_artifact(path: Path, mutate) -> None:
    """يكتب **نصَّ JSON خام** — لِما لا يجوز أن يظهر في JSON أصلاً (`Infinity` · `NaN`).

    ⚠️ `json.dumps(float('inf'))` يُنتج `Infinity` و`json.loads` يقبله: فبايثون تتسامح مع ما
    ترفضه المواصفة. وهذا بالضبط سببُ الحاجة إلى مسحٍ نصّي في البوّابة لا فحصِ قيمة.
    """
    payload = json.loads(path.read_text(encoding="utf-8"))
    mutate(payload)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _edit_doc(path: Path, pattern: str, repl: str, *, count: int = 0) -> None:
    """يستبدل بنمطٍ **متسامح مع البياض** — فالتفافُ السطر في Markdown اختياري."""
    text = path.read_text(encoding="utf-8")
    new, n = re.subn(pattern, repl, text, count=count)
    assert n > 0, f"النمط لم يُطابَق: {pattern!r}"
    path.write_text(new, encoding="utf-8")


def _replace_once(path: Path, literal: str, repl: str) -> None:
    """استبدالٌ حرفيٌّ واحد — لِمَا لا يُكتب نمطاً (أقواسٌ وشرطاتٌ عربية)."""
    text = path.read_text(encoding="utf-8")
    assert literal in text, f"النصّ الحرفي غائب: {literal[:60]!r}"
    path.write_text(text.replace(literal, repl, 1), encoding="utf-8")


def _drop(path: Path, literal: str) -> None:
    _replace_once(path, literal, "")


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
    assert "جولة القرار 05 متّسقة" in result.stdout


def test_gate_reports_the_count_of_derived_figures(tmp_path: Path) -> None:
    """المخرَجُ يذكر عددَ الأرقام المطابَقة — فبوّابةٌ لا تُبلِّغ حجمَ فحصها غيرُ قابلةٍ للتدقيق."""
    code, output = _run(**_tree(tmp_path))
    assert code == 0
    assert f"{len(gate.DERIVED_FIGURES)} رقماً" in output


def test_gate_reports_the_survey_buckets_it_derives(tmp_path: Path) -> None:
    """المخرَجُ يذكر حصائلَ المسح المشتقّة — ⛔ لا أرقامَ صامتة في نجاحٍ أخضر."""
    code, output = _run(**_tree(tmp_path))
    assert code == 0
    assert "8 مُنجَزة" in output and "1 جزئية" in output and "1 معلّقة" in output


def test_every_derived_figure_path_resolves_in_the_real_artifact() -> None:
    """كلُّ مسارٍ في `DERIVED_FIGURES` موجودٌ فعلاً — ⛔ لا حارسٌ يفحص مفتاحاً غائباً.

    ⚠️ وهذا يمنع بوّابةً «خضراءَ بالفراغ»: فلو أُعيدت تسميةُ مفتاحٍ في الملفّ لسقط المسارُ
    هنا صراحةً بدل أن يسقط في `check_measurements` برسالةٍ عن وثيقةٍ لا عن عقد.
    """
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    unresolved: list[str] = []
    for dotted, *_rest in gate.DERIVED_FIGURES:
        try:
            gate.dig(payload, dotted)
        except KeyError:
            unresolved.append(dotted)
    assert unresolved == [], f"مساراتٌ لا تُحلّ في الملفّ الحقيقي: {unresolved}"


def test_every_render_spec_named_in_the_table_is_implemented() -> None:
    """⛔ صيغةٌ في الجدول بلا تنفيذٍ في `render` تُسقط البوّابة `ValueError` لا انتهاكاً."""
    specs = {spec for _d, spec, _w, _t in gate.DERIVED_FIGURES}
    for spec in specs:
        try:
            gate.render(
                1.0
                if spec.startswith(("f",))
                else "x"
                if spec in ("str", "prefix")
                else (None if spec == "none" else ([1, 2] if spec == "len" else True)),
                spec,
            )
        #: `PERF203` غيرُ مفعَّلةٍ في هذا المستودع — والتعليقُ يبقى توثيقاً لا توجيهاً.
        except ValueError as exc:
            raise AssertionError(f"صيغةٌ غير مُنفَّذة: {spec!r} ({exc})") from exc


# --------------------------------------------------------------------------- #
# 1) الاشتقاق: رقمُ §4 مقابل ملفّ القياس
# --------------------------------------------------------------------------- #
def test_hand_written_number_drifting_from_artifact_is_blocked(tmp_path: Path) -> None:
    """⛔ «5.35×» باليد بينما الملفّ يقول 5.3478 — تدويرٌ يبدو بريئاً وهو كسرُ اشتقاق."""
    paths = _tree(tmp_path)
    _edit_doc(Path(paths["ROUND"]), r"5\.3478", "5.35")
    code, output = _run(**paths)
    assert code == 1
    assert "mitigation_reduction_factor" in output


def test_artifact_number_drifting_from_document_is_blocked(tmp_path: Path) -> None:
    """الاتجاهُ الآخر: الملفّ يُعدَّل والوثيقةُ تبقى ⇒ أحمر (لا يكفي أن يكون أحدهما صحيحاً)."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"].__setitem__("mitigation_reduction_factor", 4.0),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "mitigation_reduction_factor" in output


def test_missing_artifact_path_is_an_explicit_failure_not_a_silent_skip(tmp_path: Path) -> None:
    """مسارٌ غائب في الملفّ يجب أن يُسمّى — ⛔ لا `None` يُقرأ «لا انحراف»."""
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p["results"].pop("cpst_spread_factor"))
    code, output = _run(**paths)
    assert code == 1
    assert "results.cpst_spread_factor" in output and "غائب" in output


def test_list_indexed_path_is_supported_and_validated(tmp_path: Path) -> None:
    """مسارٌ مُفهرَس في قائمة (`per_pair.1.off_target_share`) محروسٌ كغيره."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["off_target_rate"]["per_pair"][1].__setitem__(
            "off_target_share", 0.5
        ),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "per_pair.1.off_target_share" in output


def test_out_of_range_list_index_is_an_explicit_failure(tmp_path: Path) -> None:
    """دليلُ قائمةٍ خارج الحدود خطأٌ مُسمّى لا `IndexError` خام."""
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    try:
        gate.dig(payload, "results.off_target_rate.per_pair.9.off_target_share")
    except KeyError as exc:
        assert "خارج الحدود" in str(exc)
    else:  # pragma: no cover — يجب أن يرفع
        raise AssertionError("دليلٌ خارج الحدود لم يرفع KeyError")


def test_deleting_the_derived_figure_from_the_document_is_blocked(tmp_path: Path) -> None:
    """رقمٌ في الملفّ بلا مقابلٍ في النصّ رقمٌ لا يُقرأ — فحذفُه من §4 كسر."""
    paths = _tree(tmp_path)
    #: ⚠️ الرقمُ يتكرّر في §1 و§4 و§5.2: فحذفُ حدوثٍ واحد يترك الاشتقاقَ سليماً.
    _edit_doc(Path(paths["ROUND"]), r"\*\*6\.1307×\*\*", "")
    code, output = _run(**paths)
    assert code == 1
    assert "cpst_spread_factor" in output


def test_unknown_render_spec_is_an_error_not_a_silent_pass() -> None:
    """صيغةٌ غير معروفة ترفع — ⛔ لا `str()` احتياطي يُليّن العقد."""
    try:
        gate.render(1.0, "f9")
    except ValueError as exc:
        assert "صيغةُ تنسيقٍ غير معروفة" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("صيغةٌ مجهولة لم ترفع ValueError")


def test_f6s_spec_strips_trailing_zeros_as_the_artifact_does() -> None:
    """⚠️ `f6s` عقدٌ حامل: `round(x, 6)` في الملفّ يُسقط الأصفار الذيلية.

    فـ0.30531 تُحفظ كذلك، بينما `%.6f` تُنتج 0.305310 — ومطابقةٌ حرفية بالصيغة الخطأ تفشل
    على ملفٍّ صحيح. وهذا هو الفخّ الذي أسقط خمسةَ اختباراتٍ في `test_benchmark_pin.py`.
    """
    assert gate.render(0.30531, "f6s") == "0.30531"
    assert gate.render(0.186992, "f6s") == "0.186992"
    assert gate.render(0.22049, "f6s") == "0.22049"
    assert gate.render(0.652174, "f6s") == "0.652174"
    assert gate.render(1.0, "f6s") == "1"


def test_boolj_renders_json_style_because_the_document_quotes_json() -> None:
    """الوثيقةُ تكتب `= false` (JSON) لا `= False` (Python) — والصيغتان مُفرَّقتان."""
    assert gate.render(False, "boolj") == "false"
    assert gate.render(True, "boolj") == "true"
    assert gate.render(False, "bool") == "False"
    assert "⛔" in gate.render("ليس bool", "boolj")


def test_prefix_spec_checks_a_prefix_not_equality(tmp_path: Path) -> None:
    """`suite.owner` سلسلةٌ طويلة: العقدُ بادئتُها (Berkeley RDI) لا مساواتُها."""
    payload = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    assert gate.render(payload["suite"]["owner"], "prefix").startswith("Berkeley RDI")
    assert gate.render("NONE — لا إيراد", "prefix").startswith("NONE")


def test_artifact_results_must_rebuild_byte_identically(tmp_path: Path) -> None:
    """`results` على القرص يجب أن تُعاد بناؤها حرفياً من `build()`."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]), lambda p: p["results"].__setitem__("h59_verdict", "REFUTED")
    )
    code, output = _run(**paths)
    assert code == 1
    assert "لا تُعاد بناؤها حرفياً" in output


def test_volatile_timestamp_does_not_fail_the_rebuild_check(tmp_path: Path) -> None:
    """⛔ `generated_at` طابعُ وقتٍ لا مدخل — مقارنتُه تُحمِّر البوّابة كلّ ثانية."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p.__setitem__("generated_at", "1999-01-01T00:00:00+00:00"),
    )
    code, output = _run(**paths)
    assert code == 0, output


def test_suite_block_must_also_rebuild(tmp_path: Path) -> None:
    """`suite` (الاسم · الحجم · المالك · النِسبة) محروسٌ كـ`results`."""
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p["suite"].__setitem__("instances", 900))
    code, output = _run(**paths)
    assert code == 1
    assert "`suite`" in output


# --------------------------------------------------------------------------- #
# 2) حارسُ المجال — H59/H60: صفرُ UNPINNED على دبابيسَ كاملة
# --------------------------------------------------------------------------- #
def test_an_unpinned_pin_in_the_correct_domain_is_blocked(tmp_path: Path) -> None:
    """⛔ جوهرُ الجولة: `UNPINNED` في المجال الصحيح يعني أنّ **القياس** مُعيب لا الأداة."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["pin_evaluations"].__setitem__("unpinned_count", 1),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "unpinned_count" in output and "H60 فاشلة" in output


def test_a_pin_with_a_missing_field_is_blocked(tmp_path: Path) -> None:
    """حقلُّ دبوسٍ ناقص ⇒ `UNPINNED` **عادل** لا كاذب، فالبوّابة ترفض اكتمالاً مُدَّعى."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["pin_evaluations"]["per_pin"][0].__setitem__("harness", None),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "حقولٌ ناقصة" in output and "harness" in output


def test_ahws_own_missing_fields_verdict_is_trusted_over_our_recomputation(tmp_path: Path) -> None:
    """⚠️ `missing_fields` هو **حُكمُ AHW نفسه**: فلو خالفه فحصُنا لصار عندنا منطقٌ ثانٍ."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["pin_evaluations"]["per_pin"][2].__setitem__(
            "missing_fields", ["suite_version"]
        ),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "AHW تُعلن حقولاً ناقصة" in output


def test_a_pin_state_outside_the_graded_scale_is_blocked(tmp_path: Path) -> None:
    """الحالةُ يجب أن تكون من المُدرَّج — ⛔ لا `UNPINNED` ولا `None` ولا اختراعُ حالة."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["pin_evaluations"]["per_pin"][1].__setitem__(
            "pin_state", "FRESHISH"
        ),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "خارج المُدرَّج" in output


def test_a_stale_pin_marked_quotable_is_blocked(tmp_path: Path) -> None:
    """⛔ منتهيُ الصلاحية لا يُقتبس دليلاً على قدرةٍ قائمة — وإلا فالحارسُ زينة."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["pin_evaluations"]["per_pin"][0].__setitem__("quotable", True),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "quotable" in output


def test_dropping_age_governs_not_missingness_is_blocked(tmp_path: Path) -> None:
    """إن حكم النقصُ لا العمرُ فالحكمُ عن اكتمال الدبوس لا عن صلاحية الاقتباس."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["pin_evaluations"].__setitem__("age_governs_not_missingness", False),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "age_governs_not_missingness" in output


def test_dropping_all_stale_by_age_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["pin_evaluations"].__setitem__("all_stale_by_age", False),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "all_stale_by_age" in output


def test_changing_the_h59_verdict_is_blocked(tmp_path: Path) -> None:
    """⛔ الحسمُ قياسٌ لا رأي: فـ`CONFIRMED_IN_DOMAIN` نتيجةٌ لا تسمية."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["pin_evaluations"].__setitem__("h59_verdict", "REFUTED"),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "H59 لا تُحسم بالحجّة" in output


def test_dropping_the_purpose_qualifier_is_blocked(tmp_path: Path) -> None:
    """بلا `purpose_qualifier` يُقرأ `STALE` تكذيباً للرقم لا انتهاءً لصلاحية اقتباسه."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["pin_evaluations"].__setitem__("purpose_qualifier", ""),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "purpose_qualifier" in output


def test_dropping_all_pins_is_an_explicit_failure(tmp_path: Path) -> None:
    """⛔ قائمةٌ فارغة تُقرأ «لا انحراف» في بوّابةٍ أقلّ صرامة — هنا تُسمّى."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["pin_evaluations"].__setitem__("per_pin", []),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "لا حكمَ بلا دبابيس" in output


def test_a_missing_suite_level_pin_axis_is_blocked(tmp_path: Path) -> None:
    """محورا الحزمة (`suite.version` · `suite_issued_on`) يُفحصان مرّةً واحدة لا سبعاً."""
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p["suite"].pop("version"))
    code, output = _run(**paths)
    assert code == 1
    assert "suite.version" in output


def test_a_blank_suite_issue_date_is_blocked(tmp_path: Path) -> None:
    """تاريخٌ فارغ ⇒ لا عمرَ محسوباً ⇒ الدبوسُ ناقصٌ ولو امتلأت حقولُ الزوج."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["pin_evaluations"].__setitem__("suite_issued_on", ""),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "report_date" in output


def test_removing_the_stale_constraint_from_the_prose_is_blocked(tmp_path: Path) -> None:
    """⛔ القيدُ في الملفّ وحده لا يكفي: فـ122 يوماً يجب أن تُقرأ في النصّ مانعاً للاقتباس."""
    paths = _tree(tmp_path)
    #: ⚠️ العبارةُ ملفوفةٌ على سطرَين في §7 — فالمطابقةُ الحرفية تفشل على نصٍّ سليم.
    _edit_doc(Path(paths["ROUND"]), r"لا يُقتبس أيُّ رقمٍ هنا دليلاً على\s+القدرة الحالية", "")
    code, output = _run(**paths)
    assert code == 1
    assert "قيدُ `STALE`" in output


# --------------------------------------------------------------------------- #
# 3) انضباطُ صفرِ المقام — D-212: الغيابُ لا يُصفَّر ولا يُلاعَن
# --------------------------------------------------------------------------- #
def test_infinity_in_the_artifact_is_blocked_by_a_text_scan(tmp_path: Path) -> None:
    """⚠️ `json.dumps(inf)` يكتب `Infinity` و`json.loads` يقبله — فالمسحُ النصّي هو الحارس."""
    paths = _tree(tmp_path)
    _write_raw_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["safeguard_pair"].__setitem__("ratio", float("inf")),
    )
    raw = Path(paths["ARTIFACT"]).read_text(encoding="utf-8")
    assert "Infinity" in raw, "المقدّمةُ نفسها: بايثون تكتب ما ترفضه المواصفة"
    code, output = _run(**paths)
    assert code == 1
    assert "'Infinity'" in output and "D-212" in output


def test_nan_in_the_artifact_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _write_raw_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["safeguard_pair"].__setitem__("ratio", float("nan")),
    )
    assert "NaN" in Path(paths["ARTIFACT"]).read_text(encoding="utf-8")
    code, output = _run(**paths)
    assert code == 1
    assert "'NaN'" in output


def test_a_computed_ratio_where_the_denominator_is_zero_is_blocked(tmp_path: Path) -> None:
    """⛔ 0 ← 120: أيُّ رقمٍ هنا اختلاقٌ (inf؟ 0؟ 120؟) — فالصحيحُ `None`."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["safeguard_pair"].__setitem__("ratio", 120.0),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "المقامُ صفر" in output


def test_a_none_ratio_without_a_spoken_reason_is_blocked(tmp_path: Path) -> None:
    """`None` بلا سببٍ منطوق يُقرأ خطأً برمجياً لا غيابَ معلومات."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["safeguard_pair"].__setitem__("ratio_undefined_reason", ""),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "ZERO_DENOMINATOR" in output


def test_recording_the_zero_denominator_as_a_number_not_a_pair_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["safeguard_pair"].__setitem__("recorded_as", "RATIO"),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "PAIR_NOT_RATIO" in output


def test_a_nonzero_denominator_must_be_recomputed_not_kept_as_a_pair(tmp_path: Path) -> None:
    """⚠️ الحارسُ يعمل في الاتّجاهَين: لو صار المقامُ 1 فـ`None` **خطأ** لا انضباط."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["safeguard_pair"].__setitem__("successes_default_filters", 3),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "فالمقامُ لم يعد صفراً" in output


# --------------------------------------------------------------------------- #
# 4) انضباطُ التعارض — ⛔ لا متوسطَ بين طرفَين أوّليين
# --------------------------------------------------------------------------- #
def test_declaring_the_conflict_reconciled_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["unsolved_conflict"].__setitem__("reconciled", True),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "لا يُحسم بجمع" in output


def test_a_reconciliation_basis_other_than_pin_difference_is_blocked(tmp_path: Path) -> None:
    """⛔ «AVERAGE» أساسٌ يبدو معقولاً وينتج رقماً بلا مرجع."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["unsolved_conflict"].__setitem__(
            "reconciliation_basis", "ARITHMETIC_MEAN"
        ),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "PIN_DIFFERENCE_NOT_AVERAGE" in output


def test_dropping_pin_axes_below_four_is_blocked(tmp_path: Path) -> None:
    """تعارضٌ بلا تسميةِ محاوره يُقرأ غموضاً لا فرقَ دبوس."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["unsolved_conflict"].__setitem__(
            "pin_axes_that_differ", ["model_id"]
        ),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "محاورَ مختلفة" in output


def test_a_domain_sum_that_does_not_match_the_suite_total_is_blocked(tmp_path: Path) -> None:
    """⛔ 520+185+193 ≠ 898 ⇒ النسبتان مقسومتان على مقامَين مختلفَين فالتعارضُ وهمي."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["unsolved_conflict"].__setitem__(
            "domain_sum_matches_instances", False
        ),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "domain_sum_matches_instances" in output


def test_a_corrupted_spread_factor_is_recomputed_and_blocked(tmp_path: Path) -> None:
    """البوّابة تُعيد حسابَ الانتشار من النسبتَين — ⛔ لا ثقةَ عمياء بالملفّ."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["unsolved_conflict"].__setitem__("share_spread_factor", 2.0),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "share_spread_factor" in output


def test_removing_the_no_averaging_rationale_from_the_prose_is_blocked(tmp_path: Path) -> None:
    """المنعُ بلا تعليلٍ يُقرأ تحفّظاً لا قاعدة."""
    paths = _tree(tmp_path)
    _drop(Path(paths["ROUND"]), "متوسطُ طرفَين أوّليين بدبوسَين مختلفَين")
    code, output = _run(**paths)
    assert code == 1
    assert "R4" in output


def test_removing_the_no_reference_argument_is_blocked(tmp_path: Path) -> None:
    """«رقمٌ بلا مرجع» هو **السبب** لا الوصف — فحذفُه يترك منعاً بلا حجّة."""
    paths = _tree(tmp_path)
    _drop(Path(paths["ROUND"]), "رقمٌ **بلا مرجع**")
    code, output = _run(**paths)
    assert code == 1
    assert "بلا مرجع" in output


# --------------------------------------------------------------------------- #
# 5) مرساةُ CPST — D-290 L7
# --------------------------------------------------------------------------- #
def test_changing_the_cpst_unit_is_blocked(tmp_path: Path) -> None:
    """⛔ L7: المقارنةُ بـCPST لا بأجرٍ ساعيّ — والوحدةُ شرطُ المقارنة لا تفصيل."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["cpst_band"].__setitem__("unit", "USD_PER_HOUR"),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "USD_PER_SUCCESSFUL_TASK" in output


def test_dropping_the_doctrine_citation_is_blocked(tmp_path: Path) -> None:
    """رقمٌ بلا حكمٍ مذهبي يُقرأ ملاحظةً لا التزاماً."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["cpst_band"].__setitem__("doctrine_compliance", "بلا إسناد"),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "D-290 L7" in output


def test_imputing_the_undisclosed_cpst_is_blocked(tmp_path: Path) -> None:
    """⛔ استكمالُ الغائبة بمتوسط الباقي يُزيح النطاقَ للأسفل — والأقوى أداءً هو الغائب."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["cpst_band"].__setitem__("undisclosed_imputed", True),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "undisclosed_imputed" in output


def test_an_inverted_cpst_band_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["cpst_band"].__setitem__("band_usd", [22.99, 3.75]),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "band_usd" in output


def test_a_spread_factor_inconsistent_with_the_band_is_recomputed_and_blocked(
    tmp_path: Path,
) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]), lambda p: p["results"].__setitem__("cpst_spread_factor", 3.0)
    )
    code, output = _run(**paths)
    assert code == 1
    assert "cpst_spread_factor" in output


def test_dropping_the_between_alternatives_distinction_is_blocked(tmp_path: Path) -> None:
    """⚠️ الإبرةُ هي **النفي**: «بين بدائل» وحده لا يمنع الخلط، بينما النفيُ يستبعده صراحةً.

    فتشتّتُ سوق الجولة 04 (77.9778×) قُضي بأنّه بلا قيمةٍ ترتيبية لأنّه تقديراتٌ متعددة
    للكمية نفسها؛ وانتشارُ CPST بين أزواجٍ مختلفة قيمةٌ حقيقية. والخلطُ بينهما يُنتج
    ترتيباً من ضجيج.
    """
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["cpst_band"].__setitem__(
            "reading", "نطاقُ CPST المُفصَح عنه بانتشارٍ كبير."
        ),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "لا يميّز الانتشارَ" in output


# --------------------------------------------------------------------------- #
# 6) أمانةُ النسب — H67: الحزمةُ لـBerkeley RDI لا لـOpenAI
# --------------------------------------------------------------------------- #
def test_attributing_the_suite_to_openai_is_blocked(tmp_path: Path) -> None:
    """⛔ هذا هو خطأُ الجولة 04 بعينه (C1) — والحارسُ يمنع عودتَه في أيّ قياسٍ لاحق."""
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p["suite"].__setitem__("owner", "OpenAI"))
    code, output = _run(**paths)
    assert code == 1
    assert "هذا هو خطأُ الجولة 04 بعينه" in output


def test_a_suite_owner_that_is_not_berkeley_rdi_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]), lambda p: p["suite"].__setitem__("owner", "جهةٌ مجهولة")
    )
    code, output = _run(**paths)
    assert code == 1
    assert "Berkeley RDI" in output


def test_dropping_the_attribution_note_is_blocked(tmp_path: Path) -> None:
    """تصحيحٌ بلا نفيٍ صريح يُقرأ إضافةً لا تصحيحاً."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]), lambda p: p["suite"].__setitem__("attribution_note", "")
    )
    code, output = _run(**paths)
    assert code == 1
    assert "attribution_note" in output


def test_removing_the_c1_correction_from_the_prose_is_blocked(tmp_path: Path) -> None:
    """خطأٌ في نصٍّ مُثبَّت لا يُغلقه الصمت — فيجب أن يبقى التصحيحُ مرئياً."""
    paths = _tree(tmp_path)
    _drop(Path(paths["ROUND"]), "ExploitGym ليست حزامَ OpenAI")
    code, output = _run(**paths)
    assert code == 1
    assert "§3.1 C1" in output


def test_removing_the_owner_vs_operator_distinction_is_blocked(tmp_path: Path) -> None:
    """التمييزُ بين مالكِ الحزمة ومُشغِّلِ النموذج هو **جوهرُ** التصحيح لا تفصيلُه."""
    paths = _tree(tmp_path)
    _drop(Path(paths["ROUND"]), "مالكِ الحزمة")
    code, output = _run(**paths)
    assert code == 1
    assert "§3.1 C1" in output


def test_omitting_that_the_correction_raises_evidence_value_is_blocked(tmp_path: Path) -> None:
    """⛔ استقلالُ القياس عمّن يملك النموذجَ المقاس معلومةٌ، لا تفصيلٌ تجميلي."""
    paths = _tree(tmp_path)
    _drop(Path(paths["ROUND"]), "قيمة الدليل")
    code, output = _run(**paths)
    assert code == 1
    assert "يرفع" in output


# --------------------------------------------------------------------------- #
# 7) التناقضُ الداخلي D1 — يُسجَّل بلا حلّ
# --------------------------------------------------------------------------- #
def test_resolving_d1_without_reading_the_paper_is_blocked(tmp_path: Path) -> None:
    """⛔ الحسمُ بلا نصٍّ اختلاق: فالفرقُ قد يكون تعريفَ «نجاح» أو عيّنةً فرعية."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["self_contradictions"][0].__setitem__("resolved", True),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "اختلاقٌ لا استنتاج" in output


def test_a_contradiction_without_a_spoken_reason_is_blocked(tmp_path: Path) -> None:
    """تعليقٌ بلا سببٍ منطوق يُقرأ إهمالاً لا انضباطاً."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["self_contradictions"][0].__setitem__("why_unresolved", ""),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "why_unresolved" in output


def test_a_contradiction_without_declared_handling_is_blocked(tmp_path: Path) -> None:
    """⛔ التناقضُ المسجَّل بلا معالجةٍ معلَنة **يُقتبس** — فالمعالجةُ جزءٌ من السجلّ."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["self_contradictions"][0].__setitem__("handling", ""),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "handling" in output


def test_deleting_the_contradiction_record_entirely_is_blocked(tmp_path: Path) -> None:
    """حذفُ السجلّ أسوأُ من تركه معلّقاً: فيصير الجدولُ 1 والشكلُ 5 غيرَ متعارضَين صمتاً."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]), lambda p: p["results"].__setitem__("self_contradictions", [])
    )
    code, output = _run(**paths)
    assert code == 1
    assert "فارغة" in output


def test_a_single_valued_contradiction_is_blocked(tmp_path: Path) -> None:
    """تناقضٌ بقيمةٍ واحدة ليس تناقضاً."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p["results"]["self_contradictions"][0].__setitem__("values", {"table1": 157}),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "قيمتَين" in output


# --------------------------------------------------------------------------- #
# 8) إشارةُ الطلب H69 — ⛔ n=1 ليست تحقّقَ سوق
# --------------------------------------------------------------------------- #
def test_upgrading_the_practitioner_comment_to_a_primary_source_is_blocked(tmp_path: Path) -> None:
    """⛔ أخطرُ إغراءٍ في الجولة: تعليقٌ واحد يبدو «إثباتَ طلب» فيصير أساسَ رفع التزام."""
    paths = _tree(tmp_path)
    _set_evidence(Path(paths["EVIDENCE"]), "S102", "status", "P — طرفٌ أوّل يُثبت الطلب")
    code, output = _run(**paths)
    assert code == 1
    assert "S102" in output and "comment" not in output and "المتوقّع L" in output


def test_a_demand_signal_without_an_explicit_negation_is_blocked(tmp_path: Path) -> None:
    """إشارةُ طلبٍ بلا نفيٍ تُقرأ دليلاً — فالنفيُ هو ما يمنع الانزلاق."""
    paths = _tree(tmp_path)
    _set_evidence(
        Path(paths["EVIDENCE"]), "S102", "independence_note", "ممارسٌ مهتمٌّ ببناء أدواتٍ ضدّ هذا الأثر."
    )
    code, output = _run(**paths)
    assert code == 1
    assert "نفياً صريحاً" in output


def test_escalating_h69_above_e0_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H69", "max_level", "E1")
    code, output = _run(**paths)
    assert code == 1
    assert "إشارةُ طلبٍ واحدة لا ترفع التزاماً" in output


def test_marking_h69_as_held_is_blocked(tmp_path: Path) -> None:
    """⚠️ الحالةُ الصحيحة «مُنجَزة»: فالمنعُ نفسه هو المُنجَز، لا قبولُ السوق."""
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H69", "gate_state", "معلّقة على مقابلةٍ واحدة")
    _replace_once(
        Path(paths["ROUND"]),
        "| **مُنجَزة** (قياسٌ على القرص يحسمها) | **8** |",
        "| **مُنجَزة** (قياسٌ على القرص يحسمها) | **7** |",
    )
    _replace_once(
        Path(paths["ROUND"]),
        "| **معلّقة على دليل لازم** | **1** |",
        "| **معلّقة على دليل لازم** | **2** |",
    )
    code, output = _run(**paths)
    assert code == 1
    assert "المنعُ نفسه هو المُنجَز" in output


def test_h69_silently_counted_into_the_interview_card_is_blocked(tmp_path: Path) -> None:
    """⛔ الصمتُ هنا يُقرأ ضمّاً: فيجب أن تعلن H69 أنّها لا تُحتسب في `T47`."""
    paths = _tree(tmp_path)
    _set_ledger(
        Path(paths["LEDGER"]), "H69", "decision", "تُذكر الإشارةُ في أيّ عرضٍ بوصفها تعليقاً عاماً."
    )
    code, output = _run(**paths)
    assert code == 1
    assert "T47" in output


def test_dropping_the_demand_signal_row_entirely_is_blocked(tmp_path: Path) -> None:
    """حذفُ S102 يقطع الحارسَ كلّه — فالبوّابة تُسمّي الغياب لا تتجاوزه."""
    paths = _tree(tmp_path)
    rows = [r for r in _rows(Path(paths["EVIDENCE"])) if r["id"] != "S102"]
    _rewrite_csv(Path(paths["EVIDENCE"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "S102" in output


# --------------------------------------------------------------------------- #
# 9) السجلّ: المستويات والترقيم والتفريد
# --------------------------------------------------------------------------- #
def test_escalating_a_hypothesis_to_e2_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H61", "max_level", "E2")
    code, output = _run(**paths)
    assert code == 1
    assert "خارج E0/E1" in output


def test_a_second_e1_hypothesis_is_blocked(tmp_path: Path) -> None:
    """⛔ رفعُ سقفِ أكثرَ من فرضيةٍ واحدة في جولةٍ بصفرِ مقابلة تضخيمٌ لا قياس."""
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H62", "max_level", "E1")
    code, output = _run(**paths)
    assert code == 1
    assert "واحدةً" in output


def test_e1_on_the_wrong_hypothesis_is_blocked(tmp_path: Path) -> None:
    """القرارُ المعلَن في §1/§6.1 يقول `H61` — فنقلُ E1 إلى غيرها تغييرٌ في القرار."""
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H61", "max_level", "E0")
    _set_ledger(Path(paths["LEDGER"]), "H62", "max_level", "E1")
    code, output = _run(**paths)
    assert code == 1
    assert "H61" in output


def test_an_e1_hypothesis_marked_completed_is_contradictory_and_blocked(tmp_path: Path) -> None:
    """⛔ ما أُنجِز لا ينتظر قبولاً، وما ينتظر قبولاً لم يُنجَز."""
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H61", "gate_state", "مُنجَزة: قبولُ المشترى محسوم")
    code, output = _run(**paths)
    assert code == 1
    assert "تناقض" in output


def test_breaking_hypothesis_id_continuity_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["LEDGER"]))
    rows[3]["id"] = "H63b"
    _rewrite_csv(Path(paths["LEDGER"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "غير فريدة" in output or "اتّصالاً" in output


def test_reusing_a_claim_id_from_round04_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H60", "key_claim", "C56")
    code, output = _run(**paths)
    assert code == 1
    assert "الجولة 04" in output


def test_reusing_a_card_id_from_round04_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H60", "key_test", "T54")
    code, output = _run(**paths)
    assert code == 1
    assert "الجولة 04" in output


def test_non_contiguous_claim_ids_are_blocked(tmp_path: Path) -> None:
    """⛔ القفزُ في الترقيم يترك ادّعاءً بلا مرجعٍ في أيّ سجل."""
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H63", "key_claim", "C99")
    code, output = _run(**paths)
    assert code == 1
    assert "غيرُ متّصلة" in output


def test_malformed_claim_or_test_id_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H65", "key_claim", "C-61")
    code, output = _run(**paths)
    assert code == 1
    assert "خارج الصيغة" in output


def test_dropping_the_shared_dependency_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H61", "shared_dependency", "")
    code, output = _run(**paths)
    assert code == 1
    assert "اعتماد مشترك" in output


def test_an_unclassifiable_gate_state_is_blocked(tmp_path: Path) -> None:
    """⛔ الحالةُ المعلَنة يجب أن تبدأ بأحد التصريحات الخمسة في §6.1."""
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H64", "gate_state", "قيد الدراسة")
    code, output = _run(**paths)
    assert code == 1
    assert "لا تُصنَّف" in output


def test_dropping_a_counterparty_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H65", "counterparty", "")
    code, output = _run(**paths)
    assert code == 1
    assert "بلا طرفٍ مقابل" in output


def test_bucket_state_checks_partial_before_completed() -> None:
    """⚠️ الترتيبُ عقديٌّ: «مُنجَزة جزئياً» **قبل** «مُنجَزة».

    فلو فُحص الأعمُّ أولاً لابتلع الجزئيَّ وصارت `H62` مُنجَزةً وهي ليست كذلك — ولمرّت
    البوّابةُ على سجلٍّ يُبالغ في الإنجاز.
    """
    assert gate.bucket_state("مُنجَزة جزئياً: مرساةٌ موجودة") == "partial"
    assert gate.bucket_state("مُنجَزة: صفرُ UNPINNED") == "completed"
    assert gate.bucket_state("معلّقة على دليل لازم: صفرُ مقابلة") == "held"
    assert gate.bucket_state("فاشلة في التكوين الحالي") == "failed"
    assert gate.bucket_state("غير مفحوصة: بلا طرفٍ مقابل") == "untested"
    assert gate.bucket_state("قيد الدراسة") == "other"


def test_the_partial_bucket_is_derived_from_the_ledger_not_the_prose(tmp_path: Path) -> None:
    """قلبُ `H62` من جزئيةٍ إلى مُنجَزة **مع** تحديث §6.1 يجب أن يمرّ — فالتصنيفُ من السجلّ.

    ⚠️ اختبارٌ موجبٌ وسط سلبية: فلو مرّ الكسرُ السابق (بلا تحديث §6.1) ومرّ هذا أيضاً،
    لكان الفحصُ يقرأ الوثيقة لا السجلّ. ونجاحُ هذا وحده يثبت أنّ المصدر هو السجلّ.
    """
    paths = _tree(tmp_path)
    _set_ledger(Path(paths["LEDGER"]), "H62", "gate_state", "مُنجَزة: مرساةُ CPST على القرص")
    _replace_once(
        Path(paths["ROUND"]),
        "| **مُنجَزة** (قياسٌ على القرص يحسمها) | **8** |",
        "| **مُنجَزة** (قياسٌ على القرص يحسمها) | **9** |",
    )
    _replace_once(
        Path(paths["ROUND"]), "| **مُنجَزة جزئياً** | **1** |", "| **مُنجَزة جزئياً** | **0** |"
    )
    code, output = _run(**paths)
    assert code == 0, output


# --------------------------------------------------------------------------- #
# 10) §6.1: الأعدادُ المعلَنة يجب أن تُشتقّ لا أن تُكتب
# --------------------------------------------------------------------------- #
def test_a_hand_written_completed_count_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _replace_once(
        Path(paths["ROUND"]),
        "| **مُنجَزة** (قياسٌ على القرص يحسمها) | **8** |",
        "| **مُنجَزة** (قياسٌ على القرص يحسمها) | **10** |",
    )
    code, output = _run(**paths)
    assert code == 1
    assert "ليس اشتقاقاً" in output


def test_a_hand_written_held_count_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _replace_once(
        Path(paths["ROUND"]),
        "| **معلّقة على دليل لازم** | **1** |",
        "| **معلّقة على دليل لازم** | **0** |",
    )
    code, output = _run(**paths)
    assert code == 1
    assert "معلّقة على دليل لازم" in output


def test_a_hand_written_e1_count_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _replace_once(
        Path(paths["ROUND"]),
        "| **سقفٌ أقصى مسموح = E1** | **1** |",
        "| **سقفٌ أقصى مسموح = E1** | **3** |",
    )
    code, output = _run(**paths)
    assert code == 1
    assert "عددُ E1" in output


def test_declaring_any_hypothesis_e2_eligible_is_blocked(tmp_path: Path) -> None:
    """⛔ لا سقف خسارة معتمداً ولا مرساةَ فاتورة ⇒ ولا واحدةَ تبلغ E2."""
    paths = _tree(tmp_path)
    _replace_once(
        Path(paths["ROUND"]),
        "| **مؤهَّلة نظرياً لـE2 عند تفويض** | **0** |",
        "| **مؤهَّلة نظرياً لـE2 عند تفويض** | **1** |",
    )
    code, output = _run(**paths)
    assert code == 1
    assert "E2" in output


def test_deleting_a_survey_row_is_blocked(tmp_path: Path) -> None:
    """صفٌّ محذوفٌ من §6.1 إخفاءٌ لا اختصار — فالبوّابة تُسمّيه."""
    paths = _tree(tmp_path)
    _drop(
        Path(paths["ROUND"]),
        "| **مُنجَزة جزئياً** | **1** | `H62` (مرساةٌ موجودة، ومرساةُ الفاتورة غائبة) |",
    )
    code, output = _run(**paths)
    assert code == 1
    assert "لا صفَّ معلن" in output


def test_a_survey_total_that_does_not_add_up_is_blocked(tmp_path: Path) -> None:
    """⛔ 8+1+1 = 10: فلو سقط صفٌّ أو أُضيف لصار المجموعُ غيرَ عددِ الفرضيات."""
    paths = _tree(tmp_path)
    rows = [r for r in _rows(Path(paths["LEDGER"])) if r["id"] != "H68"]
    _rewrite_csv(Path(paths["LEDGER"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "مجموعُ حصائل المسح" in output or "اتّصالاً" in output


# --------------------------------------------------------------------------- #
# 11) سجلّ الأدلّة: النطاق والدرجات والتواريخ
# --------------------------------------------------------------------------- #
def test_breaking_evidence_id_continuity_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["EVIDENCE"]))
    rows[0]["id"] = "S105"
    _rewrite_csv(Path(paths["EVIDENCE"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "اتّصالاً" in output


def test_dropping_an_evidence_row_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    rows = [r for r in _rows(Path(paths["EVIDENCE"])) if r["id"] != "S103"]
    _rewrite_csv(Path(paths["EVIDENCE"]), rows)
    code, output = _run(**paths)
    assert code == 1
    assert "سنداً" in output


def test_a_source_grade_outside_the_convention_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _set_evidence(Path(paths["EVIDENCE"]), "S99", "status", "مصدرٌ جيد")
    code, output = _run(**paths)
    assert code == 1
    assert "خارج العُرف" in output


def test_a_missing_as_of_date_is_blocked(tmp_path: Path) -> None:
    """T43 يلزم تاريخاً لكلّ صفّ — فدليلٌ بلا تاريخٍ بلا انتهاء."""
    paths = _tree(tmp_path)
    _set_evidence(Path(paths["EVIDENCE"]), "S96", "as_of", "مايو 2026")
    code, output = _run(**paths)
    assert code == 1
    assert "T43" in output


def test_a_note_where_a_url_should_be_is_blocked(tmp_path: Path) -> None:
    """⛔ حاشيةٌ مكان الرابط تُقرأ إسناداً."""
    paths = _tree(tmp_path)
    _set_evidence(Path(paths["EVIDENCE"]), "S97", "url", "بلا رابط")
    code, output = _run(**paths)
    assert code == 1
    assert "ليس رابطاً" in output


def test_an_unstated_row_carrying_a_url_is_blocked(tmp_path: Path) -> None:
    """الوسمُ يناقض السند — فإمّا غيابٌ مُعلَن أو رابطٌ حقيقي."""
    paths = _tree(tmp_path)
    _set_evidence(Path(paths["EVIDENCE"]), "S101", "status", "UNSTATED — لم يُتحقّق")
    code, output = _run(**paths)
    assert code == 1
    assert "يناقض السند" in output


def test_dropping_the_independence_note_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _set_evidence(Path(paths["EVIDENCE"]), "S96", "independence_note", "")
    code, output = _run(**paths)
    assert code == 1
    assert "ملاحظةِ استقلال" in output


def test_dropping_the_reverification_trigger_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _set_evidence(Path(paths["EVIDENCE"]), "S98", "reverification_trigger", "")
    code, output = _run(**paths)
    assert code == 1
    assert "محفّزِ إعادة تحقّق" in output


def test_inventing_a_new_evidence_schema_is_blocked(tmp_path: Path) -> None:
    """⛔ عُرفُ الأعمدة موروثٌ من الجولتين 02/04 — فلا اختراعَ مخطّطٍ في الجولة 05."""
    paths = _tree(tmp_path)
    rows = _rows(Path(paths["EVIDENCE"]))
    with Path(paths["EVIDENCE"]).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["id", "claim", "url"])
        writer.writeheader()
        for row in rows:
            writer.writerow({"id": row["id"], "claim": row["claim_summary_ar"], "url": row["url"]})
    code, output = _run(**paths)
    assert code == 1
    assert "أعمدةُ سجلّ الأدلّة" in output


# --------------------------------------------------------------------------- #
# 12) الأصفار: في الملفّ وفي النصّ معاً (L9)
# --------------------------------------------------------------------------- #
def test_claiming_a_model_run_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p.__setitem__("model_runs_executed", 7))
    code, output = _run(**paths)
    assert code == 1
    assert "model_runs_executed" in output


def test_claiming_a_client_measurement_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p.__setitem__("client_measurements", 1))
    code, output = _run(**paths)
    assert code == 1
    assert "client_measurements" in output


def test_claiming_a_reproduced_exploit_is_blocked(tmp_path: Path) -> None:
    """⛔ الحدُّ الأخلاقيّ: إعادةُ إنتاج نواقل الحادثة ممنوعةٌ في التكوين الحالي."""
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p.__setitem__("exploits_reproduced", 2))
    code, output = _run(**paths)
    assert code == 1
    assert "exploits_reproduced" in output


def test_claiming_exploit_code_is_present_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(Path(paths["ARTIFACT"]), lambda p: p.__setitem__("exploit_code_present", True))
    code, output = _run(**paths)
    assert code == 1
    assert "exploit_code_present" in output


def test_zero_counters_must_also_be_declared_in_the_prose(tmp_path: Path) -> None:
    """⛔ صفرٌ في الملفّ وحده لا يكفي: فالنصّ هو ما يُقرأ ويُقتبس."""
    paths = _tree(tmp_path)
    #: ⚠️ مرّتان (الترويسة و§6.2 G4): فالبوّابةُ تبحث عن الصيغة بلا أقواسٍ أيضاً.
    _edit_doc(Path(paths["ROUND"]), r"exploits_reproduced = 0", "")
    code, output = _run(**paths)
    assert code == 1
    assert "غيرُ مُعلَن في وثيقة الجولة" in output


def test_claiming_revenue_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p.__setitem__("revenue_claim", "USD 12,000 متوقّعة في الربع الثالث"),
    )
    code, output = _run(**paths)
    assert code == 1
    assert "revenue_claim" in output


def test_revenue_claim_may_carry_an_arabic_explanation(tmp_path: Path) -> None:
    """العقدُ بادئةُ `NONE` لا مساواة — فشرحٌ عربيٌّ بعد NONE مقبول."""
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]),
        lambda p: p.__setitem__("revenue_claim", "NONE — صفرُ عميل وصفرُ فاتورة"),
    )
    code, output = _run(**paths)
    assert code == 0, output


def test_dropping_the_no_cash_spend_phrase_is_blocked(tmp_path: Path) -> None:
    """⛔ لا توصيةَ بإنفاقٍ بلا سقف — والعبارةُ شرطٌ لا زخرف."""
    paths = _tree(tmp_path)
    _drop(Path(paths["ROUND"]), "بلا إنفاقٍ نقدي")
    code, output = _run(**paths)
    assert code == 1
    assert "بلا إنفاقٍ نقدي" in output


def test_dropping_the_no_pricing_statement_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _drop(Path(paths["ROUND"]), "⛔ لا تسعيرَ ولا رقمَ إيراد")
    code, output = _run(**paths)
    assert code == 1
    assert "L6 · L3" in output


def test_dropping_the_no_eighth_offer_line_statement_is_blocked(tmp_path: Path) -> None:
    """⛔ L6: لا خطَّ ثامنَ بلا قرار حوكمة — وجولةُ بحثٍ ليست قرارَ حوكمة."""
    paths = _tree(tmp_path)
    _drop(Path(paths["ROUND"]), "⛔ لا خطَّ ثامن")
    code, output = _run(**paths)
    assert code == 1
    assert "L6 · L3" in output


def test_a_duplicate_offer_id_is_blocked(tmp_path: Path) -> None:
    """بعد D-296 لا حصرَ عددياً (D-297 أزال عدّ السبعة من هذا الفارض) — لكنّ مُعرِّفاً مكرَّراً يُحجب."""
    paths = _tree(tmp_path)
    catalog = json.loads(Path(paths["CATALOG"]).read_text(encoding="utf-8"))
    key = "offer_lines" if "offer_lines" in catalog else "offers"
    catalog[key].append({"id": catalog[key][0]["id"], "status": "PROPOSED"})
    Path(paths["CATALOG"]).write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    code, output = _run(**paths)
    assert code == 1
    assert "مكرَّر" in output


# --------------------------------------------------------------------------- #
# 13) شيفرةُ الاستغلال وسلسلةُ التقنيات — ⚔️ الحدُّ الأخلاقيّ
# --------------------------------------------------------------------------- #
def test_exploit_primitive_in_the_artifact_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _patch_artifact(
        Path(paths["ARTIFACT"]), lambda p: p["boundaries"].append("نُسخ `__reduce__` للاستعمال")
    )
    code, output = _run(**paths)
    assert code == 1
    assert "__reduce__" in output


def test_exploit_technique_chain_in_the_document_is_blocked(tmp_path: Path) -> None:
    """⛔ سلسلةُ تقنيات V8/kernel المُعلَنة في المصدر لا تُنسخ في أيّ نصٍّ لنا (§6.3)."""
    paths = _tree(tmp_path)
    with Path(paths["ROUND"]).open("a", encoding="utf-8") as handle:
        handle.write("\nالخطواتُ: OOB read ثمّ pointer leak ثمّ fake string ثمّ SROP.\n")
    code, output = _run(**paths)
    assert code == 1
    assert "نمطُ استغلالٍ" in output


def test_shellcode_and_use_after_free_are_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    with Path(paths["EVIDENCE"]).open("a", encoding="utf-8") as handle:
        handle.write("\nملاحظةٌ عن shellcode و use-after-free و heap spray.\n")
    code, output = _run(**paths)
    assert code == 1
    assert "نمطُ استغلالٍ" in output


def test_metadata_server_access_in_the_document_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    with Path(paths["ROUND"]).open("a", encoding="utf-8") as handle:
        handle.write("\nالوصولُ إلى 169.254.169.254 كان الخطوةَ الأولى.\n")
    code, output = _run(**paths)
    assert code == 1
    assert "169" in output


def test_defensive_control_names_are_allowed(tmp_path: Path) -> None:
    """⚠️ اختبارٌ موجبٌ وسط السلبية: فاسمُ **الدفاع** معلومةٌ تنظيمية لا ناقلُ هجوم.

    ولو مُنعت أسماءُ الحمايات (ASLR · KASLR · canaries · heap sandbox) لصارت الجولةُ عاجزةً
    عن قياس أثرِ الحمايات — وهو بالضبط ما تقيسه (`H61` · 369 ← 69).
    """
    paths = _tree(tmp_path)
    with Path(paths["ROUND"]).open("a", encoding="utf-8") as handle:
        handle.write("\nالحماياتُ المقاسة: ASLR وKASLR وstack canaries وV8 heap sandbox.\n")
    code, output = _run(**paths)
    assert code == 0, output


def test_the_artifact_fields_agree_with_the_text_scan(tmp_path: Path) -> None:
    """⛔ حقلٌّ يقول «صفرُ استغلال» ونصٌّ يحوي شيفرةَ استغلال ⇒ تناقضٌ يُسمّى مرّتَين."""
    paths = _tree(tmp_path)
    with Path(paths["ROUND"]).open("a", encoding="utf-8") as handle:
        handle.write("\nreverse_shell مُستنسخ.\n")
    code, output = _run(**paths)
    assert code == 1
    assert "reverse_shell" in output


# --------------------------------------------------------------------------- #
# 14) المحرّمات: الادّعاءاتُ المدحوضة لا تعود إلى النصوص
# --------------------------------------------------------------------------- #
def test_refuted_mitigation_claim_outside_negation_is_blocked(tmp_path: Path) -> None:
    """⛔ R1: العبارةُ العامة صادقةٌ إجمالاً وخاطئةٌ تفصيلاً — فلا تعود بيعيةً عامة."""
    paths = _tree(tmp_path)
    with Path(paths["ROUND"]).open("a", encoding="utf-8") as handle:
        handle.write("\nوخلاصتُنا أنّ الحماياتُ القياسية لا تكفي لأيّ مؤسسة.\n")
    code, output = _run(**paths)
    assert code == 1
    assert "الحماياتُ القياسية لا تكفي" in output


def test_refuted_claim_inside_explicit_negation_is_allowed(tmp_path: Path) -> None:
    """المنعُ الصريح سياقٌ مشروع — فالبوّابة تمنع الاقتباس لا الذكر."""
    paths = _tree(tmp_path)
    with Path(paths["ROUND"]).open("a", encoding="utf-8") as handle:
        handle.write("\n⛔ ممنوعٌ قولُ «الحماياتُ القياسية لا تكفي» عبارَةً بيعيةً عامة.\n")
    code, output = _run(**paths)
    assert code == 0, output


def test_refuted_averaging_claim_outside_negation_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    with Path(paths["ROUND"]).open("a", encoding="utf-8") as handle:
        handle.write("\nواعتمدنا متوسطُ النسبتَين تقديراً أدقّ.\n")
    code, output = _run(**paths)
    assert code == 1
    assert "متوسطُ النسبتَين" in output


def test_refuted_offensive_capability_claim_outside_negation_is_blocked(tmp_path: Path) -> None:
    """⛔ R8: رقمُ قدرةٍ هجومية لطرفٍ ثالث لا يُستعمل في عرضٍ دفاعي لنا."""
    paths = _tree(tmp_path)
    with Path(paths["EVIDENCE"]).open("a", encoding="utf-8") as handle:
        handle.write("\nفرصتُنا: 34 ثغرة يوم-صفر اكتُشفت بالحزمة السابقة.\n")
    code, output = _run(**paths)
    assert code == 1
    assert "34 ثغرة يوم-صفر" in output


def test_a_pricing_claim_derived_from_third_party_cpst_is_blocked(tmp_path: Path) -> None:
    """⛔ R2: CPST المنشورة كلفةُ تشغيلِ وكيلٍ على حزمةٍ هجومية، لا سعرُ خدمةٍ دفاعية."""
    paths = _tree(tmp_path)
    with Path(paths["ROUND"]).open("a", encoding="utf-8") as handle:
        handle.write("\nوبما أنّ النطاقَ [3.75، 22.99] فهذا سعرُ خدمتنا.\n")
    code, output = _run(**paths)
    assert code == 1
    assert "هذا سعرُ خدمتنا" in output


def test_an_inherited_round03_refutation_is_still_guarded(tmp_path: Path) -> None:
    """⛔ دحضُ الجولة 03 يبقى نافذاً في نصوص الجولة 05 — فالجولةُ الجديدة لا تُبيح القديم."""
    paths = _tree(tmp_path)
    with Path(paths["ROUND"]).open("a", encoding="utf-8") as handle:
        handle.write("\nالمعدّلُ السوقي 143 دولار/ساعة.\n")
    code, output = _run(**paths)
    assert code == 1
    assert "143 دولار/ساعة" in output


def test_the_ledger_csv_is_scanned_for_refuted_claims_too(tmp_path: Path) -> None:
    """⛔ سجلٌّ CSV نصٌّ يُقتبس — فمسحُه لازم لا اختياري.

    ⚠️ `H60` لا `H61`: فالمسحُ يعمل على **السطر كلّه** (كلّ الأعمدة)، وصفُّ `H61` يحمل ⛔ في
    عمود قراره فيُعفى عبارةً مدحوضةً فيه. وهذا ليس عيباً بل هو العقد: السياقُ سطرٌ، فالعبارةُ
    المدحوضة تُختبر في صفٍّ نظيف.
    """
    paths = _tree(tmp_path)
    _set_ledger(
        Path(paths["LEDGER"]), "H60", "hypothesis_ar", "الحماياتُ القياسية لا تكفي لأيّ مؤسسة"
    )
    code, output = _run(**paths)
    assert code == 1
    assert "decision_ledger_round05.csv" in output


def test_a_proven_verdict_row_is_exempt_from_the_negation_requirement(tmp_path: Path) -> None:
    """⚠️ صفوفُ الحكم المُثبت (`**مُثبتة**`) ليست ادّعاءات — فاستثناؤها يمنع إيجاباً كاذباً."""
    paths = _tree(tmp_path)
    with Path(paths["ROUND"]).open("a", encoding="utf-8") as handle:
        handle.write("\n| الحماياتُ القياسية لا تكفي | **مُثبتة** |\n")
    code, output = _run(**paths)
    assert code == 0, output


# --------------------------------------------------------------------------- #
# 15) مسارُ القياس: stdlib فقط وبلا شبكة
# --------------------------------------------------------------------------- #
def test_a_third_party_import_in_the_measure_script_is_blocked(tmp_path: Path) -> None:
    """⛔ بوّابةٌ تستورد ما تقيسه يجب أن تثق بمدخلاته — فـ`requests` كسرٌ للموضوع."""
    copy = tmp_path / "measure_benchmark_pin.py"
    copy.write_text(MEASURE.read_text(encoding="utf-8") + "\nimport requests\n", encoding="utf-8")
    failures: list[str] = []
    saved, gate.MEASURE = gate.MEASURE, copy
    try:
        gate.check_measure_is_stdlib_only(failures)
    finally:
        gate.MEASURE = saved
    assert any("خارج المكتبة القياسية" in f and "requests" in f for f in failures), failures


def test_a_network_call_in_the_measure_script_is_blocked(tmp_path: Path) -> None:
    copy = tmp_path / "measure_benchmark_pin.py"
    copy.write_text(
        MEASURE.read_text(encoding="utf-8") + "\n# urllib.request.urlopen(url)\n", encoding="utf-8"
    )
    failures: list[str] = []
    saved, gate.MEASURE = gate.MEASURE, copy
    try:
        gate.check_measure_is_stdlib_only(failures)
    finally:
        gate.MEASURE = saved
    assert any("urllib" in f for f in failures), failures


def test_dynamic_execution_in_the_measure_script_is_blocked(tmp_path: Path) -> None:
    """⛔ `eval`/`exec`/`__import__` تُبطل حتميةَ القياس وتفحصُه AST لا فرزٌ نصّي."""
    copy = tmp_path / "measure_benchmark_pin.py"
    copy.write_text(MEASURE.read_text(encoding="utf-8") + "\nX = eval('1+1')\n", encoding="utf-8")
    failures: list[str] = []
    saved, gate.MEASURE = gate.MEASURE, copy
    try:
        gate.check_measure_is_stdlib_only(failures)
    finally:
        gate.MEASURE = saved
    assert any("تنفيذٌ ديناميكي" in f for f in failures), failures


def test_future_and_repo_local_imports_are_allowed(tmp_path: Path) -> None:
    """⚠️ اختبارٌ موجب: `__future__` جزءٌ من اللغة، و`shared` وحدةُ المستودع نفسها.

    فإعادةُ استعمال `evaluate_pin` هي **جوهرُ `H60`** — ومنعُها يمنع الحسمَ لا يحميه.
    """
    failures: list[str] = []
    gate.check_measure_is_stdlib_only(failures)
    assert failures == [], failures


# --------------------------------------------------------------------------- #
# 16) بنيةُ الوثيقة
# --------------------------------------------------------------------------- #
def test_dropping_a_required_section_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _edit_doc(Path(paths["ROUND"]), r"## 5\. المعرفة الجديدة", "## 5. ملاحظات")
    code, output = _run(**paths)
    assert code == 1
    assert "قسمٌ إلزامي غائب" in output


def test_dropping_the_self_correction_subsection_is_blocked(tmp_path: Path) -> None:
    """⛔ §3.1 (تصحيحاتٌ في عملنا نحن) إلزامية: فالتصحيحُ لا يُدمج في الدحض ويُخفى."""
    paths = _tree(tmp_path)
    _edit_doc(Path(paths["ROUND"]), r"### 3\.1 تصحيحاتٌ في عملنا نحن", "### 3.1 ملاحظات")
    code, output = _run(**paths)
    assert code == 1
    assert "قسمٌ إلزامي غائب" in output


def test_dropping_a_next_step_card_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _drop(Path(paths["ROUND"]), "**T61**")
    code, output = _run(**paths)
    assert code == 1
    assert "T61" in output


def test_every_card_in_the_declared_range_is_required(tmp_path: Path) -> None:
    """⛔ T55–T64 كلّها معاييرُ خروج، لا قائمةٌ تُختصر."""
    paths = _tree(tmp_path)
    for card in range(*gate.CARD_RANGE):
        assert f"**T{card}**" in Path(paths["ROUND"]).read_text(encoding="utf-8"), f"T{card} غائبة"


def test_an_overlong_decision_page_is_blocked(tmp_path: Path) -> None:
    """محرك §3: صفحةُ القرار ≤250 كلمة — فالقرارُ الذي لا يُقرأ لا يُتَّخذ."""
    paths = _tree(tmp_path)
    _replace_once(
        Path(paths["ROUND"]),
        "## 1. صفحة القرار (≤250 كلمة)\n",
        "## 1. صفحة القرار (≤250 كلمة)\n" + "كلمةٌ حشوٌ " * 40 + "\n",
    )
    code, output = _run(**paths)
    assert code == 1
    assert "صفحةُ القرار" in output


def test_the_real_decision_page_is_within_the_ceiling() -> None:
    """⚠️ السقفُ المطبَّق هو المعلن — ⛔ لا سقفٌ أوسعُ في الكود ورسالةٌ تقول غيره."""
    text = (STUDY / "DECISION-ROUND-05.md").read_text(encoding="utf-8")
    section = text.split("## 1. صفحة القرار", 1)[-1].split("## 2. عقد القرار", 1)[0]
    words = len(re.findall(r"[\w\u0600-\u06FF]+", re.sub(r"[*`>|#_⛔]", " ", section)))
    assert gate.DECISION_PAGE_WORD_CEILING == 250, "السقفُ المعلَن تغيّر في الكود"
    assert words <= 250, f"صفحةُ القرار {words} كلمة"
    #: وهامشٌ معقول: فصفحةٌ عند 249 كلمة ليست «محكومة» بل على الحافّة.
    assert words >= 120, f"صفحةُ القرار {words} كلمة — قصيرةٌ بحيث لا تحمل القرار"


def test_dropping_a_declared_alternative_is_blocked(tmp_path: Path) -> None:
    """محرك §4: القرارُ بلا بدائله المُثبَّتة ليس قراراً."""
    paths = _tree(tmp_path)
    _drop(Path(paths["ROUND"]), "أفضلُ استخدامٍ بديلٌ للموارد")
    code, output = _run(**paths)
    assert code == 1
    assert "البديلُ المُثبَّت" in output


def test_dropping_the_do_nothing_alternative_is_blocked(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    _drop(Path(paths["ROUND"]), "عدمُ التنفيذ")
    code, output = _run(**paths)
    assert code == 1
    assert "البديلُ المُثبَّت" in output


def test_silence_must_be_a_recorded_outcome_not_a_gap(tmp_path: Path) -> None:
    """⛔ معيارُ نهاية الجولة يجب أن يجعل الصمتَ نتيجةً موثّقة لا فراغاً."""
    paths = _tree(tmp_path)
    _edit_doc(Path(paths["ROUND"]), r"صمتٌ موثَّق", "")  # ⚠️ مرّتان في §8: فالحذفُ يجب أن يشملهما
    code, output = _run(**paths)
    assert code == 1
    assert "الصمتَ نتيجةً" in output


# --------------------------------------------------------------------------- #
# 17) وجودُ الملفّات اللازمة
# --------------------------------------------------------------------------- #
def test_a_missing_artifact_is_an_explicit_failure(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    Path(paths["ARTIFACT"]).unlink()
    code, output = _run(**paths)
    assert code == 1
    assert "ملفٌّ لازمٌ غائب" in output


def test_a_missing_ledger_is_an_explicit_failure(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    Path(paths["LEDGER"]).unlink()
    code, output = _run(**paths)
    assert code == 1
    assert "ملفٌّ لازمٌ غائب" in output


def test_a_missing_measure_script_is_an_explicit_failure(tmp_path: Path) -> None:
    paths = _tree(tmp_path)
    paths["MEASURE"] = tmp_path / "does_not_exist.py"
    code, output = _run(**paths)
    assert code == 1
    assert "ملفٌّ لازمٌ غائب" in output


def test_the_measure_script_check_mode_still_passes() -> None:
    """⛔ البوّابةُ وملفُّ القياس يجب أن يتّفقا — فـ`--check` هو الحارسُ الأسرع."""
    result = subprocess.run(
        [sys.executable, str(MEASURE), "--check"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
