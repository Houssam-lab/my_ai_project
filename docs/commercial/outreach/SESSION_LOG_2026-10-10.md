# سجلّ جلسة 9–10 أكتوبر 2026 — من أرشفة Turing إلى أول دولار: OpenTrain حيّ

> **التاريخ:** 2026-10-09 15:07 → 2026-10-10 00:38 (توقيت الجزائر) · **الطبيعة:** توثيقٌ كامل بأدلّته لما جرى في جلسة المالك والوكيل.
>
> ⛔ **الحالة:** `GATE_C = ABSENT` ما تزال — لا عقد ولا دفعة. الجديد هذه الليلة: **أول ردٍّ بشري حقيقي** في السجل التجاري (Anton K، 09-26)، و**حساب OpenTrain حيٌّ مكتمل البناء**.
>
> 📌 **ما حُذف عمداً (المستودع عامّ):** الهاتف، البريد، المدينة/الولاية، ملفّ السيرة الذاتية، وروابط الحسابات. سيرةُ المالك رُفعت إلى المنصة فقط ولم تُلتزم هنا لأنها بيانات شخصية.

---

## 0) خلفية الجلسة

- 2026-10-09 15:07: لوحة Turing تُظهر طلب «AI - Analyst | Photographer - Arabic» في **Archived (1)** و«Submitted (0)」 بلا سبب معروض (الواقعة مسجّلة في PR #2607 بصفّ `CLOSED_DECLINED`). المالك أعلن حالةً نفسيةً خطِرة؛ الجلسة تحوّلت بطلبه الصريح إلى هدف «دولار واحد».
- قواعد الجلسة الموروثة من المستودع: لا وعدَ بدخل؛ UNKNOWN أفضل من يقينٍ زائف؛ أيُّ رسوم «تسجيل/تفعيل» = احتيال.

## 1) الشطر الأول: قراءة المستودع (أسئلة المالك)

- **الـPR القائم على الفرع** هو D-317 (تخطّي إعادة ضبط المخطط حين لا تتغير قاعدة الاختبار): الفرق الحقيقي مقابل `origin/main` = 4 ملفات (+310/−3)، لا عرضُ الـ3478 ملفاً الذي يصنعه الاستنساخ الضحل. اختبارات الحارس 13/13 خضراء محلياً؛ وبتعطيل شرط التخطي (طفرة) سقطت 3 اختبارات بالضبط — الاختبارات غير صورية.
- **Turing في المستودع:** 9 أسطر/6 ملفات بمعنيين (آلان تورينغ 1936 في `app/core/foundations/computability.py` ومرآتها المصغّرة؛ وturing.com منصّةً في دراسات العملة الصعبة). صفر ذكر في فرق D-317.
- **تصنيف المستودع نفسه للمنصة:** دليلٌ ضعيف/وساطة مزدوجة (`studies/algeria-hard-currency/evidence_round06.csv:15`) — الأرشفة وافقت حكمَ المستودع لا العكس.

## 2) خيط Anton K — أول ردٍّ حقيقي

- **2026-09-23:** المالك يرسل بريداً (لقطة Gmail) يعرض «شبكة جزائرية متعددة التخصصات من الخبراء والباحثين» مع مرفق، إلى Anton K.
- **2026-09-26:** ردّ Anton K حرفياً: «Hi Houssam, We will need someone with environmental education and experience. The Delegated Regulation explicitly requires it.»
- **ثلاث قراءات:** (أ) التأهيل ملحقٌ بالتحقق المعتمد؛ (ب) فريقه يفتقر إليه ويريد حمله؛ (ج) مغطّى داخلياً. المستودع كان اكتشف الجدار نفسه مستقلاً: رواق EU_CBAM سُحب من مسار العميل في 09-28 للسبب ذاته (الدوسييه §11 / OPP-11) وبالنص: «دورنا تجهيز البيانات لا إصدار تحقق».
- **قرار المالك في الجلسة:** «يمكنني البحث عن مختصين وبناء فريق» — خطة بناءٍ بصفر كلفة قبل إشارة العميل: ثلاث **محادثات** لا عقود (مهندس HSE/بيئة أو عمليات بخبرة صناعية؛ محاسب/مدقق سجلات صناعية؛ شخص رقمنة) — لا توظيف قبل جواب Anton (قواعد القتل من الدوسييه §12).

### 2.1 مسودة الرد النهائية على Anton K — **غير مُرسَلة بعد** (يُرسلها المالك)

```text
Hi Anton,

Thank you for the candid reply — and apologies for the slow one. In a
regulated field, a fast wrong answer costs more than a slow right one,
and I wanted mine to be right.

You are correct, and I will not argue with the Delegated Regulation:
the environmental education and experience it demands is a gate I
respect. The assessment, the verification, the professional sign-off —
that work stays with your qualified people. Full stop. I am not
proposing to touch it.

What I am proposing is the layer beneath it, described precisely,
including what it is not.

The side of your suppliers' files I know from the inside is the
Algerian one. If your Algerian files resemble what I see on the ground,
the bottleneck is not the calculation; it is the raw material beneath
it — installation-level electricity and fuel records, production and
precursor figures, held in Arabic, on paper, or in informal records.
From Europe that is a black box, and a closed black box is what pushes
declarations toward default values nobody defends by choice.

My proposed role is narrow and deliberately unglamorous: retrieve those
records at source, organize them, and document their provenance —
source document, date, language, retrieval method, confidence flag —
mapped to the fields your reviewers will actually need. I would not
represent the content of those records as verified or independently
checked. A sourced record is not a certified number; I know the
difference, and I would rather lose a sale than blur it.

Two caveats, because you deserve the candour you gave me. This is a
capability I am formalizing now, not a machine I already run: I am
selecting the environmental and field specialists it requires, and
installation access will be case by case. And a sample can demonstrate
our documentation standard, not our field access.

Two questions, each answerable in one line:

1. Is your gap upstream — primary data out of non-EU suppliers —
   downstream — qualified reviewers — or both?
2. If upstream is live, would a one-page illustrative dossier be a
   useful test: public data, stated assumptions, provenance structure,
   and an explicit list of what it cannot prove?

And if the honest answer is "we cover this internally," a one-line
pointer to where a multidisciplinary Algerian network could genuinely
serve you would still be a gift I'd act on.

Best regards,
Houssam
```

**مبادئ النسخة:** موافقةٌ على شرطه بلا تفسيرٍ قانوني منّا؛ تقسيمُ عملٍ لا ادّعاءَ قانون؛ الحدودُ مُعلَنة قبل أن تُكتشف («أُبَبننُ القدرة الآن»)؛ عينةٌ من صفحة واحدة ببيانات عمومية وبند «ما لا تثبته»؛ سؤالان تشخيصيان بسطر؛ ومخرجٌ يتيح له اقتراح تعاونٍ آخر.

## 3) فلتر «الدولار الواحد»: السكة التي تعمل، لا الأجر الأعلى

من تدقيق السكك في تقرير 2026-10-04 §2: **Mercor** يدفع للجزائر عبر Stripe Connect (موثّق من المالك 08-23، أسبوعي) · **OpenTrain** يدفع Stripe وصفحة دوله تذكر الجزائر · Upwork→Payoneer يعمل · PayPal ❌ استقبال · Wise ⚠️ · الكريبتو ⛔ لا خطة رسمية. القرار: OpenTrain أولاً لأن نصف بابه مفتوح منذ 07-10.

## 4) استكمال بناء OpenTrain — 23:55 → 00:38

| الخطوة | ما اعتُمد |
|---|---|
| الدور | I'm a Freelance AI Trainer |
| 1/6 السيرة | سيرة المالك نفسه PDF (لم تُلتزم هنا)؛ المنصة تستخرج الملف |
| 3/6 البلد | Algeria (المدينة والهاتف أُدخلا في المنصة وحدها) |
| 3/6 السعر | **15 $/س** بدءاً متعمَّداً: أول دولار قبل السمعة، ويُرفع لاحقاً |
| 3/6 التوفر | 20+ hours/week |
| 3/6 الظهور | Visible to anyone |
| 4/6 اللغات | بعد تصحيحٍ ضروري: الاستخراج كتب English (Fluent) خلافاً للسيرة؛ صُحِّحت إلى **Conversational** — الصدق قاعدة تشغيلية |
| 4/6 أنواع المهام | البند المتبقي اكتمل في اللوحة (اختيارات المالك على المنصة) |
| 5/6 الصورة | تُخطِّيت (الأفتار الافتراضي) |
| 6/6 | مكتمل ⇒ لوحة حيّة: Sample Job + Find Jobs |

**لم يكتمل الليلة:** إعداد الدفع **Stripe** (القائمة ← Payments) — فحصُ اليقين المؤجل: نعم ⇒ تقديم للوظائف الداخلية؛ لا ⇒ Mercor غداً (سكة موثّقة).

## 5) بحث «Arabic» — 00:34: ست بطاقات وقراران

| الوظيفة | الأجر | المصدر | القرار |
|---|---|---|---|
| Arabic Multimodal Image Evaluation Annotator | غير محدد | via Turing (خارجي) | **موجة ثانية:** وصفُها حرفياً Task 001 (صور غير منشورة، قصّ/حجب، prompts/معايير/ملاحظات حل بالإنجليزية، إخفاء الهوية) — السوقُ صادق على المنتج؛ لكن التقديم عبر الباب الذي أرشف المالك أمس يؤجَّل إلى نهارٍ صافٍ (قاعدة Turing: الإغلاق يخصّ نفس الدور فقط، وهذه دورٌ آخر) |
| Arabic Personalized AI Response Evaluator | 15 $/س | via Turing | مؤجل (خارجي) |
| Arabic Language AI Analyst | غير محدد | via Turing | مؤجل (خارجي) |
| Arabic Voice Actor for AI Training | غير محدد | via Turing | تجاوز (ليس عمل المالك) |
| AI Safety Content Evaluator (Arabic/English Required) | 15–40 $/س | **داخلية** | **الأولوية:** red-teaming المالك حقيقي (190 مسباراً)؛ شرط الشهادة يقبل «equivalent experience»؛ C1 الإنجليزية هو المطّ الوحيد |
| Bilingual AI Response Quality Reviewer (BA/BS Required) | 6–12 $/س | **داخلية** | احتياط (تشترط BA/BS لغويات صراحة) |

وظائف التبويب الأول (قانون/أسهم/عمليات) غير مطابقة وتُجاوزت.

## 6) سيرة PDF ولّدها الوكيل (خارج المستودع)

- `/home/user/Houssam_Benmerah_AI_Trainer_Resume.pdf` (صفحة واحدة، reportlab) وسكربت البناء خارج المستودع.
- **سبب عدم الالتزام:** ثنائيٌّ يتطلّب تسجيل `docs/governance/ASSET_LICENSE_CLEARANCE.json` (مسار محمي) + بيانات شخصية قرّر المالك إبقاءها خارج العام. المالك رفع سيرته الأشمل؛ استخراجُ المنصة جاء ممتازاً.

## 7) السجلّ: صفّان مقترحان — ولماذا **لم** يُلحقا في هذا الـPR

جُرّب محلياً إلحاق الصفّين أدناه مع توجيه المسار إلى OPP-11 (الردّ هو اعتراض CBAM بعينه الذي تنبأ به المستودع): البوابات الثلاث خضراء (outbound · scorecard · value_chain بعد إعادة التوليد)، لكن `tests/shared/test_economic_truth.py::test_real_every_sentence_stays_within_its_evidence` انكسر (`LEDGER:4` غير موجود): هذا الفرع ما يزال يحمل علّة `last_event` التي يصلحها PR #2607 تحديداً (يقرأ آخر صفٍّ في السجل كله بينما قائمة الأدلة تعدّ صفوف الأطروحة فقط). إلحاقُ صفٍّ خارج الأطروحة النشطة قبل دمج #2607 = تصنيعُ أحمرَ وتكرارُ إصلاحه. **القرار:** لا صفَّ في هذا الـPR؛ النصُّ المقترح حرفياً لـfollow-up بعد دمج #2607:

```csv
2026-09-23,ANTON_K_TARGET_2026-09-23.csv#id=1,Anton K,EU,email,EMAIL_SENT,,docs/commercial/outreach/SESSION_LOG_2026-10-10.md#2,"Pitch (owner screenshot 2026-10-09): multidisciplinary Algerian expert network; attachment included. Personal data withheld."
2026-09-26,ANTON_K_TARGET_2026-09-23.csv#id=1,Anton K,EU,email,REPLY_RECEIVED,,docs/commercial/outreach/SESSION_LOG_2026-10-10.md#2,"Reply verbatim: «We will need someone with environmental education and experience. The Delegated Regulation explicitly requires it.» Draft reply (unsent): §2.1."
```

مع ملف الهدف `docs/commercial/ANTON_K_TARGET_2026-09-23.csv` وإضافة `"ANTON_K_TARGET_2026-09-23.csv"` إلى `ledger_routes` لـOPP-11 (كلاهما اختُبر وأخضر قبل التراجع).

## 8) مفتوح (أفعال بشرية)

- [ ] بدء محادثات المختصين الثلاث، ثم إرسال مسودة §2.1.
- [ ] OpenTrain ← Payments/Stripe: فحص اليقين.
- [ ] إن نعم: AI Safety Content Evaluator أولاً.
- [ ] الموجة الثانية نهاراً: Multimodal Annotator.
- [ ] Payoneer · ANAE · سؤال البنك كتابةً — معلّقات موروثة.
- [ ] قسم `HUMAN:` في وصف هذا الـPR — يكتبه المالك.

## 9) ما يغيّره هذا الـPR

ملفٌّ واحد هو هذا السجل، تحت `docs/commercial/outreach/` المستثنى من بوّابة تجميد البحث (D-297). لا كود، لا سجلّ، لا مشتقّات.
