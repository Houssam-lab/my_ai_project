"""أوامر إدارة قاعدة البيانات مع التزام واضح بمبادئ KISS وDRY."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from logging import Logger

import click
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel

from app import models
from app.cli_handlers.context import CLIContext, get_cli_context
from app.core.config import AppSettings
from app.core.database import engine
from app.services.bootstrap import ensure_admin_email_allowed

SessionFactory = Callable[[], AsyncGenerator[AsyncSession, None]]


@dataclass(frozen=True)
class AdminSeedPlan:
    """يصف سيناريو تهيئة حساب المشرف بشكل بيانات قابلة للاختبار."""

    email: str
    password: str
    promote_to_admin: bool = True


def register_db_commands(root: click.Group) -> None:
    """يسجل أوامر قاعدة البيانات ضمن مجموعة CLI الرئيسية."""

    @root.group("db")
    def db_group() -> None:
        """حزمة الأوامر الخاصة بإدارة قاعدة البيانات."""

    @db_group.command("create-all")
    @click.pass_context
    def create_all(ctx: click.Context) -> None:
        """ينشئ جميع الجداول المعرّفة في نماذج النظام."""

        context = get_cli_context(ctx)
        _run_create_all_tables(context.logger)

    @db_group.command("seed")
    @click.option("--confirm", is_flag=True, default=False, help="تأكيد تنفيذ التهيئة")
    @click.option("--dry-run", is_flag=True, default=False, help="تنفيذ تجريبي دون حفظ")
    @click.pass_context
    def seed(ctx: click.Context, confirm: bool, dry_run: bool) -> None:
        """يهيئ حساب المشرف الافتراضي مع دعم وضع التجربة."""

        context = get_cli_context(ctx)
        plan = _build_admin_seed_plan(context.settings)
        _validate_seed_flags(confirm, dry_run)
        _run_seed_plan(plan, context, dry_run)


def _run_create_all_tables(logger: Logger) -> None:
    """يشغّل مهمة إنشاء الجداول باستخدام حدث واحد مترابط."""

    async def _create() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    logger.info("إنشاء جميع جداول قاعدة البيانات...")
    asyncio.run(_create())
    logger.info("تم إنشاء الجداول بنجاح.")


def _run_seed_plan(plan: AdminSeedPlan, context: CLIContext, dry_run: bool) -> None:
    """ينفّذ خطة تهيئة المشرف مع دعم التراجع التجريبي."""

    async def _seed() -> None:
        async with transactional_session(
            context.session_provider, context.logger, dry_run=dry_run
        ) as session:
            await _ensure_admin_user(session, context.logger, plan)

    asyncio.run(_seed())


def _validate_seed_flags(confirm: bool, dry_run: bool) -> None:
    """يتحقق من سلامة خيارات التنفيذ لتجنب الحذف غير المقصود."""

    if not confirm and not dry_run:
        raise click.UsageError(
            "إضافة --confirm مطلوبة للتنفيذ الفعلي (أو استخدم --dry-run للتجربة)."
        )


def _build_admin_seed_plan(settings: AppSettings) -> AdminSeedPlan:
    """ينشئ خطة بيانات لتهيئة حساب المشرف مع أخذ المتغيرات البيئية بعين الاعتبار."""

    email = os.getenv("ADMIN_EMAIL", settings.ADMIN_EMAIL) or settings.ADMIN_EMAIL
    password = os.getenv("ADMIN_PASSWORD", settings.ADMIN_PASSWORD) or settings.ADMIN_PASSWORD
    return AdminSeedPlan(email=email, password=password)


async def _ensure_admin_user(session: AsyncSession, logger: Logger, plan: AdminSeedPlan) -> None:
    """يضمن وجود مستخدم مشرف واحد على الأقل وفق الخطة المحددة."""

    # ISS-210: نفس حارس الإقلاع — لا مدير ببريدٍ نائب على قاعدةٍ غير محلّية.
    ensure_admin_email_allowed(plan.email, session)

    result = await session.execute(select(models.User).filter_by(email=plan.email))
    user = result.scalar()

    if user is None:
        user = models.User(email=plan.email, is_admin=plan.promote_to_admin, full_name="Admin User")
        user.set_password(plan.password)
        session.add(user)
        logger.info("تم إنشاء مستخدم المشرف الافتراضي.")
        return

    user.set_password(plan.password)
    if plan.promote_to_admin and not user.is_admin:
        user.is_admin = True
        logger.info("تم ترقية المستخدم الموجود إلى مشرف.")
    session.add(user)
    logger.info("تم تحديث كلمة مرور حساب المشرف الحالي.")


@asynccontextmanager
async def transactional_session(
    session_factory: SessionFactory, logger: Logger, *, dry_run: bool = False
) -> AsyncGenerator[AsyncSession, None]:
    """يدير دورة حياة جلسة قاعدة البيانات مع خيار التراجع التجريبي."""

    candidate = session_factory()

    @asynccontextmanager
    async def _wrap_generator() -> AsyncGenerator[AsyncSession, None]:
        async for session in candidate:
            yield session

    manager = candidate if hasattr(candidate, "__aenter__") else _wrap_generator()

    async with manager as session:
        try:
            yield session
            if dry_run:
                logger.info("تشغيل تجريبي: سيتم التراجع عن التغييرات (dry-run: rolling back).")
                await session.rollback()
            else:
                await session.commit()
                logger.info("تم اعتماد المعاملة بنجاح.")
        except Exception:
            logger.exception("خطأ أثناء تنفيذ أمر CLI؛ سيتم التراجع عن المعاملة.")
            await session.rollback()
            raise
