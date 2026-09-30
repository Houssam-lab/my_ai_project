#!/usr/bin/env python3
"""مصفوفة «يجيب على كل سؤال» — تجريبٌ حيّ لا محاكاة (D-266 · ISS-159).

## لماذا هذا السكربت موجود

طلبُ المالك: «التأكد أن النظام يجيب على كل الأسئلة مهما كانت». والقياس قبله كان
`live_student_journey.py`: **أربعة** أسئلة، كلّها من تمرين احتمالات. أي أنّ المسار
الوحيد المُثبَت حياً هو المسار الذي وقعت فيه ISS-159 — بينما الفيزياء والعلوم
واللغات لم يقسها شيء.

هذا يقيس **العرض** لا العمق: أربع عشرة زاوية عبر ثلاث مواد وثلاث لغات، وكلٌّ منها
يفرض العقد نفسه على الدور.

## ما يفرضه على كل دور

| القاعدة | المصدر |
|---|---|
| إطارٌ نهائي **واحد** — لا صفر ولا اثنان | §6.5 (`_emit_terminal_frames`) |
| محتوى غير فارغ — لا دورَ صامت | ISS-145 · ISS-154 |
| لا نصَّ جاهزاً بثوب إجابة، ولا ردَّ بلا حرفٍ عربي على سؤالٍ عربي | D-298 (`reply_judge`) |
| جوابٌ **وَلَّده نموذج**: بصمة التوليد في سجلّ الـorchestrator داخل نافذة الدور | D-303 · E2b |
| صفر خطف موضوع: سؤال فيزياء لا يُجاب بمفردات الاحتمالات | **ISS-159** |
| صفر نصّ نظامٍ بدور الطالب | D-117 · D-229 · ISS-146 |
| صفر تسريب إجابة التمرين المرجعي | D-113 · ISS-148 |
| كائنٌ مُولَّد تعرف الواجهة رسمه | ISS-145 (`KNOWN_UI_COMPONENTS`) |

وتُبلَّغ ولا تحجب: كل مخالفةٍ يسمّي نصُّها بلاغاً **مؤجَّلاً بتصريح** في
`scripts/e2e/deferred_findings.py` — واليوم أحدُها: تسرّبُ نثرٍ لاتيني (ISS-150)، وهو
🔴 مفتوحٌ بقرارٍ مكتوبٍ بتأجيله. تُطبَع بنصّها في كل تشغيل، ويتغيّر رمز الخروج وحده.

⛔ **الأسرار من البيئة حصراً** — لا مفتاح ولا كلمة مرور في هذا الملفّ (D-265 L8).

    python scripts/e2e/universal_answerability_live.py --base http://localhost:8000
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import websockets

# جذر المستودع على المسار قبل أي استيرادٍ محلّي. تشغيل `python scripts/e2e/x.py`
# يضع `scripts/e2e/` في `sys.path[0]` لا جذر المستودع، و`live-e2e.yml` لا يضبط
# `PYTHONPATH` — فبدون هذا السطر يموت السكربت بـ`ModuleNotFoundError: app` على
# العدّاء. نفس نمط `honcho_live_probe.py` — مصدرٌ واحد لثلاثتها.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.contracts.streaming import KNOWN_UI_COMPONENTS

#: المصدر الوحيد لما يُبلَّغ ولا يحجب (ISS-199). ⛔ ولا قائمة ثانية هنا (D-186).
from scripts.e2e.deferred_findings import (
    mark,
    outage_floor_problem,
    render_deferred,
    split_problems,
    spoken_error_problem,
)

#: الحَكَم الذي يميّز الإجابة من النصّ الجاهز (D-298) — مشتركٌ مع رحلة الطالب.
from scripts.e2e.reply_judge import degraded_reply, reply_problems
from shared.memory import is_system_authored

_TERMINAL = {"assistant_final", "error", "assistant_error"}

#: مفردات العقل الاحتمالي. ظهورُها في جواب سؤالٍ من مادةٍ أخرى **هو** ISS-159.
_PROBABILITY_VOCABULARY = (
    "فضاء العينة",
    "فضاء العيّنة",
    "الحالات الملائمة",
    "التوافيق",
    "كرات",
    "نسحب",
    "الحادثة A",
)

#: أرقام التمرين المرجعي. ظهورُها في أيّ دورٍ لم يسأل عنها تسريبٌ (D-113 · ISS-148).
_REFERENCE_EXERCISE_NUMBERS = ("165", "= 14", "4 + 10")

#: عدد الكلمات اللاتينية المتتابعة التي تُعتبر نثراً مُسرَّباً (منقولٌ من
#: `live_student_journey.py` — الرياضيات تكتب `\dfrac` والتسمية الثنائية مقصودة).
_LATIN_PROSE_WORDS = 3


@dataclass(frozen=True)
class Probe:
    """سؤالٌ واحد وما يجب أن **لا** يظهر في جوابه."""

    question: str
    #: المادة المتوقّعة — للتقرير، ولاشتقاق حظر مفردات الاحتمالات.
    subject: str
    #: هل يُمنع أن يحمل الجواب مفردات الاحتمالات؟ (كل ما ليس رياضيات احتمالية)
    forbid_probability_vocabulary: bool = False
    note: str = ""
    #: هل يجب أن يُولِّد الجوابَ نموذجٌ لغوي؟ (D-303 · E2b) — الافتراضي **نعم**: سؤالٌ
    #: جديد يُطالَب بالبرهان ما لم يُصرَّح بمساره الحتمي. كان الحارس يقبل أيّ نصٍّ
    #: غير جاهز، فجوابٌ من قالبٍ أو مخزنٍ ثابت يجتازه كأنه تعليم.
    needs_llm: bool = True


#: المصفوفة. كلّ صفٍّ زاويةٌ مختلفة — لا تكرارٌ لنفس المسار بصياغةٍ أخرى (D-207).
MATRIX: tuple[Probe, ...] = (
    Probe("السلام عليكم", "—", note="التحية: مسارٌ حتمي قبل أيّ LLM (D-067)", needs_llm=False),
    Probe("اعطني تمرين الاحتمالات 2024", "mathematics", note="الاسترجاع المُفهرَس", needs_llm=False),
    Probe("لم أفهم", "mathematics", note="الحيرة: تشخيصٌ لا إعادة اشتقاق (D-113)"),
    Probe("كيف نحسب عدد الحالات الممكنة", "mathematics", note="سؤالٌ إجرائي (D-207)"),
    Probe("اشرح لي قانون أوم", "physics", True, "ISS-159: كان يُجاب بتمرين الكرات"),
    Probe("ما هو مبدأ أرخميدس", "physics", True, "ISS-159: الصنف لا الحالة"),
    Probe("ما الفرق بين الجهد والتيار", "physics", True, "ISS-159: «الفرق» تفتح البوّابة"),
    Probe("ما معنى الرمز Ω في الفيزياء", "physics", True, "ISS-159: الرمز داخل مادته"),
    Probe("ما هو التناضح الخلوي", "natural_sciences", True, "المادة معاملها ٦ (D-193)"),
    Probe("اشرح لي تركيب البروتين", "natural_sciences", True, "علوم الطبيعة"),
    Probe("اشرح لي الدالة الأسية", "mathematics", True, "رياضياتٌ غير احتمالية"),
    Probe("واش راهو الاشتقاق؟", "mathematics", True, "الدارجة الجزائرية"),
    Probe("Explique-moi la loi d'Ohm", "physics", True, "الفرنسية"),
    Probe("كيفاش نحسب مساحة الدائرة", "mathematics", True, "دارجة + خارج المنهاج المباشر"),
)


@dataclass
class TurnResult:
    probe: Probe
    total_s: float = 0.0
    terminal_frames: int = 0
    content: str = ""
    components: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)
    #: نصّ خطأٍ **منطوق** للطالب (`error.payload.message`) — فشلٌ مُعلَن لا صمت.
    spoken_error: str = ""
    #: عدد بصمات التوليد في سجلّ الـorchestrator خلال الدور؛ ``None`` = لم يُقَس (لا سجلّ).
    model_fingerprints: int | None = None


def _latin_leak(text: str) -> str | None:
    """نثرٌ إنجليزي داخل ردٍّ عربي — ISS-150 (تُنزَع الرياضيات أوّلاً)."""
    if not re.search(r"[؀-ۿ]", text):
        return None  # ردٌّ غير عربي أصلاً (سؤال فرنسي) — خارج النطاق
    stripped = re.sub(r"\$\$.*?\$\$|\$[^$]*\$", " ", text, flags=re.DOTALL)
    stripped = re.sub(r"\\\(.*?\\\)|\\\[.*?\\\]", " ", stripped, flags=re.DOTALL)
    stripped = re.sub(r"\\[A-Za-z]+", " ", stripped)
    match = re.search(
        rf"(?:\b[A-Za-z]{{2,}}\b[\s,:;-]+){{{_LATIN_PROSE_WORDS - 1},}}\b[A-Za-z]{{2,}}\b", stripped
    )
    return match.group(0).strip() if match else None


def _delivery_problems(result: TurnResult) -> list[str]:
    """عقد التسليم: إطارٌ نهائيّ واحد، وشيءٌ وصل الطالب فعلاً.

    ── الصمت ليس الفشل، والفشل المنطوق ليس صمتاً ─────────────────────────────
    أوّل نسخةٍ من هذا الحارس قرأت `payload.content` وحده، فأبلغت عن **١٢ دوراً
    صامتاً** بينما كان الخادم يُرسل إطار `error` يحمل رسالةً عربية صريحة في
    `payload.message` («النظام يتطلب الخدمات الذكية المتقدمة…»). أي أنّ الطالب كان
    **يقرأ** الفشل، والحارس أعلن كارثةً لا وجود لها.

    وهذا نفس صنف ISS-145 الذي أُغلق **بالتفنيد**: فحصٌ على المعيار الخطأ. ومعيارٌ خطأ
    في أداة تحقّقٍ أسوأ من غيابها — يُنتج بلاغاتٍ كاذبة تستهلك ثقةَ من يقرؤها.
    """
    problems: list[str] = []
    if result.terminal_frames != 1:
        problems.append(f"إطاراتٌ نهائية = {result.terminal_frames} والعقد يوجب **واحداً** (§6.5)")
    if result.spoken_error:
        problems.append(spoken_error_problem(result.spoken_error))
    elif not result.content.strip() and not result.components:
        problems.append("دورٌ صامت: لا نصَّ ولا كائن ولا خطأٌ منطوق (ISS-145 · ISS-154)")
    else:
        # D-298: نصٌّ غير فارغ ليس بالضرورة إجابة — النصّ الجاهز فشلٌ بثوب إجابة.
        problems.extend(reply_problems(result.probe.question, result.content))
    return problems


def _purity_problems(result: TurnResult) -> list[str]:
    """نقاء المخرَج: لا شظيّة لاتينية، ولا نصّ نظامٍ يصل الطالب."""
    problems: list[str] = []
    leak = _latin_leak(result.content)
    if leak:
        problems.append(f"شظيّة لاتينية في ردٍّ عربي: {leak!r} (ISS-150)")
    if is_system_authored(result.content):
        problems.append("نصُّ نظامٍ وصل الطالب (D-117/D-229)")
    return problems


def _topic_problems(result: TurnResult) -> list[str]:
    """خطفُ الموضوع وتسريب أرقام التمرين المرجعي — قلبُ ISS-159 وD-113."""
    if not result.probe.forbid_probability_vocabulary:
        return []
    problems: list[str] = []
    hijacked = [word for word in _PROBABILITY_VOCABULARY if word in result.content]
    if hijacked:
        problems.append(
            f"خطفُ موضوع: مفردات الاحتمالات {hijacked} في سؤال {result.probe.subject} (ISS-159)"
        )
    leaked = [num for num in _REFERENCE_EXERCISE_NUMBERS if num in result.content]
    if leaked:
        problems.append(f"تسريب أرقام التمرين المرجعي {leaked} (D-113 · ISS-148)")
    return problems


def _component_problems(result: TurnResult) -> list[str]:
    """كل كائنٍ مُولَّد تعرف الواجهة رسمه (ISS-145)."""
    return [
        f"مكوّنٌ لا تعرف الواجهة رسمه: {name!r} (ISS-145)"
        for name in result.components
        if name not in KNOWN_UI_COMPONENTS
    ]


def _generation_problems(result: TurnResult) -> list[str]:
    """جوابٌ وصل ولم يُولِّده نموذج — D-303 · E2b.

    يُطبَّق على ما يُعَدّ «أجاب» فقط: الدور الذي فشل صراحةً مُبلَّغٌ عنه أصلاً، ولا يُضاف
    إليه سببٌ ثانٍ. ولا حكم بلا قياس: سجلٌّ لم يُمرَّر ⇒ ``None`` ⇒ لا مخالفة، ويُطبَع ذلك
    في رأس التشغيل لأن الغياب لا يُقرأ نجاحاً (D-206 L11).
    """
    if result.model_fingerprints is None or not result.probe.needs_llm:
        return []
    if result.model_fingerprints == 0 and _answered(result):
        return ["أُجيب بلا بصمة توليد في سجلّ الـorchestrator — نصٌّ لم يولّده نموذج (D-303 · E2b)"]
    return []


def _turn_violations(result: TurnResult) -> list[str]:
    """كل ما يخالف عقد الدور — خمس عائلاتٍ مستقلّة، كلٌّ تُقرأ وحدها."""
    return [
        *_delivery_problems(result),
        *_purity_problems(result),
        *_topic_problems(result),
        *_component_problems(result),
        *_generation_problems(result),
    ]


class ModelLog:
    """نافذةُ الدور على سجلّ الـorchestrator: كم بصمة توليدٍ كُتبت منذ بدأ الدور."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def offset(self) -> int:
        return self.path.stat().st_size if self.path.exists() else 0

    def _count_since(self, start: int) -> int:
        from microservices.orchestrator_service.src.services.llm.client import (
            MODEL_SERVED_MARKER,
        )

        if not self.path.exists():
            return 0
        with self.path.open("rb") as handle:
            handle.seek(start)
            return handle.read().decode("utf-8", errors="replace").count(MODEL_SERVED_MARKER)

    async def served_since(self, start: int, *, wait_s: float = 3.0) -> int:
        """البصمة تُكتب قبل الإطار النهائي؛ المهلة القصيرة احتياطٌ من تأخّر الكتابة لا غير."""
        deadline = time.monotonic() + wait_s
        while True:
            count = self._count_since(start)
            if count or time.monotonic() >= deadline:
                return count
            await asyncio.sleep(0.25)


