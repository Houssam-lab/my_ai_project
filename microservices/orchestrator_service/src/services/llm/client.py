"""AI Client for Orchestrator Service.
Provides a simple interface to OpenAI-compatible LLMs.

ISS-200 (D-288 — 2026-09-09): this client used to send every request to
``ActiveModels.PRIMARY`` and nothing else. Two failures compounded there:

1. **No fallback chain.** The monolith gateway
   (``app/core/gateway/simple_client.py``) rotates over ``[PRIMARY, FALLBACK_1..5]``
   and skips a model that 404s / 429s / returns ``content=None``. This client —
   the one the live chat graph actually calls
   (``services/overmind/graph/general_knowledge.py``, ``.../graph/search.py``) —
   did not. When OpenRouter stopped serving the pinned free model
   (``"endpoints": []``), *every* student turn died here while CI stayed green,
   because ``live-e2e.yml`` overrides PRIMARY through ``OPENROUTER_PRIMARY_MODEL``.
2. **The base URL was hardcoded**, so the chain could not be repointed at a
   gateway/proxy (or a test double) without editing source.

The client now rotates the same canonical chain the parity gate guards, reads the
base URL from the ``OPENROUTER_BASE_URL`` Settings field, and raises
:class:`AllModelsFailedError`
when the whole chain is exhausted — so a caller can report an outage instead of
answering a student with a canned line. **No model id is spelled out here**: the
single source of truth stays in ``ai_config``/``shared.ai_models.model_chain``
(gates: ``check_model_client_literals``, ``check_model_chain_parity``).
"""

import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator, Awaitable
from contextlib import suppress
from typing import Any

from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletionChunk

from microservices.orchestrator_service.src.core.ai_config import ActiveModels, get_ai_config
from microservices.orchestrator_service.src.core.config import get_settings

logger = logging.getLogger("ai-client")

#: Default OpenRouter surface. The *override knob* is a Settings field (D-270 L5: one
# home per programmatic identifier), so this module never re-declares the env name.
DEFAULT_BASE_URL = "https://openrouter.ai/api/v1"

#: Bound a model that connects but never produces content (monolith D-177 analogue:
#: an empty/slow model must not hold the turn for the whole socket timeout).
FIRST_TOKEN_TIMEOUT_ENV = "ORCHESTRATOR_LLM_FIRST_TOKEN_TIMEOUT"
DEFAULT_FIRST_TOKEN_TIMEOUT = 30.0

#: ISS-207 (D-302): one budget for the *whole* rotation until a model produces content.
#: The monolith reads this service with a 60 s timeout (``ORCHESTRATOR_CALL_TIMEOUT_S``);
#: waiting 30 s per model let two slow models outlast it, and the student was told the
#: service was down when the provider was only slow. Past this budget the chain is
#: declared exhausted — the named provider failure — so the caller always hears the
#: truth first. No env override on purpose: a test-only knob would hide the very
#: mismatch it exists to prevent (D-288). Guarded by
#: ``tests/microservices/orchestrator_service/test_iss207_chain_deadline.py``.
LLM_CHAIN_DEADLINE_S = 40.0

#: Statuses worth rotating away from immediately — a dead/rate-limited/unavailable
#: model is a routing problem, not a reason to fail the turn.
# 401/403 (مفتاح خاطئ أو صلاحية) لا تدور: كل نموذج سيفشل بنفس السبب ⇒ ارفع فوراً.
_RETRY_AS_FALLBACK_STATUS = frozenset({402, 404, 406, 408, 409, 413, 425, 429, 500, 502, 503, 504})


class AllModelsFailedError(RuntimeError):
    """كل نماذج السلسلة فشلت.

    يُرفع بدلاً من إرجاع نصٍّ جاهز: «تعذّر التوليد» حالةُ تشغيلٍ يجب أن يراها
    المُشغِّل (وإطار خطأ للعميل)، لا إجابة تُنسَب للمحتوى.
    """

    def __init__(self, attempts: list[tuple[str, str]]) -> None:
        self.attempts = list(attempts)
        detail = (
            ", ".join(f"{model}→{error}" for model, error in self.attempts)
            or "no models configured"
        )
        super().__init__(f"all models in chain failed: {detail}")
        self.models = [model for model, _ in self.attempts]


