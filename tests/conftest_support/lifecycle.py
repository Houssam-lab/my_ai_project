"""Shard: دورة حياة قاعدة البيانات قبل كل اختبار (D-258، CodeScene X-Ray).
**لماذا هذه الشريحة موجودة (Bumpy Road Ahead — الشريحة القاتلة):** كان fixture
`db_lifecycle` يحمل داخله دالةً متداخلة `_reset_db` بكامل منطقها (كشف السياق ·
تحميل النماذج · dedupe · drop · create · validate) في كتلةٍ واحدة طولها 52 سطرًا —
أعلى تعقيدٍ في `tests/conftest.py` (CodeScene: churn=12 · LOC=63 · Bumpy Road).
فُكِّكت المنطقية كلها إلى خطواتٍ نقيةٍ في `schema.py`، وبقي هنا fixture القشرة الذي
يُركِّبها عبر قفلٍ متزامنٍ على المحرك — **صفر تغيير سلوكي** (القشرة تفوض حرفيًا).

**D-317:** الإعادة نفسها تُتخطّى حين تبقى القاعدة كما تركتها آخر إعادة، بعدّادات SQLite لا
بالنيّة — القاعدة والدليل في `reset_guard.py`. كلّ اختبارٍ ما زال يبدأ على قاعدةٍ مطابقة
لما تتركه إعادةٌ جديدة؛ المتغيّر وحده أنّ الإعادة لا تُكرَّر بلا سبب.
"""

from __future__ import annotations

import pytest

from .helpers import _db_dependencies_available, _run_async, _should_skip_db_fixtures
from .registry import _get_engine_locked
from .reset_guard import reset_unless_unchanged
from .schema import _dedupe_table_indexes, _load_context_models, _reset_db_steps


def run_db_lifecycle(event_loop, request: pytest.FixtureRequest):
    """المنطق النقي لدورة الحياة — يُستدعى من قشرة fixture في `tests/conftest.py`.

    D-258: لا يُفعَّل autouse من وحدةٍ عادية، فقشرة التسجيل في conftest تفوض هنا.
    """
    if _should_skip_db_fixtures(request):
        yield
        return
    if not _db_dependencies_available():
        yield
        return

    async def _reset_db() -> None:
        is_microservice_test = "microservices" in str(request.path) or "microservices" in str(
            request.node.fspath
        )
        # قفلٌ متزامن على المحرك يضمن أن تداخل اختباراتٍ متوازية لا يعيد بناء
        # المخطط فوق بعضه (ISS-113 class: «يمرّ منفردًا ويفشل بترتيب الحزمة الكاملة»).
        locked_engine = await _get_engine_locked()
        # D-317: النماذج تُحمَّل والفهارس تُنظَّف قبل البصمة — فشكل `metadata` الذي يُقارَن
        # هو شكل هذا الاختبار، لا شكل ما قبله (سياق خدمةٍ مصغّرة يُحمِّل نماذجه هنا).
        _load_context_models(is_microservice_test)
        _dedupe_table_indexes()
        # تُعاد الخطوات نفسها بالترتيب نفسه — إلا إن بقيت القاعدة كما تركتها آخر إعادة.
        await reset_unless_unchanged(locked_engine, is_microservice_test, reset=_reset_db_steps)

    _run_async(event_loop, _reset_db())

    yield
