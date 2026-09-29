"""حَكَمُ الردّ: يميّز الإجابة من النصّ الجاهز (D-298).

## لماذا هذا الملفّ موجود

مُحكِّما الـE2E كانا يعدّان **أيّ نصٍّ غير فارغ** إجابةً. والقياس الحيّ (2026-09-29) أثبت
الثمن: بمفتاح نموذجٍ **باطل** نالت مصفوفة «يجيب على كل سؤال» **14/14 ورمز خروج 0**، وكانت
الردود كلّها نصوصاً جاهزة (اعتذار «لم أتمكن من استرجاع هذه المعلومة» ×9 · «لا توجد تفاصيل
متاحة» ×2 · تحيةٌ لطالبٍ قال «لم أفهم»). وفي الإنتاج أكثر ردٍّ تكراراً منذ 2026-08-01
اعتذارٌ واحد (١٬٠٠٦ مرّة) يُحفَظ إجابة.

## ما يحكم به

1. **ردٌّ جاهز لا إجابة**: الردّ يحمل نصّاً من :data:`DEGRADED_REPLIES`. القائمة لا تُكتب
   هنا: تُستورد من موطنَيها (المونوليث والـ orchestrator) — نصٌّ جاهز جديد يُضاف هناك
   فيراه الحَكَم تلقائياً (D-186 · D-270 L5).
2. **سؤالٌ بالعربية أُجيب بلا حرفٍ عربي**: شبكة الأمان الإنجليزية وتسرّب التفكير
   («Here's a thinking process…») كانا يمرّان لأن حارس اللاتينية يتخطّى الردّ غير العربي
   أصلاً.

المطابقة بعد **تطبيعٍ** يُسقط الترقيم والمسافات، لأن مُعقِّمات العُقد قد تمسّهما.
"""

from __future__ import annotations

import re
from typing import Final

from app.services.llm.degraded_replies import DEGRADED_REPLIES as _MONOLITH_DEGRADED
from microservices.orchestrator_service.src.core.degraded_replies import (
    DEGRADED_REPLIES as _ORCHESTRATOR_DEGRADED,
)

#: كلّ نصٍّ جاهز يمكن أن يصل الطالب إطارَ إجابة — من الخدمتين.
DEGRADED_REPLIES: Final[tuple[str, ...]] = (*_MONOLITH_DEGRADED, *_ORCHESTRATOR_DEGRADED)

_ARABIC_LETTER = re.compile(r"[ء-ي]")
_NON_WORD = re.compile(r"[^\w]+", flags=re.UNICODE)


def _normalise(text: str) -> str:
    return _NON_WORD.sub(" ", text).strip()


_NORMALISED: Final[tuple[tuple[str, str], ...]] = tuple(
    (canned, _normalise(canned)) for canned in DEGRADED_REPLIES
)


def degraded_reply(content: str) -> str | None:
    """النصّ الجاهز الذي يحمله الردّ، أو ``None`` إن كان الردّ إجابة."""
    text = _normalise(content)
    if not text:
        return None
    for canned, needle in _NORMALISED:
        if needle and needle in text:
            return canned
    return None


def language_mismatch(question: str, content: str) -> bool:
    """سؤالٌ فيه حرفٌ عربي أُجيب بنصٍّ غير فارغ لا حرف عربي فيه."""
    return (
        bool(_ARABIC_LETTER.search(question))
        and bool(content.strip())
        and not _ARABIC_LETTER.search(content)
    )


def reply_problems(question: str, content: str) -> list[str]:
    """مخالفات الردّ الحاجبة — تُضاف إلى مخالفات الدور في المُحكِّمين."""
    canned = degraded_reply(content)
    if canned:
        return [f"ردٌّ جاهز لا إجابة: {canned[:60]!r} (D-298)"]
    if language_mismatch(question, content):
        return ["سؤالٌ بالعربية أُجيب بلا حرفٍ عربي واحد (D-298)"]
    return []


__all__ = ["DEGRADED_REPLIES", "degraded_reply", "language_mismatch", "reply_problems"]
