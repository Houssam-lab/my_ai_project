# سجلّ جلسة العمل على منصّات تقييم الذكاء الاصطناعي — 7 و8 أكتوبر 2026

> **التاريخ:** 2026-10-07 → 2026-10-08 · **المسار:** OPP-03 (عمل تقييم الذكاء الاصطناعي على المنصّات — قناة تمويل شخصية، D-282) · **الغرض:** تدوين كلّ ما جرى في الجلسة بالترتيب، بأدلّته ومصادره، كي لا يضيع شيءٌ منه ولا يُعاد من الصفر.
>
> ⛔ **الحالة:** `GATE_C = ABSENT` — لا عقد، ولا دفعة، ولا دولار حتى الآن. الطلب الوحيد المُرسَل في حالة **Shortlisted**.
>
> 📌 **ما حدث فعلاً (`CONTACT_LEDGER.csv`):** صفّ `FORM_SUBMITTED` واحد لـTuring بتاريخ 2026-10-08 (القناة `platform`). أيّ تغييرٍ في الحالة يُسجَّل بصفٍّ جديد لا بتعديل هذا الملفّ.

---

## 0) النطاق وما حُذف عمداً

المستودع **عامّ**، فطلب المالك «سجلّاً كاملاً بلا بيانات شخصية». لذلك **حُذف من هذا السجلّ**:

- رقم الهاتف، والبريد الشخصي، واسم البنك ورقم الحساب، ووثائق الهوية.
- ولاية الإقامة (تُذكر «الجزائر» فقط)، ورابط مجلّد المعرض على Google Drive.
- السيرة الذاتية (صُنعت في مساحة العمل المؤقّتة ولم تُرفع).
- كلّ ما يخصّ حال المالك الشخصية.

ولم تُرفع أيّ صورة أو PDF إلى المستودع: الملفّات الثنائية تتطلّب تسجيلاً في `docs/governance/ASSET_LICENSE_CLEARANCE.json` (مسار محمي)، وإحداها صورة طرفٍ ثالث (CC BY-SA). المرفوع هو **مصادر HTML** للعيّنتين و**بصمات SHA-256** للملفّات المسلَّمة — انظر [`portfolio/MANIFEST.md`](portfolio/MANIFEST.md).

## 1) الخطّ الزمني (بتوقيت الجزائر)

