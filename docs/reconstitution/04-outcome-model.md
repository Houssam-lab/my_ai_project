# 04 — Outcome Model: مُصرِّف النتيجة، رسم النتيجة، الطبقة التعاقدية، وميزانية عدم اليقين

**التاريخ:** 2026-09-28 · **الدور:** يعرّف «ما الذي يعنيه أنّ نتيجةً وقعت» قبل أن يعرّف [05-proof-model.md](05-proof-model.md) «كيف نثبت ذلك».

---

## 1. Outcome Compiler — هل يصلح أن يكون القلب؟

السلسلة المقترحة في المهمّة:

```text
Natural Language
  → Ambiguity Detection
  → Clarification (probe واحد في كل مرّة)
  → Formal Outcome (محمولات مُنمَّطة)
  → Executable Conditions (أوراكل لكل محمول)
  → Verification Plan (أيّ بُعد يُغطّى بأيّ دليل)
  → Evidence Schema (ما يجب أن يوجد في الحزمة)
```

### ما يوجد منه في الكود (بحسب [01](01-evidence.md))

| الخطوة | موجود؟ | الموقع | الحكم |
|---|---|---|---|
| Ambiguity Detection + Clarification | **النمط** موجود: تشخيص حتميّ-أولاً ثمّ probe واحد، ومدير حوارٍ يقرّر أقلّ تدخّل | C-10 · C-11 | الآلية قابلة للنقل؛ المعرفة مُثبَّتة على تمرين واحد — **لا تُعاد صياغة الكود الآن** |
| Formal Outcome | **النوع** موجود: `Constraint(dimension, predicate → Outcome)` + `ConstraintSet` يرفض التغطية الناقصة | C-02 | قابل للاستعمال حرفياً كمخطّط عقد |
| Executable Conditions | جزئياً: محمولات تُكتب يدوياً بـPython؛ لا مكتبة أوراكل أعمال (count · field · idempotency · timing) | C-02 · C-12 | **يُبنى** (صغير) |
| Verification Plan | موجود بالبنية: خمسة أبعاد، والمتروك يُصرَّح بسببه | C-02 | مباشر |
| Evidence Schema | موجود: صنف مغلق + إعادة إنتاج + مرجع | C-03 · C-06 | مباشر |

**الحكم:** المُصرِّف **ليس** القلب التقني اليوم؛ هو **عملٌ بشري أوّلاً** (المقابلة تُخرج `contract.yaml`) لأنّ (أ) لا نعرف مفردات البنود الحقيقية قبل 5 عقود، و(ب) أتمتة الجهل تُنتج بنوداً جميلةً وخاطئة (D-01 §X.2). القلب التقني الآن هو [مُصرِّف البرهان](05-proof-model.md).

## 2. Outcome Graph — تمثيلٌ واحد للنيّة والنتيجة

```text
Intent      : «lead المؤهَّل يصل صاحبه الصحيح مرّةً واحدة ولا يُراسَل بلا موافقة»
  ↓
Condition   : preconditions (staging · credentials · clean state)
  ↓
Action      : allowed / forbidden actions (create test contact ✓ · email حقيقي ✗)
  ↓
State       : system-of-record قبل/بعد (CRM count · owner · fields)
  ↓
Event       : execution_id · source_event_id · timestamps (source vs recorded)
  ↓
Effect      : expected side-effects / forbidden side-effects
  ↓
Outcome     : assertions → HOLDS | VIOLATED | INCONCLUSIVE
  ↓
Evidence    : kind · reproduction · source_reference · hash
```

**هل هو primitive معماري أم تمايز منتج؟** — الرسم **primitive**: أيّ منافس يستطيع رسمه. التمايز ليس الرسم بل **ثلاثة التزامات على الرسم**: (1) الحكم ثلاثي ولا يُرقّى `INCONCLUSIVE`؛ (2) البُعد المتروك يُصرَّح ويُحسب ضدّ المُختبَر لا له؛ (3) الحكم يحمل صلاحيةً (نموذج · حزمة · نسخة · تاريخ) وينتهي. الثلاثة موجودة في C-02 وC-07 ومفروضة بالنوع.

## 3. الطبقة التعاقدية — Outcome Contract كواجهةٍ بين الدافع والنظام

الأسئلة الخمسة التي يجب أن يجيبها العقد (وليس القانوني):

