"""ISS-207 (D-302) — the orchestrator must end a turn before its caller gives up.

Measured in CI (run 36572150771): the monolith reads the orchestrator's HTTP stream with a
60 s timeout, while the orchestrator waited up to 30 s *per model* for a first token and
sent nothing while it rotated. Two slow free-tier models were enough: the monolith timed
out and told the student «النظام يتطلب الخدمات الذكية المتقدمة وهي غير متاحة» — a slow
provider misreported as a dead service.

These tests pin the contract:

1. The whole rotation has one budget (``LLM_CHAIN_DEADLINE_S``). When no model has
   produced content within it, ``stream_chat`` raises ``AllModelsFailedError`` — the
   named provider failure — instead of letting the caller time out.
2. The budget bounds a stalled ``create()`` and a silent stream alike.
3. Content already flowing is never cut: the budget covers finding a model, not answering.
4. The budget stays below the monolith's read timeout, with room for non-LLM node work.
"""

from __future__ import annotations

import asyncio
import time
from types import SimpleNamespace
from typing import Any

import pytest

from microservices.orchestrator_service.src.services.llm.client import (
    DEFAULT_BASE_URL,
    LLM_CHAIN_DEADLINE_S,
    AIClient,
    AllModelsFailedError,
)

_MESSAGES = [{"role": "user", "content": "لم أفهم"}]


def _chunk(text: str | None) -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=text))])


class _TimedStream:
    """A stream whose items are chunks or delays (seconds) awaited before the next item."""

    def __init__(self, items: list[Any]) -> None:
        self._items = list(items)

    def __aiter__(self) -> _TimedStream:
        return self

    async def __anext__(self) -> Any:
        while self._items:
            item = self._items.pop(0)
            if isinstance(item, (int, float)):
                await asyncio.sleep(item)
                continue
            return item
        raise StopAsyncIteration

    async def close(self) -> None:
        self._items = []


class _Completions:
    def __init__(self, behaviours: dict[str, Any], create_delay: dict[str, float]) -> None:
        self._behaviours = behaviours
        self._create_delay = create_delay
        self.calls: list[str] = []

    async def create(self, **kwargs: Any) -> Any:
        model = str(kwargs.get("model"))
        self.calls.append(model)
        await asyncio.sleep(self._create_delay.get(model, 0.0))
        return _TimedStream(self._behaviours[model])


def _client(
    behaviours: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    *,
    deadline: float,
    create_delay: dict[str, float] | None = None,
) -> tuple[AIClient, _Completions]:
    client = AIClient.__new__(AIClient)
    completions = _Completions(behaviours, create_delay or {})
    client.client = SimpleNamespace(chat=SimpleNamespace(completions=completions))
    client.default_model = "test/primary:free"
    client.first_token_timeout = 30.0  # the per-model guard alone would wait far longer
    client.chain_deadline = deadline
    client.last_model = None
    client.base_url = DEFAULT_BASE_URL
    client.timeout = 30.0
    monkeypatch.setattr(client, "model_chain", lambda: list(behaviours))
    return client, completions


async def test_silent_models_exhaust_the_budget_as_a_named_provider_failure(monkeypatch) -> None:
    """Two models that never produce content: a named failure inside the budget."""
    client, completions = _client(
        {"test/slow1:free": [5.0], "test/slow2:free": [5.0], "test/fast:free": [_chunk("x")]},
        monkeypatch,
        deadline=0.3,
    )
    started = time.monotonic()
    with pytest.raises(AllModelsFailedError) as exc:
        _ = [c async for c in client.stream_chat(_MESSAGES)]
    assert time.monotonic() - started < 1.5
    assert "chain_deadline" in str(exc.value)
    # The budget is spent on the first model; the rest are named as skipped, not tried.
    assert completions.calls == ["test/slow1:free"]
    assert exc.value.models == ["test/slow1:free", "test/slow2:free", "test/fast:free"]


async def test_a_stalled_create_is_bounded_too(monkeypatch) -> None:
    """A provider that never returns the stream object cannot hold the turn."""
    client, _ = _client(
        {"test/hang:free": [_chunk("never")]},
        monkeypatch,
        deadline=0.3,
        create_delay={"test/hang:free": 5.0},
    )
    started = time.monotonic()
    with pytest.raises(AllModelsFailedError):
        _ = [c async for c in client.stream_chat(_MESSAGES)]
    assert time.monotonic() - started < 1.5


async def test_a_fast_model_after_a_slow_one_still_answers_within_budget(monkeypatch) -> None:
    client, completions = _client(
        {"test/slow:free": [0.05, _chunk(None)], "test/fast:free": [_chunk("إجابة")]},
        monkeypatch,
        deadline=2.0,
    )
    client.first_token_timeout = 0.01  # the slow model is abandoned by the per-model guard
    out = [c async for c in client.stream_chat(_MESSAGES)]
    assert [c.choices[0].delta.content for c in out] == ["إجابة"]
    assert completions.calls == ["test/slow:free", "test/fast:free"]


async def test_content_already_flowing_is_not_cut_by_the_budget(monkeypatch) -> None:
    """Once the student is reading an answer, the budget no longer applies."""
    client, _ = _client(
        {"test/primary:free": [_chunk("بداية "), 0.5, _chunk("نهاية")]},
        monkeypatch,
        deadline=0.2,
    )
    out = [c async for c in client.stream_chat(_MESSAGES)]
    assert [c.choices[0].delta.content for c in out] == ["بداية ", "نهاية"]


def test_budget_stays_below_the_monolith_read_timeout() -> None:
    """The orchestrator must always answer before its caller gives up (ISS-207)."""
    from app.infrastructure.clients.orchestrator_client import ORCHESTRATOR_CALL_TIMEOUT_S

    #: Room for the non-LLM work of a node (retrieval, reranking, persistence).
    margin_s = 15.0
    assert LLM_CHAIN_DEADLINE_S + margin_s <= ORCHESTRATOR_CALL_TIMEOUT_S
    assert AIClient.chain_deadline == LLM_CHAIN_DEADLINE_S
