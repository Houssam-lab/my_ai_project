"""اختبار تفاضلي للمصادقة بين المونوليث و`user_service` — الحقيقة قبل الإصلاح.

**ما الذي يحرسه هذا الملف؟**

للمستودع نسختان حيّتان من منطق JWT، وبقاؤهما متوازيتين **مقصود** لا عرضيّ:
`microservices/user_service/src/services/auth/crypto.py` يُصرّح في تعليقه أنه
"لمطابقة monolith's app/services/auth/crypto.py". إذن التكافؤ عقدٌ مكتوب،
وليس صدفةً يجوز أن تنحرف بصمت.

وقد انحرف. هذا الملف يُثبت الانحراف بالتنفيذ — يُحمّل **النسختين الحقيقيتين**
في عملية واحدة بالمفتاح نفسه (وهو ما يفعله `tests/conftest.py` فعلاً، وهو ما
وحّده D-WS-SECRET-KEY-001)، ثم يُصدر بإحداهما ويتحقّق بالأخرى.

**تحذير من المبالغة — هذا ليس تجاوزاً للمصادقة.**
كل رمز مقبول أدناه موقّعٌ توقيعاً صحيحاً، أي أن صاحبه مُصادَقٌ أصلاً. الخلل
هو **التباس نوع/نطاق** (type confusion): رمزٌ أُصدر لغرضٍ ضيّق يُقبَل لغرضٍ
أوسع. خطيرٌ بما يكفي ليُحرَس، وليس ثقباً يدخل منه مجهول.

**كيف وُلد الخلل؟** من تركيب إصلاحَين صحيحَين كلٌّ على حدة:
  · D-236 أضاف مطالبة `type` إلى المونوليث وحده، وأبقى بند توافق يقبل الرموز
    الخالية من `type` كرموز وصول (تدهور رشيق: لا تُطرد الجلسات القائمة).
  · D-WS-SECRET-KEY-001 وحّد `SECRET_KEY` عبر الخدمات.
أيٌّ منهما وحده سليم. معاً: رمزٌ مُصدَرٌ في أي خدمة صالحٌ في كل خدمة، و
`user_service` لا يُصدر `type` إطلاقاً — فتمرّ رموزه كلّها عبر بند التوافق.

**لماذا `xfail(strict=True)` ولم يُصلَح هنا؟**
الإصلاح قرار معماري لمالك النظام، لا للاختبار: بند التوافق **حامل للحِمل** لا
بقيّة أثرية — `app/services/boundaries/auth_boundary_service.py` ينادي
`user_service` أولاً وبلا راية، فكل تسجيل دخول عبر ذلك المسار يُصادَق اليوم
بالفرع "القديم". حذف البند بلا تسلسل هجرة يكسر الدخول. فالاختبار يُثبّت العقد
المطلوب ويبقى `xfail` حتى يُستوفى؛ و`strict=True` تعني أن أول من يُصلح الخلل
سيرى هذه الاختبارات **تفشل بالنجاح** (XPASS) فيُجبَر على رفع العلامة — فلا
يُغلَق الثقب بصمتٍ ولا يُنسى مفتوحاً.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import jwt
import pytest
from fastapi import HTTPException

from app.core.config import get_settings as get_monolith_settings
from app.services.auth.crypto import (
    ACCESS_TOKEN_TYPE,
    REAUTH_TOKEN_TYPE,
    SERVICE_TOKEN_TYPE,
)
from app.services.auth.crypto import AuthCrypto as MonolithCrypto
from microservices.user_service.src.services.auth.crypto import AuthCrypto as UserServiceCrypto

pytestmark = pytest.mark.security


# ── مُعينات ───────────────────────────────────────────────────────────────
# الدالّتان `encode_*` تقرآن من المستخدم حقلين فقط (`id` و`is_admin`)، فبديلٌ
# خفيف يكفي: لا قاعدة بيانات، ولا تثبيت لنموذجٍ قد يتغيّر. الاختبار يقيس
# منطق الرموز، لا طبقة البيانات.
def _user() -> SimpleNamespace:
    return SimpleNamespace(id=uuid.uuid4(), is_admin=False)


@pytest.fixture
def mono() -> MonolithCrypto:
    # المونوليث يحقن الإعدادات، والخدمة تجلبها بنفسها — فارقٌ تصميميّ قائم
    # نلتزم به كما هو بدل توحيده هنا؛ هذا الملف يقيس ولا يُعيد التصميم.
    return MonolithCrypto(get_monolith_settings())


@pytest.fixture
def usvc() -> UserServiceCrypto:
    return UserServiceCrypto()


def _accepts(fn, token: str) -> bool:
    """هل يَقبل هذا المُتحقِّق الرمز؟ — 401 وحدها تعني الرفض."""
    try:
        fn(token)
    except HTTPException as exc:
        if exc.status_code == 401:
            return False
        raise
    return True


def _secret(crypto) -> str:
    return str(crypto.settings.SECRET_KEY)


# ── 1. المقدّمة التي تجعل الاختبار ذا معنى ────────────────────────────────
def test_both_services_share_one_signing_key(mono, usvc):
    """المفتاح موحَّد (D-WS-SECRET-KEY-001) — وهذا سببُ عبور الرموز الحدود.

    لو انفصل المفتاحان لسقط كل ما بعده بلا معنى؛ فنُثبته أولاً صراحةً بدل
    افتراضه ضمناً.
    """
    assert _secret(mono) == _secret(usvc)


# ── 2. تكافؤٌ قائم — يُقفَل حتى لا ينحدر ──────────────────────────────────
# هذه ليست حشواً: هي الضمانات التي **صمدت**، وقيمتها أن انحدارها سيُكتشف.
@pytest.mark.parametrize(
    "name, make",
    [
        (
            "wrong_secret",
            lambda _c: jwt.encode({"sub": "x"}, "a-different-secret-entirely", algorithm="HS256"),
        ),
        ("alg_none", lambda _c: jwt.encode({"sub": "x"}, "", algorithm="none")),
        ("garbage", lambda _c: "not.a.jwt"),
        ("empty", lambda _c: ""),
        (
            "expired",
            lambda c: jwt.encode(
                {
                    "sub": "x",
                    "type": ACCESS_TOKEN_TYPE,
                    "exp": datetime.now(UTC) - timedelta(hours=1),
                },
                _secret(c),
                algorithm="HS256",
            ),
        ),
    ],
)
def test_both_services_reject_the_same_bad_tokens(mono, usvc, name, make):
    """نظافة التوقيع متكافئة: لا نسخةَ أضعف من الأخرى أمام رمزٍ فاسد."""
    assert not _accepts(lambda t: mono.verify_jwt(t, expected_type=ACCESS_TOKEN_TYPE), make(mono))
    assert not _accepts(usvc.verify_jwt, make(usvc))


def test_each_service_accepts_its_own_access_token(mono, usvc):
    """خطّ الأساس: المسار السعيد يعمل في النسختين."""
    assert _accepts(
        lambda t: mono.verify_jwt(t, expected_type=ACCESS_TOKEN_TYPE),
        mono.encode_access_token(_user(), ["user"], {"read"}),
    )
    assert _accepts(usvc.verify_jwt, usvc.encode_access_token(_user(), ["user"], {"read"}))


def test_monolith_rejects_its_own_reauth_token_as_access(mono):
    """D-236 يعمل **داخل** المونوليث — الحارس موجود، لكنه لا يرى عبر الحدود.

    مرور هذا الاختبار مع فشل ما بعده هو بالضبط شكل الخلل: ليس حارساً غائباً،
    بل حارساً أعمى عن رموز الجار.
    """
    token, _ = mono.encode_reauth_token(_user())
    assert not _accepts(lambda t: mono.verify_jwt(t, expected_type=ACCESS_TOKEN_TYPE), token)


# ── 3. السبب الجذري ───────────────────────────────────────────────────────
def test_user_service_tokens_carry_no_type_claim_today(mono, usvc):
    """توصيفٌ للواقع: رموز الخدمة بلا `type`، ورموز المونوليث تحمله.

    هذا الاختبار **يصف** ولا يُبارك. هو الفارق الواحد الذي تتفرّع منه كل
    الأعراض أدناه، ويبقى ناجحاً حتى يُسَدّ الفارق — وعندها يُحذف مع العلامات.
    """
    usvc_access = jwt.decode(
        usvc.encode_access_token(_user(), ["user"], {"read"}), _secret(usvc), algorithms=["HS256"]
    )
    usvc_reauth = jwt.decode(
        usvc.encode_reauth_token(_user())[0], _secret(usvc), algorithms=["HS256"]
    )
    mono_access = jwt.decode(
        mono.encode_access_token(_user(), ["user"], {"read"}), _secret(mono), algorithms=["HS256"]
    )

    assert "type" not in usvc_access
    assert "type" not in usvc_reauth
    assert mono_access.get("type") == ACCESS_TOKEN_TYPE


# ── 4. العقد المطلوب — مفتوحٌ عمداً حتى يُتّخذ قرار الهجرة ────────────────
@pytest.mark.xfail(
    strict=True,
    reason=(
        "فجوة معروفة: `user_service.encode_*` لا يُصدر `type`. "
        "عند سدّها تنجح هذه الحالة فيلزم رفع العلامة."
    ),
)
def test_contract_user_service_should_stamp_token_type(usvc):
    """العقد: كل رمزٍ يقول **لماذا** أُصدر، في النسختين لا في واحدة."""
    access = jwt.decode(
        usvc.encode_access_token(_user(), ["user"], {"read"}), _secret(usvc), algorithms=["HS256"]
    )
    reauth = jwt.decode(usvc.encode_reauth_token(_user())[0], _secret(usvc), algorithms=["HS256"])
    assert access.get("type") == ACCESS_TOKEN_TYPE
    assert reauth.get("type") == REAUTH_TOKEN_TYPE


@pytest.mark.xfail(
    strict=True,
    reason=(
        "فجوة معروفة: `verify_access_token` ينادي `verify_jwt` بلا `expected_type`، "
        "فرمز إعادة المصادقة يمرّ كرمز وصول داخل الخدمة نفسها."
    ),
)
def test_contract_user_service_should_reject_reauth_as_access(usvc):
    """العقد: ما يرفضه المونوليث لنفسه يجب أن ترفضه الخدمة لنفسها."""
    token, _ = usvc.encode_reauth_token(_user())
    assert not _accepts(usvc.verify_jwt, token)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "فجوة معروفة: بند التوافق في المونوليث يقبل الرموز الخالية من `type` "
        "كرموز وصول، ورموز `user_service` كلّها كذلك."
    ),
)
def test_contract_monolith_should_reject_user_service_reauth_as_access(mono, usvc):
    """**العَرَض الأخطر**: رمز إعادة مصادقة من الخدمة يصير وصولاً كاملاً في المونوليث.

    رمز إعادة المصادقة عمره دقائق ودوره إثبات حضورٍ لحظي قبل عمليةٍ حسّاسة؛
    قبوله كرمز وصول يمنحه نطاقاً ومدّةً لم يُصدَر لهما.
    """
    token, _ = usvc.encode_reauth_token(_user())
    assert not _accepts(lambda t: mono.verify_jwt(t, expected_type=ACCESS_TOKEN_TYPE), token)


@pytest.mark.xfail(
    strict=True,
    reason="فجوة معروفة: `verify_access_token` لا يفحص النوع، فيقبل رمز الخدمة الداخلي.",
)
def test_contract_user_service_should_reject_internal_service_token(mono, usvc):
    """رمز الخدمة الداخلي ليس رمز مستخدم، ولا يجوز أن يُقبَل كواحد."""
    service_token = jwt.encode(
        {
            "sub": "monolith",
            "type": SERVICE_TOKEN_TYPE,
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        _secret(mono),
        algorithm="HS256",
    )
    assert not _accepts(usvc.verify_jwt, service_token)