async def _login(base: str, email: str, password: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{base}/api/security/login", json={"email": email, "password": password}
        )
        if response.status_code != 200:
            raise SystemExit(f"تعذّر تسجيل الدخول: {response.status_code} — {response.text[:200]}")
        return str(response.json()["access_token"])


def _absorb_frame(result: TurnResult, event: dict[str, Any]) -> bool:
    """يستوعب إطاراً واحداً. يُرجِع `True` حين يكون الإطار **نهائياً** فينتهي الدور."""
    etype = event.get("type", "")
    payload = event.get("payload") or {}
    if etype == "assistant_delta" and payload.get("content"):
        result.content += str(payload["content"])
        return False
    if etype == "ui_component":
        result.components.append(str(payload.get("component", "")))
        return False
    if etype not in _TERMINAL:
        return False
    result.terminal_frames += 1
    if etype == "assistant_final" and payload.get("content"):
        result.content = result.content or str(payload["content"])
    if etype in {"error", "assistant_error"}:
        # Non-empty outage text is still an error, not an answer.  The old probe
        # counted assistant_error.content as successful content, exactly masking
        # the production symptom this matrix claims to detect.
        result.spoken_error = str(
            payload.get("message") or payload.get("content") or payload.get("details") or etype
        )
    return True


async def _next_event(ws: Any, result: TurnResult) -> dict[str, Any] | None:
    """الإطار التالي مُحلَّلاً، أو `None` حين يتعذّر — والتعذّر **يُبلَّغ** ولا يُبتلع."""
    try:
        raw = await asyncio.wait_for(ws.recv(), timeout=150.0)
    except TimeoutError:
        result.problems.append("انتهت المهلة بلا إطارٍ نهائي — دورٌ معلَّق")
        raise
    try:
        return dict(json.loads(raw))
    except json.JSONDecodeError:
        result.problems.append("إطارٌ ليس JSON — تسريبُ بنية إلى الدردشة")
        return None


