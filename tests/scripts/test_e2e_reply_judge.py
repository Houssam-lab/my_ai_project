"""D-298 — مُحكِّم الـE2E لا يعدّ النصّ الجاهز إجابة.

القياس الحيّ الذي وُلد منه هذا الملفّ (2026-09-29، تشغيلٌ محلي بمفتاحٍ باطل):
المصفوفة نالت **14/14 ورمز خروج 0** وكانت الردود كلّها نصوصاً جاهزة. هذه الاختبارات
تُعيد تمثيل ذلك التشغيل دون شبكة، وتُثبت أن الحكم صار **أحمر** عليه (البرهان السلبي،
D-270 L4)، وأنه يبقى أخضر على إجابةٍ حقيقية.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.services.llm import degraded_replies as monolith
from microservices.orchestrator_service.src.core import degraded_replies as orchestrator
from microservices.orchestrator_service.src.services.llm.client import (
    PROVIDER_UNAVAILABLE_MESSAGE,
)
from scripts.e2e import live_student_journey as journey
from scripts.e2e import universal_answerability_live as matrix
from scripts.e2e.reply_judge import (
    DEGRADED_REPLIES,
    degraded_reply,
    language_mismatch,
    reply_problems,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

_REAL_ANSWER = (
    "قانون أوم يربط بين الجهد والتيار والمقاومة: $$U = R \\cdot I$$ "
    "أي أن شدة التيار تتناسب طردياً مع فرق الجهد."
)


# ── الحَكَم ─────────────────────────────────────────────────────────────────────


def test_the_judge_sees_both_services() -> None:
    assert set(monolith.DEGRADED_REPLIES) <= set(DEGRADED_REPLIES)
    assert set(orchestrator.DEGRADED_REPLIES) <= set(DEGRADED_REPLIES)


@pytest.mark.parametrize("canned", DEGRADED_REPLIES)
def test_every_canned_reply_is_detected(canned: str) -> None:
    assert degraded_reply(canned) == canned


@pytest.mark.parametrize("canned", DEGRADED_REPLIES)
def test_detection_survives_sanitizer_punctuation_and_spacing(canned: str) -> None:
    """مُعقِّمات العُقد تمسّ الترقيم والمسافات — والحَكَم لا يُخدَع بذلك."""
    mangled = "\n  " + canned.rstrip(".!؟?") + "  \n"
    assert degraded_reply(mangled) == canned


def test_a_real_answer_is_not_degraded() -> None:
    assert degraded_reply(_REAL_ANSWER) is None
    assert reply_problems("اشرح لي قانون أوم", _REAL_ANSWER) == []


def test_the_honest_provider_error_is_not_in_the_list() -> None:
    """رسالة انقطاع المزوّد تصل إطارَ خطأ — وهي السلوك الصادق، لا نصٌّ بثوب إجابة."""
    assert PROVIDER_UNAVAILABLE_MESSAGE not in DEGRADED_REPLIES


def test_english_reply_to_an_arabic_question_is_refused() -> None:
    assert language_mismatch("اشرح لي قانون أوم", monolith.SAFETY_NET_REPLY)
    assert language_mismatch("لم أفهم", "Here's a thinking process: analyze the user input")
    assert reply_problems("لم أفهم", "Here's a thinking process: analyze the user input")


def test_a_french_question_may_be_answered_in_french() -> None:
    assert not language_mismatch("Explique-moi la loi d'Ohm", "La loi d'Ohm s'écrit U = R × I.")


# ── البرهان السلبي: إعادة تمثيل تشغيل المفتاح الباطل ──────────────────────────


def _replay_invalid_key_run() -> list[matrix.TurnResult]:
    """الأدوار الأربعة عشر كما خرجت حيّاً بمفتاحٍ باطل (التشغيل 4، 2026-09-29)."""
    greeting = "وعليكم السلام ورحمة الله وبركاته! 🌿 كيف يمكنني مساعدتك في دراستك اليوم؟"
    exercise = "## التمرين الأول (04 نقاط) — الاحتمالات\n\nيحتوي كيس على 11 كرة متماثلة."
    canned_by_index = {
        2: orchestrator.CHAT_FALLBACK_REPLY,
        6: orchestrator.NO_DETAILS_REPLY,
        10: orchestrator.NO_DETAILS_REPLY,
    }
    results: list[matrix.TurnResult] = []
    for index, probe in enumerate(matrix.MATRIX):
        if index == 0:
            content = greeting
        elif index == 1:
            content = exercise
        else:
            content = canned_by_index.get(index, orchestrator.GENERAL_KNOWLEDGE_FAILED_REPLY)
        result = matrix.TurnResult(probe=probe, terminal_frames=1, content=content)
        result.problems.extend(matrix._turn_violations(result))
        results.append(result)
    return results


def test_the_invalid_key_run_is_now_red(capsys: pytest.CaptureFixture[str]) -> None:
    """كان هذا التشغيل يخرج 0 بـ«✅ كل سؤالٍ أُجيب». الآن يُفشِل ويسمّي السبب."""
    results = _replay_invalid_key_run()
    assert matrix._verdict(results) == 1
    out = capsys.readouterr().out
    assert "أجابت: 2" in out
    assert "ردٌّ جاهز: 12" in out
    assert "ردٌّ جاهز لا إجابة" in out


def test_a_real_answer_run_stays_green(capsys: pytest.CaptureFixture[str]) -> None:
    results = []
    for probe in matrix.MATRIX:
        french = probe.question.startswith("Explique")
        content = "La loi d'Ohm s'écrit U = R × I." if french else _REAL_ANSWER
        result = matrix.TurnResult(probe=probe, terminal_frames=1, content=content)
        result.problems.extend(matrix._turn_violations(result))
        results.append(result)
    assert matrix._verdict(results) == 0
    capsys.readouterr()


# ── رحلة الطالب: محادثةٌ واحدة ─────────────────────────────────────────────────


def _turn(question: str, conversation_id: int | None) -> journey.TurnResult:
    return journey.TurnResult(question=question, conversation_id=conversation_id)


def test_the_journey_requires_one_conversation() -> None:
    split = [_turn("السلام عليكم", 71), _turn("لم أفهم", 72)]
    assert journey._continuity_problems(split)
    same = [_turn("السلام عليكم", 75), _turn("لم أفهم", 75)]
    assert journey._continuity_problems(same) == []


def test_the_journey_refuses_a_missing_conversation_id() -> None:
    assert journey._continuity_problems([_turn("السلام عليكم", None)])


def test_the_journey_flags_a_canned_reply() -> None:
    turn = journey.TurnResult(
        question="كيف نحسب A", terminal_frames=1, content=monolith.ARABIC_GUARD_FALLBACK_REPLY
    )
    assert any("ردٌّ جاهز" in problem for problem in journey._turn_violations(turn))


# ── موطنٌ واحد لكل نصٍّ جاهز ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("home", "tree"),
    [
        ("app/services/llm/degraded_replies.py", "app"),
        (
            "microservices/orchestrator_service/src/core/degraded_replies.py",
            "microservices/orchestrator_service/src",
        ),
    ],
)
def test_each_canned_reply_is_written_once(home: str, tree: str) -> None:
    """نصٌّ جاهز مكتوبٌ حرفياً خارج موطنه نصٌّ لا يراه الحَكَم (D-186 · D-298).

    بالـAST لا بالبحث النصّي: وثيقةٌ تذكر النصّ في شرحها ليست نسخةً منه.
    """
    import ast

    module = monolith if home.startswith("app/") else orchestrator
    canned_texts = set(module.DEGRADED_REPLIES)
    offenders: list[str] = []
    for path in (REPO_ROOT / tree).rglob("*.py"):
        relative = path.relative_to(REPO_ROOT).as_posix()
        if relative == home:
            continue
        tree_ast = ast.parse(path.read_text(encoding="utf-8"))
        offenders.extend(
            f"{relative}:{node.lineno}: {node.value[:40]!r}"
            for node in ast.walk(tree_ast)
            if isinstance(node, ast.Constant) and node.value in canned_texts
        )
    assert not offenders, offenders
