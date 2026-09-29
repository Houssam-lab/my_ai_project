"""النصوص الجاهزة التي يُرسلها الـ orchestrator حين لا يملك إجابة حقيقية (D-298).

**لماذا هذا الملفّ:** كلّ نصٍّ هنا كان حرفيةً مُضمَّنة في عقدة، فلا يعرف أحدٌ من خارجها أنه
نصٌّ جاهز لا محتوى. واختبار «يجيب على كل سؤال» كان يعدّ أيّ نصٍّ غير فارغ إجابة، فنالت
المصفوفة **14/14 ورمز خروج 0 بمفتاحٍ باطل** بينما كانت الردود كلّها من هذه القائمة.

القانون: لكلّ نصٍّ موطنٌ واحد (D-186 · D-270 L5). العُقد تستورده من هنا، ومُحكِّم الـE2E
يستورد :data:`DEGRADED_REPLIES` نفسها ليعدّ ظهور أحدها **فشلاً للدور لا إجابة**.

⛔ ليس منها :data:`PROVIDER_UNAVAILABLE_MESSAGE` (``services/llm/client.py``): تلك تصل
الطالب إطارَ خطأٍ صريحاً، وهو السلوك الصادق. هذه تصل إطارَ إجابةٍ بحالة ``ok``.
"""

from __future__ import annotations

from typing import Final

#: عقدةٌ أو محوِّلٌ لم يجد نصّاً بشرياً يعيده (مظروفٌ بلا حقل، أو ناتجٌ فارغ).
NO_DETAILS_REPLY: Final = "لا توجد تفاصيل متاحة."

#: ``GeneralKnowledgeNode`` — استثناءٌ غير انقطاع المزوّد.
GENERAL_KNOWLEDGE_FAILED_REPLY: Final = "عذراً، لم أتمكن من استرجاع هذه المعلومة الآن."

#: ``ChatFallbackNode`` — النصّ الابتدائي حين لا يبثّ النموذج شيئاً.
CHAT_FALLBACK_REPLY: Final = (
    "وعليكم السلام! أنا هنا للمساعدة. أخبرني بما تحتاجه وسأتابع معك خطوة بخطوة."
)

#: ``SynthesizerNode`` — فشل مسار DSPy الاحتياطي.
SYNTHESIS_FAILED_REPLY: Final = (
    "عذراً، تعذر صياغة الشرح المطلوب بسبب خطأ داخلي. يرجى إعادة صياغة السؤال."
)

#: ``ValidatorNode`` — فشل إعادة المحاولة.
CONTEXT_FAILED_REPLY: Final = "عذراً، لم أتمكن من معالجة السياق."

#: ``SafetyNetService`` — شبكة الأمان في بوّابة المزوّد.
SERVER_PRESSURE_REPLY: Final = "عذراً، الخادم يواجه ضغطاً شديداً حالياً. يرجى المحاولة لاحقاً."

#: القائمة التي يستوردها المُحكِّم. نصٌّ جاهز جديد يُضاف هنا أو يبقى غير مرئيٍّ للقياس.
DEGRADED_REPLIES: Final[tuple[str, ...]] = (
    NO_DETAILS_REPLY,
    GENERAL_KNOWLEDGE_FAILED_REPLY,
    CHAT_FALLBACK_REPLY,
    SYNTHESIS_FAILED_REPLY,
    CONTEXT_FAILED_REPLY,
    SERVER_PRESSURE_REPLY,
)