async def _stream_turn(ws: Any, result: TurnResult) -> None:
    """يقرأ الأطر حتى الإطار النهائي — حلقةٌ واحدة بلا قرارٍ داخلها."""
    while True:
        try:
            event = await _next_event(ws, result)
        except TimeoutError:
            return
        if event is not None and _absorb_frame(result, event):
            return


async def _run_turn(
    ws_url: str, token: str, probe: Probe, model_log: ModelLog | None = None
) -> TurnResult:
    """دورٌ واحد كامل: اتصال · إرسال · قراءةٌ حتى النهاية · حكم."""
    result = TurnResult(probe=probe)
    log_start = model_log.offset() if model_log else 0
    started = time.perf_counter()
    try:
        async with websockets.connect(
            ws_url, subprotocols=["jwt", token], open_timeout=30, close_timeout=10
        ) as ws:
            await ws.send(json.dumps({"question": probe.question}))
            await _stream_turn(ws, result)
    except Exception as exc:  # نُبلِّغ ولا نبتلع (§0)
        result.problems.append(f"انقطاع الاتصال: {exc.__class__.__name__}: {exc}")
    result.total_s = time.perf_counter() - started
    if model_log is not None and probe.needs_llm:
        result.model_fingerprints = await model_log.served_since(log_start)
    result.problems.extend(_turn_violations(result))
    return result