| السؤال | الحقل في `contract.yaml` | من يجيب | مثال lead |
|---|---|---|---|
| ماذا يجب أن يحدث؟ | `expected_effects[]` | مالك النتيجة (الدافع) | سجلّ CRM واحد بصاحبٍ صحيح + إشعار واحد |
| ماذا يجب ألّا يحدث؟ | `forbidden_effects[]` | مالك النتيجة + الباني | لا تكرار · لا outreach بلا موافقة · لا حذف |
| ما الدليل الكافي؟ | `evidence_requirements[]` + `oracle` لكل assertion | المُشهِد | readback من CRM API + execution_id + hash |
| متى يُعدّ التسليم مقبولاً؟ | `acceptance_rule` (انظر §5) | الدافع | صفر انتهاك حرج و`INCONCLUSIVE ≤ budget` |
| ماذا بعد الفشل؟ | `on_hold` (retest واحد · نافذة · من يدفع) | الطرفان | retest واحد ضمن الرسم؛ الثاني يُفوتر |

**الفارق عن مواصفة اختبار:** المواصفة تصف ما يفحصه المهندس؛ العقد يصف **ما يُفرج المال**. ولذلك يحمل `acceptance_authority` (من يوقّع) و`expiry` (تغيّر النموذج/الـprompt/الـworkflow/API يُبطل الحكم — AHW).

**تحذير مصداقية (L10):** العقد **ملحقٌ تقني** لنطاق خدمة؛ ليس عقداً قانونياً ولا نصيحةً قانونية. صياغة شروط الدفع تخصّ الطرفين ومستشاريهما.

## 4. المُحوَّل من التعليم إلى العقد (النمط لا النصّ)

| في التعليم | في العقد | ما لا ينتقل |
|---|---|---|
| «الطالب يبدو فاهماً» ≠ «الطالب يتقن بلا دعم بعد تأخير» | «الـrun أخضر» ≠ «الحالة downstream صحيحة بعد إعادة التشغيل» | معادلات BKT/FSRS |
| probe واحد قبل التدخّل | سؤال توضيحٍ واحد قبل كتابة assertion | قاموس المفاهيم الرياضي |
| `dead_ends` تمنع تكرار التدخّل | `supersedes_run_id` يمنع مسح الـrun السابق | حقول `learning_stage` |
| `MIN_OBS` ⇒ `None` لا صفر | `INCONCLUSIVE` ⇒ `UNVERIFIED` لا `PASS` | — (النمط نفسه حرفياً) |
| التعريف قبل المثال (D-185) | البند قبل السيناريو | سجلّ الرموز الرياضية |

## 5. Uncertainty Budget — عدم اليقين جزءٌ من المنتج

كل assertion تحمل واحدةً من: `Known` (أوراكل حتمي متاح) · `Probable` (أوراكل إحصائي: نافذة زمنية · عيّنة) · `Ambiguous` (يحتاج حكماً بشرياً مسمّى) · `Unknown` (لا أوراكل) · `Conflicting` (مصدران يختلفان) · `Unverifiable` (وصولٌ مرفوض).

التحويل إلى حكم:

```text
Known/Probable  → HOLDS | VIOLATED   (بحسب الأوراكل)
Ambiguous       → HOLDS | VIOLATED   فقط بتوقيع مراجعٍ مسمّى برُبريك؛ وإلا INCONCLUSIVE
Unknown/Unverifiable/Conflicting → INCONCLUSIVE  (لا استثناء)
```

**ميزانية العقد:** `max_inconclusive_share_critical` يحدّدها **الدافع** لا المُشهِد (مثلاً 0.05 أو 0.0). القاعدة:

```text
ACCEPT      iff violated_critical == 0  AND  inconclusive_share_critical ≤ budget
HOLD        iff violated_critical  > 0
UNVERIFIED  iff violated_critical == 0  AND  inconclusive_share_critical > budget
```

**لماذا هذا منتجٌ لا تفصيلاً:** الميزانية تسعّر الوصول. كلّما منح الدافع وصولاً أوسع (readback · staging) انخفض `INCONCLUSIVE` وارتفع احتمال `ACCEPT` بلا تغييرٍ في الـworkflow. فالحزمة تقول للطرفين **ما الذي يجب شراؤه/إتاحته** لإغلاق القبول — وهي القيمة التي سمّتها D-01 (NK-4) ولم تربطها بالسعر.

## 6. أربعة أشياء لا يفعلها هذا النموذج (حدّ المصداقية)

1. لا يضمن uptime أو سلوكاً مستقبلياً؛ الحكم على input/version/window بعينها.
2. لا يصدر رأياً قانونياً أو امتثالياً؛ الخرائط إلى معايير عملٌ لاحق على الدليل نفسه.
3. لا يجعل الدردشة oracle؛ لا يصدر `ACCEPT` نصٌّ حرّ.
4. لا يُحوَّل `Probable` إلى `Known` بتسمية؛ الأوراكل الإحصائي يبقى إحصائياً في الحزمة.
