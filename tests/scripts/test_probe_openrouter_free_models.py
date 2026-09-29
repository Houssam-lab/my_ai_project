"""D-298 — مسبار النماذج المجانية يختار نموذجاً **يجيب بالعربية**، لا نموذجاً يُرجِع حروفاً.

الحيّ (2026-09-29): اختار المسبار القديم ``nvidia/nemotron-3.5-lightning`` لأنه أرجع ١١٥
حرفاً لسؤالٍ من ٣٢ رمزاً بلا تعليمة نظام. وتحت تعليمة الأستاذ الحقيقية أرجع النموذج نفسه
«Here's a thinking process» بالإنجليزية داخل ``content``.
"""

from __future__ import annotations

from scripts.e2e import probe_openrouter_free_models as probe_module
from scripts.e2e.probe_openrouter_free_models import (
    arabic_answer_problem,
    chain_first,
    probe,
)
from shared.ai_models.model_chain import MODEL_CHAIN

#: النصّ الذي أرجعه النموذج المُختار حيّاً (مقتطفٌ حرفي).
_LIVE_LEAK = (
    "Here's a thinking process:\n\n1.  **Analyze User Input:**\n   - Role: "
    '"أنت أستاذ بكالوريا جزائري" (You are an Algerian Baccalaureate teacher)'
)

#: الإجابة التي أرجعها ``nemotron-3-ultra`` حيّاً للسؤال نفسه (مقتطف).
_LIVE_ARABIC = (
    "ينص قانون أوم على أن شدة التيار الكهربائي المار في موصل ما تتناسب طردياً مع فرق "
    "الجهد بين طرفيه، وعكسياً مع مقاومته الكهربائية: $$U = R \\cdot I$$."
)


def test_the_live_reasoning_leak_is_rejected() -> None:
    assert arabic_answer_problem(_LIVE_LEAK) is not None


def test_the_live_arabic_answer_is_accepted() -> None:
    assert arabic_answer_problem(_LIVE_ARABIC) is None


def test_an_english_answer_is_rejected() -> None:
    assert arabic_answer_problem("Ohm's law states that V = I R across a resistor.")


def test_an_empty_answer_is_rejected() -> None:
    assert arabic_answer_problem("   ") == "empty content"


def test_the_declared_chain_is_probed_first() -> None:
    catalog = ["new/model:free", MODEL_CHAIN[1], "other/model:free", MODEL_CHAIN[0]]
    ordered = chain_first(catalog)
    assert ordered[:2] == [MODEL_CHAIN[0], MODEL_CHAIN[1]]
    assert set(ordered) == set(catalog)


def _fake_reply(content: str):
    def _request_json(*_args, **_kwargs):
        return 200, {"choices": [{"message": {"content": content}}]}

    return _request_json


def test_probe_marks_a_leaking_model_as_not_working(monkeypatch) -> None:
    monkeypatch.setattr(probe_module, "request_json", _fake_reply(_LIVE_LEAK))
    result = probe("https://example.invalid/api/v1", "key", "leaky/model:free", 5)
    assert result.ok is False
    assert "reasoning leak" in (result.error or "")


def test_probe_marks_an_arabic_model_as_working(monkeypatch) -> None:
    monkeypatch.setattr(probe_module, "request_json", _fake_reply(_LIVE_ARABIC))
    result = probe("https://example.invalid/api/v1", "key", "good/model:free", 5)
    assert result.ok is True
    assert result.arabic_share is not None and result.arabic_share > 0.6
