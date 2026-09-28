# 01 — Evidence: الجدار المعرفي (Epistemic Firewall)

**التاريخ:** 2026-09-28 · **الدور:** سجلّ الأدلّة الوحيد لهذه الإعادة · **القاعدة:** لا ينتقل ادّعاءٌ من طبقةٍ إلى أعلى منها إلا بدليلٍ مستقلّ مذكور هنا بتاريخه.

> **الطبقات الأربع** — `FACT` قابل للإثبات من الكود الحالي أو مصدرٍ أولي مؤرَّخ · `INFERENCE` استنتاج مبني على حقائق مذكورة · `HYPOTHESIS` علاقة قابلة للاختبار لم تُختبر · `LEGACY BELIEF` شيء تكرّر أو بُني سابقاً بلا دليلٍ كافٍ.
> **الممنوع:** `HYPOTHESIS → FACT` و`LEGACY BELIEF → DESIGN DECISION` بلا سطرٍ جديد في هذا الملفّ.

---

## 1. حقائق الكود (FACT — كلّها مقروءة من المصدر في هذه الجلسة)

| # | الحقيقة | الموقع | ما تعنيه للأطروحة |
|---|---|---|---|
| C-01 | مسار الدردشة الحيّ ينتهي بـ`ValidatorNode` **يطابق عباراتٍ نصّية** (`لم أفهم` · `يرجى التوضيح` · `لا أستطيع`) ويُعيد المحاولة مرّةً واحدة | [`nodes.py`](../../microservices/orchestrator_service/src/services/overmind/graph/nodes.py) `class ValidatorNode` · [`_conditions.py`](../../microservices/orchestrator_service/src/services/overmind/graph/graph_support/_conditions.py) `check_quality` | «التحقّق» على مسار الدردشة **حدسٌ لا تحقّق**. أيّ وثيقةٍ تصف مسار الدردشة كـ«validator» تبالغ |
| C-02 | يوجد قلب تحقّق حتميّ مستقلّ عن المجال: مسار (`Trajectory`) بخطواتٍ وحالات قبل/بعد، قيود على **خمسة أبعاد** مغلقة، حكمٌ ثلاثي `HOLDS / VIOLATED / INCONCLUSIVE`، ومجموعة قيودٍ **ترفض التقييم** إن تركت بُعداً بلا سببٍ منطوق | [`constraint.py`](../../naas_verifier/core/constraint.py) · [`trajectory.py`](../../naas_verifier/core/trajectory.py) · [`verdict.py`](../../naas_verifier/core/verdict.py) | هذا هو **الأصل الأعمق** في المستودع: حكمٌ لا يُرقّي «لا أعرف» إلى نجاح، ولا يُحسب البُعد المتروك في صالح المُختبَر |
| C-03 | الدليل نوعٌ لا رقم: كل `Evidence` يحمل صنفاً من قائمة مغلقة و`reproduction` و`source_reference`، ويرفع خطأً عند الإنشاء إن غاب أحدها | [`evidence.py`](../../naas_verifier/core/evidence.py) | «رقمٌ بلا أمر إعادة إنتاج ليس دليلاً» مفروضٌ بالنوع |
| C-04 | القلب مغطّى بـ55 دالّة اختبار (13 + 20 + 14 + 8) ومكتبة قياسية فقط، بلا استيراد من `app/` | [`tests/naas_verifier/`](../../tests/naas_verifier/) | قابل للشحن إلى عميلٍ لا يملك تبعياتنا |
| C-05 | محرّك «فجوة الوهم» يفصل الأداء **المدعوم** عن **الدائم غير المدعوم بعد تأخير**، ويُرجِع `None` لا صفراً تحت `MIN_OBS` | [`shared/illusion/engine.py`](../../shared/illusion/engine.py) · [`illusion_gap_skill.py`](../../app/services/skills/illusion_gap_skill.py) | النمط القابل للنقل: **النجاح الظاهر ≠ النجاح المُثبَت**، والغياب ليس صفراً |
| C-06 | بروتوكول دليلٍ قابل للحمل: سلسلة هاش · جذر ميركل · التزامات مملَّحة · إيصال تقييم · بصمة إعادة تشغيل مستقلّة عن الترتيب — «برهانٌ على المطابقة لا على الصحّة» بنصّ الملفّ | [`verifiable_evidence.py`](../../shared/research/verifiable_evidence.py) | الطبقة التي تحوّل «ثق بنا» إلى «أعد التشغيل بنفسك» موجودة ومُختبَرة |
| C-07 | نافذة صلاحية التقرير: حالات `FRESH / THROTTLED / STALE / UNPINNED`، `FRESH_DAYS = 14`، `MAX_REPORT_AGE_DAYS = 90`، و`adjudicate` يحكم على استقلال المصدر | [`assurance_window.py`](../../shared/research/assurance_window.py) | الحكم له **تاريخ انتهاء** وحقل «من صاغ النطاق» — وهذا ما لا تحمله لوحات التتبّع |
| C-08 | كمون الإشارة→القرار مقيس كطبقةٍ مُلزِمة من حادثتَين منشورتَين (HF/OpenAI · يوليو 2026) | [`decision_latency.py`](../../shared/research/decision_latency.py) | «مزيدٌ من الكشف» يستهدف طبقةً غير مُلزِمة — درسٌ يحكم اختيار المنتج |
| C-09 | الحالة التربوية الدائمة: صفّ `tutor_state` واحد لكل محادثة (upsert) بحقول `active_concept · kc_progress · dead_ends · interventions_used · last_step_emitted · turn_count`؛ و`student_bkt_analytics` مُلحَق-فقط | [`tutor_state.py`](../../app/core/domain/tutor_state.py) · [`tutor_state_service.py`](../../app/services/analytics/tutor_state_service.py) | نمط «حالة طويلة العمر + مانع تكرار + سجلّ أدلّة مُلحَق» موجود — لكنه **مسمّى تربوياً** حرفياً |
| C-10 | محرّك سياسة حتميّ: `Observe → Update → Estimate → Choose Lowest Useful Intervention` مع حراسة ضدّ الحلقات (`dead_ends` · `interventions_used`) | [`pedagogical_policy_engine.py`](../../app/services/skills/pedagogical_policy_engine.py) · [`dialogue_manager_skill.py`](../../app/services/skills/dialogue_manager_skill.py) | النمط «أقلّ تدخّلٍ مفيد + منع الحلقة» قابل للتعميم؛ **المعادلات لا** |
| C-11 | التشخيص حتميّ-أولاً ثم LLM محروس بـenum، لكن الـenum **مُثبَّت على تمرينٍ واحد** (`denominator · numerator · color_red …`) | [`concept_diagnosis_skill.py`](../../app/services/skills/concept_diagnosis_skill.py) | الآلية قابلة للنقل؛ المعرفة **غير** قابلة |
| C-12 | المنفّذ الآمن: `argv` + `shell=False` + قائمة سماح (بلا `curl`/`wget`) + سجن مسارات؛ سياسة الأدوات تمنع الكتابة ما لم يُرفع `TOOL_POLICY_ALLOW_WRITE`؛ وقفل D-187 يمنع توصيل مُخطِّط/نموذج بالأدوات قبل `M1→M4` | [`sandbox/policy.py`](../../app/services/agent_tools/sandbox/policy.py) · [`sandbox/executor.py`](../../app/services/agent_tools/sandbox/executor.py) · [`core_policy.py`](../../app/services/agent_tools/core_policy.py) | لا يوجد **موصل أعمال** واحد (CRM · بريد · تقويم). المنفّذ يحمي مستودعنا لا أنظمة عميل |
| C-13 | جهاز حوكمة: 99 بوّابة `check_*.py` في `scripts/fitness/`، 22 دستوراً في السجلّ، سجلّ بوّابات القرار بأربع بوّابات كلّها `ABSENT` مع سببٍ منطوق | [`scripts/fitness/`](../../scripts/fitness/) · [`CONSTITUTION_REGISTRY.json`](../governance/CONSTITUTION_REGISTRY.json) · [`GATE_LEDGER.json`](../governance/GATE_LEDGER.json) | ثقافة «الادّعاء لا يُرقّى بلا برهان» مفروضةٌ آلياً — وهي **الأصل الأندر** لمن يبيع أحكاماً |
| C-14 | أدوات العملة الصعبة: مُحقّقا فوترة (فرنسا · بلجيكا) · ZATCA · حاسبة CBAM · ماسح EAA · مُرسِل CRM · عقود | [`tools/hard_currency_engine/`](../../tools/hard_currency_engine/) | أوراكل مجالٍ محدّد؛ **ليست** قلب المنتج |
| C-15 | حجم المستودع: ≈207 ألف سطر Python في `app + shared + microservices`، 538 ملفّ اختبار، 350 وثيقة Markdown في `docs/` | قياس `wc`/`find` في هذه الجلسة | حجم الاستثمار المدفوع الذي يجب ألّا يحدّد الحدود ولا يُهمَل |
| C-16 | صفر عقد · صفر فاتورة · صفر دفعة · صفر مقابلة اكتشاف مؤرَّخة لأيّ خطّ — `GATE_C = ABSENT` | [`GATE_LEDGER.json`](../governance/GATE_LEDGER.json) · [`assurance_window_truth.md`](../../.memory/assurance_window_truth.md) | نقطة البداية الوحيدة الصادقة |

