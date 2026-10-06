"""موجّه «مركز العملة الصعبة» (D-305) — **للمدير وحده**.

  • ``GET  /admin/api/hard-currency/frontier``                    — خريطة الجبهة: 25 مساراً على السلسلة.
  • ``POST /admin/api/hard-currency/einvoicing-audits``           — ورشة الفوترة FR/BE (CSV · بلا تخزين).
  • ``GET  /admin/api/hard-currency/cbam/codes``                  — رموز CN المدبوسة.
  • ``GET  /admin/api/hard-currency/cbam/codes/{cn}``             — القيم والعتبة ورسم المسار لسنة.
  • ``POST /admin/api/hard-currency/cbam/codes/{cn}/decision``    — رقم المنشأة ⇒ أوّل سنةٍ أرخص.
  • ``GET  /admin/api/hard-currency/redteam/classes``             — أصناف الاختراق وحالة نشرها.
  • ``GET  /admin/api/hard-currency/chamber``                     — غرفة القرار (D-314): أقصى ما يُقال،
    وأوّل دليلٍ ناقص، وفعلٌ بشريٌّ واحد — بجملٍ مُصنَّفة لكلٍّ دليلها.
  • ``POST /admin/api/hard-currency/chamber/cross-examination``   — سؤالٌ من مجموعةٍ مغلقة (لا محادثة حرّة).
  • ``POST /admin/api/hard-currency/chamber/outcome-preview``     — صفُّ سجلٍّ مقترَح ⇒ مقبولٌ أو مرفوض
    بأسبابه وما يتغيّر. ⛔ لا يُكتب شيء: المالك يلتزم السطر عبر git.

الموجِّه رقيق: الحساب في المحرّكات القائمة، والتغليف في ``app/services/hard_currency/``. وغيابُ
مصدرٍ في هذا النشر ⇒ 503 بسببٍ منطوق — لا قائمةٌ فارغة تُقرأ «لا شيء» (§0: المجهول أفضل من
يقين زائف). ⛔ لا نموذج لغوي في أيّ مسارٍ هنا، ولا كتابة في جداول الرسائل.
"""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, Request, UploadFile
from pydantic import Field, JsonValue

from app.core.schemas import RobustBaseModel
from app.deps.auth import CurrentUser, require_roles
from app.middleware.rate_limiter_middleware import TokenBucketRateLimiter
from app.services.hard_currency import (
    cbam_explorer,
    decision_chamber,
    einvoicing_audit,
    frontier,
    redteam_classes,
)
from app.services.hard_currency.sources import (
    HardCurrencySources,
    InputRejectedError,
    SourceUnavailableError,
    get_hard_currency_sources,
)
from app.services.rbac import ADMIN_ROLE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/api/hard-currency", tags=["Hard-Currency Center"])

#: العمليات الحسابية/الرفع فقط — القراءة الخفيفة بلا حدّ.
_compute_limiter = TokenBucketRateLimiter(max_requests=30, window_seconds=60)


async def _rate_limited(
    request: Request, current: CurrentUser = Depends(require_roles(ADMIN_ROLE))
) -> CurrentUser:
    request.state.user_id = current.user.id
    allowed, metadata = _compute_limiter.is_allowed(request)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="طلباتٌ كثيرة — أعد المحاولة بعد قليل",
            headers={"Retry-After": str(metadata.get("retry_after", 1))},
        )
    return current


def _raise_http(exc: Exception) -> None:
    if isinstance(exc, InputRejectedError):
        raise HTTPException(status_code=exc.status_code, detail=exc.reason_ar) from exc
    if isinstance(exc, SourceUnavailableError):
        logger.warning("hard_currency_source_unavailable", extra={"reason": exc.reason_ar})
        raise HTTPException(status_code=503, detail=exc.reason_ar) from exc
    raise exc


class FrontierResponse(RobustBaseModel):
    as_of: str | None
    gate_c: str | None
    funnel: dict[str, JsonValue] | None
    by_classification: dict[str, int]
    next_actor_human: int
    next_actor_code: int
    committed_snapshot_current: bool
    links: list[dict[str, JsonValue]]
    paths: list[dict[str, JsonValue]]


class AuditResponse(RobustBaseModel):
    corridor: str
    filename: str
    summary: dict[str, JsonValue]
    anomalies: list[dict[str, JsonValue]]
    anomalies_truncated: bool
    report_markdown: str
    cleaned_csv: str
    cleaned_filename: str
    stored: bool
    online_checks: bool