#: المفتاح نفسه مرفوض: كل نموذجٍ في السلسلة سيرفضه بالسبب نفسه، فلا دوران.
_AUTH_FAILURE_STATUS = frozenset({401, 403})


class ProviderAuthError(AllModelsFailedError):
    """المزوّد رفض المفتاح (401/403) — لا نموذج يستطيع الإجابة الآن.

    D-298: كان الخطأ الخام يسقط إلى ``except Exception`` في العُقد، فيصل الطالبَ نصٌّ
    جاهز («لم أتمكن من استرجاع هذه المعلومة») بحالة ``ok``، ويعدّه اختبار الإجابة
    ردّاً: بمفتاحٍ باطل نالت المصفوفة 14/14 ورمز خروج 0. هو صنفٌ فرعي من
    :class:`AllModelsFailedError` لأنّ العاقبة واحدة، فكلّ عقدةٍ تُعلن
    ``provider_error`` لانقطاع السلسلة تُعلنه لرفض المفتاح بلا سطرٍ إضافي.
    """


#: رسالة الحالة التشغيلية — تُعرَّف هنا لأن مصدرها فشل السلسلة نفسها، وتستهلكها عقد
#: الرسم بدل أن تخترع كلُّ عقدة نصّاً مختلفاً يُقرأ كأنه «إجابة» (ISS-200 / D-288).
PROVIDER_UNAVAILABLE_MESSAGE = (
    "⚠️ تعذّر الوصول إلى مزوّد الذكاء الاصطناعي حالياً: كل نماذج السلسلة فشلت في هذه "
    "الدورة. السؤال سليم والعطل في الخدمة — أعد المحاولة بعد لحظات."
)

#: بصمةُ التوليد في السجلّ: سطرٌ يُكتب حين يُنهي نموذجٌ حقيقيّ توليده بنجاح. يقرؤها
#: ``scripts/e2e/universal_answerability_live.py`` ليُثبت أنّ الجواب وَلَّده نموذج لا قالب
#: (D-303 · E2b) — فموطنها هنا، ولا تُكتب حرفيّتها في موضعٍ ثانٍ.
MODEL_SERVED_MARKER = "served by model="


