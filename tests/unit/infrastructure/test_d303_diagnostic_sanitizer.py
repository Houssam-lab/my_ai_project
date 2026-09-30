"""D-303 — the topology sanitizer blocks leaked internals, not the word «diagnostic».

Before: any reply containing «diagnostic» was replaced wholesale with the canned
«service unavailable» text. «Le diagnostic» is ordinary French, and a diagnostic
question is the platform's own teaching move, so correct answers were destroyed.
What actually leaks is the attempt chain ``<url> => <error>`` or a serialized
``"diagnostic":`` key — the word alone appears in neither.
"""

from __future__ import annotations

import pytest

from app.infrastructure.clients.orchestrator.text_streaming import TextStreamingMixin
from app.services.llm.degraded_replies import SERVICE_UNAVAILABLE_REPLY

_sanitize = TextStreamingMixin._sanitize_text_for_user


@pytest.mark.parametrize(
    "answer",
    [
        "Le diagnostic est simple : la loi d'Ohm s'écrit U = R × I.",
        "نبدأ بسؤالٍ تشخيصي (diagnostic question): ما وحدة المقاومة؟",
        "A diagnostic test helps you find the gap before the exam.",
    ],
)
def test_ordinary_prose_with_the_word_survives(answer: str) -> None:
    assert _sanitize(answer) == answer


@pytest.mark.parametrize(
    "leak",
    [
        "http://orchestrator:8006/api/chat/messages => ConnectError: refused",
        "https://orch.internal.example/api => ReadTimeout",
        '{"type": "error", "diagnostic": "all endpoints failed"}',
    ],
)
def test_the_internal_attempt_chain_is_still_blocked(leak: str) -> None:
    assert _sanitize(leak) == SERVICE_UNAVAILABLE_REPLY


def test_the_existing_host_tokens_still_block() -> None:
    assert _sanitize("see localhost:8006 for details") == SERVICE_UNAVAILABLE_REPLY