def _print_turn(result: TurnResult) -> None:
    head = (result.content.strip() or result.spoken_error.strip()).replace("\n", " ")[:90]
    status = "❌" if result.problems else "✅"
    print(
        f"  {status} [{result.probe.subject:16s}] {result.total_s:6.2f}s · {len(result.content):5d} حرفاً"
    )
    print(f"     ↳ {head}…" if head else "     ↳ (بلا نصّ)")
    for problem in result.problems:
        print(f"     {mark(problem)}")


def _answered(result: TurnResult) -> bool:
    """وصل الطالبَ شيءٌ يُقرأ — نصّاً حقيقياً أو كائناً. ⛔ النصّ الجاهز ليس إجابة (D-298)."""
    real_text = bool(result.content.strip()) and degraded_reply(result.content) is None
    return bool(real_text or result.components)


def _tally(results: list[TurnResult], blocking: int, deferred: int) -> str:
    """سطر الحصيلة — أربع حالات: أجاب · ردٌّ جاهز · فشلٌ منطوق · صمتٌ تام."""
    answered = sum(1 for r in results if _answered(r))
    canned = sum(1 for r in results if not _answered(r) and degraded_reply(r.content))
    spoken = sum(1 for r in results if r.spoken_error and not _answered(r))
    silent = sum(
        1
        for r in results
        if not _answered(r) and not r.spoken_error and not degraded_reply(r.content)
    )
    return (
        f"أدوار: {len(results)} · أجابت: {answered} · ردٌّ جاهز: {canned} · "
        f"فشلٌ منطوق: {spoken} · صمتٌ تام: {silent} · "
        f"مخالفات حاجبة: {blocking} · مؤجَّلة بتصريح: {deferred}"
    )


