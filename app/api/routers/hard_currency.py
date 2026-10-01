"""موجّه «مركز العملة الصعبة» (D-305) — **للمدير وحده**.

  • ``GET  /admin/api/hard-currency/frontier``                    — خريطة الجبهة: 25 مساراً على السلسلة.
  • ``POST /admin/api/hard-currency/einvoicing-audits``           — ورشة الفوترة FR/BE (CSV · بلا تخزين).
  • ``GET  /admin/api/hard-currency/cbam/codes``                  — رموز CN المدبوسة.
  • ``GET  /admin/api/hard-currency/cbam/codes/{cn}``             — القيم والعتبة ورسم المسار لسنة.
  • ``POST /admin/api/hard-currency/cbam/codes/{cn}/decision``    — رقم المنشأة ⇒ أوّل سنةٍ أرخص.
  • ``GET  /admin/api/hard-currency/redteam/classes``             — أصناف الاختراق وحالة نشرها.

الموجِّه رقيق: الحساب في المحرّكات القائمة، والتغليف في ``app/services/hard_currency/``. وغيابُ
مصدرٍ في هذا النشر ⇒ 503 بسببٍ منطوق — لا قائمةٌ فارغة تُقرأ «لا شيء» (§0: المجهول أفضل من
يقين زائف). ⛔ لا نموذج لغوي في أيّ مسارٍ هنا، ولا كتابة في جداول الرسائل.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, Request, UploadFile
from pydantic import Field

from app.core.schemas import RobustBaseModel
from app.deps.auth import CurrentUser, require_roles
from app.middleware.rate_limiter_middleware import TokenBucketRateLimiter
from app.services.hard_currency import cbam_explorer, einvoicing_audit, frontier, redteam_classes
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
    funnel: dict[str, Any] | None
    by_classification: dict[str, int]
    next_actor_human: int
    next_actor_code: int
    committed_snapshot_current: bool
    links: list[dict[str, Any]]
    paths: list[dict[str, Any]]


class AuditResponse(RobustBaseModel):
    corridor: str
    filename: str
    summary: dict[str, Any]
    anomalies: list[dict[str, Any]]
    anomalies_truncated: bool
    report_markdown: str
    cleaned_csv: str
    cleaned_filename: str
    stored: bool
    online_checks: bool


class CbamCodesResponse(RobustBaseModel):
    provenance: dict[str, Any]
    codes: list[dict[str, Any]]


class CbamDetailResponse(RobustBaseModel):
    cn: str
    sector: str
    description: str
    default_see_t: dict[str, float | None]
    computable: bool
    absent_reason: str | None
    provenance: dict[str, Any]
    year: int | None = None
    certificates_default: dict[str, Any] | None = None
    crossover: dict[str, Any] | None = None
    path_toll: dict[str, Any] | None = None
    trajectory: list[dict[str, Any]] | None = None


class CbamDecisionRequest(RobustBaseModel):
    see_actual: float = Field(
        ..., gt=0, le=cbam_explorer.MAX_SEE_T, description="tCO₂e/t مقيسٌ للمنشأة"
    )


class CbamDecisionResponse(RobustBaseModel):
    cn: str
    see_actual_t: float
    first_sellable_year: int | None
    never_within_horizon: bool
    trajectory: list[dict[str, Any]]
    provenance: dict[str, Any]
    reading_ar: str


class RedTeamResponse(RobustBaseModel):
    source: str
    decision: str | None
    classes: list[dict[str, Any]]
    publishable_count: int
    external_probe: dict[str, Any] | None


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
