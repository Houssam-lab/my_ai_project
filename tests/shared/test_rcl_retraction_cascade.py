"""اختباراتُ تتالي السحب — RCL (الدفعة الحادية عشرة).

تُثبِت أربعةَ أشياء:

1. **الحكمُ دالةٌ في الاعتماد لا في الأهمية** — ادّعاءٌ تافهٌ يعتمد على مسحوبٍ يسقط،
   وادّعاءٌ مركزيٌّ له سندٌ مستقلٌّ ينجو مضيَّقاً.
2. **الفراغُ `None` لا صفر** — الهامشُ المسحوب كميةٌ غيرُ معرَّفة، وطلبُ حسابِه
   يرفع لا يُقرِّب.
3. **البصمةُ تُحسَب** — أيُّ تحريفٍ في مُدخَلٍ واحدٍ يُسقطها.
4. **شروطُ القتل قادرةٌ على الإطلاق** — لكلٍّ من K1–K5 برهانٌ سلبيٌّ هنا؛ شرطٌ
   لا يُطلَق زينةٌ تُقرأ حماية.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from shared.research.retraction_cascade import (
    AS_OF,
    BATCH,
    CARDS,
    CLAIMS,
    CREDIT_CAP_DAYS,
    CREDIT_INSURED_CAP_DAYS,
    REPLACEMENT_CONSTRAINTS,
    WITHDRAWALS,
    Card,
    Claim,
    ClaimState,
    Executor,
    RetractionError,
    Withdrawal,
    WithdrawnModelError,
    adjudicate,
    buffer_days,
    card_ledger,
    credit_term_admissibility,
    inputs_fingerprint,
    kill_switches,
    ledger,
    measure_all,
    path_disjointness,
    rail_readiness_gate,
    repatriation_slack_days,
    sendable_path,
)

TOOL = REPO_ROOT / "shared" / "research" / "retraction_cascade.py"
MEASUREMENTS = REPO_ROOT / "docs" / "research" / "RCL_MEASUREMENTS.json"


# ── الهويةُ المجمَّدة ────────────────────────────────────────────────────────────


def test_frozen_identity() -> None:
    """رقمُ الدفعة وتاريخُ التجميد ثابتان — لا يُقرآن من الساعة."""
    assert BATCH == "RCL-11"
    assert AS_OF == "2026-09-15"


def test_batch_number_follows_fiv() -> None:
    """FIV كانت العاشرة على القرص — وهذه الحادية عشرة، لا عاشرة ثانية."""
    fiv = json.loads((REPO_ROOT / "docs" / "research" / "FIV_MEASUREMENTS.json").read_text("utf-8"))
    assert fiv["batch"] == "FIV-10"
    assert BATCH.endswith("-11")


def test_stdlib_only() -> None:
    """لا استيراد من app/ ولا microservices/ — تُشحَن إلى عميلٍ بلا تبعياتنا."""
    source = TOOL.read_text(encoding="utf-8")
    for banned in ("from app", "import app", "from microservices", "import requests", "openai"):
        assert banned not in source, banned


# ── سجلُّ السحب ──────────────────────────────────────────────────────────────────


def test_every_withdrawal_has_a_quote_and_a_source() -> None:
    """سحبٌ بلا نصٍّ مقتبسٍ وبلا مصدرٍ على القرص ليس حدثاً — بل رأي."""
    for w in WITHDRAWALS:
        assert w.quote.strip()
        assert w.source.strip()
        assert w.withdrawn_on


def test_w1_is_the_fcm_day_budget_withdrawal() -> None:
    """W1 موثّقةٌ بنصّها الحرفي من FCM §2.1."""
    w1 = next(w for w in WITHDRAWALS if w.withdrawal_id == "W1")
    assert w1.voided_model == "RSM_DAY_BUDGET"
    assert "grants no day budget" in w1.quote
    assert "FCM.md" in w1.source


def test_withdrawal_requires_identity() -> None:
    """برهانٌ سلبي: سحبٌ بلا معرّفٍ أو بلا نموذجٍ مرفوض."""
    with pytest.raises(RetractionError):
        Withdrawal("", "X", "2026-09-15", "s", "q", None)
    with pytest.raises(RetractionError):
        Withdrawal("W9", "", "2026-09-15", "s", "q", None)
    with pytest.raises(RetractionError):
        Withdrawal("W9", "X", "2026-09-15", "", "q", None)


def test_every_replacement_points_at_a_real_constraint() -> None:
    """بديلٌ يشير إلى قيدٍ غير معلَن ثقبٌ في السجل."""
    ids = {c.constraint_id for c in REPLACEMENT_CONSTRAINTS}
    for w in WITHDRAWALS:
        assert w.replaced_by is None or w.replaced_by in ids


# ── سطحُ الاقتباس: الحكمُ دالةٌ في الاعتماد ──────────────────────────────────────


def _claim(**kw: object) -> Claim:
    base: dict[str, object] = {
        "claim_id": "X1",
        "batch": "TST-0",
        "artifact": "tests/x.json",
        "quantity": "كمية",
        "depends_on": (),
    }
    base.update(kw)
    return Claim(**base)  # type: ignore[arg-type]


def test_claim_with_no_dependency_is_quotable() -> None:
    assert adjudicate(_claim()).state is ClaimState.QUOTABLE


def test_claim_on_withdrawn_model_with_no_ground_is_void() -> None:
    v = adjudicate(_claim(depends_on=("RSM_DAY_BUDGET",)))
    assert v.state is ClaimState.VOID_WITHDRAWN
    assert v.voided_by == ("W1",)


def test_claim_with_independent_ground_survives_narrower() -> None:
    """النتيجةُ المحورية: A9 تُمنع لسببَين، يسقط أحدُهما فيبقى الحكم مضيَّقاً."""
    v = adjudicate(
        _claim(depends_on=("RSM_DAY_BUDGET",), independent_grounds=("K5_foreign_entity",))
    )
    assert v.state is ClaimState.SURVIVES_NARROWER_GROUND
    assert "K5_foreign_entity" in v.surviving_grounds


def test_reclassified_precedes_void() -> None:
    """برهانٌ سلبيٌّ على الترتيب: لو سبق `VOID` لأُتلِف مقياسٌ صالحٌ في سؤالٍ آخر."""
    v = adjudicate(_claim(depends_on=("RSM_DAY_BUDGET",), reclassified_to="مقياسُ تدفّقٍ نقدي"))
    assert v.state is ClaimState.RECLASSIFIED


def test_reclassification_requires_a_named_target() -> None:
    with pytest.raises(RetractionError):
        adjudicate(_claim(depends_on=("RSM_DAY_BUDGET",), reclassified_to="  "))


def test_unknown_dependency_is_rejected() -> None:
    """ادّعاءٌ يعتمد على معرّفٍ غير معلَن لا يُدقَّق — بل يُرفض."""
    with pytest.raises(RetractionError):
        _claim(depends_on=("SOMETHING_NOT_DECLARED",))


def test_official_text_gate_blocks_an_otherwise_sound_claim() -> None:
    v = adjudicate(_claim(depends_on=("S_A",), needs_official_text=True))
    assert v.state is ClaimState.BLOCKED_PENDING_TEXT


def test_claim_on_a_live_constraint_is_quotable() -> None:
    assert adjudicate(_claim(depends_on=("S_A",))).state is ClaimState.QUOTABLE


def test_wod_k2_prior_art_is_registered_and_quotable() -> None:
    """الأسبقيةُ على القرص: WOD نصّت على البوّابة قبل هذه الدفعة بيوم."""
    c16 = next(c for c in CLAIMS if c.claim_id == "C16")
    assert "bank_export_declaration" in c16.artifact
    assert adjudicate(c16).state is ClaimState.QUOTABLE


def test_the_novelty_claim_is_void_by_our_own_withdrawal() -> None:
    """C17 ادّعاؤنا نحن — سُحِب بسحبٍ سجّلناه على أنفسنا (W7)."""
    c17 = next(c for c in CLAIMS if c.claim_id == "C17")
    v = adjudicate(c17)
    assert v.state is ClaimState.VOID_WITHDRAWN
    assert v.voided_by == ("W7",)


def test_w7_source_is_the_wod_note_verbatim() -> None:
    w7 = next(w for w in WITHDRAWALS if w.withdrawal_id == "W7")
    assert w7.voided_model == "T4_NO_PRIOR_ART"
    assert "لا عقدَ قبل إيداع التصريح" in w7.quote
    assert "WOD_MEASUREMENTS.json" in w7.source


def test_k3_is_recorded_as_fired_on_this_batch() -> None:
    """K3 ليس زينة: أُطلِق على الدفعة نفسها، والحالةُ مكتوبةٌ في القياس."""
    k3 = next(k for k in kill_switches() if k["id"] == "K3")
    assert k3.get("state") == "FIRED_ON_SELF"
    assert "bank_export_declaration" in k3["fired_on_ar"]


def test_real_c15_is_quotable_and_untouched() -> None:
    """A0 فئةُ الفاتورة الأولى (WOD) لا تعتمد على أيّ نموذج مسحوب."""
    c15 = next(c for c in CLAIMS if c.claim_id == "C15")
    assert c15.depends_on == ()
    assert adjudicate(c15).state is ClaimState.QUOTABLE


def test_real_c1_buffer_is_void() -> None:
    """`buffer_days` في AHW محسوبةٌ على النموذج المسحوب — لا سندَ مستقلّ لها."""
    c1 = next(c for c in CLAIMS if c.claim_id == "C1")
    assert adjudicate(c1).state is ClaimState.VOID_WITHDRAWN


def test_real_c2_and_c10_survive_on_the_credit_cap() -> None:
    """«≤45 يوماً» تنجو — لكن على S_A، لا على الهامش."""
    for cid in ("C2", "C10"):
        v = adjudicate(next(c for c in CLAIMS if c.claim_id == cid))
        assert v.state is ClaimState.SURVIVES_NARROWER_GROUND, cid
        assert "S_A" in v.surviving_grounds


def test_real_c8_c9_are_reclassified_not_deleted() -> None:
    for cid in ("C8", "C9"):
        v = adjudicate(next(c for c in CLAIMS if c.claim_id == cid))
        assert v.state is ClaimState.RECLASSIFIED, cid
        assert "تدفّق" in v.action_ar or "تفاوض" in v.action_ar


def test_ledger_counts_are_closed_and_sum_to_total() -> None:
    surface = ledger()
    assert sum(surface["by_state"].values()) == surface["total"] == len(CLAIMS)
    assert set(surface["by_state"]) == {s.value for s in ClaimState}


def test_ledger_share_is_none_on_empty_not_zero() -> None:
    """الفراغُ `None` لا صفراً (D-212) — نسبةٌ على صفر ليست قياساً."""
    assert ledger(())["quotable_share"] is None


def test_quotable_share_is_below_one_third() -> None:
    """القياسُ لا الأمنية: أكثرُ من ثلثَي السطح غيرُ قابلٍ للاقتباس كما كُتب."""
    surface = ledger()
    assert surface["quotable_share"] is not None
    assert surface["quotable_share"] < 1 / 3


# ── القيدُ البديل ────────────────────────────────────────────────────────────────


def test_credit_cap_admits_up_to_120() -> None:
    for t in (0, 15, 30, 45, 60, 90, 120):
        assert credit_term_admissibility(t)["status"] == "ADMISSIBLE"


def test_credit_cap_needs_insurance_between_120_and_180() -> None:
    assert credit_term_admissibility(150)["status"] == "NEEDS_CREDIT_INSURANCE"
    assert (
        credit_term_admissibility(150, credit_insured=True)["status"] == "ADMISSIBLE_INSURED_ONLY"
    )


def test_credit_cap_prohibits_over_180() -> None:
    assert credit_term_admissibility(270)["status"] == "PROHIBITED"
    assert credit_term_admissibility(270, credit_insured=True)["status"] == "PROHIBITED"


def test_prepayment_is_admissible() -> None:
    """الدفعُ المُقدَّم (0 يوم) أقوى تجارياً وأقلّ تعرّضاً — لا يُرفض."""
    assert credit_term_admissibility(0)["status"] == "ADMISSIBLE"


def test_negative_term_rejected() -> None:
    with pytest.raises(RetractionError):
        credit_term_admissibility(-1)


def test_caps_are_the_sourced_numbers() -> None:
    assert (CREDIT_CAP_DAYS, CREDIT_INSURED_CAP_DAYS) == (120, 180)


# ── الكميةُ غيرُ المعرَّفة ───────────────────────────────────────────────────────


def test_slack_is_none_with_a_spoken_reason() -> None:
    out = repatriation_slack_days()
    assert out["slack_days"] is None
    assert out["reason"].strip()
    assert "RSM_DAY_BUDGET" in out["reason"]


def test_buffer_days_always_raises() -> None:
    """الفارض: كودٌ قديمٌ يستدعيها يسقط فوراً بدل أن يُنتج رقماً مسحوباً بهدوء."""
    with pytest.raises(WithdrawnModelError):
        buffer_days(30)
    with pytest.raises(WithdrawnModelError):
        buffer_days(45, 120)


def test_withdrawn_error_is_a_retraction_error() -> None:
    assert issubclass(WithdrawnModelError, RetractionError)


def test_void_arithmetic_is_still_reachable_in_the_old_instruments() -> None:
    """برهانٌ سلبيٌّ لـ K3: الأداةُ القديمة ما تزال تُنتج الرقمَ المسحوب.

    هذا اختبارٌ على **القرص** لا على هذه الأداة: إن أُصلحت `assurance_window`
    و`fx_rail` فسيسقط هذا الاختبار — وهو السقوطُ المطلوب، لأنه يعني أنّ السحب
    انتشر إلى مصادر الأرقام لا إلى سجلّها فقط.
    """
    from shared.research.assurance_window import RepatriationRef
    from shared.research.assurance_window import buffer_days as legacy_buffer

    ref = RepatriationRef(name="نظامُ 26-02", repatriation_days=120, credit_ceiling_days=120)
    assert legacy_buffer(30, ref) == 90  # ← الرقمُ المسحوب ما زال يُحسَب


# ── البوّابةُ الجديدة (T4) ───────────────────────────────────────────────────────


def test_invoice_before_rail_is_a_breach() -> None:
    out = rail_readiness_gate(rail_declared_ready=False, invoice_issued=True)
    assert not out["passes"]
    assert any(b.startswith("INVOICE_BEFORE_RAIL") for b in out["breaches"])


def test_missing_declaration_is_a_breach() -> None:
    out = rail_readiness_gate(
        rail_declared_ready=True, invoice_issued=True, declaration_filed=False
    )
    assert any(b.startswith("DECLARATION_MISSING") for b in out["breaches"])


def test_ready_rail_with_declaration_passes() -> None:
    out = rail_readiness_gate(rail_declared_ready=True, invoice_issued=True, declaration_filed=True)
    assert out["passes"] and out["breaches"] == []


def test_no_invoice_yet_is_not_a_breach() -> None:
    """الترتيبُ قيدٌ على الإصدار لا على الوجود — بلا فاتورةٍ لا خرق."""
    assert rail_readiness_gate(rail_declared_ready=False, invoice_issued=False)["passes"]


def test_gate_is_not_legal_advice() -> None:
    out = rail_readiness_gate(rail_declared_ready=True, invoice_issued=True, declaration_filed=True)
    assert "ليس رأياً قانونياً" in out["reported_as"]


# ── المسارُ الحرج ────────────────────────────────────────────────────────────────


def test_card_graph_is_acyclic_and_closed() -> None:
    """التحقّقُ جرى عند الاستيراد؛ هذا يُثبِت أنّه يرفض الدورة فعلاً."""
    from shared.research import retraction_cascade as rcl

    cyclic = (
        Card(
            card_id="A", source="t", summary_ar="a", executor=Executor.RESEARCHER, depends_on=("B",)
        ),
        Card(
            card_id="B", source="t", summary_ar="b", executor=Executor.RESEARCHER, depends_on=("A",)
        ),
    )
    with pytest.raises(RetractionError):
        rcl._validate_card_graph(cyclic)


def test_card_graph_rejects_unknown_dependency() -> None:
    from shared.research import retraction_cascade as rcl

    dangling = (
        Card(
            card_id="A", source="t", summary_ar="a", executor=Executor.RESEARCHER, depends_on=("Z",)
        ),
    )
    with pytest.raises(RetractionError):
        rcl._validate_card_graph(dangling)


def test_card_graph_rejects_duplicates() -> None:
    from shared.research import retraction_cascade as rcl

    dup = (
        Card(card_id="A", source="t", summary_ar="a", executor=Executor.RESEARCHER),
        Card(card_id="A", source="t", summary_ar="a", executor=Executor.RESEARCHER),
    )
    with pytest.raises(RetractionError):
        rcl._validate_card_graph(dup)


def test_path_rejects_an_undeclared_lane() -> None:
    with pytest.raises(RetractionError):
        Card(card_id="A", source="t", summary_ar="a", executor=Executor.RESEARCHER, path="NOPE")


def test_critical_path_to_first_invoice_is_owner_free() -> None:
    """النتيجةُ المقرِّرة: أقصرُ مسارٍ إلى T70 لا يمرّ بالمالك إطلاقاً."""
    p = sendable_path("T70")
    assert p["owner_free"] is True
    assert p["by_executor"]["OWNER"] == []
    assert p["minimum_set"] == ["T66", "T68", "T77", "T78", "T70"]


def test_critical_path_length_is_five() -> None:
    assert sendable_path("T70")["length"] == 5


def test_critical_path_is_topologically_ordered() -> None:
    """التابعُ بعد متبوعه — وإلا فـ«المسار» قائمةٌ لا ترتيب."""
    p = sendable_path("T70")
    order = p["minimum_set"]
    by_id = {c.card_id: c for c in CARDS}
    for cid in order:
        for dep in by_id[cid].depends_on:
            assert order.index(dep) < order.index(cid), f"{dep} قبل {cid}"


def test_unknown_target_rejected() -> None:
    with pytest.raises(RetractionError):
        sendable_path("T999")


def test_owner_blocked_path_is_reported_as_such() -> None:
    """برهانٌ سلبي: مسارُ القنوات محجوبٌ بالمالك فعلاً — والأداةُ تقول ذلك."""
    p = sendable_path("T73")
    assert p["owner_free"] is False
    assert "T71" in p["owner_blocking"]


def test_card_ledger_counts_sum() -> None:
    out = card_ledger()
    assert sum(out["by_executor"].values()) == out["total"] == len(CARDS)
    assert sum(out["by_path"].values()) == out["total"]


def test_a0_and_ch_are_fully_disjoint() -> None:
    d = path_disjointness("A0", "CH")
    assert d["cards_disjoint"] and d["closure_disjoint"]


def test_a0_and_fx_are_entangled_through_the_official_text() -> None:
    """غيرُ بديهي: المساران منفصلان بالبطاقات ومتشابكان بالتبعية عبر T77."""
    d = path_disjointness("A0", "FX")
    assert d["cards_disjoint"] is True
    assert d["closure_disjoint"] is False
    assert d["closure_intersection"] == ["T77"]


# ── شروطُ القتل — قادرةٌ على الإطلاق ─────────────────────────────────────────────


def test_kill_switches_are_a_closed_set_of_five() -> None:
    ks = kill_switches()
    assert [k["id"] for k in ks] == ["K1", "K2", "K3", "K4", "K5"]
    for k in ks:
        assert k["condition_ar"].strip()
        assert k["consequence_ar"].strip()
        assert k["observable_ar"].strip()


def test_k1_fires_if_the_official_text_restores_a_day_budget() -> None:
    """برهانٌ سلبي: لو زال W1 من السجلّ لعاد `buffer_days` كميةً معرَّفةً في الحكم."""
    c1 = next(c for c in CLAIMS if c.claim_id == "C1")
    without_w1 = tuple(w for w in WITHDRAWALS if w.withdrawal_id != "W1")
    assert adjudicate(c1, without_w1).state is not ClaimState.VOID_WITHDRAWN


def test_k3_fires_on_an_uncaught_dependent_claim() -> None:
    """برهانٌ سلبي: ادّعاءٌ يعتمد على مسحوبٍ ولا تلتقطه الأداة ⇒ الحكمُ ناقص."""
    shadow = _claim(claim_id="SHADOW", depends_on=("RSM_DAY_BUDGET",))
    assert adjudicate(shadow).state is ClaimState.VOID_WITHDRAWN
    assert shadow.claim_id not in {c.claim_id for c in CLAIMS}


def test_k5_is_stated_as_a_condition_on_the_actor() -> None:
    """العائقُ الأخيرُ ليس معرفةً — وشرطُ قتله مكتوبٌ كذلك."""
    k5 = next(k for k in kill_switches() if k["id"] == "K5")
    assert "T66" in k5["observable_ar"] and "T78" in k5["observable_ar"]


# ── الحمولةُ والبصمة ────────────────────────────────────────────────────────────


def test_declared_zeros_are_all_zero_and_no_revenue() -> None:
    z = measure_all()["declared_zeros"]
    assert z["revenue_claim"] == "NONE"
    for key, value in z.items():
        if key != "revenue_claim":
            assert value == 0, key


def test_fingerprint_is_deterministic() -> None:
    assert inputs_fingerprint() == inputs_fingerprint()
    assert len(inputs_fingerprint()) == 64


def test_fingerprint_is_computed_not_written() -> None:
    """⛔ البصمةُ المكتوبةُ باليد ادّعاء — لا تُقرأ من الملفّ بل تُعاد."""
    source = TOOL.read_text(encoding="utf-8")
    assert "hashlib.sha256" in source
    filed = json.loads(MEASUREMENTS.read_text(encoding="utf-8"))
    assert filed["inputs_fingerprint"] == inputs_fingerprint()


def test_measure_all_is_deterministic() -> None:
    assert json.dumps(measure_all(), sort_keys=True) == json.dumps(measure_all(), sort_keys=True)


def test_measure_all_carries_the_limits() -> None:
    limits = measure_all()["limits_ar"]
    joined = " ".join(limits)
    assert "ليس رأياً قانونياً" in joined
    assert "لا خطَّ عرضٍ ثامن" in joined
    assert "لا رقمَ إيراد" in joined


def test_filed_measurements_match_recomputation() -> None:
    """بوّابةُ الانحراف: الملفّ المودَع = إعادةُ الحساب، حرفاً بحرف."""
    filed = json.loads(MEASUREMENTS.read_text(encoding="utf-8"))
    fresh = measure_all()
    for key in ("batch", "as_of", "declared_zeros", "inputs_fingerprint", "results", "limits_ar"):
        assert filed[key] == fresh[key], key


def test_no_offer_line_is_promoted_by_this_batch() -> None:
    """هذه الدفعة قياسٌ لا عرض — لا خطَّ فوق `PROPOSED` بلا معاملةٍ مُسوّاة.

    حصرُ السبعة ألغاه المالك في D-296؛ والشرط الباقي (D-297) بنيويّ: مُعرِّفٌ فريد
    لكلّ خطّ، ولا ترقيةَ بلا معاملة. عدُّ الخطوط هنا كان يُحمِّر `main` بعد إلغاء الحصر.
    """
    offers = json.loads(
        (REPO_ROOT / "docs" / "commercial" / "OFFER_CATALOG.json").read_text("utf-8")
    )["offers"]
    ids = [offer.get("id") for offer in offers]
    assert offers
    assert all(ids) and len(ids) == len(set(ids))
    assert all(offer.get("status") == "PROPOSED" for offer in offers)
