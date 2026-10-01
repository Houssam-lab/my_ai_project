"""نافذة قراءةٍ على المحرّك المدبوس ``shared/research/cbam_pin.py`` — بلا منطق CBAM جديد (D-305).

كلّ رقمٍ هنا مدبوسٌ من ملحق IR 2025/2620 داخل المحرّك المختبَر (95 اختباراً). ⛔ لا انبعاثٌ
مُخترَع: رقم المنشأة يُدخله المشتري ولا نملكه. ⛔ والأداة القديمة ``tools/.../cbam_calculator.py``
تبقى مسحوبة (≈71× — D-297 §4) ولا تُستورَد.
"""

from __future__ import annotations

from app.services.hard_currency.sources import InputRejectedError
from shared.research import cbam_pin

#: سقفٌ للمُدخَل — أعلى من أيّ قيمةٍ افتراضيةٍ مدبوسة بهامشٍ واسع، وأدنى من خطأ إدخال وحدات.
MAX_SEE_T = 50.0


def _normalized(cn: str) -> str:
    code = "".join(ch for ch in (cn or "") if ch.isdigit())
    if code not in cbam_pin.ALGERIA_DEFAULTS:
        raise InputRejectedError(404, f"رمز CN غير مدبوس: {cn!r}")
    return code


def _year(year: int) -> int:
    if year not in cbam_pin.HORIZON:
        raise InputRejectedError(
            422, f"السنة {year} خارج الأفق المدبوس {cbam_pin.HORIZON[0]}–{cbam_pin.HORIZON[-1]}"
        )
    return year


def _provenance() -> dict[str, object]:
    asymmetry = cbam_pin.column_asymmetry()
    return {
        "source_ar": "ملحق IR 2025/2620 — قيمٌ مدبوسة في shared/research/cbam_pin.py",
        "inputs_fingerprint": cbam_pin.inputs_fingerprint(),
        "quarter": cbam_pin.DEFAULT_QUARTER,
        "horizon": list(cbam_pin.HORIZON),
        "route_pairs_pinned": asymmetry["route_pairs_pinned"],
        "pairs_where_switching_forfeits_credit": asymmetry["column_b_larger"],
        "pairs_without_toll": asymmetry["columns_equal"],
    }


def list_codes() -> dict[str, object]:
    pinned = cbam_pin.pinned_codes()
    codes = []
    for cn, meta in sorted(pinned.items()):
        row = cbam_pin.ALGERIA_DEFAULTS[cn]
        codes.append(
            {
                "cn": cn,
                "sector": meta["sector"],
                "description": row.description,
                "route": row.route,
                "computable": bool(meta["rankable"]),
                "absent_reason": meta["absent_reason"],
            }
        )
    return {"provenance": _provenance(), "codes": codes}


def code_detail(cn: str, year: int) -> dict[str, object]:
    code = _normalized(cn)
    _year(year)
    meta = cbam_pin.pinned_codes()[code]
    row = cbam_pin.ALGERIA_DEFAULTS[code]
    base: dict[str, object] = {
        "cn": code,
        "sector": row.sector,
        "description": row.description,
        "default_see_t": {"direct": row.direct, "indirect": row.indirect, "total": row.total},
        "computable": bool(meta["rankable"]),
        "absent_reason": meta["absent_reason"],
        "provenance": _provenance(),
    }
    if not meta["rankable"]:
        # لا رقم بدل رقمٍ مضلِّل: السبب يُعرَض كما سجّله المحرّك.
        return base
    try:
        base.update(
            {
                "year": year,
                "certificates_default": cbam_pin.certificates_default(code, year),
                "crossover": cbam_pin.crossover_see(code, year),
                "path_toll": cbam_pin.path_toll(code, year),
                "trajectory": [
                    {
                        "year": y,
                        "crossover_see_t": cbam_pin.crossover_see(code, y)["crossover_see_t"],
                    }
                    for y in cbam_pin.HORIZON
                ],
            }
        )
    except cbam_pin.PinError as exc:
        raise InputRejectedError(422, str(exc)) from exc
    return base


def decision(cn: str, see_actual: float) -> dict[str, object]:
    """رقم المنشأة المقيس ⇒ أوّل سنةٍ يصير فيها إعلان البيانات الفعلية أرخص، أو لا ضمن الأفق."""
    code = _normalized(cn)
    if not (0.0 < see_actual <= MAX_SEE_T):
        raise InputRejectedError(422, f"الانبعاث المقيس يجب أن يكون > 0 و≤ {MAX_SEE_T} tCO₂e/t")
    try:
        result = cbam_pin.first_sellable_year(code, see_actual)
    except cbam_pin.PinError as exc:
        raise InputRejectedError(422, str(exc)) from exc
    return {
        **result,
        "provenance": _provenance(),
        "reading_ar": (
            "أداة قرار لا إعلانٌ رسمي: المقارنة بين رقم منشأتك وعتبة العبور المدبوسة. "
            "رقم المنشأة يجب أن يكون مُتحقَّقاً منه قبل أيّ إعلان."
        ),
    }
