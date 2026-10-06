"""D-317: the per-test schema reset is skipped only when the test database provably did not change.

The guard lives in `tests/conftest_support/reset_guard.py`. These tests drive it with
a private in-memory engine and their own ledger, so they never touch the shared test
database or the session's counters.
"""

from __future__ import annotations

import pytest
from sqlalchemy import Column, Integer, MetaData, Table, text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import StaticPool

from tests.conftest_support.reset_guard import (
    ResetLedger,
    _db_fingerprint,
    _metadata_fingerprint,
    reset_unless_unchanged,
)


def _engine() -> AsyncEngine:
    return create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def _metadata(*table_names: str) -> MetaData:
    metadata = MetaData()
    for name in table_names:
        Table(name, metadata, Column("id", Integer, primary_key=True))
    return metadata


class _Reset:
    """A stand-in for `_reset_db_steps`: rebuilds one table and seeds one row.

    The seed row plays the part of `validate_and_fix_schema`'s own writes, which must
    count as part of the reset and not as a change made by the next test.
    """

    def __init__(self) -> None:
        self.calls = 0

    async def __call__(self, engine: AsyncEngine, is_microservice_test: bool) -> None:
        self.calls += 1
        async with engine.begin() as conn:
            await conn.execute(text("DROP TABLE IF EXISTS t"))
            await conn.execute(text("CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT)"))
            await conn.execute(text("INSERT INTO t (v) VALUES ('seed')"))


async def _run(engine, ledger, reset, *, metadata=None, microservice=False) -> bool:
    return await reset_unless_unchanged(
        engine,
        microservice,
        reset=reset,
        ledger=ledger,
        metadata=metadata if metadata is not None else _metadata("t"),
    )


@pytest.mark.asyncio
async def test_the_first_call_always_resets() -> None:
    ledger, reset = ResetLedger(), _Reset()
    assert await _run(_engine(), ledger, reset) is True
    assert (reset.calls, ledger.resets, ledger.skips) == (1, 1, 0)


@pytest.mark.asyncio
async def test_an_untouched_database_is_not_reset_again() -> None:
    engine, ledger, reset = _engine(), ResetLedger(), _Reset()
    await _run(engine, ledger, reset)
    assert await _run(engine, ledger, reset) is False
    assert await _run(engine, ledger, reset) is False
    assert (reset.calls, ledger.resets, ledger.skips) == (1, 1, 2)


@pytest.mark.asyncio
async def test_reads_do_not_count_as_a_change() -> None:
    engine, ledger, reset = _engine(), ResetLedger(), _Reset()
    await _run(engine, ledger, reset)
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM t"))).scalar() == 1
    assert await _run(engine, ledger, reset) is False


@pytest.mark.asyncio
async def test_a_committed_insert_forces_a_reset() -> None:
    engine, ledger, reset = _engine(), ResetLedger(), _Reset()
    await _run(engine, ledger, reset)
    async with engine.begin() as conn:
        await conn.execute(text("INSERT INTO t (v) VALUES ('left behind')"))
    assert await _run(engine, ledger, reset) is True
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT count(*) FROM t"))).scalar() == 1


@pytest.mark.asyncio
async def test_a_rolled_back_insert_still_forces_a_reset() -> None:
    engine, ledger, reset = _engine(), ResetLedger(), _Reset()
    await _run(engine, ledger, reset)
    async with engine.connect() as conn:
        await conn.execute(text("INSERT INTO t (v) VALUES ('rolled back')"))
        await conn.rollback()
    assert await _run(engine, ledger, reset) is True


@pytest.mark.asyncio
async def test_ddl_forces_a_reset() -> None:
    engine, ledger, reset = _engine(), ResetLedger(), _Reset()
    await _run(engine, ledger, reset)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE TABLE extra (id INTEGER PRIMARY KEY)"))
    assert await _run(engine, ledger, reset) is True


@pytest.mark.asyncio
async def test_temp_table_ddl_forces_a_reset() -> None:
    engine, ledger, reset = _engine(), ResetLedger(), _Reset()
    await _run(engine, ledger, reset)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE TEMP TABLE scratch (a INTEGER)"))
    assert await _run(engine, ledger, reset) is True


@pytest.mark.asyncio
async def test_a_new_model_table_forces_a_reset() -> None:
    engine, ledger, reset = _engine(), ResetLedger(), _Reset()
    await _run(engine, ledger, reset, metadata=_metadata("t"))
    assert await _run(engine, ledger, reset, metadata=_metadata("t", "u")) is True


@pytest.mark.asyncio
async def test_switching_between_monolith_and_microservice_forces_a_reset() -> None:
    engine, ledger, reset = _engine(), ResetLedger(), _Reset()
    await _run(engine, ledger, reset, microservice=False)
    assert await _run(engine, ledger, reset, microservice=True) is True
    assert await _run(engine, ledger, reset, microservice=True) is False


@pytest.mark.asyncio
async def test_the_fingerprint_counts_changes_and_both_schema_versions() -> None:
    engine = _engine()
    start = await _db_fingerprint(engine)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE TABLE t (id INTEGER PRIMARY KEY)"))
        await conn.execute(text("INSERT INTO t (id) VALUES (1)"))
        await conn.execute(text("CREATE TEMP TABLE tt (a INTEGER)"))
    after = await _db_fingerprint(engine)
    assert [a > b for a, b in zip(after, start, strict=True)] == [True, True, True]


def test_the_metadata_fingerprint_sees_columns_and_indexes() -> None:
    plain = _metadata("t")
    wider = MetaData()
    Table("t", wider, Column("id", Integer, primary_key=True), Column("n", Integer, index=True))
    assert _metadata_fingerprint(plain) != _metadata_fingerprint(wider)
    assert _metadata_fingerprint(plain) == _metadata_fingerprint(_metadata("t"))


def test_the_summary_line_names_both_counts() -> None:
    ledger = ResetLedger(resets=3, skips=97)
    assert ledger.summary_line() == (
        "db_lifecycle (D-317): 3 schema resets, 97 skipped because the test database was unchanged"
    )


def test_the_summary_is_reported_once_even_when_the_hook_runs_twice() -> None:
    # The root conftest re-exports tests/conftest.py's hooks with `import *`, so pytest
    # calls pytest_terminal_summary twice.
    ledger, lines = ResetLedger(resets=1, skips=2), []
    ledger.report_once(lines.append)
    ledger.report_once(lines.append)
    assert lines == [ledger.summary_line()]
