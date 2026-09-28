# INCIDENT: System Does Not Answer Questions

**Date:** 2026-09-27  
**STATUS:** Root Cause Found

## ROOT CAUSE

السبب الجذري ليس الواجهة ولا وصول السؤال ولا الـWebSocket. السبب هو **فقدان دلالة فشل مزوّد النموذج بين LangGraph وطبقة النقل**:

1. عقدتا `GeneralKnowledgeNode` و`SynthesizerNode` تضعان `provider_error=True` عندما تفشل سلسلة النماذج كلها.
2. محرك البث كان يتجاهل `provider_error`، يأخذ جملة انقطاع جاهزة من `final_response`، ثم يغلفها كـ`assistant_final` مع `status="ok"`.
3. مسار الـHTTP يعيد `200` لأن `StreamingResponse` بدأ بنجاح، رغم أن السؤال لم يحصل على جواب.
4. اختبارات E2E كانت تعدّ أي `assistant_error.content` أو أي نص غير فارغ جوابًا، كما كانت تشغّل المونوليث وحده مع `REQUIRE_ORCHESTRATOR=0`. لذلك بقيت خضراء من دون تشغيل الـorchestrator أو StateGraph أصلًا.

المحفّز التشغيلي المثبت في الكود والسجل الهندسي هو نفاد سلسلة نماذج OpenRouter/إزالة endpoints أو فشلها. أما الخلل المعماري الذي حوّل هذا الفشل إلى «نجاح بلا جواب» فهو إسقاط `provider_error` في طبقة البث.

تشغيل CI الحي `36365245206` عزل طبقة المزوّد أكثر: الكتالوج عرض 16 نموذج نصي مجاني؛ نجح استدعاء `nvidia/nemotron-3.5-lightning:free` و`nvidia/nemotron-3-ultra-550b-a55b:free` فعلياً بـHTTP 200 ومحتوى، بينما أعادت نماذج أخرى 429 أو `ResourceExhausted`. بعد ذلك أجابت الرحلة عن أول سؤالين وفشلت 12/14. هذا النمط، مع حد OpenRouter الرسمي للحساب المجاني (20 طلباً/دقيقة و50/يوم لمن اشترى أقل من 10 أرصدة)، يثبت أن المشكلة المتبقية سعة/حصة مجانية وليست غياب كل نموذج. أضيف لذلك فحص `GET /api/v1/key` يحجز حصة المصفوفة ويرفض تشغيلها مبكراً إن لم تكفِ، بدل حرق بقية الطلبات وإعادة 12 رسالة عطل.

## FIRST FAILURE POINT

`microservices/orchestrator_service/src/api/chat_stream_engine.py::_run_chat_langgraph`

أول انحراف دلالي كان بعد انتهاء `app_graph.astream(...)`: كانت تحديثات العقد تحمل `provider_error=True`، لكن المحرك لا يقرأها ويصدر بدلًا منها:

```text
assistant_final(status="ok", content=<provider outage notice>)
```

أي إن الـLLM لم يُنتج جوابًا، والرسم عرف ذلك، لكن Response Assembly حوّل الفشل إلى نجاح.

## BINARY ISOLATION EVIDENCE

| الاختبار | النتيجة | الدليل |
|---|---|---|
| A — هل السؤال يصل Backend؟ | نعم | `handle_turn` يقرأ `payload.question` ويحفظه بدور user قبل استدعاء orchestrator. |
| B — هل Backend يستدعي Agent؟ | نعم | `_stream_and_wait → orchestrator_client.chat_with_agent`. |
| C — هل Agent يصل إلى Graph/LLM؟ | نعم في المسار القانوني | سياسة التوجيه الافتراضية `state_graph → /api/chat/messages`، ثم `_run_chat_langgraph → app_graph.astream`; عقد الإجابة تستدعي `AIClient.stream_chat/generate`. |
| D — هل LLM يعيد محتوى؟ | لا عند نفاد السلسلة | العقد تضبط `provider_error=True` وتستخدم `PROVIDER_UNAVAILABLE_MESSAGE`. |
| E — هل المحتوى يعود إلى API؟ | يعود إشعار العطل، لا جواب السؤال | كان `final_response` يحمل رسالة الانقطاع. |
| F — هل API يرسله؟ | نعم لكن بنوع خاطئ | كان يصدر `assistant_final/status=ok`، والـHTTP يظل 200. |
| G — هل Frontend يستلمه؟ | نعم | `useAgentSocket` يعالج `assistant_final` و`assistant_error`. |
| H — هل Frontend يعرضه؟ | نعم | يعرض إشعار العطل/ينهي الفقاعة؛ إذًا المشكلة ليست اختفاء frame في React. |