| الوقت | ما حدث |
|---|---|
| 2026-10-07 (نهاراً) | تسجيل أفعال التواصل مع Balagué وT2F وARCOEX في السجلّ (§2) |
| 2026-10-07 | المالك يطلب «دولاراً واحداً» عبر عملٍ على المنصّات؛ تحليل 210 وظيفة على OpenTrain مفتوحة للجزائر (كلّها تشترط إنجليزية قوية) |
| 2026-10-07 | إنشاء ملفّ OpenTrain وتصحيحه (§4)؛ بحث طرق الدفع من الجزائر (§3.1) |
| 2026-10-07 | OpenTrain يحيل إلى Turing لدور «AI - Analyst \| Photographer - Arabic»؛ ملء ملفّ Turing (§5) |
| 2026-10-07 ليلاً | Case 00 من صورة Wikimedia، ثم نقدُه وتحويله إلى «تحليل فشل» (§6.1–6.2) |
| 2026-10-08 00:06 | الطلب مُرسَل؛ الحالة **Shortlisted** («If your profile is selected for an interview, we'll get in touch soon») |
| 2026-10-08 17:11–18:13 | المالك يصوّر 21 صورة ميدانية حول المدرسة العليا لعلوم التسيير بعنابة (§6.3) |
| 2026-10-08 20:55–21:02 | ثلاث تجارب على أدوات ذكاء اصطناعي بصورة المهمة: ثلاث إجابات مختلفة، صفر صحيحة (§6.3) |
| 2026-10-08 ليلاً | ملفّ Task 001 النهائي؛ التحقّق من الحقيقة الأرضية بالجريدة الرسمية |

## 2) العمل في المستودع على نفس الفرع (قبل هذا السجلّ)

| الدفعة | ما فعلته |
|---|---|
| `cb3bc70` | تسجيل «مكالمة» لـBalagué بتاريخ 2026-09-22 — **أُزيلت لاحقاً**: المالك صحّح أنه لم يتّصل هاتفياً بأحد |
| `1aad771` | إصلاح اختبار: `tests/shared/test_economic_truth.py` كان يقرأ السجلّ الحقيقي بتاريخ مثبَّت (2026-10-02) فيُرفض كلّ صفٍّ لاحق ويُقرأ السجلّ فارغاً بصمت |
| `053deac` | بريد الإغلاق إلى Balagué Expertise + `CLOSED_NO_REPLY` |
| `4ef931b` | أوّل بريد إلى Groupe T2F + إعلان ملفّ الأهداف V2 مساراً تحت OPP-01 |
| `f094f28` | حذف صفّ T2F لأنّ البريد ارتدّ (`550 5.7.64 TenantAttribution`)، وتصحيح العنوان إلى العنوان المنشور في موقع المكتب |
| `88ad36c` | تسجيل إعادة الإرسال إلى العنوان الصحيح |
| `2b7793e` | إزالة صفّ مكالمة Balagué (لم تُجرَ) |
| `a9afe5f` | تسجيل بريد ARCOEX المُرسَل في 2026-09-22 (كشفه المالك بلقطات شاشة) |
| `2a57275` · `d8980ff` · `e62b8da` · `a081f74` · `22217be` · `7cb2df9` · `a623c11` | حزم القبول بعد كلّ تغيير |

اللوحة المشتقّة بعد ذلك: 5 صفوف · 4 اتصالات (كلّها بريد) · 3 كيانات · 0 ردود · 0 دفعات · `GATE_C = ABSENT`.

## 3) البحوث ونتائجها (بالمصادر)

كلّ بحثٍ شغّله وكيلُ بحثٍ ثم وكيلٌ مُشكِّك يعيد فتح المصادر. ما لم يُعثر عليه كُتب UNKNOWN.

### 3.1 طرق استلام المال من الجزائر

- **OpenTrain:** يدفع عبر Stripe إلى حساب بنكي محلّي، وصفحة الدول عنده (محدَّثة 2026-05-01) تذكر الجزائر.
- **PayPal في الجزائر:** الاستلام يشترط حساباً بنكياً أمريكياً أو بطاقة Visa ائتمانية.
- **Grey:** للجزائر حسابا EUR وGBP فقط، بلا USD وبلا سحب إلى البنوك الجزائرية (`grey.co/blog/compte-devise-algerie`، 2026-09-01). رسوم الاستلام 0.8٪ (حدّ أدنى 2، أقصى 10).
- **Wise:** الجزائر ليست في قائمة الدول التي يمكن الاحتفاظ فيها بالمال.
- **Payoneer → بنك جزائري:** لم يؤكّده أيّ مصدر أوّلي.
- **العملات المستقرّة:** القانون 25-10 (الجريدة الرسمية، 24 جويلية 2025) يجرّم حيازة العملات المشفّرة واستعمالها — **مصدرٌ ثانوي، غير متحقَّق من النصّ الرسمي**؛ لذلك نُصح بعدم استلام أجرٍ بها.
- **مستقل وخمسات:** حدّ السحب الأدنى 250 دولاراً.
- **الحكم على «ربط Grey بـPayPal»:** ممكن بشروط فقط ولا يُعتمد عليه؛ ولا يجوز أبداً التصريح بإقامة غير جزائرية.

### 3.2 كيف تدفع Turing ومن يدفع

- **الجهة المذكورة علناً:** `Turing Enterprises, Inc.`، شركة Delaware، 548 Market Street, PMB 18282, San Francisco, CA 94104 (شروط الخدمة وتذييل `help.turing.com`). الطرف الموقِّع لهذا الدور بعينه **UNKNOWN** (العقد خلف تسجيل الدخول).
- **العميل النهائي لا يدفع للمتعاقد:** شروط العملاء تقول «Client will pay Turing».
- **أربعة مسارات** (`help.turing.com/articles/6582454854`): مسار Turing (تحويل مباشر إلى البنك عبر «معالجي دفع» غير مسمَّين — «Deel is not used for payments in this flow») · مسار Deel · مسار شريك · كيان من كيانات Turing. يُحدَّد المسار لكلّ مشروع.
- **التوقيت:** مقالان رسميان يتعارضان — «5th calendar day + 2–3 days» مقابل «5th business day + 5–7 business days».
- **شروط الانضمام:** جواز سفر أو رخصة سياقة فقط (بطاقة التعريف الوطنية لا تُقبل)، والاسم مطابق لحساب الاستلام، ونموذج W-8BEN لغير المقيمين في أمريكا.
- **حالة الجزائر:** `unclear` — لا صفحة تؤكّدها ولا صفحة تستثنيها؛ شهادة مطوّر جزائري (2024) على `turing.com/review` تذكر «good and timely payments».
- **تحذير صريح من Turing:** «Any attempt to falsify work or misuse AI tools may result in immediate contract termination and loss of payments».

### 3.3 شكل التقييم عند Turing

- ليس امتحاناً ورقياً. الاختبارات (إن وُجدت) على الحاسوب مع **مشاركة الشاشة كاملة + كاميرا + ميكروفون**.
- **ممنوع ChatGPT وأيّ أداة خارجية** (شروط 2024-03-14، «Fair Assessment Policy»).
- إيقاف المشاركة أكثر من 4 مرّات ⇒ إقصاء و**90 يوماً** انتظار؛ الرفض الرسمي ⇒ 3 أشهر قبل إعادة التقديم لنفس الدور.
- **لهذا الدور تحديداً** (النسختان الفرنسية والبرتغالية من الإعلان): «Shortlisted candidates will receive a Job Interest Form» ولا امتحان مذكور. وفي أدوار عربية مشابهة: تحدٍّ تحليلي + كتابة إنجليزية + اختبار لغة (نحو 80–90 دقيقة، أحياناً خلال 24 ساعة).
- «An interview is typically required for all roles».

### 3.4 أنماط الاحتيال (عامّة، لا حالة مؤكَّدة باسم Turing)

- القنوات الرسمية فقط: `no-reply@turing.com`، و`work.turing.com`، ودعوة Deel الرسمية.
- أيّ رسوم «تسجيل/تدريب/تفعيل» = احتيال؛ وشيكٌ يُطلب ردّ جزءٍ منه = احتيال (FTC، 2026-04-30).
- لا جواز ولا بيانات بنكية عبر تطبيقات الدردشة.

## 4) OpenTrain

- الملفّ منشور. صُحّحت فيه بيانات أُدخلت خطأً: الاسم، ومستوى الإنجليزية (من «Native» إلى مستوى محادثة صادق)، والفرنسية (Fluent)، ومستوى الخبرة (Entry level).
- إعداد الدفع (Stripe) **لم يكتمل بعد**؛ صفحته تقول «Stripe will verify payout availability for Algeria during setup».
- وظيفتان مناسبتان لم يُقدَّم لهما بعد: محلّل بيانات LLM ناطق بالفرنسية، ومراجع جودة إجابات ثنائي اللغة.

## 5) Turing — الطلب

**الملفّ:** رُفعت السيرة، ثم المعلومات الأساسية، والتعليم (ماستر في الاقتصاد النقدي والبنكي)، والمهارات واللغات (العربية Native · الفرنسية Advanced · الإنجليزية Intermediate)، والخبرة (Founder & Lead Architect — CogniForge، منذ جوان 2025، Self-Employed)، والروابط (GitHub).

**قرار المهارات:** نصحتُ بحذف ROOT وSwitching وPhysics وMathematics لأنّ «Your technical assessment will focus on these». قرّر المالك الإبقاء على القائمة الواسعة «وتعلّم تلك المهارات». الدور المفضّل بقي «AI Engineer» لعدم وجود بديل أقرب في القائمة.

**أدوار راجعناها ولم يُقدَّم لها:**

| الدور | السبب |
|---|---|
| Senior Software Engineer – Python (LLM Evaluation & Repository Validation) | **«Location: India, Pakistan, Nigeria, Kenya, Egypt, Ghana, Bangladesh, Turkey, Mexico»** — الجزائر ليست فيها؛ و3+ سنوات بمستوى tech lead |
| Mathematics Expert | مستوى JEE Advanced (أصعب 1–2٪)؛ نُصح باختبار ذاتي (4 من 5 مسائل في ساعة) قبل أيّ تقديم |
| Python/FastAPI BE · Sr. Architect UI Gyms · Physics SME · Creative professionals | امتحانات برمجة أو اختصاص لا يناسب الآن، أو خارج المجال |

**نموذج التقديم للدور العربي** (الأجوبة الإنجليزية كما أُرسلت، مع حجب ولاية الإقامة):

| # | السؤال | الجواب |
|---|---|---|
| 1 | Commit up to 40 hrs/week | Yes |
| 3 | Arabic proficiency | Native |
| 4 | Start on September 21, 2026 | Yes (التاريخ مضى؛ المعنى: جاهز الآن) |
| 5 | Current state and country | `<wilaya withheld>, Algeria` |
| 6 | Authorized to work as a contractor | «Yes. I am an Algerian citizen living in Algeria, and I can work as an independent contractor from here. I am not in the US, so the 1099 form does not apply to me.» |
| 7 | Hourly model at $26/hour | Yes |
| 8 | Years in photography / editing / annotation | «I have no paid professional experience in photography yet. … about one year of experience reviewing and evaluating AI outputs … My portfolio includes a sample task: a masked landmark image with a prompt, a rubric and solution notes.» |
| 9 | First-hand knowledge of local monuments | Yes |
| 10 | Portfolio link | مجلّد Google Drive عامّ (الرابط محجوب هنا) |
| 11 | Sourcing licensed imagery | «Yes, at a basic level. For my portfolio sample I sourced a photo from Wikimedia Commons, checked its licence (CC BY-SA 4.0) and author on the file page … I know the difference between public domain (CC0), CC BY and CC BY-SA …» |

**وصف الدور (المقتطف الحاكم):** «create evaluation materials using cropped, occluded, or degraded images … require multimodal agents to conduct multi-step web research using … Google Lens, or reverse image search … All prompts, rubrics, and solution notes must be written in English … Local cultural knowledge … is a critical requirement … Evaluation Process: Shortlisted candidates will receive a Job Interest Form.»

**الأجر إن قُبل:** 26 $/ساعة؛ عند 20 ساعة/أسبوع ≈ 2,250 $/شهر، وعند 40 ساعة ≈ 4,500 $/شهر، لمدّة تصل إلى 16 أسبوعاً — **مشروطٌ** بالقبول وبطريق دفعٍ يصل إلى الجزائر.

## 6) معرض الأعمال (Portfolio)

### 6.1 Case 00 — مهمّة من صورة Wikimedia، ثم رفضها

- الصورة: مقرّ ولاية الطارف (Wikimedia Commons، Habib kaki، CC BY-SA 4.0 — تحقّقتُ من الرخصة عبر واجهة Commons). أُخفيت اللافتة «ولاية الطارف».
- **العيب القاتل:** الصورة الأصلية منشورة، وهي صورة صندوق المعلومات في مقال ويكيبيديا الفرنسية «Wilaya d'El Tarf»، فبحثٌ عكسي واحد يحلّ المهمّة بلا استعمال أيّ دليل مرئي. أي أنها لا تقيس «البحث متعدّد الخطوات» المطلوب.
- عيوب أخرى: أدلّة غير مميِّزة، وصعوبة «medium» بلا قياس، وتاريخ في السؤال لا يعزل أيّ قدرة.
- **القرار:** المهمّة مرفوضة للإنتاج، ومحفوظة مثالاً سلبياً موثَّقاً بعنوان «QA postmortem» مع خمس قواعد لإعادة التصميم. المصدر: [`portfolio/case00.html`](portfolio/case00.html).

### 6.2 نقدان من نموذج ذكاء اصطناعي آخر — ودرسُهما

- أعطى نموذجٌ لغويٌّ (لصق المالك ردوده) المهمّةَ نفسها **0/10** ثم **9.1/10** بعد تغيير العنوان والتأطير فقط. الحكم: **علامات المقيِّم اللغوي ليست قياساً**؛ تُؤخذ منه الملاحظة القابلة للتحقّق (تسرّب البحث العكسي، بيانات EXIF، البدائل المرفوضة، قائمة الجودة) وتُهمل الأرقام.
- **ما رُفض من نصائحه:** «لا تصوّر الآن» (يناقض حلّه هو: الصورة غير المنشورة هي العلاج)؛ خطّة 14 يوماً قبل التقديم (العميل يطلب البدء فوراً)؛ معيار «sufficient evidence» (غير موضوعي)؛ سؤال بلا تقييد زمني.

### 6.3 Task 001 — المدرسة العليا لعلوم التسيير بعنابة (صور غير منشورة)

**الميدان:** 21 صورة (Samsung Galaxy S10، 2026-10-08 بين 17:11 و18:13). المرشَّحة: الصورة `180812` (البرج المغاربي ذو الشُّرَف + الشارع + برجٌ بشرفات ملوّنة). الحقيقة الأرضية: الصورة `181356` وفيها اللافتة «ÉCOLE SUPÉRIEURE DES SCIENCES DE GESTION – ANNABA» — لا تُعرض على النموذج.

**المعالجة:** قصّ، وإخفاء اسم فندقٍ مضيء مقروء في العمق («HOTEL LE MAJESTIC» — طريقٌ مختصر إلى المدينة)، وطمس لوحتي سيارتين ومارٍّ واحد، وحذف بيانات EXIF (تحقّقتُ: صفر وسوم)، واسم ملفّ محايد. لافتة المدرسة خارج الإطار أصلاً.

**السؤال (كما استُعمل في التجربة 3):** «This photo was taken in October 2026. Identify the specific institution housed in the white building with arched windows on the right side of the photo. Use the visual clues and web search. Give the institution's official name as of October 2026 and its city, and explain your evidence.»

**المعيار:** «The response names the École Supérieure des Sciences de Gestion d'Annaba (ESSG Annaba) as the institution and Annaba, Algeria, as the city.» (المالك طلب أن أكتبه.)

**التجارب (من لقطات شاشة المالك):**

| # | الأداة | الوقت | الإجابة | المدينة | المؤسسة |
|---|---|---|---|---|---|
| 1 | Google AI (نصّ السؤال غير مسجَّل) | 20:55 | Siège de la Wilaya d'Alger, Bd Zighout Youcef | ❌ | ❌ |
| 2 | Google AI Overview، «ما هذا المبنى» | 20:57 | مقرّ بلدية عنابة العتيق | ✅ | ❌ |
| 3 | Gemini «Pro Extended»، السؤال أعلاه | 21:02 | APC de Mostaganem (مع مهندس وتاريخ 1927) | ❌ | ❌ |

ثلاث محاولات، ثلاث إجابات مختلفة، صفر صحيحة. القاسم المشترك: افتراض «مقرّ إداري» (ولاية/بلدية) وعدم التفكير في مؤسسة تعليم عالٍ، واختلاق أدلّة (مهندس، تاريخ، ساحة).

**الحقيقة الأرضية (متحقَّق منها):**

- الاسم القانوني «école supérieure des sciences de gestion à Annaba» / «المدرسة العليا في علوم التسيير بعنابة» — المرسوم التنفيذي **17-88** المؤرّخ في 15 فبراير 2017 (JORADP رقم 12، 2017-02-22). حلّت محلّ المدرسة التحضيرية المنشأة بالمرسوم **10-164** المؤرّخ في 28 جوان 2010.
- المبنى: إكمالية البنات في بونة (رُخّص 1907، افتُتح جويلية 1910) → Lycée Ernest Mercier → Lycée Pierre et Marie Curie → المدرسة التحضيرية (2010) → ESSG (2017). نشرة المدرسة رقم 01: «L'école est domiciliée à l'ex-lycée Pierre et Marie Curie, rue du 24 février 1956». لذلك **التقييد بـ«as of October 2026» ذو معنى**: الاسم القديم إجابة خاطئة.
- العنوانان المتداولان (Bd de la Révolution du 24 Février 1956 / Rue Zighout Youcef) يصفان على الأرجح واجهتين لنفس المربّع (OpenStreetMap).
- **تفسير الخطأ 1:** في الجزائر العاصمة أيضاً شارع زيغود يوسف، وعليه مقرّ الولاية (رقم 16) — تصادم أسماء.
- **الخطأ 2:** بلدية عنابة مبنى حقيقي على بعد نحو 200 م جنوباً، بُني 1884–1888 بطراز «انتقائي» لا مغاربي — ليس هذا المبنى.
- **المبنى ذو الأعمدة يساراً:** على الأرجح البريد المركزي لعنابة (Algérie Poste، نحو 70 م حسب OpenStreetMap). ادّعاء «وكالة BEA» في التجربة 2 بلا سند.
- **البرج الملوّن:** على الأرجح فندق Seybouse International (نحو 200 م؛ أُعيد افتتاحه 2024-02-20).

**حدود المهمّة (مكتوبة في الملفّ):** للمدرسة جولة افتراضية رسمية 360° (ديسمبر 2023) تُظهر الواجهة من نفس الساحة، فبحثٌ عكسي قويّ قد يطابقها — ولم تفعل ذلك أيّ من التجارب الثلاث؛ وثلاث تجارب فقط فالصعوبة غير معايَرة. المصدر: [`portfolio/task001.html`](portfolio/task001.html).

## 7) نصوص جاهزة

**رسالة سؤال الدفع إلى `support@turing.com`** (لم يؤكّد المالك إرسالها بعد):

```
Subject: Payment question before signing – AI Analyst | Photographer – Arabic

Hello Turing Support,

I am applying for the role "AI - Analyst | Photographer - Arabic". I live in Algeria.
Before signing, could you please confirm in writing:

1. Is this role open to people living in Algeria?
2. Is it paid through the Turing flow (direct bank transfer) or through Deel?
3. Can I be paid by SWIFT transfer to my own bank account in Algeria?
   If not, which payout accounts do you accept for a resident of Algeria?
4. What is the hourly rate, in which currency, and are any fees deducted?
```

**أسئلة المقابلة المتوقّعة (للتدرّب، بلا أيّ مساعد أثناء المقابلة):** Tell me about yourself · Why this role · How would you find where a photo was taken · How do you check an image is free to use · Walk me through your portfolio sample · Local places tourists don't know · Can you work 4 hours overlapping Pacific Time (≈ 17:00–21:00 بتوقيت الجزائر).

## 8) أخطائي في هذه الجلسة (مصحَّحة)

1. **بنيتُ Case 00 على صورة منشورة**، فكانت تُحلّ ببحثٍ عكسي واحد. صُحّح بتحويلها إلى «تحليل فشل» وبناء Task 001 من صور غير منشورة.
2. **قرأتُ اللافتة الزرقاء «بريد الجزائر» قبل التحقّق.** صحّحتُ إلى «غير مؤكَّد»، ثم رجّحت OpenStreetMap البريد المركزي.
3. **أعطيتُ النقد الأوّل علامة متساهلة (6/10)** قبل أن أعترف بعيب التسرّب.
4. **تعطّلت ثلاثة سير عمل بحدّ الاستخدام** فأُعيد تشغيلها؛ ولم يُبلَّغ المالك بأيّ نتيجةٍ قبل اكتمال وكيلها المُشكِّك.

## 9) ما بقي مفتوحاً

- [ ] جواب Turing على سؤال الدفع (الرسالة في §7).
- [ ] إكمال إعداد الدفع في OpenTrain، والتقديم لوظيفتين فيه.
- [ ] رفع Task 001 إلى مجلّد المعرض بجانب Case 00.
- [ ] مكالمة المتابعة مع Groupe T2F (تذكير 2026-10-09، 9:00–11:00) — اختيارية، وتُسجَّل نتيجتها بصفٍّ جديد.
- [ ] قسم `HUMAN:` في وصف الـPR — يكتبه المالك بنفسه.
