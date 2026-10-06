"""Shard: إعادة ضبط المخطّط فقط حين تكون قاعدة الاختبار قد تغيّرت فعلاً (D-317).

**لماذا هذه الشريحة موجودة (قياسٌ لا رأي):** كان `db_lifecycle` يُسقط المخطّط كلّه ويعيد
إنشاءه ثمّ يتحقّق منه قبل **كلّ** اختبار — 6220 مرّة في الحزمة، ~140 م.ث محلياً لكلّ مرّة
(drop 16 · create 40 · validate 84)، أي **1172 ث من 1640** (71٪) من زمن الحزمة. ومسبارٌ على
الحزمة كاملةً (2026-10-06) وجد أنّ **5984 من 6220** إعادةً جرت على قاعدةٍ لم يتغيّر فيها شيء
منذ الإعادة السابقة. فسقف `test-monolith` (D-315) كان يُرفَع لأنّ الحزمة تقيس إعادة الضبط لا
الاختبارات.

**القاعدة (لا ثقة بالنيّة، ثقة بالعدّاد):** قاعدة الاختبار اتّصال SQLite واحد داخل الذاكرة
(`StaticPool`)، وSQLite نفسه يعدّ كلّ تغيير على ذلك الاتّصال:
- `total_changes()` كلّ صفٍّ أُدرِج أو عُدِّل أو حُذِف — **حتى ما تراجعت عنه المعاملة**؛
- `PRAGMA schema_version` و`PRAGMA temp.schema_version` كلّ DDL، دائماً ومؤقّتاً.
والقراءة لا تحرّك أيّاً منها. فمفتاح الحالة = (سياق الخدمة · شكل `SQLModel.metadata` · بصمة
القاعدة)، يُسجَّل **بعد** الإعادة (فكتابات `validate_and_fix_schema` نفسها جزءٌ من الإعادة)،
وإن طابقه المفتاح قبل الاختبار التالي فالقاعدة مطابقةٌ بالبايت لما تتركه إعادةٌ جديدة.

**ما لا يتغيّر:** خطوات الإعادة نفسها (`schema._reset_db_steps`) وترتيبها وقفل المحرّك ومسارا
`SKIP_DB_FIXTURES` وغياب الاعتمادات. والعدّادان يُطبَعان في آخر الجلسة — لا سلوكٌ صامت.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy import MetaData
    from sqlalchemy.ext.asyncio import AsyncEngine

ResetStep = Callable[["AsyncEngine", bool], Awaitable[None]]


@dataclass
class ResetLedger:
    """آخر حالةٍ تركتها إعادة الضبط، وعدّادا الجلسة."""

    last_key: tuple[object, ...] | None = None
    resets: int = 0
    skips: int = 0
    reported: bool = False

    def summary_line(self) -> str:
        return (
            f"db_lifecycle (D-317): {self.resets} schema resets, {self.skips} skipped "
            "because the test database was unchanged"
        )

    def report_once(self, write_line: Callable[[str], object]) -> None:
        """يطبع السطر مرّةً واحدة: الـconftest الجذري يعيد تصدير خطافات `tests/conftest.py`
        بـ`import *` فيُستدعى الخطاف مرّتين."""
        if not self.reported:
            self.reported = True
            write_line(self.summary_line())


LEDGER = ResetLedger()


def _metadata_fingerprint(metadata: MetaData | None = None) -> tuple[tuple[str, int, int], ...]:
    """شكل النماذج المُحمَّلة: (الجدول · عدد الأعمدة · عدد الفهارس) مرتّبة.

    نموذجٌ جديد يستورده اختبار، أو جدولٌ تعيد تعريفه خدمةٌ مصغّرة، يغيّر الشكل فيفرض إعادةً.
    """
    if metadata is None:
        from sqlmodel import SQLModel

        metadata = SQLModel.metadata
    return tuple(
        sorted(
            (name, len(table.columns), len(table.indexes))
            for name, table in metadata.tables.items()
        )
    )


async def _db_fingerprint(engine: AsyncEngine) -> tuple[int, int, int]:
    """بصمة القاعدة في رحلة قراءةٍ واحدة: التغييرات · نسخة المخطّط · نسخة المخطّط المؤقّت."""
    from sqlalchemy import text

    async with engine.connect() as conn:
        changes = (await conn.execute(text("SELECT total_changes()"))).scalar_one()
        schema_version = (await conn.execute(text("PRAGMA schema_version"))).scalar_one()
        temp_version = (await conn.execute(text("PRAGMA temp.schema_version"))).scalar_one()
    return (int(changes), int(schema_version), int(temp_version))


async def _state_key(
    engine: AsyncEngine, is_microservice_test: bool, metadata: MetaData | None
) -> tuple[object, ...]:
    return (
        is_microservice_test,
        _metadata_fingerprint(metadata),
        await _db_fingerprint(engine),
    )


async def reset_unless_unchanged(
    engine: AsyncEngine,
    is_microservice_test: bool,
    *,
    reset: ResetStep,
    ledger: ResetLedger = LEDGER,
    metadata: MetaData | None = None,
) -> bool:
    """يعيد الضبط إلا إن بقيت القاعدة كما تركتها آخر إعادة. يُرجِع True إن أعاد."""
    if await _state_key(engine, is_microservice_test, metadata) == ledger.last_key:
        ledger.skips += 1
        return False
    await reset(engine, is_microservice_test)
    ledger.resets += 1
    ledger.last_key = await _state_key(engine, is_microservice_test, metadata)
    return True