## EVIDENCE

1. `AgentState` يصرح صراحة بالحقل `provider_error`.
2. `GeneralKnowledgeNode` و`SynthesizerNode` يعيدان `provider_error=True` عند `AllModelsFailedError`.
3. النسخة السابقة من `_run_chat_langgraph` لم تقرأ الحقل إطلاقًا وكانت دائمًا تصدر `assistant_final(status="ok")`.
4. `_stream_chat_langgraph` المباشر كان يفعل الشيء نفسه، ثم يرسل `complete` بعد `assistant_final/assistant_error`، أي إطارين نهائيين متناقضين.
5. `StreamNormalizationMixin` كان يسقط الحدث العام `error` إلى `noop`.
6. دورة المونوليث كانت تمرر `assistant_error` فورًا ثم تصدر خطأ نهائيًا ثانيًا أثناء `_close_turn`.
7. `live-e2e.yml` كان يضبط `REQUIRE_ORCHESTRATOR="0"` ولا يقلع خدمة orchestrator؛ لذلك اسم “Full Stack” لم يكن مطابقًا للمسار المقاس.
8. محللا E2E كانا يعتبران نص `assistant_error.content` محتوى ناجحًا.
9. مسار compatibility facade كان يكتب رسالة المستخدم والمساعد مرتين: مرة في المونوليث ومرة في `/api/chat/messages`، ما يلوث التاريخ ويضاعف السؤال في الأدوار التالية.

## FAILURE CHAIN

```text
User Question
↓
Frontend sends {question, conversation_id, client_request_id}
↓
Monolith WebSocket receives and persists the exact question
↓
OrchestratorClient POST /api/chat/messages
↓
Conversation + thread u<user>:c<conversation> resolved
↓
LangGraph supervisor routes to answer node
↓
LLM model chain exhausted / provider unavailable
↓
Node sets provider_error=True
↓
[FAILURE] stream engine discards provider_error
↓
Outage sentence wrapped as assistant_final(status=ok)
↓
HTTP 200 + non-empty body
↓
E2E misclassifies outage text as answer and stays green
↓
Frontend displays no actual answer to the question
```

## AFFECTED FILES

- `microservices/orchestrator_service/src/api/chat_stream_engine.py`
- `microservices/orchestrator_service/src/api/routes.py`
- `app/infrastructure/clients/orchestrator/stream_normalization.py`
- `app/api/routers/customer_chat_support/turn_lifecycle.py`
- `app/api/routers/customer_chat_support/frames.py`
- `scripts/e2e/universal_answerability_live.py`
- `scripts/e2e/live_student_journey.py`
- `.github/workflows/live-e2e.yml`
- `tests/regressions/test_answer_delivery_incident.py`

## AFFECTED FUNCTIONS

- `_run_chat_langgraph`
- `_stream_chat_langgraph`
- `chat_messages_endpoint`
- `StreamNormalizationMixin._normalize_stream_event`
- `_stream_and_wait._forward_event`
- `_emit_terminal_frames`
- `_absorb_frame` في مصفوفة E2E
- `_absorb_terminal` و`_turn_violations` في رحلة الطالب

## WHY THE CURRENT ARCHITECTURE CAUSED THE FAILURE

- الحالة التشغيلية (`provider_error`) والحالة المحتوائية (`final_response`) كانتا في نفس state بلا تحويل إلزامي إلى عقد نقل typed.
- HTTP status يخص إنشاء stream، لا نجاح الدور؛ لم توجد قاعدة تمنع `status=ok` عند `provider_error=True`.
- توجد سلطتا terminal frame: orchestrator يرسل terminal، ثم المونوليث يعيد إنشاء terminal آخر.
- توجد سلطتا persistence عند compatibility facade، فتتضاعف الرسائل ويتلوث history.
- بوابة E2E قاست fallback محليًا بدل العمود الفقري المعلن، ثم عرّفت «نص غير فارغ» بوصفه جوابًا.

## MINIMAL FIX