## 2. حقائق الوثائق الداخلية (FACT عن الوثائق — لا عن السوق)

| # | الحقيقة | الموقع |
|---|---|---|
| D-01 | وثيقتا 2026-09-28 خلصتا إلى: «محرّك قبول قائم على الدليل» ثمّ **تضييقٌ** إلى «Verified Workflow Recovery» بعد حادثة، سعر اختباري `€350` موسوم `PRICING HYPOTHESIS`، و**منع البناء قبل الدفع** | [`HIDDEN_PROJECT_REDISCOVERY_AR.md`](../research/HIDDEN_PROJECT_REDISCOVERY_AR.md) · [`OUTCOME_ASSURANCE_COMMERCIAL_PROOF_AR.md`](../research/OUTCOME_ASSURANCE_COMMERCIAL_PROOF_AR.md) |
| D-02 | أطروحة VEP: العائق أمام التصدير من الجزائر هو **كلفة تحقّق المشتري البعيد**؛ التحويل من سلعة ثقة إلى سلعة فحص عبر إيصالٍ يُعاد تشغيله عند المشتري؛ أجل سداد آمن ≤45 يوماً | [`HARD_CURRENCY_NEW_KNOWLEDGE_VERA.md`](../research/HARD_CURRENCY_NEW_KNOWLEDGE_VERA.md) |
| D-03 | أطروحة AHW: الاطمئنان أصلٌ متقادم؛ دورة إحلال التكوين (84 يوماً مقيسة) أسرع من دورة البيع (90) ⇒ ما يُشترى بوّابة انحدارٍ مُفعَّلة بالإصدار | [`HARD_CURRENCY_NEW_KNOWLEDGE_AHW.md`](../research/HARD_CURRENCY_NEW_KNOWLEDGE_AHW.md) |
| D-04 | WOD: وصف الدفعة «خدمة» بدل «ترخيص» في الولايات المتحدة يغيّر الاستقطاع من 30% إلى 0% — الصياغة التعاقدية تغيّر الربحية أكثر من تحسين المنتج | [`HARD_CURRENCY_NEW_KNOWLEDGE_WOD.md`](../research/HARD_CURRENCY_NEW_KNOWLEDGE_WOD.md) |
| D-05 | SSI: العروض المكتملة البنية (سعر · نطاق · زمن · عكس مخاطر · مدخل مجاني) هي أضيقُها نطاقاً؛ طبقة الدخول ≤ $5K | [`HARD_CURRENCY_NEW_KNOWLEDGE_SSI.md`](../research/HARD_CURRENCY_NEW_KNOWLEDGE_SSI.md) |
| D-06 | MF: 123 حالة بيعٍ موثّقة عبر 47 مجالاً — كلّها **أسعار الغير**؛ أعلاها: امتثال تنظيمي · أتمتة AI مفوترة · أمن مُلزِم · نسبة من مالٍ متحرّك | [`WHERE-THE-HARD-CURRENCY-IS.md`](../../studies/market-first-sales-reality/WHERE-THE-HARD-CURRENCY-IS.md) |
| D-07 | تعليمة بنك الجزائر 06-2021: احتفاظ المُصدِّر الرقمي بـ100% من الحصيلة (موسوم 🟢 داخلياً)؛ **أجل الترحيل متضارب** (306 مقابل 120 يوماً) وسؤالٌ مفتوح حتى مراجعة أكتوبر | [`fx_doctrine_truth.md`](../../.memory/fx_doctrine_truth.md) |
| D-08 | UCL: الحركة الوحيدة التي قِيست قيمتها المباشرة **صفراً** هي «نظافة المستودع/تخضير main» — وهي صنف العمل الذي استهلك أغلب تاريخ المستودع | [`HARD_CURRENCY_NEW_KNOWLEDGE_UCL.md`](../research/HARD_CURRENCY_NEW_KNOWLEDGE_UCL.md) |

