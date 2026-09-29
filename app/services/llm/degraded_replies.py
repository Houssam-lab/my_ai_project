"""النصوص الجاهزة التي يُرسلها المونوليث حين لا يملك إجابة حقيقية (D-298).

مرآة ``microservices/orchestrator_service/src/core/degraded_replies.py`` في جهة
المونوليث — لا يستورد أحدهما الآخر (حدّ الخدمة)، ومُحكِّم الـE2E يستورد الاثنين.

**لماذا:** أكثر ردٍّ تكراراً في قاعدة الإنتاج منذ 2026-08-01 هو
:data:`ARABIC_GUARD_FALLBACK_REPLY` (١٬٠٠٦ مرّة)، يُحفَظ إجابةً ويعدّه اختبار «يجيب على كل
سؤال» ردّاً. نصٌّ بلا موطنٍ مُسمّى لا يستطيع القياس أن يراه.
"""

from __future__ import annotations

from typing import Final

#: ``arabic_stream_guard`` — رُفضت المحاولتان (نافذة إنجليزية أو غارباج).
ARABIC_GUARD_FALLBACK_REPLY: Final = (
    "عذراً، تعذّر توليد إجابة سليمة بالعربية في هذه اللحظة. "
    "يرجى إعادة صياغة سؤالك أو المحاولة مرة أخرى."
)

#: ``SafetyNetService`` — استُنفدت سلسلة النماذج في بوّابة المونوليث.
SAFETY_NET_REPLY: Final = (
    "⚠️ System Alert: Unable to reach external intelligence providers. Please try again later."
)

#: تعقيم الطوبولوجيا في ``text_streaming`` — يستبدل نصّاً كاملاً ذُكرت فيه بنيةٌ داخلية.
SERVICE_UNAVAILABLE_REPLY: Final = (
    "تعذر إتمام طلبك حالياً بسبب ضغط أو عطل مؤقت في خدمة المحادثة. حاول مرة أخرى بعد لحظات."
)

#: القائمة التي يستوردها المُحكِّم.
DEGRADED_REPLIES: Final[tuple[str, ...]] = (
    ARABIC_GUARD_FALLBACK_REPLY,
    SAFETY_NET_REPLY,
    SERVICE_UNAVAILABLE_REPLY,
)