def _verdict(results: list[TurnResult]) -> int:
    """رمز الخروج هو ما تقرأه CI — والمخالفات تُطبَع بنصّها لا مُلخَّصة.

    الحاجبة تُفشِل، والمؤجَّلة **بتصريح** تُطبَع ولا تُفشِل (ISS-199) — وتُطبَع حتى
    في التشغيل الأخضر، لأن خُضرةً لا تقول ما رأته تُقرأ «لم يحدث شيء» (D-206 L11).
    """
    blocking = [(r.probe.question, p) for r in results for p in split_problems(r.problems)[0]]
    deferred = [p for r in results for p in split_problems(r.problems)[1]]
    # D-301: تأجيل انقطاع المزوّد (ISS-206) لا يغطّي انقطاعاً شاملاً.
    floor = outage_floor_problem(sum(1 for r in results if _answered(r)), len(results))
    if floor:
        blocking.append(("المصفوفة كلّها", floor))
    print("\n" + "═" * 70)
    print(_tally(results, len(blocking), len(deferred)))
    if deferred:
        print("\n⚠️ مؤجَّلة بتصريح — تُبلَّغ ولا تحجب:")
        for line in render_deferred(deferred):
            print(line)
    if not blocking:
        print("\n✅ كل سؤالٍ أُجيب بإطارٍ نهائيٍّ واحد، من مادته، بلا نصّ نظامٍ ولا دورٍ صامت.")
        return 0
    print("\n❌ المخالفات الحاجبة:")
    for question, problem in blocking:
        print(f"   • «{question}» — {problem}")
    return 1


