"""D-303 · E2b — a model-bound answer must prove a model generated it.

Before: the matrix accepted any non-canned text. A reply from a template or a
static store passed as tutoring. In the local live run of 2026-09-29 the student
journey passed with **zero** model calls: its four turns are all deterministic, so
"the journey is green" said nothing about the model path.

The proof is the orchestrator's own line, written only when a real model finishes
a generation (``MODEL_SERVED_MARKER`` in the LLM client — one home).
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from types import SimpleNamespace

from microservices.orchestrator_service.src.services.llm.client import (
    MODEL_SERVED_MARKER,
    AIClient,
)
from scripts.e2e.universal_answerability_live import (
    MATRIX,
    ModelLog,
    Probe,
    TurnResult,
    _generation_problems,
    _turn_violations,
)

_ARABIC_ANSWER = "ينص قانون أوم على أن شدة التيار تتناسب طردياً مع فرق الجهد."
_MODEL_PROBE = Probe("اشرح لي قانون أوم", "physics", True, "ISS-159")
_GREETING = MATRIX[0]


def _served_line(model: str = "google/gemma-4-31b-it:free") -> str:
    return f"INFO:ai-client:AI stream {MODEL_SERVED_MARKER}{model} chunks=42\n"


def test_the_log_line_the_client_writes_carries_the_marker() -> None:
    """The format in the client and the marker the matrix counts are the same text."""
    assert _served_line().count(MODEL_SERVED_MARKER) == 1
    assert "AI stream served by model=" in _served_line()


def test_only_lines_written_after_the_turn_started_count(tmp_path: Path) -> None:
    log = tmp_path / "orchestrator.log"
    log.write_text(_served_line("previous/turn:free"), encoding="utf-8")
    model_log = ModelLog(log)
    start = model_log.offset()
    with log.open("a", encoding="utf-8") as handle:
        handle.write("INFO:graph:SUPERVISOR_NODE → routing to → general_knowledge\n")
        handle.write(_served_line())
    assert asyncio.run(model_log.served_since(start, wait_s=0)) == 1


def test_a_missing_log_counts_zero_not_success(tmp_path: Path) -> None:
    model_log = ModelLog(tmp_path / "absent.log")
    assert asyncio.run(model_log.served_since(0, wait_s=0)) == 0


def test_an_answer_without_a_fingerprint_is_blocking() -> None:
    result = TurnResult(probe=_MODEL_PROBE, terminal_frames=1, content=_ARABIC_ANSWER)
    result.model_fingerprints = 0
    problems = _generation_problems(result)
    assert problems and "D-303" in problems[0]
    assert "(ISS-" not in problems[0]  # never deferred
    assert problems[0] in _turn_violations(result)


def test_an_answer_with_a_fingerprint_passes() -> None:
    result = TurnResult(probe=_MODEL_PROBE, terminal_frames=1, content=_ARABIC_ANSWER)
    result.model_fingerprints = 1
    assert _generation_problems(result) == []


def test_a_declared_deterministic_probe_needs_no_model() -> None:
    assert _GREETING.needs_llm is False
    result = TurnResult(probe=_GREETING, terminal_frames=1, content="وعليكم السلام")
    result.model_fingerprints = 0
    assert _generation_problems(result) == []


def test_no_log_means_not_measured_not_failed() -> None:
    result = TurnResult(probe=_MODEL_PROBE, terminal_frames=1, content=_ARABIC_ANSWER)
    assert result.model_fingerprints is None
    assert _generation_problems(result) == []


def test_a_spoken_failure_is_not_reported_twice() -> None:
    result = TurnResult(probe=_MODEL_PROBE, terminal_frames=1, spoken_error="⚠️ تعذّر")
    result.model_fingerprints = 0
    assert _generation_problems(result) == []


def test_new_probes_need_a_model_unless_declared() -> None:
    """Default is the safe side: only the two deterministic paths are exempt."""
    exempt = [probe.question for probe in MATRIX if not probe.needs_llm]
    assert exempt == ["السلام عليكم", "اعطني تمرين الاحتمالات 2024"]
    assert Probe("سؤال جديد", "physics").needs_llm is True


class _OneModelCompletions:
    """An OpenAI-compatible fake that serves one Arabic answer, streamed or not."""

    async def create(self, **kwargs: object) -> object:
        if kwargs.get("stream"):
            return _OneChunkStream()
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="نعم"))])


class _OneChunkStream:
    def __init__(self) -> None:
        self._sent = False

    def __aiter__(self) -> _OneChunkStream:
        return self

    async def __anext__(self) -> object:
        if self._sent:
            raise StopAsyncIteration
        self._sent = True
        return SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="نعم"))])


def _single_model_client() -> AIClient:
    client = AIClient.__new__(AIClient)
    client.client = SimpleNamespace(chat=SimpleNamespace(completions=_OneModelCompletions()))
    client.default_model = "test/only:free"
    client.first_token_timeout = 5.0
    client.last_model = None
    client.timeout = 5.0
    return client


def test_a_single_target_still_leaves_a_fingerprint(tmp_path: Path, caplog) -> None:
    """The proof must not depend on chain length: a caller that pins one model
    (``targets == [model]``) used to generate without writing the line, so a real
    answer would have been reported as ungenerated."""
    client = _single_model_client()

    async def _both() -> None:
        [chunk async for chunk in client.stream_chat([{"role": "user", "content": "؟"}], "m:free")]
        await client.generate(model="m:free", messages=[{"role": "user", "content": "؟"}])

    with caplog.at_level(logging.INFO, logger="ai-client"):
        asyncio.run(_both())
    log = tmp_path / "orchestrator.log"
    log.write_text("\n".join(caplog.messages) + "\n", encoding="utf-8")
    assert asyncio.run(ModelLog(log).served_since(0, wait_s=0)) == 2
