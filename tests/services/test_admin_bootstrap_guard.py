"""حارس تهيئة المدير (ISS-210) — وعقد كلمة سرّ المالك (K-001).

الواقع المقيس في الإنتاج (2026-10-01، قراءةٌ عبر موصِّل Supabase): ثلاثة حسابات مدير نشطة.
حساب المالك، و``admin@cogniforge.com`` (افتراضيّ الكود: 740 إقلاعاً حتى 2026-09-29)،
و``admin@example.com`` (افتراضيّ ``supervisor.sh``). كلاهما بلا مالك، وكلمة سرّه الافتراضية
منشورة في المستودع. والإقلاع يعيد تفعيلهما فيُلغى أيّ تعطيل يدويّ.

وكان ``scripts/ensure_admin.py`` يعيد كتابة كلمة سرّ المدير القائم في كلّ إقلاع.
"""

from __future__ import annotations

import ast
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.domain.user import User
from app.core.settings.helpers import DEFAULT_ADMIN_EMAIL, is_placeholder_admin_email
from app.services.bootstrap import (
    AdminBootstrapRefusedError,
    bootstrap_admin_account,
    is_local_database_url,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

#: مضيفٌ بعيد بصيغة Supabase المباشرة — لا يُتّصل به: الحارس يرفض قبل أيّ عبارة.
REMOTE_URL = "postgresql+asyncpg://postgres:x@db.remote-project.supabase.co:5432/postgres"


def _settings(email: str, password: str, *, force: str | None = None) -> MagicMock:
    settings = MagicMock()
    settings.ADMIN_EMAIL = email
    settings.ADMIN_PASSWORD = password
    settings.ADMIN_NAME = "Admin"
    settings.ADMIN_FORCE_PASSWORD_SYNC = force
    return settings


@pytest.mark.parametrize(
    "email",
    [
        DEFAULT_ADMIN_EMAIL,
        "ADMIN@COGNIFORGE.COM ",
        "admin@example.com",
        "ops@sub.example.org",
        "admin@cogniforge.test",
        "root@corp.invalid",
        "admin@localhost",
    ],
)
def test_placeholder_emails_are_recognized(email: str) -> None:
    assert is_placeholder_admin_email(email)


@pytest.mark.parametrize(
    "email",
    ["owner@gmail.com", "admin@cogniforge.dz", "admin@example.com.dz", "", "no-at-sign"],
)
def test_real_emails_are_not_placeholders(email: str) -> None:
    assert not is_placeholder_admin_email(email)


@pytest.mark.parametrize(
    ("url", "local"),
    [
        ("sqlite+aiosqlite:///:memory:", True),
        ("postgresql+asyncpg://u:p@localhost:5432/db", True),
        ("postgresql+asyncpg://u:p@127.0.0.1:5432/db", True),
        ("postgresql+asyncpg://u:p@[::1]:5432/db", True),
        ("postgresql+asyncpg://u:p@10.0.0.5:5432/db", True),
        ("postgresql+asyncpg://u:p@postgres:5432/db", True),
        (REMOTE_URL, False),
        ("postgresql+asyncpg://u:p@aws-0-eu-west-3.pooler.supabase.com:6543/db", False),
        ("postgresql+asyncpg://u:p@8.8.8.8:5432/db", False),
        ("postgresql+asyncpg://u:p@/db", False),
    ],
)
def test_local_database_classification(url: str, local: bool) -> None:
    assert is_local_database_url(make_url(url)) is local


def test_unknown_bind_is_treated_as_remote() -> None:
    assert is_local_database_url(None) is False


@pytest.mark.asyncio
@pytest.mark.parametrize("email", [DEFAULT_ADMIN_EMAIL, "admin@example.com"])
async def test_placeholder_admin_is_refused_on_a_remote_database(email: str) -> None:
    """البرهان السلبي: على الكود القديم يحاول الإقلاع الاتّصال بالقاعدة البعيدة بدل الرفض."""
    engine = create_async_engine(REMOTE_URL)
    session = AsyncSession(bind=engine)
    try:
        with pytest.raises(AdminBootstrapRefusedError):
            await bootstrap_admin_account(session, settings=_settings(email, "password"))
    finally:
        await session.close()
        await engine.dispose()


@pytest.mark.asyncio
async def test_placeholder_admin_still_works_on_a_local_database(db_session) -> None:
    """المحلّية كما هي: الاختبارات وبيئات sqlite تعتمد ``admin@example.com``."""
    admin = await bootstrap_admin_account(
        db_session, settings=_settings("admin@example.com", "local-dev-pass")
    )
    assert admin.is_admin and admin.is_active


@pytest.mark.asyncio
async def test_existing_admin_password_is_never_rewritten_without_force(db_session) -> None:
    """عقد المالك: الإقلاع لا يغيّر كلمة سرّ مديرٍ موجود مهما كانت ``ADMIN_PASSWORD``."""
    email = "owner-k001@cogniforge.dz"
    existing = (
        await db_session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing is None:
        existing = User(email=email, full_name="Owner", is_admin=True)
        db_session.add(existing)
    existing.set_password("owner-chosen")
    await db_session.commit()

    admin = await bootstrap_admin_account(
        db_session, settings=_settings(email, "a-different-env-value")
    )

    assert admin.check_password("owner-chosen")
    assert not admin.check_password("a-different-env-value")


@pytest.mark.asyncio
async def test_existing_admin_password_resyncs_only_with_explicit_force(db_session) -> None:
    email = "owner-force@cogniforge.dz"
    existing = (
        await db_session.execute(select(User).where(User.email == email))
    ).scalar_one_or_none()
    if existing is None:
        existing = User(email=email, full_name="Owner", is_admin=True)
        db_session.add(existing)
    existing.set_password("old-value")
    await db_session.commit()

    admin = await bootstrap_admin_account(
        db_session, settings=_settings(email, "new-value", force="1")
    )

    assert admin.check_password("new-value")


def test_codespaces_seed_script_delegates_to_the_single_bootstrap_path() -> None:
    """``scripts/ensure_admin.py`` كان يعيد كتابة كلمة السرّ في كلّ إقلاع — لا مسار ثانٍ بعد اليوم."""
    source = (REPO_ROOT / "scripts" / "ensure_admin.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    touched = {
        node.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute)
        and node.attr in {"password_hash", "set_password", "hash"}
    }
    assert "bootstrap_admin_account" in called
    assert touched == set(), f"ensure_admin.py writes passwords directly: {sorted(touched)}"
    assert DEFAULT_ADMIN_EMAIL not in source