class CbamCodesResponse(RobustBaseModel):
    provenance: dict[str, JsonValue]
    codes: list[dict[str, JsonValue]]


class CbamDetailResponse(RobustBaseModel):
    cn: str
    sector: str
    description: str
    default_see_t: dict[str, float | None]
    computable: bool
    absent_reason: str | None
    provenance: dict[str, JsonValue]
    year: int | None = None
    certificates_default: dict[str, JsonValue] | None = None
    crossover: dict[str, JsonValue] | None = None
    path_toll: dict[str, JsonValue] | None = None
    trajectory: list[dict[str, JsonValue]] | None = None


class CbamDecisionRequest(RobustBaseModel):
    see_actual: float = Field(
        ..., gt=0, le=cbam_explorer.MAX_SEE_T, description="tCO₂e/t مقيسٌ للمنشأة"
    )


class CbamDecisionResponse(RobustBaseModel):
    cn: str
    see_actual_t: float
    first_sellable_year: int | None
    never_within_horizon: bool
    trajectory: list[dict[str, JsonValue]]
    provenance: dict[str, JsonValue]
    reading_ar: str


class RedTeamResponse(RobustBaseModel):
    source: str
    decision: str | None
    classes: list[dict[str, JsonValue]]
    publishable_count: int
    external_probe: dict[str, JsonValue] | None


@router.get("/frontier", response_model=FrontierResponse, summary="Value-chain frontier")
async def get_frontier(
    _: CurrentUser = Depends(require_roles(ADMIN_ROLE)),
    sources: HardCurrencySources = Depends(get_hard_currency_sources),
) -> FrontierResponse:
    """كلّ مسارٍ بتصنيفه المُشتقّ وحلقته التالية وفاعلها — والقمع الحقيقي في الأعلى."""
    try:
        return FrontierResponse.model_validate(frontier.build_frontier(sources))
    except (InputRejectedError, SourceUnavailableError) as exc:
        _raise_http(exc)
        raise


@router.post("/einvoicing-audits", response_model=AuditResponse, summary="E-invoicing audit")
async def post_einvoicing_audit(
    file: UploadFile = File(..., description="ملفّ أطرافٍ ثالثة CSV"),
    corridor: str = Form(..., description="fr أو be"),
    _: CurrentUser = Depends(_rate_limited),
) -> AuditResponse:
    """تدقيقٌ حتمي بلا شبكة. ⛔ الملفّ لا يُخزَّن ولا يُسجَّل محتواه."""
    content = await file.read(einvoicing_audit.MAX_UPLOAD_BYTES + 1)
    try:
        result = einvoicing_audit.run_audit(
            corridor=corridor, filename=file.filename or "", content=content
        )
    except (InputRejectedError, SourceUnavailableError) as exc:
        _raise_http(exc)
        raise
    logger.info(
        "hard_currency_audit_completed",
        extra={"corridor": corridor, "rows": result["summary"].get("total")},
    )
    return AuditResponse.model_validate(result)


@router.get("/cbam/codes", response_model=CbamCodesResponse, summary="Pinned CBAM codes")
async def get_cbam_codes(
    _: CurrentUser = Depends(require_roles(ADMIN_ROLE)),
) -> CbamCodesResponse:
    return CbamCodesResponse.model_validate(cbam_explorer.list_codes())


@router.get("/cbam/codes/{cn}", response_model=CbamDetailResponse, summary="Pinned CBAM detail")
async def get_cbam_detail(
    cn: str = Path(..., max_length=12),
    year: int = Query(2026),
    _: CurrentUser = Depends(require_roles(ADMIN_ROLE)),
) -> CbamDetailResponse:
    try:
        return CbamDetailResponse.model_validate(cbam_explorer.code_detail(cn, year))
    except InputRejectedError as exc:
        _raise_http(exc)
        raise


@router.post(
    "/cbam/codes/{cn}/decision", response_model=CbamDecisionResponse, summary="CBAM decision"
)
async def post_cbam_decision(
    payload: CbamDecisionRequest,
    cn: str = Path(..., max_length=12),
    _: CurrentUser = Depends(_rate_limited),
) -> CbamDecisionResponse:
    try:
        return CbamDecisionResponse.model_validate(cbam_explorer.decision(cn, payload.see_actual))
    except InputRejectedError as exc:
        _raise_http(exc)
        raise


