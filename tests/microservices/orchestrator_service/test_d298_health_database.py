"""D-298 — ``/health`` لا يقول ``ok`` ومجمّع المحادثة ميت.

الحيّ (2026-09-29، بيئة CI نفسها): ``{"status":"ok","graph_ready":true}`` بينما سجّل
المجمّع ٢٧ ``PoolTimeout``، وكل رسالةٍ ماتت بـ500 بعد 30 ثانية. خطوة الإقلاع في CI تثق
بهذا الجسم فتنتقل إلى الرحلة ثمّ تفشل بعيداً عن السبب.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

import pytest

import microservices.orchestrator_service.main as orchestrator_main


class _Conn:
    async def execute(self, *_: Any) -> None:
        return None


class _LivePool:
    @asynccontextmanager
    async def connection(self, timeout: float | None = None):
        yield _Conn()


class _DeadPool:
    @asynccontextmanager
    async def connection(self, timeout: float | None = None):
        raise TimeoutError("couldn't get a connection after 30.00 sec")
        yield  # pragma: no cover


@pytest.fixture
def ready_app(monkeypatch):
    monkeypatch.setattr(orchestrator_main.app.state, "startup_state", "ready", raising=False)
    monkeypatch.setattr(orchestrator_main.app.state, "app_graph", object(), raising=False)
    monkeypatch.setattr(orchestrator_main.app.state, "startup_errors", [], raising=False)
    return orchestrator_main


async def test_a_dead_pool_is_degraded_not_ok(ready_app, monkeypatch) -> None:
    monkeypatch.setattr(ready_app, "get_psycopg_pool", lambda: _DeadPool())
    body = await ready_app.health_check()
    assert body["database"] == "unreachable"
    assert body["status"] == "degraded"
    assert body["graph_ready"] is True  # الرسم موجود — والدردشة مع ذلك ميتة


async def test_a_live_pool_is_ok(ready_app, monkeypatch) -> None:
    monkeypatch.setattr(ready_app, "get_psycopg_pool", lambda: _LivePool())
    body = await ready_app.health_check()
    assert body["database"] == "ok"
    assert body["status"] == "ok"


async def test_no_pool_does_not_change_the_verdict(ready_app, monkeypatch) -> None:
    """SQLite محلياً: لا مجمّع يُفحَص — والحالة لا تتغيّر بسبب غيابه."""
    monkeypatch.setattr(ready_app, "get_psycopg_pool", lambda: None)
    body = await ready_app.health_check()
    assert body["database"] == "not_pooled"
    assert body["status"] == "ok"