1. جعل `provider_error` sticky خلال stream updates.
2. إصدار `assistant_error` واحد بكود `LLM_PROVIDER_UNAVAILABLE` وحالة 503 بدل `assistant_final(status=ok)`.
3. تمرير حدث `error` وعدم إسقاطه إلى `noop`.
4. تخزين terminal upstream مؤقتًا وإصداره مرة واحدة من سلطة الإغلاق.
5. منع حفظ رسالة الانقطاع كرسالة assistant.
6. احترام `compatibility_facade` لمنع الكتابة المزدوجة.
7. تصفير `provider_error=False` صراحةً عند بداية كل turn في مساري HTTP وWS؛ فالـcheckpointer يحفظ سياق المحادثة، لا نتيجة تشغيلية يجب أن تسمّم الدور التالي.

## ARCHITECTURAL FIX

- اعتماد terminal outcome موحد: `success | provider_error | transport_error | persistence_error`، وتحويله إلى frame في موضع واحد فقط.
- اعتبار `assistant_final` وحده نجاحًا محتملًا، وبشرط وجود محتوى فعلي أو deltas فعلية وعدم وجود operational error.
- إبقاء المونوليث single writer عند compatibility facade؛ orchestrator ينفذ graph فقط.
- تشغيل CI على المسار الحقيقي: monolith → orchestrator → StateGraph → LLM → stream → monolith → WebSocket parser.
- رفض الخضرة إذا لم تكن `graph_ready=true` أو إذا ظهر أي `assistant_error/error`.

## REGRESSION RISKS

- عملاء قدامى كانوا ينتظرون `complete` بعد `assistant_final`; العقد الحالي يوجب terminal واحدًا، لذلك أزيل التكرار في مسار WS المباشر.
- عند فشل المزود بعد بث جزئي، سيرى المستخدم النص الجزئي ثم terminal error؛ هذا أدق من نجاح كاذب، ويجب أن تبقي الواجهة الفقاعة بحالة error.
- تغيير سلطة persistence قد يكشف اعتمادًا خفيًا على الصفوف المكررة؛ التاريخ الصحيح يجب أن يحوي user واحدًا وassistant واحدًا لكل دور.
- إذا لم يُصفّر علم العطل عند إدخال الدور، فقد يستعيد checkpoint قيمة `provider_error=True` القديمة؛ لذلك يوجد invariant واختبار بأن كل invocation يبدأ بـFalse ثم تصبح True فقط من update في التشغيل الجاري.
- بوابة E2E الحقيقية أبطأ وأكثر حساسية لتوافر الخدمات الخارجية، لكنها تفشل بسبب العطل الحقيقي بدل إعطاء خضرة وهمية.

## REGRESSION TESTS

- provider exhaustion عبر HTTP graph ⇒ `assistant_error` واحد، صفر `assistant_final`، ومدخل `provider_error=False` يمنع تسرّب عطل الدور السابق من checkpoint.
- transport normalization يحافظ على `error`.
- terminal assembly يرسل explicit upstream error مرة واحدة.
- E2E يعتبر `error/assistant_error` فشلًا حتى إن كان النص غير فارغ.
- Full-stack CI يقلع orchestrator ويتحقق من `graph_ready=true` ويفرض `REQUIRE_ORCHESTRATOR=1`.
- اختبارات الواجهة الحالية تتحقق من إنهاء streaming bubble عند error وعدم تعليق زر الإرسال.

## VERIFICATION

1. شغّل اختبارات regression الجديدة على Python 3.12.
2. شغّل كل `frontend/tests/*.test.mjs`.
3. شغّل workflow `CI` مع أسرار E2E الحقيقية.
4. تحقق في log من إقلاع `orchestrator-service` و`graph_ready=true`.
5. تحقق من مرور مصفوفة الأسئلة ورحلة الطالب دون `assistant_error/error`.
6. في اختبار فشل متعمد لمفتاح/مزود النموذج، تحقق من `assistant_error(code=LLM_PROVIDER_UNAVAILABLE)` واحد وصفر حفظ assistant.
7. افحص قاعدة البيانات: لكل دور صف user واحد وصف assistant واحد فقط.
8. افتح الواجهة وتحقق أن السؤال الحقيقي يعرض جوابًا، وأن فشل المزود يظهر خطأ صريحًا ولا يُسجل كجواب ناجح.

## CONFIDENCE

**High** في نقطة الفشل وفقدان الدلالة وسلسلة التسليم؛ الأدلة مباشرة من مسارات التنفيذ والعقود والـworkflow.  
**Medium** في توفر مزود OpenRouter لحظة التشغيل المحلي لأن شبكة sandbox أغلقت TLS قبل الوصول إليه؛ بوابة GitHub المعدلة هي برهان التشغيل الخارجي الملزم.
