# 06 — Economic Engine: طوبولوجيا المال، فيزياء القيمة، الإسفين، والمعاملة الأولى

**التاريخ:** 2026-09-28 · **القاعدة:** كل رقمٍ هنا إمّا سطرٌ في [01](01-evidence.md) أو موسوم `PRICING HYPOTHESIS`. لا رقم ثالث.

---

## 1. Money Topology — من أين يأتي المال إلى المنتج؟

```text
Who suffers                 : الباني (كاشه محجوز) + العميل (لا يعرف إن حصل على ما دفع له)
  ↓
Who controls budget         : مالك الوكالة/البائع الصغير — «الميزانية» هي المبلغ المحجوز نفسه
  ↓
Who approves purchase       : الشخص نفسه (تحت ≈$5K لا لجنة — D-05 · S83 في MF: عتبة $10K)
  ↓
Who receives outcome        : الطرفان — الباني يُقبض، والعميل يقبل بثقةٍ لا تعتمد على الباني
  ↓
Who bears risk              : الباني (عدم الدفع) · العميل (دفعٌ مقابل لا-نتيجة) · لاحقاً المؤمِّن
  ↓
Who pays for workaround now : الباني بساعاتٍ غير مفوترة (لقطات · فيديوهات · مكالمات) · العميل بـUAT يدوي
  ↓
Who could reallocate budget : الباني من هامش المرحلة؛ لاحقاً بائع OBP من كلفة النزاع؛ لاحقاً المؤمِّن كشرط تغطية
```

**Budget Transfer Point:** هامش الباني على المرحلة، **يُفرج عنه عند القبول**. الرسم يُدفع من مالٍ سيصل الباني بسبب الحزمة — لا من بند «assurance» جديد. إن قال الباني «هذا يجب أن يكون داخل build مجاناً» فهو خارج الـICP لا اعتراضاً يُقنَع (D-01 §IV.3 — يبقى صحيحاً).

## 2. Value Physics — نموذجٌ للسوق المكتشف، لا معادلةٌ مفترَضة

للباني (المشتري الأوّل):

```text
V_builder = blocked_amount × [P(release | packet) − P(release | no packet)]
          + days_saved × blocked_amount × r_daily
          + proof_hours_avoided × loaded_rate
          + dispute_hours_avoided × owner_rate
          + [renewal/referral effect]                      ← تخميني حتى يُصرَّح
```

للدافع (المستفيد الثاني):

```text
V_client  = P(wrong acceptance) × downstream_cleanup_cost
          + UAT_hours_avoided × staff_rate
          + [confidence in outcome-billed invoice]         ← يظهر مع OBP
```

| المكوّن | قابل للإثبات في أوّل pilot؟ | كيف |
|---|---|---|
| فارق أيام الإفراج | نعم | تاريخ التسليم → تاريخ التسوية، مقارنةً بآخر مرحلةٍ للباني نفسه (control داخلي) |
| ساعات الإثبات الموفَّرة | نعم | يصرّح بها الباني قبل الحزمة |
| ساعات النزاع | نعم إن وُجد نزاع | — |
| أثر التجديد/الإحالة | لا | لا يُنسب سببياً بلا تصريحٍ ودليل (D-01 §XVIII) |
| كلفة القبول الخاطئ | جزئياً | فقط إن كشفت الحزمة `HOLD` حقيقياً |

**ما يدفع العميل مقابله مباشرة:** الإفراج عن المال (المكوّن الأوّل). الباقي حجّة لا فاتورة.

## 3. Economic Wedge — أصغر نقطةٍ يجتمع فيها الألم والمشتري والإثبات والدفع

```text
Narrow Buyer   : بانٍ أتمتة (وكالة/بائع 1–20 شخصاً) خارج الجزائر، يفوتر بالـEUR/USD
+ Narrow Workflow: trigger → قرار AI → تغيير حالة في نظامٍ مسجِّل (lead → CRM أوّلاً)
+ Narrow Outcome : «لهذا الحدث وقعت النتيجة المتعاقَدة مرّةً واحدة ولم يقع محظور»
+ High Pain      : دفعةٌ محجوزة/منازَعة الآن (H-01)
+ Fast Proof     : الدافع يُعيد تشغيل الحزمة خلال دقائق (C-06)
+ Fast Payment   : الرسم أقلّ من 10% من المحجوز؛ 50/50؛ Net ≤ 45 يوماً (D-02)
```

