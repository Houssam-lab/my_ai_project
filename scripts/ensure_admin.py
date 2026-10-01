#!/usr/bin/env python3
"""يضمن وجود مدير النظام عند إقلاع Codespaces — بتفويضٍ كامل إلى ``bootstrap_admin_account``.

يشغّله ``.devcontainer/supervisor.sh`` (الخطوة 3) قبل إقلاع الخادم.

⛔ لماذا التفويض (ISS-210): كان هذا السكربت مساراً ثانياً لتهيئة المدير يخالف سياسة K-001،
فيعيد كتابة كلمة سرّ المدير القائم **في كلّ إقلاع** من ``ADMIN_PASSWORD``. بيئةٌ بقيمةٍ
مختلفة كانت تكسر دخول المالك بصمت. وكان بريده الافتراضيّ نائباً بكلمة سرٍّ افتراضية
منشورة، فيُنشئ مديراً بلا مالك على أيّ قاعدةٍ يُوجَّه إليها.

المسار الواحد الآن يحمل القاعدتين:
- لا تُكتب كلمة سرّ حسابٍ موجود إلّا بـ``ADMIN_FORCE_PASSWORD_SYNC=1``.
- لا مدير ببريدٍ نائب على قاعدةٍ غير محلّية.
"""

import asyncio
import os
import sys

# Ensure the app can be imported
sys.path.append(os.getcwd())

from dotenv import load_dotenv

load_dotenv()

from app.core.database import async_session_factory
from app.services.bootstrap import AdminBootstrapRefusedError, bootstrap_admin_account


async def ensure_admin() -> None:
    async with async_session_factory() as session:
        admin = await bootstrap_admin_account(session)
        print(
            f"Admin account ensured (id={admin.id}). An existing password is never rewritten "
            "without ADMIN_FORCE_PASSWORD_SYNC=1."
        )


if __name__ == "__main__":
    try:
        asyncio.run(ensure_admin())
    except AdminBootstrapRefusedError as refused:
        print(f"Admin seeding refused: {refused}")
        sys.exit(1)
    except Exception as e:
        print(f"Error ensuring admin: {e}")
        sys.exit(1)
