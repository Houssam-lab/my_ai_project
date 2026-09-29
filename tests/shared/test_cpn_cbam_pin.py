"""اختباراتُ دبوس CBAM — CPN (الدفعة الثانية عشرة).

تُثبِت خمسةَ أشياء:

1. **الدبوسُ منقولٌ لا مُختَرع** — كلّ قيمةٍ بلدِيّةٍ ومرجعٍ مُثبَّتةٌ بحرفها من
   ملفَّي المفوضية، والحارسُ `self_check()` يسقط لو حُرِّف رقمٌ واحد.
2. **معاملُ CBAM مضروبٌ في المرجع لا في الانبعاث** — الاتجاهُ يهبط من 0.975 إلى 0،
   وبرهانُ K3 السلبيّ يسقط لو قُلِب.
3. **الفراغُ `None` لا صفر** — الألومنيوم غيرُ مستخرج، و`7208` غيرُ مستخرج، وسعرُ
   الربع الثالث غيرُ منشور، و`31025000` مساره غامض: أربعةُ أصنافِ غيابٍ مختلفة
   الأسباب، وكلُّ طلبٍ لها يرفع `UnpinnedError` ولا يُرجِع صفراً.
4. **العتبةُ معلومةٌ والقرارُ للمشتري** — `crossover_see` و`unconditional_year`
   ⛔ لا يستعملان `CANDIDATE_SEE` إطلاقاً؛ وهذا مُختبَر بمسحِ المصدر لا بالنية.
5. **شروطُ القتل قادرةٌ على الإطلاق** — لكلٍّ من K1–K5 برهانٌ سلبيٌّ هنا.

وبرهانٌ سادسٌ على القرص لا على الأداة: **الحسابُ المسحوب ما زال يُحسَب في
مصدرَيه** (`cbam_value.py` و`markup_gradient.py`)، عمداً — عرف RCL: السحبُ يُسجَّل
في سجلِّه ولا يُنشَر إلى مصادر الأرقام إلا بقرارٍ مكتوب.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from shared.research.cbam_pin import (
    ALGERIA_DEFAULTS,
    AS_OF,
    BATCH,
    BENCHMARKS,
    CANDIDATE_SEE,
    CBAM_FACTOR,
    CERT_PRICE_EUR,
    CSCF,
    HORIZON,
    MARKUP,
    SOURCES,
    PinError,
    UnpinnedError,
    Verdict,
    benchmark_resolution,
    certificates_actual,
    certificates_default,
    closure_audit,
    column_asymmetry,
    crossover_see,
    cscf_sensitivity,
    default_route,
    error_identity,
    first_sellable_year,
    inputs_fingerprint,
    kill_switches,
    markup_relief,
    measure_all,
    net_required_reduction,
    overstatement,
    path_toll,
    pinned_codes,
    saving,
    self_check,
    unconditional_year,
)

TOOL = REPO_ROOT / "shared" / "research" / "cbam_pin.py"
MEASUREMENTS = REPO_ROOT / "docs" / "research" / "CPN_MEASUREMENTS.json"
LEGACY_VALUE = REPO_ROOT / "research" / "fx-hard-currency" / "cbam_value.py"
LEGACY_GRADIENT = REPO_ROOT / "studies" / "cbam-markup-gradient-002" / "markup_gradient.py"


# ── الهويةُ المجمَّدة ────────────────────────────────────────────────────────────


def test_frozen_identity() -> None:
    """رقمُ الدفعة وتاريخُ التجميد ثابتان — لا يُقرآن من الساعة."""
    assert BATCH == "CPN-12"
    assert AS_OF == "2026-09-15"


def test_batch_number_follows_rcl() -> None:
    """RCL كانت الحادية عشرة على القرص — وهذه الثانية عشرة، لا حادية عشرة ثانية."""
    rcl = json.loads((REPO_ROOT / "docs" / "research" / "RCL_MEASUREMENTS.json").read_text("utf-8"))
    assert rcl["batch"] == "RCL-11"
    assert BATCH.endswith("-12")


def test_stdlib_only() -> None:
    """لا استيراد من app/ ولا microservices/ — تُشحَن إلى عميلٍ بلا تبعياتنا."""
    source = TOOL.read_text(encoding="utf-8")
    for banned in ("from app", "import app", "from microservices", "import requests", "openai"):
        assert banned not in source, banned


def test_horizon_stops_where_the_formula_changes() -> None:
    """2034 آخرُ الأفق: من 2034 «لا ينطبق معامل CBAM» (S3) ⇒ الاستمرارُ تخمين."""
    assert tuple(range(2026, 2035)) == HORIZON
    assert CBAM_FACTOR[2034] == 0.0


# ── الدبابيس: القيم الافتراضية الجزائرية (S1) ───────────────────────────────────


def test_pinned_headline_values_are_verbatim() -> None:
    """أربعةُ أرقامٍ اسمية منقولةٌ حرفياً — أيُّ تحريكٍ لها يُسقط الحارس."""
    assert ALGERIA_DEFAULTS["25232900"].total == 1.300
    assert ALGERIA_DEFAULTS["31021019"].total == 1.410
    assert ALGERIA_DEFAULTS["31023090"].total == 2.420
    assert ALGERIA_DEFAULTS["72071114"].total == 3.000
    assert ALGERIA_DEFAULTS["28041000"].total == 10.820


def test_self_check_passes_and_is_not_decorative() -> None:
    """`self_check()` يمرّ — ويسقط لو حُرِّف دبوسٌ واحد."""
    self_check()
    original = ALGERIA_DEFAULTS["25232900"]
    try:
        ALGERIA_DEFAULTS["25232900"] = type(original)(
            cn=original.cn,
            sector=original.sector,
            description=original.description,
            direct=original.direct,
            indirect=original.indirect,
            total=1.290,  # ← تحريفٌ مقصود
            route=original.route,
        )
        with pytest.raises(AssertionError):
            self_check()
    finally:
        ALGERIA_DEFAULTS["25232900"] = original
    self_check()


def test_algerian_carbon_steel_is_uniformly_pinned_to_route_c() -> None:
    """نتيجةٌ لا مُدخَل: كلُّ صفٍّ لصلب الكربون الجزائريّ 3.000 بمسار (C)."""
    rows = [r for r in ALGERIA_DEFAULTS.values() if r.sector == "iron_steel" and r.route == "(C)"]
    assert len(rows) >= 10
    assert {r.total for r in rows} == {3.000}


def test_dri_row_is_the_only_low_country_value_for_iron() -> None:
    """7203 (الاختزال المباشر) 0.810 — مقابل 3.000 لكلّ منتجٍ لاحق. هذا هو التناقض."""
    assert ALGERIA_DEFAULTS["7203"].total == 0.810
    assert ALGERIA_DEFAULTS["7208"].total == 3.000


def test_absent_country_value_is_none_not_zero() -> None:
    """«-» في الملفّ الرسميّ ⇒ `None`، ⛔ لا 0.0 — لأنّ المعنى «استعمل جدول البلدان الأخرى»."""
    for cn in ("720211", "720241", "72026000", "2507008080", "25233000"):
        row = ALGERIA_DEFAULTS[cn]
        assert row.total is None
        assert row.direct is None


def test_sectors_covering_direct_only_have_indirect_none() -> None:
    """«N/A» ≠ «-»: الأولى «القطاعُ لا يُسعّر غير المباشر»، والثانية «لا قيمة بلدِيّة»."""
    assert ALGERIA_DEFAULTS["7601"].indirect is None
    assert ALGERIA_DEFAULTS["7601"].total == 0.360
    assert ALGERIA_DEFAULTS["28041000"].indirect is None


def test_row_rejects_unknown_sector() -> None:
    """برهانٌ سلبي: قطاعٌ غيرُ مُعرَّف مرفوضٌ عند البناء."""
    row_type = type(ALGERIA_DEFAULTS["25232900"])
    with pytest.raises(PinError):
        row_type("x", "plastics", "d", None, None, None, None)


# ── الإغلاق: نتيجةٌ على الملفّ الرسميّ نفسه ─────────────────────────────────────


def test_official_file_does_not_close_on_ten_algerian_rows() -> None:
    """**قياسٌ على المنشور لا على نقلنا**: 10 من 34 صفاً ثلاثيّ الأعمدة لا تجمع."""
    audit = closure_audit()
    assert audit["rows_open"] == 10
    assert audit["rows_closed"] == 24
    assert audit["rows_with_three_columns"] == 34


def test_every_open_row_is_at_rounding_scale() -> None:
    """أقصى فجوةٍ 0.010 t/t ⇒ تقريبٌ مستقلٌّ لكلّ عمود، ⛔ لا خطأُ نقلٍ عندنا."""
    audit = closure_audit()
    assert audit["max_abs_gap_t"] == 0.010
    assert audit["all_gaps_are_rounding_scale"] is True
    for row in audit["open_rows"]:
        assert abs(row["gap_t"]) == 0.010


def test_open_rows_name_the_operative_column() -> None:
    """لكلّ صفٍّ لا يُغلق: العمودُ النافذ «total» وسندُه S6 — لا يُترك للقارئ."""
    for row in closure_audit()["open_rows"]:
        assert row["operative_column"] == "total"
        assert row["rule_source"] == "S6"


def test_grey_portland_cement_is_one_of_the_open_rows() -> None:
    """1.230 + 0.060 = 1.290 والإجماليّ المطبوع 1.300 — الرمزُ الأشهرُ في العرض."""
    row = next(r for r in closure_audit()["open_rows"] if r["cn"] == "25232900")
    assert row["gap_t"] == 0.010


# ── الجدولةُ التنظيمية (S3 وS6) ─────────────────────────────────────────────────


def test_cbam_factor_descends_from_975_not_ascends_from_25() -> None:
    """**هذا هو الحسم**: المعاملُ ما تبقّى من التخصيص المجانيّ، فهو يهبط."""
    assert CBAM_FACTOR[2026] == 0.975
    assert CBAM_FACTOR[2030] == 0.515
    assert CBAM_FACTOR[2034] == 0.000
    values = [CBAM_FACTOR[y] for y in HORIZON]
    assert values == sorted(values, reverse=True)


def test_the_withdrawn_reading_is_not_the_pinned_one() -> None:
    """برهانٌ سلبيٌّ صريح: القراءةُ المسحوبة (0.025 مضروباً في الفجوة) ليست هنا."""
    assert 0.025 not in CBAM_FACTOR.values()
    assert 0.025 not in CSCF.values()


def test_markup_applies_to_the_total_column_only() -> None:
    """S6: «the default values of the column 'total emissions' shall be selected»."""
    result = certificates_default("25232900", 2026)
    assert result["marked_up_see_t"] == round(1.300 * 1.10, 5)


def test_fertiliser_markup_is_flat_one_percent_across_the_horizon() -> None:
    """⛔ ليست متصاعدة: نصّ S6 يقول «1 % for the year 2026 and onwards»."""
    assert {MARKUP["fertilisers"][y] for y in HORIZON} == {0.01}


def test_other_sectors_step_10_20_30_then_freeze() -> None:
    for sector in ("cement", "iron_steel", "aluminium", "hydrogen"):
        assert MARKUP[sector][2026] == 0.10
        assert MARKUP[sector][2027] == 0.20
        assert MARKUP[sector][2028] == 0.30
        assert {MARKUP[sector][y] for y in range(2029, 2035)} == {0.30}


def test_certificate_price_absent_quarter_is_none_not_carried() -> None:
    """الربعُ الثالث يُنشر 2026-10-05 ⇒ `None`، ⛔ لا استمرارٌ لقيمة الربع الثاني."""
    assert CERT_PRICE_EUR["2026Q1"] == 75.36
    assert CERT_PRICE_EUR["2026Q2"] == 75.28
    assert CERT_PRICE_EUR["2026Q3"] is None
    with pytest.raises(UnpinnedError):
        certificates_default("25232900", 2026, quarter="2026Q3")


def test_cscf_is_declared_grade_b_with_a_sensitivity() -> None:
    """الدرجةُ partٌ من الرقم: CSCF من مصدرٍ ثانويّ ⇒ حساسيةٌ محسوبة لا ثقة."""
    assert SOURCES["S8"]["grade"] == "ب"
    assert CSCF[2026] == 1.000
    sens = cscf_sensitivity("25232900", 2026)
    assert sens["spread_t"] > 0
    assert sens["variants"]["1.0"] == sens["base_cscf_1.000"]


# ── المراجع: العمودان A وB (S2) ─────────────────────────────────────────────────


def test_column_b_is_never_smaller_than_column_a() -> None:
    """النتيجةُ المركزية: 90 زوجاً مدبوساً، **ولا واحدٌ** فيه A > B."""
    asym = column_asymmetry()
    assert asym["route_pairs_pinned"] == 90
    assert asym["column_a_larger"] == 0
    assert asym["column_a_larger_pairs"] == []


def test_but_the_asymmetry_is_not_universal_it_has_seventeen_ties() -> None:
    """⛔ لا تعميم: 17 زوجاً يتساوى فيه العمودان ⇒ رسمُ المسار هناك صفر."""
    asym = column_asymmetry()
    assert asym["columns_equal"] == 17
    assert asym["column_b_larger"] == 73
    assert len(asym["tied_pairs"]) == 17
    assert asym["share_where_switching_forfeits_credit"] == 0.8111


def test_the_largest_pinned_gap_is_the_steel_route_c_pair() -> None:
    """1.629 − 0.453 = 1.176 t/t — أقصى تخلٍّ عن الاعتماد في الدبابيس كلّها."""
    assert column_asymmetry()["max_gap_t"] == 1.176
    slab = BENCHMARKS["72072015"]
    assert slab["B"]["(C)"] - slab["A"]["(C)"] == pytest.approx(1.176)


def test_unpaired_benchmark_rows_are_named_not_silently_matched() -> None:
    """`72051000`: العمود A بلا مفتاح مسار والعمود B بثلاثة ⇒ ⛔ لا يُخمَّن القرين."""
    assert column_asymmetry()["unpaired_benchmark_cns"] == ["72051000"]
    assert set(BENCHMARKS["72051000"]["A"]) == {""}
    assert set(BENCHMARKS["72051000"]["B"]) == {"(C)", "(D)", "(E)"}


def test_the_extreme_asymmetries_are_pinned_verbatim() -> None:
    assert BENCHMARKS["25232900"] == {"A": {"": 0.000}, "B": {"": 0.666}}
    assert BENCHMARKS["31023090"] == {"A": {"": 0.019}, "B": {"": 0.767}}
    assert BENCHMARKS["72071114"]["A"]["(C)"] == 0.188
    assert BENCHMARKS["72071114"]["B"]["(C)"] == 1.364


def test_aluminium_benchmarks_are_absent_not_zero() -> None:
    """K5: لم تُستخرج ⇒ ⛔ لا صفرَ يُختبأ خلفه."""
    assert not any(cn.startswith("76") for cn in BENCHMARKS)
    assert ALGERIA_DEFAULTS["7601"].total == 0.360  # الصفُّ البلدِيّ موجود
    with pytest.raises(UnpinnedError):
        path_toll("7601", 2026)


def test_cn_7208_column_a_is_absent() -> None:
    """7208 له صفٌّ بلدِيٌّ (3.000) ولا مرجعَ مستخرجاً ⇒ غيرُ قابلٍ للترتيب."""
    assert ALGERIA_DEFAULTS["7208"].total == 3.000
    assert pinned_codes()["7208"]["rankable"] is False
    assert pinned_codes()["7208"]["absent_reason"] == "BENCHMARKS_NOT_EXTRACTED"


def test_route_ambiguous_country_row_is_unrankable_with_a_spoken_reason() -> None:
    """`31025000`: المرجعان مقسومان على (1)/(2) والصفُّ الجزائريّ بلا مؤشر ⇒ غموض."""
    info = pinned_codes()["31025000"]
    assert info["rankable"] is False
    assert info["absent_reason"] == "BENCHMARK_ROUTE_AMBIGUOUS_COUNTRY_ROW_HAS_NO_INDICATOR"
    with pytest.raises(UnpinnedError):
        crossover_see("31025000", 2026)


def test_absent_country_value_is_unrankable_with_the_fallback_reason() -> None:
    info = pinned_codes()["720241"]
    assert info["rankable"] is False
    assert info["absent_reason"] == "NO_COUNTRY_VALUE_USE_OTHER_COUNTRIES_TABLE"


def test_pin_inventory_is_closed() -> None:
    """الجردُ مغلق: قابلٌ للترتيب + غيرُ قابل = كلُّ الصفوف، ولا صفَّ بلا سبب."""
    inventory = pinned_codes()
    assert len(inventory) == len(ALGERIA_DEFAULTS)
    assert sum(1 for v in inventory.values() if v["rankable"]) == 43
    for info in inventory.values():
        assert (info["absent_reason"] is None) is info["rankable"]


def test_benchmark_prefix_resolution_is_declared_not_guessed() -> None:
    """الملحقُ I بـ 4/6 خانات والمراجعُ بـ 8 ⇒ الربطُ إجراءٌ معلَن بأربعة أصناف."""
    assert benchmark_resolution("25232900")["resolution"] == "EXACT_CN8"
    assert benchmark_resolution("7201")["resolution"] == "PREFIX_UNIQUE"
    assert benchmark_resolution("7208")["resolution"] == "BENCHMARK_NOT_FOUND"


def test_cn_7203_is_ambiguous_in_numbering_only_not_in_value() -> None:
    """`7203` ⇒ مرشّحان `72031000`/`72039000` بجداولَ **متطابقة** ⇒ الحلُّ سليم.

    هذا هو الفرقُ بين البحث المليمتريّ والتقدير: لو أُعلن الرمزُ «غيرَ قابلٍ للترتيب»
    لضاع رمزُ الاختزال المباشر — وهو **أهمُّ رمزٍ في الصلب الجزائريّ** (0.810 مقابل
    3.000 لكلّ منتجٍ لاحق). ولو اختير «الأوّل» بصمتٍ لكان القرارُ تخميناً.
    """
    out = benchmark_resolution("7203")
    assert out["resolution"] == "PREFIX_VALUE_IDENTICAL"
    assert out["candidates"] == ["72031000", "72039000"]
    assert BENCHMARKS["72031000"] == BENCHMARKS["72039000"]
    assert pinned_codes()["7203"]["rankable"] is True


def test_cn_7205_has_unpaired_route_keys_and_is_excluded_by_name() -> None:
    """العمود A بلا مفتاحِ مسارٍ والعمود B بثلاثة ⇒ ⛔ لا يُخمَّن القرين."""
    assert benchmark_resolution("7205")["resolution"] == "PREFIX_UNIQUE"
    assert pinned_codes()["7205"]["rankable"] is False
    assert pinned_codes()["7205"]["absent_reason"] == "BENCHMARK_ROUTE_KEYS_UNPAIRED"


def test_the_dri_row_is_the_structural_contradiction_in_algerian_steel() -> None:
    """نتيجةٌ اسمية: 0.810 t/t للاختزال المباشر مقابل 3.000 t/t لكلّ منتجٍ لاحق.

    ⛔ لا تُقرأ «الجزائرُ نظيفة»: المسارُ (C) مُدبَّس على صفوف المنتجات اللاحقة
    نفسها، فالمفوضيةُ تفترض فرنَ الصهر/المحوّل لا الاختزالَ المباشر. الفارقُ
    3.7× في الرمز نفسه هو **سؤالٌ يُطرح على المفوضية**، لا استنتاجٌ عندنا.
    """
    assert ALGERIA_DEFAULTS["7203"].total == 0.810
    assert ALGERIA_DEFAULTS["7208"].total == 3.000
    assert round(3.000 / 0.810, 2) == 3.7
    assert certificates_default("7203", 2026)["eur_per_t"] == 37.94
    assert certificates_default("72071114", 2026)["eur_per_t"] == 148.31


def test_year_outside_horizon_is_rejected() -> None:
    """برهانٌ سلبي: 2035 خارج الأفق ⇒ خطأٌ منطوق، ⛔ لا استمرارٌ للمعامل."""
    with pytest.raises(PinError):
        path_toll("25232900", 2035)


# ── رسمُ المسار (CPN-1) ─────────────────────────────────────────────────────────


def test_path_toll_is_the_benchmark_gap_scaled_by_the_factor() -> None:
    toll = path_toll("72071114", 2026)
    assert toll["benchmark_gap_t"] == round(1.364 - 0.188, 5)
    assert toll["toll_t"] == round(0.975 * 1.000 * 1.176, 5)
    assert toll["toll_eur_per_t"] == round(0.975 * 1.176 * 75.28, 2)


def test_toll_is_zero_where_the_two_columns_agree() -> None:
    """الهيدروجين والكلِنكر الأبيض: A = B ⇒ لا رسم. هذا يثبت أنّ الرسمَ ليس ثابتاً."""
    assert path_toll("28041000", 2026)["toll_t"] == 0.0
    assert path_toll("2523100010", 2026)["toll_t"] == 0.0


def test_toll_collapses_as_the_factor_falls() -> None:
    """2034: المعاملُ صفر ⇒ الرسمُ صفر ⇒ الأطروحةُ القديمة تصير صحيحة. وهذا هو K1 زمنياً."""
    assert path_toll("72071114", 2034)["toll_t"] == 0.0
    assert path_toll("31021019", 2034)["toll_t"] == 0.0


def test_relief_is_the_markup_only() -> None:
    relief = markup_relief("31021019", 2026)
    assert relief["relief_t"] == round(1.410 * 0.01, 5)
    assert relief["relief_eur_per_t"] == round(1.410 * 0.01 * 75.28, 2)


def test_required_reduction_is_toll_minus_relief() -> None:
    out = net_required_reduction("25232900", 2026)
    assert out["required_reduction_t"] == round(out["toll_t"] - out["relief_t"], 5)


def test_required_reduction_is_positive_in_2026_where_the_toll_beats_the_relief() -> None:
    """جوهرُ الدفعة: 36 من 43 رمزاً لا يصير الانتقالُ فيها مجانياً في 2026."""
    conditional = [
        cn
        for cn, info in pinned_codes().items()
        if info["rankable"] and net_required_reduction(cn, 2026)["required_reduction_t"] > 0
    ]
    assert len(conditional) == 36
    for cn in conditional:
        assert path_toll(cn, 2026)["toll_t"] > markup_relief(cn, 2026)["relief_t"], cn


def test_a_positive_toll_does_not_imply_a_conditional_code() -> None:
    """⛔ لا تعميم: حديدُ الزهر `7201` رسمُه موجبٌ لكن إعفاءَه أكبر ⇒ غيرُ مشروط.

    الرسمُ (1.210−1.089)×0.975 = 0.118 t مقابل إعفاءٍ 2.870×0.10 = 0.287 t.
    الإبلاغُ عن «كلُّ رمزٍ حاملِ رسمٍ مشروط» كان سيسقط هنا — وهو سببُ القياس لا الحدس.
    """
    assert path_toll("7201", 2026)["toll_t"] > 0
    assert markup_relief("7201", 2026)["relief_t"] > path_toll("7201", 2026)["toll_t"]
    assert net_required_reduction("7201", 2026)["required_reduction_t"] < 0
    assert unconditional_year("7201")["unconditional_year"] == 2026


def test_toll_free_codes_are_unconditional_from_2026() -> None:
    """الستةُ المتعادلةُ الأعمدة: رسمٌ صفر + إعفاءٌ موجب ⇒ مطلوبٌ سالبٌ من اليوم."""
    inventory = pinned_codes()
    free = [
        cn
        for cn, info in inventory.items()
        if info["rankable"] and path_toll(cn, 2026)["toll_t"] == 0.0
    ]
    assert sorted(free) == [
        "2523100010",
        "2523100090",
        "26011200",
        "28041000",
        "28141000",
        "28142000",
    ]
    for cn in free:
        assert net_required_reduction(cn, 2026)["required_reduction_t"] < 0
        assert unconditional_year(cn)["unconditional_year"] == 2026


# ── البرهانُ المغلق: حجمُ الخطأ ثابتٌ وبلا بيانات منشأة ──────────────────────────


def test_the_naive_error_equals_the_path_toll_exactly() -> None:
    """**أقوى نتيجةٍ في الدفعة**: الخطأ = الرسم، لكلّ انبعاثٍ في النطاق الاقتصاديّ.

    يُختبَر على شبكة: `(SEEₘ−SEE)·p − [(SEEₘ−SEFA_B) − (SEE−SEFA_A)]·p = (SEFA_B−SEFA_A)·p`.
    ⛔ لا يحتاج انبعاثَ منشأة — وهذا ما يجعله مُنتَجاً لا رأياً.
    """
    ident = error_identity("72071114", 2026, "(C)")
    assert ident["toll_eur_per_t"] == 86.32
    assert ident["regime_above_column_a_error_is_constant"] is True
    assert ident["grid_points_above"] >= 60
    assert ident["tolerance_eur"] == 0.02


def test_the_identity_holds_for_every_rankable_code_in_three_years() -> None:
    """تعميمٌ مُختبَر لا موعود: 41 رمزاً × {2026, 2030, 2034} ⇒ لا استثناء."""
    for cn, info in pinned_codes().items():
        if not info["rankable"]:
            continue
        for year in (2026, 2030, 2034):
            assert error_identity(cn, year)["regime_above_column_a_error_is_constant"], (cn, year)


def test_below_column_a_the_error_grows_as_the_plant_gets_cleaner() -> None:
    """الأرضيةُ (S5) تمنع الاسترداد بينما الفجوةُ الساذجة تتّسع ⇒ الخطأُ يتضخّم."""
    ident = error_identity("31021019", 2026)
    assert ident["saturation_point_see_t"] == 0.05167
    assert ident["regime_below_column_a_error_grows"] is True
    assert ident["error_at_zero_emissions_eur_per_t"] == 66.20
    assert ident["error_at_zero_emissions_eur_per_t"] > ident["toll_eur_per_t"]


def test_beyond_the_marked_up_default_the_naive_gap_clips_to_zero() -> None:
    """فوق القيمة المُعلاة تدّعي الأطروحةُ القديمة صفراً بينما الحقيقةُ سالبة."""
    ident = error_identity("25232900", 2026)
    assert ident["regime_beyond_default_naive_clips_to_zero"] is True
    assert saving("25232900", 2026, 3.0)["naive_gap_eur_per_t"] == 0.0
    assert saving("25232900", 2026, 3.0)["saving_eur_per_t"] < 0


def test_max_real_saving_is_capped_by_the_whole_default_charge() -> None:
    """**السقف**: قيمةُ البيانات الفعلية لا تتجاوز الفاتورةَ كلّها — بلا استرداد."""
    assert error_identity("31021019", 2026)["max_real_saving_eur_per_t"] == 41.00
    assert error_identity("72071114", 2026, "(C)")["max_real_saving_eur_per_t"] == 148.31


def test_urea_naive_gap_exceeds_the_ceiling_and_is_therefore_impossible() -> None:
    """دحضٌ حسابيّ: «وفّرنا 46.98 €/t» من فاتورةٍ مجموعُها 41.00 €/t. ⛔ مستحيل.

    ⛔ لا يحتاج انبعاثَ المنشأة ليرفض — وهذا أمتنُ شكلٍ للسحب: الادّعاءُ يسقط من
    داخله، لا بمقارنةٍ مع بياناتٍ لا نملكها.
    """
    out = saving("31021019", 2026, 0.800)
    assert out["naive_exceeds_ceiling"] is True
    assert out["naive_gap_eur_per_t"] == 46.98
    assert out["ceiling_eur_per_t"] == 41.00
    assert out["ceiling_excess_eur_per_t"] == 5.98


def test_the_impossible_case_is_reported_separately_from_the_reversals() -> None:
    """الحالتان صنفان مختلفان: انقلابُ إشارةٍ يُقاس، واستحالةٌ تُدحض. لا يخلطان."""
    payload = measure_all()["results"]
    impossible = payload["naive_impossible_cases"]
    assert [item["cn"] for item in impossible] == ["31021019"]
    assert all(item["impossible_without_any_plant_data"] is True for item in impossible)


# ── العتبةُ والسنةُ غيرُ المشروطة ────────────────────────────────────────────────


def test_crossover_widens_monotonically_across_the_horizon() -> None:
    """العلاوةُ تصعد والمعاملُ يهبط ⇒ العتبةُ تتّسع. الإجابةُ تاريخٌ لا نعم/لا."""
    for cn in ("25232900", "31021019", "31023090", "72071114"):
        values = [crossover_see(cn, y)["crossover_see_t"] for y in HORIZON]
        assert values == sorted(values), cn


def test_crossover_at_2034_equals_the_marked_up_default() -> None:
    """عند المعامل صفر يسقط الاعتمادُ كلُّه ⇒ العتبةُ = القيمة البلدِيّة × (1+العلاوة)."""
    cross = crossover_see("25232900", 2034)["crossover_see_t"]
    assert cross == round(1.300 * 1.30, 5)


def test_crossover_never_reads_candidate_see() -> None:
    """**المنتجُ بلا افتراض**: مسحٌ نصيٌّ على جسمَي الدالتين، لا على النية."""
    source = TOOL.read_text(encoding="utf-8")
    for name in ("def crossover_see", "def unconditional_year", "def net_required_reduction"):
        start = source.index(name)
        end = source.index("\ndef ", start + 1)
        assert "CANDIDATE_SEE" not in source[start:end], name


def test_unconditional_year_is_a_date_not_a_hope() -> None:
    """أربعُ نتائجَ اسمية: الإسمنتُ والصلبُ 2030، واليوريا ونتراتُ الأمونيوم 2034."""
    assert unconditional_year("25232900")["unconditional_year"] == 2030
    assert unconditional_year("72071114")["unconditional_year"] == 2030
    assert unconditional_year("31021019")["unconditional_year"] == 2034
    assert unconditional_year("31023090")["unconditional_year"] == 2034


def test_unconditional_year_exists_for_every_rankable_code() -> None:
    """مبرهنةٌ بنيوية لا تفاؤل: في 2034 المعاملُ صفر ⇒ الرسمُ صفر والإعفاءُ باقٍ.

    ولهذا `unconditional_year` ⛔ لا يُرجِع `None` لأيّ رمزٍ قابلٍ للترتيب داخل الأفق —
    وأبعدُ تاريخٍ ممكنٍ هو 2034. المنتجُ إذن **تقويم**، لا حكمُ أمل.
    """
    inventory = pinned_codes()
    rankable = [cn for cn, info in inventory.items() if info["rankable"]]
    years = [unconditional_year(cn)["unconditional_year"] for cn in rankable]
    assert None not in years
    assert max(years) == 2034
    assert min(years) == 2026


def test_the_unconditional_calendar_is_a_histogram_not_a_single_date() -> None:
    """التقويمُ المُنتَج: 7 رموزٍ اليوم، و**24 رمزاً (55.8%) لا قبل 2034**."""
    import collections

    years = [
        unconditional_year(cn)["unconditional_year"]
        for cn, info in pinned_codes().items()
        if info["rankable"]
    ]
    hist = dict(sorted(collections.Counter(years).items()))
    assert hist == {2026: 7, 2027: 1, 2029: 2, 2030: 7, 2031: 2, 2034: 24}
    assert hist[2034] / len(years) == pytest.approx(0.558, abs=0.001)


def test_unconditional_year_is_none_outside_the_pinned_horizon() -> None:
    """برهانٌ سلبي: الأفقُ ينتهي 2034 لأنّ الصيغةَ تتغيّر بعدها ⇒ ⛔ لا امتداد."""
    out = unconditional_year("31021019")
    assert [row["year"] for row in out["trajectory"]] == list(HORIZON)
    assert 2035 not in [row["year"] for row in out["trajectory"]]


def test_first_sellable_year_returns_a_year_inside_the_horizon() -> None:
    out = first_sellable_year("31021019", 0.800)
    assert out["first_sellable_year"] == 2030
    assert out["never_within_horizon"] is False
    assert len(out["trajectory"]) == len(HORIZON)


def test_first_sellable_year_is_none_above_the_widest_threshold() -> None:
    """انبعاثٌ فوق عتبة 2034 ⇒ `None` مع `never_within_horizon`، ⛔ لا «2035»."""
    out = first_sellable_year("31021019", 1.500)
    assert out["first_sellable_year"] is None
    assert out["never_within_horizon"] is True


# ── انقلابُ الإشارة ─────────────────────────────────────────────────────────────


def test_steel_saving_is_eight_times_smaller_than_the_naive_gap() -> None:
    """الرقمُ الذي يُباع: 97.86 €/t مُتخيَّلة مقابل 11.55 €/t محسوبة."""
    out = overstatement("72071114", 2026, 2.000, "(C)")
    assert out["naive_gap_eur_per_t"] == 97.86
    assert out["saving_eur_per_t"] == 11.55
    assert out["ratio"] == 8.4727
    assert out["verdict"] is Verdict.ACTUAL_CHEAPER


def test_urea_flips_sign_at_a_plausible_actual_intensity() -> None:
    """اليوريا: الفجوةُ الساذجة +46.98 €/t، والحسابُ −15.33 €/t. ⛔ لا قسمة."""
    out = overstatement("31021019", 2026, 0.800)
    assert out["naive_gap_eur_per_t"] == 46.98
    assert out["saving_eur_per_t"] == -15.33
    assert out["ratio"] is None
    assert out["reason"].startswith("SIGN_FLIP")
    assert out["verdict"] is Verdict.DEFAULT_CHEAPER


def test_cement_flips_sign_too() -> None:
    out = saving("25232900", 2026, 0.850)
    assert out["saving_eur_per_t"] == -5.22
    assert out["verdict"] is Verdict.DEFAULT_CHEAPER


def test_ammonium_nitrate_does_not_flip() -> None:
    """الاستثناءُ الذي يُبقي الحكمَ صادقاً: نتراتُ الأمونيوم تبقى مربحة في 2026."""
    out = saving("31023090", 2026, 1.200)
    assert out["saving_eur_per_t"] > 0
    assert out["verdict"] is Verdict.ACTUAL_CHEAPER
    assert overstatement("31023090", 2026, 1.200)["ratio"] == 2.4164


def test_verdict_set_is_closed_at_four() -> None:
    assert {v.value for v in Verdict} == {
        "ACTUAL_CHEAPER",
        "DEFAULT_CHEAPER",
        "EXACTLY_AT_CROSSOVER",
        "UNRANKABLE",
    }


def test_exactly_at_the_crossover_is_its_own_verdict() -> None:
    cross = crossover_see("72071114", 2026, "(C)")["crossover_see_t"]
    assert saving("72071114", 2026, cross, "(C)")["verdict"] is Verdict.EXACTLY_AT_CROSSOVER


def test_negative_emissions_are_rejected() -> None:
    """برهانٌ سلبي: انبعاثٌ سالبٌ ليس قياساً منخفضاً — إنه مُدخَلٌ فاسد."""
    with pytest.raises(PinError):
        certificates_actual("25232900", 2026, -0.1)


def test_certificate_count_is_floored_at_zero_not_negative() -> None:
    """S5: «where the number of certificates is calculated to have a negative value,
    it is set to zero» — فلا «استرداد» يُوعَد به المشتري.

    بلاطةُ صلبٍ بانبعاثٍ فعليّ 0.100 t/t ومرجعٍ A = 0.188 ⇒ الحسابُ −0.0833 ⇒ يُصفَّر.
    ⛔ لا يُبلَّغ المشتري بأنّ له رصيداً سالِباً يستردّه.
    """
    out = certificates_actual("72071114", 2026, 0.100, "(C)")
    assert out["unfloored_t"] == round(0.100 - 0.975 * 0.188, 5)
    assert out["net_certificates_t"] == 0.0
    assert out["eur_per_t"] == 0.0


def test_route_c_beats_route_d_on_the_actual_path() -> None:
    """نتيجةٌ عكسيةٌ قابلةٌ للبيع: المسارُ «الأنظف» (D) اعتمادُه في العمود A أصغر."""
    c = certificates_actual("72071114", 2026, 0.900, "(C)")["eur_per_t"]
    d = certificates_actual("72071114", 2026, 0.900, "(D)")["eur_per_t"]
    assert c < d
    assert round(d - c, 2) == 9.03


def test_default_route_falls_back_to_the_country_pin() -> None:
    assert default_route("72071114") == "(C)"
    assert certificates_actual("72071114", 2026, 2.0)["route"] == "(C)"


# ── شروطُ القتل ─────────────────────────────────────────────────────────────────


def test_kill_switches_are_a_closed_set_of_five() -> None:
    switches = kill_switches()
    assert set(switches) == {"K1", "K2", "K3", "K4", "K5"}
    for item in switches.values():
        assert item["statement_ar"].strip()
        assert "fired" in item and "evidence" in item


def test_no_kill_switch_has_fired() -> None:
    assert all(v["fired"] is False for v in kill_switches().values())


_FRESH_BENCHMARKS = json.loads(json.dumps(BENCHMARKS))


def test_k1_would_fire_if_the_columns_converged() -> None:
    """برهانٌ سلبيّ لـ K1: لو تساوى العمودان في كلِّ رمزٍ لسقط رسمُ المسار كلُّه."""
    try:
        for cn in BENCHMARKS:
            table = _FRESH_BENCHMARKS[cn]
            BENCHMARKS[cn] = {"A": dict(table["B"]), "B": dict(table["B"])}
        assert kill_switches()["K1"]["fired"] is True
        assert column_asymmetry()["column_b_larger"] == 0
    finally:
        BENCHMARKS.clear()
        BENCHMARKS.update(json.loads(json.dumps(_FRESH_BENCHMARKS)))
    assert kill_switches()["K1"]["fired"] is False
    assert column_asymmetry()["column_b_larger"] == 73


def test_k3_would_fire_if_the_factor_were_the_complement() -> None:
    """برهانٌ سلبيّ لـ K3: قراءةُ cbamguide (0.025) تُبطل الصيغةَ كلَّها."""
    original = CBAM_FACTOR[2026]
    try:
        CBAM_FACTOR[2026] = 0.025
        assert kill_switches()["K3"]["fired"] is True
    finally:
        CBAM_FACTOR[2026] = original
    assert kill_switches()["K3"]["fired"] is False


def test_k3_evidence_names_three_independent_anchors() -> None:
    """الحكمُ لا يقف على مصدرٍ واحد: S3 (مفوضية) + S4 (سوق/سلطة وطنية) + S5 (مفوضية)."""
    anchors = kill_switches()["K3"]["evidence"]["independent_anchors"]
    assert anchors == ["S3", "S4", "S5"]
    assert SOURCES["S3"]["grade"] == "أ"
    assert SOURCES["S5"]["grade"] == "أ"


def test_k4_reads_the_version_history_of_the_official_file() -> None:
    """الملفُ نُسخةٌ 2 بعد نسخةٍ 1 في ستة أشهر ⇒ التقادمُ خطرٌ مُقاس لا منسيّ."""
    evidence = kill_switches()["K4"]["evidence"]
    assert "Version 2" in evidence["version_history"]
    assert evidence["act"] == "IR (EU) 2026/1740"


def test_k5_fires_when_aluminium_benchmarks_are_extracted() -> None:
    """برهانٌ سلبيّ لـ K5: استخراجُ الألومنيوم يُطلق الشرط، لا يُوسِّع الجدولَ سرّاً."""
    assert kill_switches()["K5"]["fired"] is False
    try:
        BENCHMARKS["76010000"] = {"A": {"": 1.5}, "B": {"": 1.5}}
        assert kill_switches()["K5"]["fired"] is True
    finally:
        del BENCHMARKS["76010000"]
    assert kill_switches()["K5"]["fired"] is False


def test_k2_fires_if_cscf_moves_off_one() -> None:
    original = dict(CSCF)
    try:
        CSCF[2026] = 0.987
        assert kill_switches()["K2"]["fired"] is True
    finally:
        CSCF.clear()
        CSCF.update(original)
    assert kill_switches()["K2"]["fired"] is False


# ── السحبُ لا يُنشَر إلى مصادر الأرقام (عرف RCL) ───────────────────────────────


def test_withdrawn_arithmetic_is_still_reachable_in_the_old_instruments() -> None:
    """برهانٌ سلبيٌّ على **القرص**: الحسابان المسحوبان ما يزالان في ملفَّيهما.

    `cbam_value.py` ما يزال يستعمل `FACTOR = {2026: 0.025}` مضروباً في الفجوة،
    و`markup_gradient.py` ما يزال يستعمل `CBAM_FACTOR = {2026: 0.975}` مضروباً في
    الوفر. إن أُصلح أيٌّ منهما سقط هذا الاختبار — وهو السقوطُ المطلوب، لأنه يعني
    أنّ السحبَ انتشر إلى مصادر الأرقام بقرارٍ مكتوبٍ لا بتحريرٍ عابر.
    """
    assert LEGACY_VALUE.exists() and LEGACY_GRADIENT.exists()
    assert "2026: 0.025" in LEGACY_VALUE.read_text(encoding="utf-8")
    assert "2026: 0.975" in LEGACY_GRADIENT.read_text(encoding="utf-8")


def test_the_two_legacy_instruments_disagree_by_thirty_nine_fold() -> None:
    """قياسُ التناقض نفسِه: 0.975 ÷ 0.025 = 39 — وهذا حجمُ ما كان غيرَ محسوم."""
    assert round(0.975 / 0.025, 4) == 39.0


def test_the_ledger_highest_ranked_move_now_has_an_artifact() -> None:
    """UCL صنّفت `cbam_pin.py` أعلى حركةٍ مقيسة — والملفُّ لم يكن موجوداً. صار."""
    ucl = (REPO_ROOT / "research" / "fx-hard-currency" / "ucl_model.py").read_text("utf-8")
    assert "cbam_pin.py" in ucl
    assert TOOL.exists()


def test_ucl_inherited_fingerprints_are_not_on_disk() -> None:
    """فحصٌ مليمتريّ على الدفعة السابقة: بصماتُها الستُّ لا مصدرَ لها في المستودع.

    UCL ورثت ستّةَ أرقامٍ (SFD · ERD · PTD · PID · ABR · CPD) ببصماتٍ مُعلَنة، لكن
    لا وثيقةَ ولا ملفَّ قياسٍ لأيٍّ منها على القرص ⇒ نطاقُ M3 اليورويّ (6–60 ألف€)
    كان **غيرَ قابلٍ للتدقيق**. هذه الدفعة تشتقّ النطاقَ من مصدرٍ أوّليّ بدل ذلك.
    """
    fingerprints = [
        "6a1028752c3c0824",
        "7d893aeaf37c37b7",
        "de0af52eea68be1f",
        "2ea31466c54e784f",
        "20ec8bd4b363d6bf",
        "9b46b6569dbaef83",
    ]
    carriers: dict[str, int] = dict.fromkeys(fingerprints, 0)
    for path in REPO_ROOT.rglob("*"):
        if ".git" in path.parts or not path.is_file():
            continue
        if path.name == Path(__file__).name:  # هذا الاختبارُ نفسه يحملُها نصّاً
            continue
        if path.suffix not in {".md", ".json", ".py", ".csv", ".txt", ".yaml", ".yml"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:  # pragma: no cover - ملفٌّ غير مقروء
            continue
        for fp in fingerprints:
            if fp in text:
                carriers[fp] += 1
    # كلُّ بصمةٍ تظهر في ملفَّين **فحسب**: وثيقة UCL وأداتُه — أي في الدفعة نفسها،
    # ⛔ لا ثالث: لا ملفَّ قياسٍ مُودَع ولا دراسةً ولا وثيقةَ دفعاتٍ تحملُها.
    assert all(count == 2 for count in carriers.values()), carriers
    # ولا واحدةٌ منها تظهر في ملفِّ قياسٍ مُودَع
    for path in (REPO_ROOT / "docs" / "research").glob("*_MEASUREMENTS.json"):
        text = path.read_text(encoding="utf-8")
        assert not any(fp in text for fp in fingerprints), path.name


# ── الحمولةُ والبصمة ────────────────────────────────────────────────────────────


def test_declared_zeros_are_all_zero_and_no_revenue() -> None:
    zeros = measure_all()["declared_zeros"]
    assert zeros["revenue_claim"] == "NONE"
    for key, value in zeros.items():
        if key != "revenue_claim":
            assert value == 0, key


def test_declared_zeros_include_the_two_unextracted_absences() -> None:
    """الغيابُ يُعلَن رقماً: الألومنيوم صفر، و`7208` عمود A صفر."""
    zeros = measure_all()["declared_zeros"]
    assert zeros["aluminium_benchmarks_extracted"] == 0
    assert zeros["cn7208_column_a_extracted"] == 0
    assert zeros["installations_measured"] == 0
    assert zeros["verified_actual_emissions_obtained"] == 0


def test_fingerprint_is_deterministic_and_computed() -> None:
    assert inputs_fingerprint() == inputs_fingerprint()
    assert len(inputs_fingerprint()) == 64
    assert "hashlib.sha256" in TOOL.read_text(encoding="utf-8")


def test_fingerprint_moves_when_one_pinned_value_moves() -> None:
    """برهانٌ سلبي: دبوسٌ واحد يتغيّر ⇒ البصمةُ تتغيّر. بصمةٌ لا تتحرّك زينة."""
    before = inputs_fingerprint()
    original = ALGERIA_DEFAULTS["25232900"]
    try:
        ALGERIA_DEFAULTS["25232900"] = type(original)(
            cn=original.cn,
            sector=original.sector,
            description=original.description,
            direct=original.direct,
            indirect=original.indirect,
            total=1.301,
            route=original.route,
        )
        assert inputs_fingerprint() != before
    finally:
        ALGERIA_DEFAULTS["25232900"] = original
    assert inputs_fingerprint() == before


def test_measure_all_is_deterministic() -> None:
    assert json.dumps(measure_all(), sort_keys=True, default=str) == json.dumps(
        measure_all(), sort_keys=True, default=str
    )


def test_measure_all_carries_the_limits() -> None:
    joined = " ".join(measure_all()["limits_ar"])
    assert "ليس رأياً قانونياً" in joined
    assert "لا خطَّ عرضٍ ثامن" in joined
    assert "revenue_claim = NONE" in joined
    assert "CANDIDATE_SEE" in joined


def test_filed_measurements_match_recomputation() -> None:
    """بوّابةُ الانحراف: الملفّ المودَع = إعادةُ الحساب، حرفاً بحرف."""
    filed = json.loads(MEASUREMENTS.read_text(encoding="utf-8"))
    fresh = measure_all()
    for key in ("batch", "as_of", "declared_zeros", "inputs_fingerprint", "results", "limits_ar"):
        assert filed[key] == json.loads(json.dumps(fresh[key], default=str)), key


def test_no_offer_line_is_promoted_by_this_batch() -> None:
    """هذه الدفعة قياسٌ لا عرض — لا خطَّ فوق `PROPOSED` بلا معاملةٍ مُسوّاة.

    حصرُ السبعة ألغاه المالك في D-296؛ والشرط الباقي (D-297) بنيويّ: مُعرِّفٌ فريد
    لكلّ خطّ، ولا ترقيةَ بلا معاملة. عدُّ الخطوط هنا كان يُحمِّر `main` بعد إلغاء الحصر.
    """
    catalog_path = REPO_ROOT / "docs" / "commercial" / "OFFER_CATALOG.json"
    offers = json.loads(catalog_path.read_text("utf-8"))["offers"]
    ids = [offer.get("id") for offer in offers]
    assert offers
    assert all(ids) and len(ids) == len(set(ids))
    assert all(offer.get("status") == "PROPOSED" for offer in offers)


def test_every_source_carries_a_grade_a_date_and_a_quote() -> None:
    """لا مصدرَ بلا درجةٍ وتاريخٍ واقتباسٍ حرفيّ — وإلا فهو رأي."""
    for sid, source in SOURCES.items():
        assert source["id"] == sid
        assert source["grade"] in {"أ", "ب", "ج"}
        assert source["accessed_on"] == AS_OF
        assert source["published_on"]
        assert source["quote"].strip()
        assert source["url"].startswith(("http", "file://")), sid


def test_no_claim_rests_on_a_single_grade_b_source() -> None:
    """الصيغةُ تعتمد على S4 (ب) — لكنها مُسنَدةٌ بـ S3 وS5 (أ). هذا مُختبَر لا موعود."""
    assert SOURCES["S4"]["grade"] == "ب"
    anchors = kill_switches()["K3"]["evidence"]["independent_anchors"]
    assert sum(1 for a in anchors if SOURCES[a]["grade"] == "أ") >= 2


def test_cscf_dependent_figures_are_marked_conditional() -> None:
    quotability = measure_all()["results"]["quotability"]
    conditional = " ".join(quotability["CONDITIONAL"]).lower()
    not_found = " ".join(quotability["NOT_FOUND_IN_PRIMARY_SOURCES"]).lower()
    assert "cscf" in conditional
    assert "aluminium" in not_found


def test_candidate_see_is_declared_as_an_assumption_not_a_measurement() -> None:
    for item in measure_all()["results"]["decision_reversals"]:
        assert item["see_status"].startswith("ASSUMED_SEE")
    assert set(CANDIDATE_SEE) <= {i["cn"] for i in measure_all()["results"]["decision_reversals"]}
