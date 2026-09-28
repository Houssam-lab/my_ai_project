# 05 — Proof Model: فيزياء البرهان، رسم الدليل، معمارية الثقة، ومُصرِّف البرهان

**التاريخ:** 2026-09-28 · **الدور:** يعرّف متى يكون النظام قد **أثبت** نتيجةً، وما الذي يمنع تحويل الاستدلال إلى يقين.

---

## 1. طبقات البرهان — والتقابل مع ما في الكود

| الطبقة | المعنى | ما يوجد | الفجوة |
|---|---|---|---|
| Observation | شيءٌ سُجّل بمصدرٍ وساعة | `Step(output, state_before, state_after)` (C-02) · `occurred_at` مقابل `recorded_at` (D-01 §IX) | لا مُنتِج أعمال بعد (لا n8n adapter) |
| Execution | run بمُعرِّف ونسخة | `Trajectory(trajectory_id, metadata)` + `ReportPin` (C-07) | — |
| State Change | فرق قبل/بعد في نظامٍ مسجِّل | بُعد `state_transitions` (C-02) | أوراكل readback للقراءة فقط (يُبنى) |
| Causal Attribution | أنّ الفعل هذا سبّب الحالة تلك | بُعد `tool_use` + `intermediate_constraints` | يبقى **inferred** ما لم يُعزل السيناريو (D-01 §XI.4) |
| Outcome Confirmation | assertions على النتيجة المتعاقَدة | `verify()` على الأبعاد الخمسة كلّها لا «أوّل يفوز» | — |
| Evidence | صنف + إعادة إنتاج + مرجع + هاش | `Evidence` (C-03) + سلسلة هاش/ميركل/إيصال (C-06) | التوقيع الرقمي/الختم الخارجي مؤجَّل حتى يطلبه عميل مدفوع |
| Acceptance | توقيع سلطة القبول على الحزمة | `acceptance_authority` في العقد (04) | إجراء بشري؛ لا يُؤتمت |

## 2. أصناف البرهان — والمنع البنيوي لترقيتها

| الصنف | مثال | الحكم المسموح | المنتِج | ما يمنع الترقية |
|---|---|---|---|---|
| Deterministic | عدد السجلّات = 1؛ owner_id مطابق؛ replay لا يُنشئ ثانياً | `HOLDS/VIOLATED` | أوراكل readback | — |
| Probabilistic | الإشعار وصل خلال نافذة؛ عيّنة من N | `HOLDS/VIOLATED` **بوسم إحصائي** في الحزمة | أوراكل مؤقّت/عيّنة | لا يُكتب «مؤكَّد» |
| Inferred | «CRM قبل الكتابة لأنّ الاستجابة 200» | `INCONCLUSIVE` ما لم يُقرأ readback | سجلّ الـrunner | `Constraint.evaluate` يُحوّل الاستثناء إلى `INCONCLUSIVE` لا `HOLDS` (C-02) |
| Human-confirmed | «التصنيف الغامض مقبول» | `HOLDS/VIOLATED` بتوقيع مسمّى + رُبريك + دليلٍ رآه | مراجع | لا حكم بلا اسم |
| Insufficient | لا وصول · لا ground truth · نسخة مجهولة | `INCONCLUSIVE` | — | **لا يُرقّى أبداً** — وهو ما يفرضه `verdict.py` بالنصّ |

**القاعدة الوحيدة التي لا تُفاوَض:** `INCONCLUSIVE > false confidence`. وهي ليست شعاراً هنا؛ هي `elif inconclusive: outcome = INCONCLUSIVE` في [`verdict.py`](../../naas_verifier/core/verdict.py).

## 3. Evidence Graph — من سجلٍّ إلى طبقة provenance

```text
Outcome (contract_id/version)
├── Scenario (id, fixture_hash, expected_assertions, severity)
├── Execution (run_id, correlation_id, versions{workflow,model,prompt,config})
├── Event (source_event_id, occurred_at, recorded_at, producer)
├── State (before_hash, after_hash, source_system, read_method=readonly)
├── External Observation (readback payload_ref, redacted_summary)
├── Verification (constraint_id, dimension, outcome, verifier_version)
└── Acceptance Decision (verdict, reviewer, authority signature, issued_at, expires_at)
```