@router.get("/redteam/classes", response_model=RedTeamResponse, summary="AR/FR exploit classes")
async def get_redteam_classes(
    _: CurrentUser = Depends(require_roles(ADMIN_ROLE)),
    sources: HardCurrencySources = Depends(get_hard_currency_sources),
) -> RedTeamResponse:
    try:
        return RedTeamResponse.model_validate(redteam_classes.list_classes(sources))
    except SourceUnavailableError as exc:
        _raise_http(exc)
        raise


# ── غرفة القرار (D-314) ─────────────────────────────────────────────────────────


class ChamberResponse(RobustBaseModel):
    snapshot: dict[str, JsonValue]
    brief: dict[str, JsonValue]
    sentences: list[dict[str, JsonValue]]
    questions: list[str]
    ledger_vocabulary: dict[str, list[str]]


class CrossExaminationRequest(RobustBaseModel):
    question: Literal["ready", "build", "why_no_money", "say_to_buyer"]
    text: str | None = Field(
        None,
        max_length=decision_chamber.MAX_BUYER_TEXT_CHARS,
        description="لـsay_to_buyer وحده: الجملة المراد قولها للمشتري",
    )


class CrossExaminationResponse(RobustBaseModel):
    question: str
    verdict: str | None
    findings: list[dict[str, JsonValue]] | None
    sentences: list[dict[str, JsonValue]]


class OutcomePreviewRequest(RobustBaseModel):
    """صفٌّ مقترَح بأعمدة ``CONTACT_LEDGER.csv`` — يُتحقَّق منه ولا يُكتب."""

    date: str = Field(..., max_length=10)
    target_ref: str = Field(..., max_length=200)
    entity: str = Field(..., max_length=200)
    country: str = Field(..., max_length=8)
    channel: str = Field(..., max_length=32)
    action: str = Field(..., max_length=32)
    amount_eur: str = Field("", max_length=32)
    evidence_ref: str = Field("", max_length=300)
    note: str = Field("", max_length=1000)


class OutcomePreviewResponse(RobustBaseModel):
    accepted: bool
    problems: list[str]
    csv_line: str
    written: bool
    ledger: str
    commit_hint_ar: str
    delta: dict[str, JsonValue] | None = None


@router.get("/chamber", response_model=ChamberResponse, summary="Decision chamber")
async def get_chamber(
    _: CurrentUser = Depends(require_roles(ADMIN_ROLE)),
    sources: HardCurrencySources = Depends(get_hard_currency_sources),
) -> ChamberResponse:
    """أقصى ما يحقّ قوله، وأوّل دليلٍ ناقص، وفعلٌ بشريٌّ واحد — أو امتناعٌ بسببه (503)."""
    try:
        return ChamberResponse.model_validate(decision_chamber.chamber(sources))
    except (InputRejectedError, SourceUnavailableError) as exc:
        _raise_http(exc)
        raise


@router.post(
    "/chamber/cross-examination",
    response_model=CrossExaminationResponse,
    summary="Decision chamber cross-examination",
)
async def post_cross_examination(
    payload: CrossExaminationRequest,
    _: CurrentUser = Depends(_rate_limited),
    sources: HardCurrencySources = Depends(get_hard_currency_sources),
) -> CrossExaminationResponse:
    """سؤالٌ من المجموعة المغلقة ⇒ جملٌ مُصنَّفة. ⛔ النصّ لا يُخزَّن ولا يُسجَّل."""
    try:
        return CrossExaminationResponse.model_validate(
            decision_chamber.examine(sources, payload.question, payload.text)
        )
    except (InputRejectedError, SourceUnavailableError) as exc:
        _raise_http(exc)
        raise


@router.post(
    "/chamber/outcome-preview",
    response_model=OutcomePreviewResponse,
    summary="Decision chamber outcome preview",
)
async def post_outcome_preview(
    payload: OutcomePreviewRequest,
    _: CurrentUser = Depends(_rate_limited),
    sources: HardCurrencySources = Depends(get_hard_currency_sources),
) -> OutcomePreviewResponse:
    """الصفّ ⇒ مقبولٌ أو مرفوضٌ بأسبابه، والسطر، وما يتغيّر. ⛔ لا يُكتب شيء."""
    try:
        result = decision_chamber.preview(sources, payload.model_dump())
    except (InputRejectedError, SourceUnavailableError) as exc:
        _raise_http(exc)
        raise
    logger.info(
        "hard_currency_outcome_previewed",
        extra={"action": payload.action, "accepted": result.get("accepted")},
    )
    return OutcomePreviewResponse.model_validate(result)