async def main() -> int:
    parser = argparse.ArgumentParser(description="مصفوفة «يجيب على كل سؤال» — D-266")
    parser.add_argument("--base", default=os.environ.get("E2E_BACKEND", "http://localhost:8000"))
    parser.add_argument("--email", default=os.environ.get("DIAG_EMAIL", ""))
    parser.add_argument("--password", default=os.environ.get("DIAG_PASSWORD", ""))
    parser.add_argument(
        "--model-log",
        type=Path,
        default=os.environ.get("E2E_MODEL_LOG") or None,
        help="سجلّ الـorchestrator لإثبات أنّ نموذجاً وَلَّد كل جوابٍ يحتاجه (D-303)",
    )
    args = parser.parse_args()

    if not args.email or not args.password:
        raise SystemExit("⛔ بيانات الدخول من البيئة حصراً: DIAG_EMAIL / DIAG_PASSWORD (D-265 L8).")

    token = await _login(args.base, args.email, args.password)
    ws_url = args.base.replace("http://", "ws://").replace("https://", "wss://") + "/api/chat/ws"

    model_log = ModelLog(args.model_log) if args.model_log else None
    print(f"▶ الخادم: {args.base} · أسئلة: {len(MATRIX)}")
    print(
        f"▶ بصمة التوليد: تُفحَص في {args.model_log}\n"
        if model_log
        else "▶ بصمة التوليد: لم تُفحَص — لا سجلّ orchestrator (--model-log)\n"
    )
    results: list[TurnResult] = []
    for probe in MATRIX:
        print(f"▶ «{probe.question}»  — {probe.note}", flush=True)
        result = await _run_turn(ws_url, token, probe, model_log)
        results.append(result)
        _print_turn(result)
    return _verdict(results)


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