**المحفّزات الثلاثة (بترتيب قرب المال):**

| # | المحفّز | لماذا أوّلاً/ثانياً | الدليل |
|---|---|---|---|
| 1 | **قبول مرحلة** مشروطٌ بالنتيجة (الدفعة الأخيرة) | يخصّ **كل** تسليم لا الفاشل منه؛ المبلغ مادي (نمط 30–50% — D-01 §XIV)؛ يتكرّر مع كل مرحلة | X-04 · X-05 · D-06 |
| 2 | **فترة فوترة** بالنتيجة (عدد الحلول/الاجتماعات/الـleads) | متكرّر شهرياً بنيوياً؛ النزاع مُوثَّق لدى الكبار | X-01 · X-02 · X-06 · X-07 |
| 3 | **حادثة** متنازَع عليها (قرار 09-28) | إلحاحٌ أعلى لكن عرضيٌّ؛ ينافس الإصلاح السلعي | D-01 |

**WEDGE → EXPANSION:** لا يُفترض المسار؛ يُقرأ من سلوك المشتري الأوّل: هل يطلب حزمةً للمرحلة التالية (توسّع رأسي)؟ أم للـworkflow الثاني (أفقي)؟ أم يطلبها **عميله** مباشرةً (تبديل الدافع)؟ أم يرسلها لمكتتب (مستهلك ثانٍ — H-05)؟ كلٌّ منها بوّابةٌ في [11](11-kill-conditions.md).

## 4. First Transaction Engineering — تجربةٌ لا صفقة

| العنصر | التعريف |
|---|---|
| **Subject** | بانٍ واحد مؤهَّل (≥5 إشارات من قائمة D-01 §XIII.3 + إشارة جديدة: **مبلغٌ محجوز مسمّى**) |
| **Treatment** | حزمة شهادة نتيجةٍ لمرحلةٍ/فترةٍ واحدة (≤8 assertions حرجة، ≤3 أوراكل) |
| **Control** | آخر مرحلةٍ قَبِلها العميل نفسه بلا حزمة (تاريخ التسليم → التسوية) |
| **Outcome** | أيام الإفراج؛ ساعات الإثبات؛ هل أُعيد تشغيل الحزمة عند الدافع؟ هل وُقّع القبول؟ |
| **Evidence** | تاريخا التسليم والتسوية (من الباني)؛ توقيع القبول؛ سجلّ إعادة التشغيل (اختياري من الدافع) |
| **Payment** | رسمٌ ثابت مسوّى بالـEUR/USD في قناةٍ مهنية مُتحقَّق منها (FIV) |
| **Retest** | عند `HOLD`: retest واحد بعد إصلاح الباني ضمن الرسم؛ الثاني يُفوتر |
| **Repeat** | خلال 60 يوماً: مرحلة/فترة/إصدار تالٍ |

## 5. سلّم الأسعار — فرضياتٌ تُختبر لا أسعار

| العرض | النطاق | `PRICING HYPOTHESIS` | لماذا هذا الرقم | ما يُبطله |
|---|---|---|---|---|
| **Fit check** | قراءة export + المرحلة المتنازَعة؛ رأي «قابل للشهادة؟» | مجّاني (F في SSI) | مدخلٌ مجاني نادر في العيّنة (D-05: F=0.32) | — |
| **Attestation — simple** | workflow واحد · ≤5 assertions · أوراكل count/field/idempotency · بلا حكم بشري | `€300–€450` | ضمن طبقة الدخول ≤$5K وتحت 10% من مرحلة ≥`€3K` | 3 بناة متتالين يختارون «لقطات شاشة» بسعرٍ بديل أدنى |
| **Attestation — full** | ≤8 assertions · async/timing · حكم بشري واحد · retest | `€750–€1,200` | نسبةٌ إلى مرحلة `€7.5K–€12K`؛ مقارنةً بمرحلة اختبار `€3K–€5K` (§3.5 في 01) | التسليم >12 ساعة مباشرة |
| **Period attestation** (OBP) | عدّ الحلول/الـleads لفترة فوترة | `€400–€900/فترة` | يُقاس بنسبةٍ من الفاتورة المفوترة بالنتيجة | لا بائع صغير يفوتر بالنتيجة في العيّنة (H-06) |
| Outcome-share | نسبة من المحجوز | **مرفوض** أوّلاً | نزاع إسناد + تعارض مصالح | — |
| Risk premium | زيادة للمال/PII/الأفعال غير القابلة للعكس | **مؤجَّل** حتى وجود تأمينٍ لنا | مسؤولية | — |