class AIClient:
    """
    Simple AI Client for Orchestrator Service.
    Wraps AsyncOpenAI to provide generate and stream_chat methods, rotating the
    canonical model chain on failure (ISS-200).
    """

    #: Budget to find a model that produces content (ISS-207). Class-level so that
    #: instances built without ``__init__`` (tests, DI seams) still honour it.
    chain_deadline: float = LLM_CHAIN_DEADLINE_S

    def __init__(self) -> None:
        settings = get_settings()
        # The knob is a Settings field (D-270 L5 — one home per programmatic identifier);
        # this module only reads it. Empty override keeps the historical behaviour exactly.
        override = (settings.OPENROUTER_BASE_URL or "").strip()
        if settings.OPENROUTER_API_KEY:
            api_key = settings.OPENROUTER_API_KEY
            base_url = override or DEFAULT_BASE_URL
        else:
            api_key = settings.OPENAI_API_KEY
            base_url = override or None

        if not api_key:
            logger.warning("No API Key found for AI Client. AI features will fail.")

        # DEADLOCK FIX: bound leaf-node streaming/generate I/O. Without an
        # explicit timeout a stalled OpenRouter stream blocks the node
        # indefinitely; a bounded client raises so the node's fallback engages.
        # ISS-200: `max_retries=0` — the retry mechanism *is* the model chain.
        # Hammering one rate-limited model three times while a student waits adds
        # latency, not availability.
        self.timeout = float(os.getenv("ORCHESTRATOR_LLM_TIMEOUT", "45"))
        self.first_token_timeout = float(
            os.getenv(FIRST_TOKEN_TIMEOUT_ENV, DEFAULT_FIRST_TOKEN_TIMEOUT)
        )
        self.base_url = base_url
        self.client = AsyncOpenAI(
            api_key=api_key or "dummy-key",
            base_url=base_url,
            timeout=self.timeout,
            max_retries=0,
        )

        self.sync_client = OpenAI(
            api_key=api_key or "dummy-key",
            base_url=base_url,
            timeout=self.timeout,
            max_retries=0,
        )
        # لا حرفية هنا بعد اليوم: المصدر هو `ActiveModels.PRIMARY` — الملفّ الذي تحرسه
        # `check_model_chain_parity` بالفعل. فالقرار الواحد له موطنٌ واحد (D-186).
        # `ORCHESTRATOR_LLM_MODEL` يبقى تجاوزاً صريحاً للمُشغِّل.
        self.default_model = os.getenv("ORCHESTRATOR_LLM_MODEL", ActiveModels.PRIMARY)
        # آخر نموذج أعطى محتوى حقيقياً — للتشخيص و`/health` والـ telemetry.
        self.last_model: str | None = None

    # ------------------------------------------------------------------ chain
    def model_chain(self) -> list[str]:
        """السلسلة المرتَّبة: PRIMARY ثم الاحتياطيات، بلا تكرار (مصدر واحد للحقيقة).

        تُقرأ من `ai_config` في كل call (لا تُجمَّد عند الاستيراد) ليتبع العميلُ
        تجاوزَ المُشغِّل ``OPENROUTER_PRIMARY_MODEL`` و``OPENROUTER_EXTRA_MODELS``
        كما يفعل المونوليث بالضبط.
        """
        chain: list[str] = []
        # Runtime-discovered candidates precede the dated static recovery chain.
        # Previously OPENROUTER_EXTRA_MODELS was read by the registry probe only,
        # while the actual client silently ignored it — so CI could discover a
        # working free model and still invoke five removed/rate-limited IDs.
        runtime_fallbacks = [
            model.strip()
            for model in (get_settings().OPENROUTER_EXTRA_MODELS or "").split(",")
            if model.strip()
        ]
        candidates = [
            os.getenv("OPENROUTER_PRIMARY_MODEL", "").strip() or self.default_model,
            *runtime_fallbacks,
            *get_ai_config().get_fallback_models(),
        ]
        for candidate in candidates:
            cleaned = (candidate or "").strip()
            if cleaned and cleaned not in chain:
                chain.append(cleaned)
        return chain

    @staticmethod
    def _should_rotate(exc: Exception) -> bool:
        """هل يستحق هذا الخطأ تجربة النموذج التالي؟ (نعم لمعظم الأخطاء)."""
        if isinstance(exc, (APIConnectionError, APITimeoutError, TimeoutError, ConnectionError)):
            return True
        if isinstance(exc, APIError):
            status = getattr(exc, "status_code", None)
            if isinstance(status, int):
                return status in _RETRY_AS_FALLBACK_STATUS
            return True
        # ValueError من حارس «لا محتوى» + أخطاء الشبكة غير المصنَّفة.
        return True

    @staticmethod
    def _is_auth_failure(exc: Exception) -> bool:
        """401/403: المفتاح مرفوض — حالة تشغيل، لا خطأٌ في الطلب."""
        return (
            isinstance(exc, APIError) and getattr(exc, "status_code", None) in _AUTH_FAILURE_STATUS
        )

    def _describe(self, exc: Exception) -> str:
        status = getattr(exc, "status_code", None)
        name = type(exc).__name__
        msg = str(exc).replace("\n", " ")[:180]
        return f"{name}({status}) {msg}" if status else f"{name} {msg}"

    # --------------------------------------------------------------- generate
    async def generate(
        self,
        model: str | None = None,
        messages: list[dict[str, str]] | None = None,
        **kwargs: object,
    ) -> object:
        """
        Generate a complete response.
        If 'response_format' is JSON, returns the parsed object if possible, or the raw response.
        Use for non-streaming tasks.

        ISS-200: مع ``model=None`` تدور السلسلة كاملة؛ ومع ``model=<id>`` يبقى السلوك
        القديم (نموذج واحد، استثناء واحد) لتفادي كسر أي مستدعٍ محدِّد النموذج.
        """
        if not messages:
            messages = [{"role": "user", "content": kwargs.get("prompt", "")}]

        targets = [model] if model else self.model_chain()
        attempts: list[tuple[str, str]] = []
        for target_model in targets:
            try:
                resp = await self.client.chat.completions.create(
                    model=target_model,
                    messages=messages,
                    **kwargs,
                )
                self.last_model = target_model
                # D-303: unconditional — the E2E matrix reads this line as proof of
                # generation, so it must not depend on how many models are in the chain.
                logger.info("AI generate %s%s", MODEL_SERVED_MARKER, target_model)
                return resp
            except Exception as e:
                attempts.append((target_model, self._describe(e)))
                if self._is_auth_failure(e):
                    logger.error("AI Generation rejected by provider (auth): %s", e)
                    raise ProviderAuthError(attempts) from e
                if model or not self._should_rotate(e):
                    logger.error("AI Generation failed: %s", e)
                    raise
                logger.warning("AI generate: model=%s failed (%s) — rotating", *attempts[-1])
        raise AllModelsFailedError(attempts)

    # ------------------------------------------------------------- streaming
    async def stream_chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        **kwargs: object,
    ) -> AsyncGenerator[ChatCompletionChunk, None]:
        """
        Stream chat completion.
        Yields ChatCompletionChunk objects (OpenAI SDK type) — first chunk wins:
        a model is abandoned **only while nothing has been emitted**, so a student
        never sees two answers stitched together.
        Use extract_stream_content() to get text from each chunk safely.

        ISS-200: rotation over the canonical chain + ``content``-only guard (D-067:
        a reasoning-only model yields ``content=None`` and must not count as an
        answer) + :class:`AllModelsFailedError` when the whole chain is dead.
        """
        targets = [model] if model else self.model_chain()
        attempts: list[tuple[str, str]] = []
        chain_started = time.monotonic()
        for index, target_model in enumerate(targets):
            if time.monotonic() - chain_started >= self.chain_deadline:
                # ISS-207: the budget is spent — name every untried model, then stop.
                skipped = f"skipped: chain_deadline {self.chain_deadline:.0f}s exhausted"
                attempts.extend((untried, skipped) for untried in targets[index:])
                logger.warning(
                    "AI stream: chain_deadline %.0fs exhausted after %d model(s)",
                    self.chain_deadline,
                    index,
                )
                break
            emitted = 0
            started = time.monotonic()
            try:
                stream = await self._within_chain_budget(
                    self.client.chat.completions.create(
                        model=target_model,
                        messages=messages,
                        stream=True,
                        **kwargs,
                    ),
                    chain_started,
                    target_model,
                )
                async for chunk in self._budgeted(stream, chain_started, target_model):
                    if self._chunk_has_content(chunk):
                        if emitted == 0:
                            self.last_model = target_model
                        emitted += 1
                        yield chunk
                    elif emitted == 0 and (time.monotonic() - started) > self.first_token_timeout:
                        raise TimeoutError(
                            f"first_token_timeout model={target_model} "
                            f"after={self.first_token_timeout:.0f}s"
                        )
                if emitted == 0:
                    # نموذج بلا أي content (reasoning-only أو فراغ) = فشل، لا إجابة.
                    raise ValueError(f"empty_completion model={target_model} (content_chunks=0)")
                logger.info("AI stream %s%s chunks=%d", MODEL_SERVED_MARKER, target_model, emitted)
                return
            except Exception as e:
                if emitted > 0:
                    # وصل محتوى للطالب فعلاً: لا نعيد التوليد فوقه، ننهي الدور.
                    logger.warning(
                        "AI stream interrupted after %d chunks (model=%s): %s",
                        emitted,
                        target_model,
                        self._describe(e),
                    )
                    return
                attempts.append((target_model, self._describe(e)))
                if self._is_auth_failure(e):
                    logger.error("AI Stream rejected by provider (auth): %s", e)
                    raise ProviderAuthError(attempts) from e
                if model or not self._should_rotate(e):
                    logger.error("AI Stream failed: %s", e)
                    raise
                logger.warning("AI stream: model=%s failed (%s) — rotating", *attempts[-1])
        raise AllModelsFailedError(attempts)

    async def _within_chain_budget(
        self, awaitable: Awaitable[Any], chain_started: float, target_model: str
    ) -> Any:
        """Awaits ``awaitable`` within what is left of the chain budget (ISS-207)."""
        remaining = self.chain_deadline - (time.monotonic() - chain_started)
        try:
            return await asyncio.wait_for(awaitable, timeout=max(remaining, 0.0))
        except TimeoutError as exc:
            raise TimeoutError(
                f"chain_deadline model={target_model} after={self.chain_deadline:.0f}s"
            ) from exc

    async def _budgeted(
        self, stream: Any, chain_started: float, target_model: str
    ) -> AsyncGenerator[Any, None]:
        """Iterates ``stream``; every read before the first content chunk is budgeted.

        After content flows the budget no longer applies: the student is reading an
        answer and the caller is receiving bytes, so there is nothing to protect.
        """
        iterator = stream.__aiter__()
        content_seen = False
        while True:
            try:
                if content_seen:
                    chunk = await iterator.__anext__()
                else:
                    chunk = await self._within_chain_budget(
                        iterator.__anext__(), chain_started, target_model
                    )
            except StopAsyncIteration:
                return
            except TimeoutError:
                close = getattr(stream, "close", None)
                if close is not None:
                    with suppress(Exception):
                        await close()
                raise
            if not content_seen and self._chunk_has_content(chunk):
                content_seen = True
            yield chunk

    @staticmethod
    def _chunk_has_content(chunk: object) -> bool:
        """هل يحمل الـ chunk محتوى حقيقياً (لا reasoning فقط)؟"""
        return isinstance(AIClient.extract_stream_content(chunk), str)

    @staticmethod
    def extract_stream_content(chunk: object) -> str | None:
        """
        يستخرج محتوى النص من chunk بأمان سواء كان ChatCompletionChunk أو dict.

        ISS-STREAM-002: الإصلاح الجراحي — stream_chat يُعيد ChatCompletionChunk objects
        (OpenAI SDK) وليس dicts. الكود القديم كان يستخدم chunk.get('choices') مما يُسبب
        AttributeError يُبتلع بـ except → لا يُصدر أي محتوى → timeout كارثي.
        """
        # ChatCompletionChunk (OpenAI SDK object)
        if hasattr(chunk, "choices"):
            choices = chunk.choices
            if choices and len(choices) > 0:
                delta = choices[0].delta
                if delta is not None:
                    content = getattr(delta, "content", None)
                    if isinstance(content, str) and content:
                        return content
            return None

        # dict fallback (legacy/mock)
        if isinstance(chunk, dict):
            choices = chunk.get("choices")
            if choices and len(choices) > 0:
                delta = choices[0]
                if isinstance(delta, dict):
                    content = delta.get("delta", {}).get("content")
                else:
                    content = getattr(getattr(delta, "delta", None), "content", None)
                if isinstance(content, str) and content:
                    return content
        return None

    async def generate_text(self, prompt: str, **kwargs: object) -> str:
        """Helper for simple text generation."""
        response = await self.generate(prompt=prompt, **kwargs)
        return response.choices[0].message.content or ""

    def generate_sync(
        self,
        model: str | None = None,
        messages: list[dict[str, str]] | None = None,
        **kwargs: object,
    ) -> object:
        """
        Generate a complete response synchronously.
        """
        target_model = model or self.default_model
        if not messages:
            messages = [{"role": "user", "content": kwargs.get("prompt", "")}]

        try:
            return self.sync_client.chat.completions.create(
                model=target_model,
                messages=messages,
                **kwargs,
            )
        except Exception as e:
            logger.error(f"AI Sync Generation failed: {e}")
            raise

    def health_snapshot(self) -> dict[str, Any]:
        """لقطة تشغيل لمسار التوليد — تُستهلَك في `/health` والمسبارات الحيّة."""
        chain = self.model_chain()
        return {
            "primary": chain[0] if chain else None,
            "chain": chain,
            "last_serving_model": self.last_model,
            "base_url": self.base_url or "openai-default",
            "timeout_s": self.timeout,
            "first_token_timeout_s": self.first_token_timeout,
        }


# Singleton instance
ai_client = AIClient()


def get_ai_client() -> AIClient:
    return ai_client
