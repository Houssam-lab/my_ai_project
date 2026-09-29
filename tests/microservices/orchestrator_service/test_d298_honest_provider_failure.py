"""D-298 — رفضُ المفتاح حالةُ تشغيلٍ صريحة، لا نصٌّ جاهز بحالة ``ok``.

الحيّ (2026-09-29، مفتاحٌ باطل): ٨٤ خطأ 401 في سجلّ الـ orchestrator، وتسعة أدوار أُجيبت
بـ«عذراً، لم أتمكن من استرجاع هذه المعلومة الآن»، ودورٌ أُجيب بتحية. السبب: 401 لا يدور
(صحيح) فيخرج خطأً خاماً يقع في ``except Exception`` العام. الآن يخرج
:class:`ProviderAuthError`، وكلّ عقدةٍ تُعلن ``provider_error`` لانقطاع السلسلة تُعلنه له.
"""

from __future__ import annotations

from typing import Any

import pytest

from microservices.orchestrator_service.src.core.degraded_replies import CHAT_FALLBACK_REPLY
from microservices.orchestrator_service.src.services.llm.client import (
    PROVIDER_UNAVAILABLE_MESSAGE,
    ProviderAuthError,
)
from microservices.orchestrator_service.src.services.overmind.graph.general_knowledge import (
    GeneralKnowledgeNode,
)
from microservices.orchestrator_service.src.services.overmind.graph.main import (
    ChatFallbackNode,
)


class _RejectingClient:
    """عميلٌ يرفضه المزوّد — كما يفعل OpenRouter بمفتاحٍ باطل."""

    def __init__(self, error: Exception) -> None:
        self._error = error

    async def generate(self, **_: Any) -> Any:
        raise self._error

    async def stream_chat(self, *_: Any, **__: Any):
        raise self._error
        yield  # pragma: no cover — يجعلها مولِّداً غير متزامن

    def model_chain(self) -> list[str]:
        return ["test/primary:free"]

    @staticmethod
    def extract_stream_content(_chunk: Any) -> str | None:  # pragma: no cover
        return None


def _auth_error() -> ProviderAuthError:
    return ProviderAuthError([("test/primary:free", "AuthenticationError(401) User not found")])


async def test_general_knowledge_declares_a_rejected_key(monkeypatch) -> None:
    monkeypatch.setattr(
        "microservices.orchestrator_service.src.services.overmind.graph.general_knowledge.get_llm_client",
        lambda: _RejectingClient(_auth_error()),
    )
    result = await GeneralKnowledgeNode()({"query": "اشرح لي قانون أوم", "messages": []})
    assert result["provider_error"] is True
    assert result["final_response"] == PROVIDER_UNAVAILABLE_MESSAGE


async def test_chat_fallback_declares_a_rejected_key(monkeypatch) -> None:
    """«لم أفهم» لا تُجاب بتحية حين يكون المزوّد غائباً."""
    monkeypatch.setattr(
        "microservices.orchestrator_service.src.services.llm.client.get_ai_client",
        lambda: _RejectingClient(_auth_error()),
    )
    result = await ChatFallbackNode()({"query": "لم أفهم", "messages": []})
    assert result["provider_error"] is True
    assert result["final_response"] == PROVIDER_UNAVAILABLE_MESSAGE
    assert CHAT_FALLBACK_REPLY not in result["final_response"]


async def test_chat_fallback_other_failures_keep_the_old_text(monkeypatch) -> None:
    """عطلٌ غير المزوّد يبقى كما كان — والحَكَم يراه الآن نصّاً جاهزاً (D-298)."""
    monkeypatch.setattr(
        "microservices.orchestrator_service.src.services.llm.client.get_ai_client",
        lambda: _RejectingClient(RuntimeError("unrelated bug")),
    )
    result = await ChatFallbackNode()({"query": "لم أفهم", "messages": []})
    assert "provider_error" not in result
    assert CHAT_FALLBACK_REPLY in result["final_response"]


@pytest.mark.parametrize("node_name", ["GeneralKnowledgeNode", "ChatFallbackNode"])
def test_both_nodes_catch_the_family_not_the_subclass(node_name: str) -> None:
    """العُقد تلتقط ``AllModelsFailedError`` لا الصنف الفرعي — فأيُّ فرعٍ جديد يُعلَن تلقائياً."""
    import inspect

    from microservices.orchestrator_service.src.services.overmind.graph import (
        general_knowledge,
        nodes,
    )

    module = general_knowledge if node_name == "GeneralKnowledgeNode" else nodes
    source = inspect.getsource(getattr(module, node_name))
    assert "except AllModelsFailedError" in source
    assert "except ProviderAuthError" not in source