**قاعدة الاختبار:** لا يُغيَّر السعر لنفس النطاق بعد رؤية الميزانية. يُسجَّل لكل عرض: النطاق · السعر · الردّ · رمز الاعتراض · عربون نعم/لا · ساعات التسليم · المساهمة الإجمالية. إعادة التسعير بعد 5 عروض مؤهَّلة للطبقة أو 3 مدفوعة.

## 6. Economic Flywheel — وفصل التراكم عن الميزة

```text
blocked payment → contract → attestation → payment released
   → clause + oracle + failure signature enter the library (with usage rights)
   → next attestation faster/cheaper
   → published INCONCLUSIVE/HOLD rates build attestor credibility
   → client asks for attestation on next vendor (buyer-side pull)
   → record consumed by a second party (insurer/auditor)  ← H-05
```

| Data Accumulation (يحدث تلقائياً) | Data Advantage (يحدث بشروط) |
|---|---|
| بنود عقودٍ حقيقية | فقط إن كانت **مُنمَّطة** ومقارنة عبر العملاء |
| توقيعات فشل (duplicate · partial · silent) | فقط إن ثبت أنّها **تقلّص وقت الحزمة التالية** قياساً |
| أوراكل لكل نظامٍ مسجِّل | فقط بحقوق استعمالٍ صريحة وبلا PII |
| سجلّ أحكامٍ منشور | فقط إن كان **غير قابلٍ للفساد** ظاهراً (نسبة `HOLD` غير صفرية) |

**لا يُفترض أنّ كثرة البيانات = خندق.** الخندق الوحيد المتاح في أوّل سنة هو **سمعة الحكم** — وهي قابلة للتقليد بمن يملك الانضباط نفسه، ولذلك تُنشر مقاييسها لا تُدَّعى.

## 7. الحلقة إلى العملة الصعبة (لا تتحقّق حتى تكتمل)

```text
foreign builder with a blocked/contested outcome-dependent payment
→ free fit check on sanitized export + the contested clause
→ one-page scope + contract.yaml draft + fixed price
→ 50% deposit settled on a verified professional rail (FIV: CH1..CH5 assessed; none tested live)
→ read-only evidence pull (staging/readback) under written authorization
→ attestation packet: ledger + verdict + manifest + re-verify instructions
→ client re-runs verify, signs acceptance → builder's invoice releases
→ 50% balance, Net ≤ 45 days (D-02 safe window; regulatory deadline conflict OPEN — D-07)
→ settlement evidence recorded privately; only then GATE_C moves off ABSENT
```

**ما يقتل الصفقة قبل بدئها (كما في D-01 §XVI — لم يتغيّر):** كيانٌ مخوَّل للفوترة · قناة قبضٍ مُتحقَّق منها · شروط بيانات/NDA عند الحاجة · تفويض وصولٍ مكتوب · لا mutation إنتاجي.

## 8. الرهانات كمحفظة (لا تشتّتاً تنفيذياً)

| الرهان | المحتوى | شرط التفعيل | الحالة |
|---|---|---|---|
| **Core** | Outcome Attestation عند الدفعة المشروطة (المحفّز 1) | الآن — بيعٌ قبل بناء | `UNVALIDATED` |
| **Adjacent** | Verified Recovery عند حادثة (المحفّز 3) · Period attestation (المحفّز 2) | أوّل عميل core يطلبه؛ أو إشارة OBP صغيرة | `UNVALIDATED` |
| **Asymmetric** | السجلّ المُشهَد كدليلٍ للمكتتب/المدقّق (X-10 · X-12 · X-03) | 10 حزمٍ حقيقية + طلبٌ من مستهلكٍ ثانٍ | `HYPOTHESIS` (H-05) |
| **Escape** | `naas_verifier` كمعيار/بيئة AR-FR (الخطّ 1 القائم) + التعليم كخطٍّ جزائري مستقلّ (D-210) | فشل Core بشروط [11](11-kill-conditions.md) | قائمان اليوم |

**قاعدة عدم التشتّت:** لا يُنفَق على Adjacent أو Asymmetric ساعةٌ واحدة قبل عربون Core الأوّل، باستثناء كتابة الحزمة بصيغةٍ لا تُغلق الباب عليهما (حقول `producer_type` و`kind` مغلقة — C-03).
