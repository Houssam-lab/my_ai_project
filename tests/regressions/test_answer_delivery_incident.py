"""Regression proofs for INCIDENT: System Does Not Answer Questions.

These tests isolate the failure boundary discovered end-to-end:
LLM/provider exhaustion must remain an operational error all the way from the
StateGraph update to the browser terminal frame.  A non-empty outage sentence
is not an answer and HTTP 200 is not success.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator

import pytest

from app.api.routers.customer_chat_support.frames import _emit_terminal_frames
from app.infrastructure.clients.orchestrator_client import OrchestratorClient
from microservices.orchestrator_service.src.api import chat_stream_engine
from microservices.orchestrator_service.src.services.llm.client import (
    PROVIDER_UNAVAILABLE_MESSAGE,
)


class _ProviderFailureGraph:
    def __init__(self) -> None:
        self.inputs: dict | None = None

    async def astream(self, inputs: dict, **_kwargs) -> AsyncIterator[tuple[str, dict]]:
        self.inputs = inputs
        yield (
            "updates",
            {
                "general_knowledge": {
                    "provider_error": True,
                    "final_response": PROVIDER_UNAVAILABLE_MESSAGE,
                }
            },
        )
        yield ("updates", {"validator": {"tools_executed": False}})


@pytest.mark.asyncio
async def test_http_graph_provider_failure_is_error_not_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def no_checkpoint(_thread_id: str) -> tuple[bool, bool]:
        return False, False

    monkeypatch.setattr(chat_stream_engine, "_detect_checkpoint_state", no_checkpoint)

    graph = _ProviderFailureGraph()
    raw_frames = [
        frame
        async for frame in chat_stream_engine._run_chat_langgraph(
            "ما هو قانون أوم؟",
            {"user_id": 7, "conversation_id": 41, "thread_id": "u7:c41"},
            app_graph=graph,
            history_messages=[],
        )
    ]
    frames = [json.loads(frame) for frame in raw_frames]

    # `provider_error` is terminal for one invocation, not durable conversation
    # state. Explicit False clears an outage restored from a prior checkpoint.
    assert graph.inputs is not None
    assert graph.inputs["provider_error"] is False
    assert [frame["type"] for frame in frames] == ["phase_start", "phase_start", "assistant_error"]
    terminal = frames[-1]
    assert terminal["payload"]["content"] == PROVIDER_UNAVAILABLE_MESSAGE
    assert terminal["payload"]["code"] == "LLM_PROVIDER_UNAVAILABLE"
    assert terminal["payload"]["status_code"] == 503
    assert not any(frame["type"] == "assistant_final" for frame in frames)


def test_transport_normalization_preserves_error_event() -> None:
    # Construct without __init__: normalization is pure and should not require
    # service discovery configuration.
    client = object.__new__(OrchestratorClient)
    event = client._normalize_stream_event(
        {"type": "error", "payload": {"message": "upstream unavailable", "status_code": 503}}
    )
    assert event["type"] == "error"
    assert event["payload"]["message"] == "upstream unavailable"


class _FakeWebSocket:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_json(self, payload: dict) -> None:
        self.sent.append(payload)


@pytest.mark.asyncio
async def test_explicit_upstream_error_is_the_only_terminal_frame() -> None:
    websocket = _FakeWebSocket()
    pending = {
        "type": "assistant_error",
        "payload": {
            "content": PROVIDER_UNAVAILABLE_MESSAGE,
            "code": "LLM_PROVIDER_UNAVAILABLE",
            "request_id": "request-1",
        },
    }

    await _emit_terminal_frames(
        websocket=websocket,  # type: ignore[arg-type]
        send_lock=asyncio.Lock(),
        pending_terminal_event=pending,
        assistant_message_persisted=False,
        complete_ai_response="",
        stream_error=RuntimeError("provider exhausted"),
        local_conversation_id=41,
        stream_request_id="request-1",
    )

    assert websocket.sent == [pending]