## 3. حقائق خارجية جديدة (FACT بمصدرٍ مؤرَّخ — جُمعت 2026-09-28)

سُلَّم المصدر: `P1` أولي/رسمي/صانع · `A1` تحليل أو استبيان مسمّى · `V1` صفحة بائع أو مدوّنة تجارية (اتجاه فقط) · `R1` ورقة بحثية (arXiv، بلا تحكيم أقران ما لم يُذكر).

### 3.1 المال يتحرّك على النتائج — وتعريف النتيجة صار محلّ نزاع

| # | الحقيقة | المصدر | الرتبة | ما لا يثبته |
|---|---|---|---|---|
| X-01 | Zendesk (أبريل 2026): فوترة **لكل حلٍّ آلي** ≈ `$2` دفعٌ حسب الاستعمال / ≈ `$1.50` بحجمٍ ملتزم؛ التعريف: نافذة هدوء 72 ساعة ثمّ **نموذج تقييم منفصل يراجع النصّ**؛ التحقّق **داخلي** (الوكيل يؤكّد ثمّ نموذج يفحص)؛ الكاتب يسمّي «آليات النزاع» أمراً **غير محسوم** | [diginomica · 2026-05-19](https://diginomica.com/zendesk-relate-2026-outcome-based-future-verified-resolutions) · [The Pricing Conundrum · 2026-06-09](https://thepricingconundrum.substack.com/p/outcome-based-pricing-in-practice) | A1 | أنّ العملاء الصغار يعانون النزاع نفسه |
| X-02 | HubSpot: `$0.50` لكل محادثة محلولة · `$1` لكل lead مُوصى به؛ Salesforce Agentforce: `$2` لكل محادثة · ≈`$0.10` لكل فعل؛ الكاتب: «لا الصمت ولا الفحص الآلي يميّز مشترياً راضياً عن منسحبٍ صامت» | [The Pricing Conundrum · 2026-06-09](https://thepricingconundrum.substack.com/p/outcome-based-pricing-in-practice) | A1 | حجم السوق |
| X-03 | Deloitte DART (2026-06-04): الاعتراف بالإيراد في التسعير بالنتيجة يتطلّب «معايير **واضحة وموضوعية وقابلة للقياس** لتحديد وقوع النتيجة الناجحة»، وطريقة المخرَج كلّما وقعت النتيجة؛ **لا يتناول** التحقّق بطرفٍ ثالث | [Deloitte DART](https://dart.deloitte.com/USDART/home/publications/deloitte/industry/technology/accounting-outcome-based-pricing-agentic-ai) | P1 | أنّ المدقّقين يطلبون طرفاً ثالثاً |
| X-04 | Mayer Brown (2026-06-16) عن عقود تنفيذ الوكلاء: «اختبار واحد ناجح لا يكفي»؛ القبول «بأداءٍ إحصائي مقابل مجموعة تقييمٍ متّفقٍ عليها بعتباتٍ محدّدة»؛ اختبار **نتائج العمل داخل التشغيل الجاري لا بيئة التطوير**؛ «لا يستطيع أيٌّ من الطرفين نمذجة الخطر جيداً… فتقود مفاوضاتُ المسؤولية بنيةَ الصفقة»؛ التزامُ تحليل جذرٍ عند فشل تبعية | [Mayer Brown](https://www.mayerbrown.com/en/insights/publications/2026/06/key-contract-issues-in-agentic-ai-implementation-and-integration-deals) | P1 (مكتب محاماة) | أنّ الوكالات الصغيرة تكتب هذه العقود |
| X-05 | إطار «acceptance evals» (Visione Edge · 2026-07-08): المشتري يملك مجموعةً مجمّدة؛ **الفاتورة الأخيرة مشروطة** ببلوغ عتبات (نجاح 95% على 120 حالة · `pass^8` 90% على 30 حالة عالية الخطر …)؛ **لا طرف ثالث** | [Visione Edge](https://visione-edge.com/blog/ai-agent-acceptance-criteria-evals) | V1 | انتشار الممارسة |
| X-06 | تسعير حجز المواعيد B2B: `$300–$600` لكل اجتماعٍ مؤهَّل منعقد؛ هجين `$150–$300`؛ بائعون يعلنون «يُعاد الاعتماد إن لم يحضر خلال 10 دقائق، بلا عملية نزاع»؛ و«التعريفات والسقوف ورؤية CRM **تُقفل تعاقدياً**» | [SalesHive](https://saleshive.com/blog/pay-per-meeting-models-best-practices-deals) · [ScaliQ](https://scaliq.ai/pay-per-meeting) | V1 | أنّ النزاعات فعلاً نادرة |
| X-07 | وكالات الأتمتة: أمثلة `$1,200/شهر + $45` لكل lead مؤهَّل؛ `$40` لكل اجتماعٍ محجوز فوق أساس؛ «الهجين أساس + أداء هو النمط السائد» | [Taskip](https://taskip.net/ai-automation-agency-pricing/) · [Plura](https://www.plura.ai/articles/automated-lead-qualification-pricing) | V1 | التواتر الفعلي |

### 3.2 التأمين والاكتتاب يطلبان «سجلّاً قابلاً لإعادة التشغيل»

| # | الحقيقة | المصدر | الرتبة | ما لا يثبته |
|---|---|---|---|---|
| X-08 | من 2026-01-01 أدخلت ISO/Verisk استثناءاتٍ تُخرج أضرار الذكاء التوليدي من نماذج المسؤولية العامة؛ منتجاتٌ مخصّصة: Armilla (توسعة `$25M` يناير 2026) · AIUC (`$50M` يوليو 2025) · Testudo (يناير 2026) | [Traversaal](https://blog.traversaal.ai/ai-agent-liability-insurance-enterprise-risk-transfer-market/) · [Promise Legal](https://blog.promise.legal/ai-liability-insurance-gaps-2026/) | A1/V1 | أنّ الصغار يشترون التأمين |
| X-09 | Munich Re aiSure عبر Mosaic منذ 2026-02-26 بسعة `$15M`: «يدفع حين يفشل النموذج في **مواصفة أداءٍ متّفقٍ عليها عند الاكتتاب**، ويُسوّى على **بيانات أداءٍ قابلة للقياس** لا على سلسلةٍ سببية» | [InsureBench](https://www.insurebench.com/insurers/munich-re) · [Munich Re](https://www.munichre.com/en/solutions/for-industry-clients/insure-ai.html) | P1/A1 | من يقيس |
| X-10 | ما يطلبه المكتتبون: جرد كامل · عناية بالموردين · «**سجلٌّ مؤرَّخ قابل لإعادة التشغيل** — الملخّص المكتوب بعد الواقعة ليس دليلاً» · «إثبات أنّ الضمانات **عملت فعلاً** لا أنّها موجودة على الورق» | [Portal26](https://portal26.ai/ai-insurance-requirements/) | V1 | العتبات الكمّية |
| X-11 | AIUC-1: 130 ضابطاً (65 إلزامي)، فئات الدليل: سياسات · تنفيذ تقني · ممارسات تشغيلية · **تقييمات طرف ثالث**؛ إعادة اختبار ربع سنوية؛ Schellman أوّل مدقّق معتمد (فبراير 2026)؛ 4–8 أسابيع؛ **لا سعر منشور** | [AIUC-1](https://www.aiuc-1.com/) · [Fini](https://www.usefini.com/glossary/what-is-the-aiuc-1-standard) · [Zeltser](https://zeltser.com/aiuc-1-cert) | P1/A1 | أنّ كياناً جديداً يُعتمَد مدقّقاً |
| X-12 | ورقة «Trace-Economic Underwriting» (arXiv 2606.16465 · 2026-06-15، مُنقّحة 2026-08-11): تسعير مخاطر الوكيل من **آثار استعمال الأدوات** بعلاماتٍ اقتصادية حتمية لا حَكَم LLM؛ خطأ التسعير من `$17.7K` إلى `$569`؛ خفض CVaR 72% على 1,000 أثر SWE-smith | [arXiv](https://arxiv.org/abs/2606.16465) | R1 | تعميمها خارج مهامّ البرمجة |

### 3.3 التقييم المستقلّ صار عملاً — على مستوى النماذج لا العمليات

| # | الحقيقة | المصدر | الرتبة | ما لا يثبته |
|---|---|---|---|---|
| X-13 | Vals AI: جولة A بـ`$40M` (a16z · 2026-08-13)؛ «المختبرات تدفع لتُقيَّم كما يُدفع لـCollege Board»؛ إيراد 8× سنة 2025؛ **لا سعر منشور** | [Sacra](https://sacra.com/c/vals-ai/) · [The Investor Society](https://www.theinvestorsociety.com/vals-raises-us-40m-to-become-the-credit-rating-agency-of-ai-models/) | A1 | الطلب على مستوى **الـworkflow** الصغير |
| X-14 | AIR: `$50M` (TechCrunch · 2026-09-01) لفحص المهارات والإضافات التي يستعملها الوكلاء | [TechCrunch](https://techcrunch.com/2026/09/01/air-raises-50m-to-help-companies-vet-the-skills-and-add-ons-ai-agents-use/) | A1 | منافسةً مباشرة |
| X-15 | إطار «Trust Certificate» بأحكامٍ متدرّجة `Approved / Conditional / Rejected` للتحقّق قبل النشر (arXiv 2606.04037) | [arXiv](https://arxiv.org/pdf/2606.04037) | R1 | تبنّياً تجارياً |

### 3.4 الفشل الصامت موثّق — والبدائل تصف ولا تحكم

| # | الحقيقة | المصدر | الرتبة | ما لا يثبته |
|---|---|---|---|---|
| X-16 | استدعاء الأدوات يفشل 3–15% في الإنتاج؛ الأخطر «HTTP 200 بحمولةٍ فارغة» فلا يظهر استثناء | [Openlayer · يوليو 2026](https://www.openlayer.com/blog/ai-agent-failure-modes-tool-calling-loops-propagation) | V1 | معدّلاً عامّاً |
| X-17 | حالة منشورة: وكيلٌ أنجز العرض ثمّ أنشأ **847 سجلّ عميلٍ مكرَّراً** في الإنتاج قبل أن يلاحظ أحد حلقة إعادة المحاولة | [Fiddler](https://www.fiddler.ai/blog/ai-agent-failure-rate) | V1 | تواتراً |
| X-18 | n8n يملك «Evaluations» أصيلة: مجموعات بيانات ومقاييس وإضافة أخطاء الإنتاج إلى مجموعة الانحدار | [n8n Docs](https://docs.n8n.io/advanced-ai/evaluations/overview/) | P1 | — (منافسٌ مباشر لطبقة الاختبار الداخلي) |
| X-19 | مورّدو تحقيقٍ جنائي لحوادث الوكلاء موجودون (Corelayer · incident.io · Armalo …) | [Armalo](https://www.armalo.ai/learn/ai-agent-incident-forensics) · [Sherlocks](https://www.sherlocks.ai/discover/ai-incident-investigation-platforms) | V1 | نضجاً |

### 3.5 مراسي السعر (سند مورّد لا حجم سوق)

| الفئة | النطاق | المصدر | الرتبة |
|---|---|---|---|
| تدقيق red team لمرّة واحدة | `$8K–$25K`؛ شامل `$50K–$150K`؛ مستمرّ من `$5K/شهر` | [AI Vyuh](https://security.aivyuh.com/blog/ai-red-teaming-pricing-2026/) | V1 |
| مرحلة اختبار وتحقّق وكيل | `$5K–$50K+`؛ البسيط `€3K–€5K` في 8–10 أيام | [SoftTeco](https://softteco.com/blog/ai-agent-development-cost) · [DEV](https://dev.to/ilinmaks/how-much-does-it-cost-to-implement-an-ai-agent-in-2026-2100) | V1 |
| QA حرّ على Upwork | `$12–$20/ساعة` | [Upwork · سبتمبر 2026](https://www.upwork.com/hire/software-qa-testers/) | P1 (منصّة) |
| استشارة AI بسعرٍ ثابت | `$20K` (PoC) → `$200K+` | [Alice Labs](https://alicelabs.ai/en/insights/ai-consulting-pricing-2026) | V1 |

### 3.6 ما بقي كما كان في المستودع (لم يتغيّر بدليلٍ جديد)

- EU AI Act بعد Omnibus: الملحق الثالث من **2027-12-02**؛ التزام الناشر بحفظ السجلّات ≥6 أشهر (المادة 26) — [Secure Privacy](https://secureprivacy.ai/blog/eu-ai-act-article-26-deployer-obligations-and-what-enterprises-must-do-2026).
- AP2 (Google · 2025-09-16 · v0.2.0 أبريل 2026): تفويضات موقّعة تشفيرياً **لإثبات نيّة المستخدم** قبل الدفع، +60 منظّمة — [AP2](https://ap2-protocol.org/). ما يُقنَّن اليوم هو **إثبات النيّة**؛ إثبات **النتيجة** بلا معيار.

## 4. الاستنتاجات (INFERENCE — كلّ واحدةٍ تسمّي حقائقها)

| # | الاستنتاج | مبنيّ على |
|---|---|---|
| I-01 | الأصل الأعمق في المستودع ليس التعليم ولا LangGraph بل **حكمٌ ثلاثي صادق مربوطٌ بدليلٍ له صلاحية**، وهو يظهر في خمسة مواضع مستقلّة بالمنطق نفسه (C-02 · C-05 · C-06 · C-07 · C-13) | C-02..C-07, C-13 |
| I-02 | كلّما تحرّك المال على «وقوع نتيجة» (فوترة بالنتيجة · قبول مرحلة · تأمين على مواصفة) ظهرت الحاجة نفسها: **تعريف النتيجة + تحقّقٌ لا يملكه الطرف الذي يُدفع له** | X-01..X-05, X-09, X-10 |
| I-03 | التحقّق اليوم داخلي (Zendesk تفحص نفسها) أو يملكه المشتري وحده (Visione) — **الطرف الثالث غائب على مستوى الـworkflow** بينما هو حاضر على مستوى النموذج (Vals) والمعيار (AIUC-1 عبر مدقّقين معتمدين) | X-01, X-05, X-11, X-13 |
| I-04 | القيد المُلزِم على بائعٍ من الجزائر بلا مرجع هو كلفة تحقّق المشتري (D-02)؛ لذلك يجب أن يكون **المخرَج نفسه قابلاً لإعادة التشغيل عند المشتري** — وهذا ما تفعله C-06 حرفياً | D-02, C-06 |
| I-05 | أسعار الإصلاح والـQA سلعيّة (`$12–$35/ساعة`) بينما أسعار «الحكم المستقلّ» (تدقيق · اعتماد) أعلى بمرتبة — الفارق ليس المهارة بل **من يوقّع الحكم** | §3.5, X-11, X-13 |
| I-06 | تضييق وثيقة 09-28 إلى «بعد الحادثة» صحيحٌ كـ**مُحفِّز** لكنه ليس أقرب لحظات الشراء إلى المال: لحظة **الدفع المشروط بالنتيجة** (قبول مرحلة أو فترة فوترة) تتكرّر بنيوياً وتخصّ كل تسليمٍ لا الفاشل منه فقط | D-01, X-04, X-05, X-06 |

## 5. الفرضيات (HYPOTHESIS — لكلٍّ اختبارٌ في [09-experiments.md](09-experiments.md))

| # | الفرضية | ما يُبطلها |
|---|---|---|
| H-01 | يوجد بناة أتمتة صغار (خارج الجزائر) تُحجَز دفعتهم أو تُنازَع لأنّ العميل لا يقبل تقريرهم الذاتي عن النتيجة | 30 اتصالاً مؤهَّلاً بلا حالةٍ واحدة خلال 6 أشهر |
| H-02 | سيدفعون رسماً ثابتاً لطرفٍ ثالث إن كان أقلّ من 10% من المبلغ المحجوز ويُفرج عنه أسرع | عربونٌ واحد صفر بعد 15 عرضاً مؤهَّلاً |
| H-03 | العميل (الدافع للباني) سيُعيد تشغيل الحزمة بنفسه ويوقّع القبول | 3 حزمٍ مدفوعة لم يُعِد أحدٌ تشغيلها |
| H-04 | الطلب يتكرّر بنيوياً (مرحلة تالية · فترة فوترة تالية · إصدار جديد) لا سلوكياً | 3 حزمٍ مدفوعة بلا طلبٍ ثانٍ خلال 60 يوماً |
| H-05 | الحزمة نفسها تُقبَل لاحقاً كدليلٍ لمكتتبٍ أو مدقّق (الرهان غير المتماثل) | مكتتبٌ واحد يرفض صيغة السجلّ بعد 10 حزم |
| H-06 | الدفع بالنتيجة ينمو في 2026 لدى البائعين الصغار كما لدى الكبار | نسبة تبنّي مقيسة < 10% في العيّنة المؤهَّلة |

## 6. المعتقدات الموروثة (LEGACY BELIEF — لا تدخل قراراً)

| # | المعتقد | لماذا موروث | ما يحلّ محلّه |
|---|---|---|---|
| L-01 | «كبر كود التعليم يعني أنّ التعليم هو المنتج» | حجمٌ لا دليل قدرةٍ تجارية؛ D-08 قاس أنّ أغلب العمل التاريخي قيمته المباشرة صفر | القدرة تُنقل كنمط (I-01) لا كمنتج |
| L-02 | «`€350` سعرٌ مناسب» | مرساةٌ تحليلية بين عرضٍ منشور بـ`$149` ومشاريع بآلاف؛ لم يُسأل مشترٍ | سلّم عروضٍ يُختبر (06) |
| L-03 | «الدردشة هي الواجهة» | لأنّها الأصل الأكبر في الكود، لا لأنّ مشترياً فضّلها | مقابلة بشرية أوّلاً؛ الدردشة بعد 5 حالات (09) |
| L-04 | «BKT/FSRS ينتقلان إلى الأعمال» | معادلاتٌ تربوية لا صلاحية مثبتة لها خارج التعلّم | نمط «مدعوم/دائم» وحده ينتقل (08) |
| L-05 | «61% من بائعي AI سيتبنّون التسعير بالنتيجة بنهاية 2026 (Bessemer)» | ظهر في ملخّص بحثٍ آلي **ولم يوجد في المقال المُستدعى** | **يُحذف** من كل استدلال حتى يُقرأ من مصدره |
| L-06 | «أوت 2026 موعد الذعر التنظيمي» | صحّحته Regulation 2026/1744 (المستودع نفسه) | لا إلحاح تنظيمي قصير |
| L-07 | «LangGraph/الخدمات المصغّرة أصلٌ تجاري» | تفضيلٌ معماري؛ D-290 L4 يقول الإطار محوّل | لا يُذكر في أيّ عرض |

## 7. ما لم يُفعل في هذه الجلسة (حدود الصدق)

- لم تُجرَ مقابلة، ولم تُرسل رسالة، ولم يُفتح حساب قبض، ولم يُشغَّل نموذج.
- البحث الخارجي مُقيَّد بمحرّك بحثٍ أمريكي؛ الأسواق الفرنسية والألمانية غير ممسوحة بلغتها.
- لم يُعثر على دليلٍ مباشر (`C1`) لنزاعات دفعٍ في تسليمات أتمتة AI **الصغيرة** تحديداً؛ الدليل مجاور (X-04 للكبار · X-01 للبائعين الكبار · X-06 لحجز المواعيد). ولذلك بقيت H-01 **فرضيةً**.
- هذا الملفّ ليس رأياً قانونياً أو ضريبياً أو مصرفياً.