**هل يصير طبقة provenance؟** — يصير حين تقبله **ثلاثة مستهلكين مستقلّين** بالصيغة نفسها: الدافع (يُعيد التشغيل)، المكتتب (يطلب «سجلاً قابلاً لإعادة التشغيل» — X-10)، والمدقّق (يطلب «معايير موضوعية قابلة للقياس» — X-03). اليوم مستهلكٌ واحد محتمل (الدافع). فالرسم **أداةٌ** حتى إشعارٍ آخر، و«طبقة» فرضيةٌ (H-05).

## 4. Proof Compiler مقابل Outcome Compiler — أيّهما القلب؟

| | Outcome Compiler (04) | Proof Compiler | كلاهما كمنظومة |
|---|---|---|---|
| السلسلة | لغة → غموض → توضيح → نتيجة صورية → شروط → خطّة → مخطّط | بيانات تنفيذ خام → إعادة بناء الحالة → استدلال سببي → تقييم النتيجة → رسم دليل → أثر قبول | عقد ← ← ← حزمة |
| ما يوجد في الكود | النمط (C-10 · C-11) + النوع (C-02) | **القلب كاملاً**: `Trajectory → verify → Verdict` + إيصال + صلاحية (C-02 · C-03 · C-06 · C-07) | الالتحام غير موجود ككود (لا `attest`) |
| ما يُنتج المال | لا شيء وحده (عقدٌ بلا حكم) | لا شيء وحده (حكمٌ بلا عقد يقيس ما لا يعنيه أحد) | **الحزمة** |
| الخطر | أتمتة الجهل | «مُصحِّح لا مُتحقِّق» إن فُحص المخرَج النهائي وحده — وهو ما يمنعه `ConstraintSet` | — |
| الحكم | عملٌ بشري أوّلاً | **القلب التقني الآن** | **وحدة البيع** |

## 5. Trust Architecture — من أين تأتي الثقة (ليس من AI ولا من علامة ولا من لوحة)

```text
Trust =
  Transparency            : الحكم يُطبع مع القيود التي قِيست والتي تُركت وسببها (C-02)
+ Evidence                : كل ادّعاء بأمر إعادة إنتاج ومرجع (C-03)
+ Reproducibility         : الدافع يُعيد حساب الهاشات ويُعيد التشغيل بنفسه (C-06 · I-04)
+ Bounded Authority       : قراءة فقط · لا mutation · لا شبكة افتراضاً · لا LLM في مسار الحكم (C-12 · D-187)
+ Independent Verification: المُشهِد ≠ الباني ≠ الدافع؛ من دفع لنا مُعلَنٌ في الحزمة
+ Historical Reliability  : نسبة `INCONCLUSIVE` المنشورة عبر الحزم + سجلّ تراجعاتٍ علني (D-293 سابقة)
```

**اختبار الصيغة على السوق المكتشف:** المكتتب (X-10) يشتري البندين 2–3 ولا يثق بالبند 1؛ الدافع يشتري 3 و5؛ الباني يشتري 5 و6 (لأنّ سمعة المُشهِد تُنقل إليه). ما لا يشتريه أحدٌ حتى الآن: «AI-powered» — ولذلك لا يُذكر.

**تعارض المصالح المُعلَن:** يدفع الباني ويستفيد الدافع. الحلّ ليس إنكاره بل (أ) الإعلان عنه في الحزمة، (ب) جعل الحزمة قابلة لإعادة التشغيل عند الدافع بلا ثقةٍ فينا، (ج) نشر معدّل `HOLD/UNVERIFIED` — مُشهِدٌ لا يُصدر إلا `ACCEPT` يفقد قيمته (نمط المدقّق ووكالة التصنيف؛ Vals: «المختبرات تدفع لتُقيَّم» — X-13).

## 6. ما ليس برهاناً (يُكتب ليمنع الاستدلال الخاطئ)

- شاشة خضراء في n8n؛ `200 OK`؛ «لم يشتكِ أحد» (X-01: الصمت ليس رضا).
- تقرير LLM عن نفسه أو عن الوكيل (D-067 وX-12 يفضّلان العلامات الحتمية).
- حزمةٌ من نسخةٍ سابقة بعد تغيّر النموذج/الـprompt/الـworkflow (AHW: الحكم ينتهي).
- ملخّصٌ مكتوب بعد الواقعة (X-10 حرفياً).
