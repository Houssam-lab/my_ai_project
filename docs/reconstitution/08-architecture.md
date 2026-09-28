# 08 — Architecture: الطبقة البدائية، نواة الذكاء، خريطة السببية، مصالحة الكود، وحدود البناء

**التاريخ:** 2026-09-28 · **القاعدة:** كُتب هذا الملفّ **بعد** نضج الأطروحة لا قبلها؛ ولا يُبنى منه إلا ما في §7 «BUILD NOW».

---

## 1. Primitive Layer — أصغر بدائيات ذكيةٍ موجودة فعلاً

الحالة بحسب البرهان الثلاثي (§6.6): `ACTIVE` استيراد + سلسلة نداء + دليل تشغيل · `PARTIAL` على مسار حيّ بشرطٍ أو كسقوط · `DORMANT` كودٌ حقيقي بلا مسارٍ افتراضي · `ZOMBIE` بلا مسار · `PATTERN` النمط موجود والمعرفة مُثبَّتة على مجال.

| البدائية | موجودة؟ | أين | الحالة | قابلة للتعميم؟ | تدخل النواة؟ |
|---|---|---|---|---|---|
| **Observe** | نعم | `Trajectory/Step` (C-02) · telemetry/correlation (D-189) · `occurred_at/recorded_at` | ACTIVE (verifier) · ACTIVE (telemetry) | نعم | **نعم** |
| **Infer** | جزئياً | planning/research/reasoning services · `app/core/reasoning/` | PARTIAL — التنفيذ المتوازي بسياقٍ فارغ (D-01 §2.4) | كمقترِح لا كحاكم | لا في مسار الحكم |
| **Diagnose** | نمط | `ConceptDiagnosisSkill` (C-11) | PATTERN (enum مُثبَّت) | الآلية نعم؛ المعرفة لا | كمقابلةٍ بشرية أوّلاً |
| **Ask** | نمط | probe واحد قبل التدخّل (C-10 · C-11) | PATTERN | نعم | لاحقاً (07 §7) |
| **Plan** | جزئياً | planning-agent · `shared/workflows/plans.py` (خطط بيانات حتمية) | PARTIAL / ACTIVE (plans) | نعم | خطّة تحقّق = بيانات (نمط `plans.py`) |
| **Route** | نعم | `route_intent` (orchestrator) · intent registry | ACTIVE (تعليمياً) | domain-heavy | لا |
| **Act** | محدود | sandbox executor (C-12) · لا موصلات أعمال | ACTIVE (داخل المستودع) | لا لأنظمة عميل | **لا** — القراءة فقط |
| **Verify** | نعم/لا | `naas_verifier.core.verify` (C-02) · `probability_brain`/`foundations` · **مقابل** `ValidatorNode` (C-01 = مطابقة عبارات) | ACTIVE (core, مُختبَر) · **وهمي** على مسار الدردشة | نعم (core) | **النواة** |
| **Remember** | نعم | `TutorState` (upsert) · BKT append-only · checkpointer · history | ACTIVE بملّاكٍ متعدّدين (D-229) | النمط نعم؛ الأسماء لا | ledger مُلحَق-فقط جديد |
| **Adapt** | نمط | `PedagogicalPolicyEngine` · `DialogueManager` (C-10) | ACTIVE تربوياً | النمط (أقلّ تدخّل + منع حلقة) | كسياسة retest لا أكثر |
| **Evaluate** | نعم | `illusion` (C-05) · `assurance_window` (C-07) · SSI/VBT/CND | ACTIVE (stdlib) | نعم | **النواة** (الصلاحية) |
| **Authorize** | جزئياً | `policy_can_execute` (كلمات مفتاحية) · D-187 lock · `AuthorizationGrant` (تصميم فقط في D-01) | PARTIAL | نعم كعقدٍ مكتوب | **يُبنى صغيراً** (grant.yaml) |
| **Recover** | نمط | retry ≤1 · `dead_ends` · fallback chain | PATTERN | لا (تربوي/تشغيلي) | retest واحد بسياسة |
| **Learn** | لا | Evolution `PLANNED` (صفر كود) | ABSENT | — | لا |

**ما هو وهمي (يُقال صراحةً):** «Verify» على مسار الدردشة (C-01)، و«Plan→Research→Reason» كسلسلة (تعمل بالتوازي)، و«Learn».

## 2. Project Intelligence Kernel — ما يشكّل نواةً حقيقية

```text
KERNEL (stdlib-only, dep-free, shippable to a buyer)
├── Verify   : Trajectory × ConstraintSet → Verdict{HOLDS|VIOLATED|INCONCLUSIVE} per dimension    [naas_verifier/core]
├── Evidence : Evidence{kind, reproduction, source_reference} + hash chain/Merkle/receipt/replay   [naas_verifier/core/evidence · shared/research/verifiable_evidence]
├── Expiry   : ReportPin → FRESH|THROTTLED|STALE|UNPINNED · adjudicate(provenance)                  [shared/research/assurance_window]
└── Honesty  : None-not-zero · uncovered-dimension-declared · INCONCLUSIVE-never-promoted          [shared/illusion · constraint.py · verdict.py]

AROUND THE KERNEL (human first)
├── Contract  : contract.yaml (04 §3) — written by interview
├── Oracles   : count · field · idempotency · timing · readback (to build, small)
├── Authorize : grant.yaml — read-only scope, TTL, forbidden actions (to build, small)
└── Packet    : ledger.jsonl · verdict.json · packet.md · manifest.sha256 (to build, small)
```

**ما ليس في النواة عمداً:** LangGraph · الخدمات المصغّرة · الدردشة · BKT/FSRS · sandbox التنفيذ · أيّ LLM. النواة تُشحن إلى عميلٍ لا يملك تبعياتنا (D-02 · C-04).

## 3. Causality Map — كل انتقالٍ يسمّي حالته

```text
Existing Code                     naas_verifier/core · shared/illusion · verifiable_evidence · assurance_window     [FACT C-02..C-07]
  ↓ proven?  نعم (55 اختباراً + قياس حتمي)
Capability                        حكم ثلاثي مربوط بدليلٍ قابل لإعادة التشغيل وله صلاحية                            [FACT]
  ↓ proven?  نعم بالنوع؛ ⛔ لم يقرأ بعدُ مسار وكيلٍ من نظام طرفٍ ثالث (naas_verification_truth §2.a)
Generalized Capability            «النجاح الظاهر ≠ النجاح المُثبَت» على أيّ عملٍ له نظامٌ مسجِّل                    [INFERENCE I-01]
  ↓ proven?  لا — يُختبر بأوّل حزمةٍ على workflow حقيقي (T-0 في 09)
Problem Class                     ادّعاء نتيجة الوكيل سلعة ثقة؛ لا تمثيل محايد قابل للتحقّق                          [INFERENCE Why-7]
  ↓ proven?  جزئياً (X-01..X-05, X-10)؛ للصغار: HYPOTHESIS H-01
Customer Pain                     دفعة/فاتورة محجوزة أو منازَعة لغياب الحكم                                            [HYPOTHESIS H-01]
  ↓ proven?  لا — 30 اتصالاً مؤهَّلاً
Economic Consequence              أيام حجز × مبلغ · ساعات إثبات · نزاع                                                  [HYPOTHESIS، صيغة 03 §3]
  ↓ proven?  لا — تُملأ من المقابلة
Desired Outcome                   إفراجٌ أسرع بلا نزاع؛ قبولٌ بثقةٍ لا تعتمد على الباني                                 [HYPOTHESIS]
  ↓ proven?  لا — control داخلي (06 §4)
Required Proof                    حزمة يُعيد الدافع تشغيلها ويوقّعها                                                     [FACT كأداة · HYPOTHESIS كقبول H-03]
  ↓ proven?  لا — سجلّ إعادة تشغيل + توقيع
Payment                           رسم ثابت مسوّى بالـEUR/USD                                                             [HYPOTHESIS H-02]
  ↓ proven?  لا — عربون
```

## 4. Code Reconciliation — بعد اكتمال الاكتشاف فقط

| القدرة الموجودة | الدليل الفعلي | الدور الجديد | Keep | Refactor | Delete (من المسار الجديد) | Unknown |
|---|---|---|---|---|---|---|
| `naas_verifier/core/*` | C-02..C-04 · 55 اختباراً | **النواة**: الحكم | ✓ | — | — | — |
| `naas_verifier/adapters/multilingual_probe.py` | truth §2.a #10 | مثالُ adapter؛ يُقلَّد لموصّل readback | ✓ | — | — | — |
| `naas_verifier/corpus · targets · baselines · envs` | truth §2.a | خطّ 1 (AR/FR) — **Escape** | ✓ | — | — | — |
| `shared/research/verifiable_evidence.py` | C-06 | إيصال الحزمة وmanifest | ✓ | — | — | — |
| `shared/research/assurance_window.py` | C-07 | صلاحية الحكم + provenance | ✓ | — | — | — |
| `shared/illusion/*` | C-05 | النمط (`None` لا صفر) — لا يُستورد مباشرةً (يعرف المنهاج) | ✓ (تعليمياً) | — | — | هل يُستخرج `classify` المجرّد؟ |
| `shared/research/decision_latency.py` | C-08 | لا دور في MVP؛ يفسّر لماذا لا نبيع «كشفاً» | ✓ | — | — | — |
| `shared/research/first_invoice.py · withholding_onboarding.py · fx_rail.py` | D-04 · FIV | اختيار القناة وصياغة العقد | ✓ | — | — | — |
| `shared/research/offer_sellability.py` (SSI) | D-05 | تغليف العرض (P·S·T·R·F) | ✓ | — | — | — |
| `TutorState` + `TutorStateService` | C-09 | **نمط فقط**: حالة engagement جديدة بأسماء أعمال | ✓ (تعليمياً) | — | ✓ من المسار الجديد | — |
| `PedagogicalPolicyEngine` · `DialogueManager` | C-10 | نمط «أقلّ تدخّل + منع حلقة» لسياسة retest | ✓ | — | ✓ | — |
| `ConceptDiagnosisSkill` · `SocraticEvaluator` | C-11 | نمط المقابلة؛ لا كود | ✓ | — | ✓ | — |
| BKT · FSRS · illusion gap skill | D-210 | تعليم فقط | ✓ | — | ✓ | — |
| orchestrator graph (12 عقدة) · `ValidatorNode` | C-01 | **لا دور** — ليس مُتحقِّقاً | ✓ (تعليمياً) | — | ✓ | — |
| `skills_pipeline` المتوازي | D-01 §2.4 | لا دور | ✓ | — | ✓ | — |
| agent_tools sandbox + policy | C-12 | توليد artifacts محلياً فقط؛ **لا** ضدّ أنظمة العميل | ✓ | — | — | — |
| WS transport · chat shell · Generative UI | D-01 §13 | لا الآن (L-03) | ✓ | لاحقاً (بطاقات contract/verdict) | — | — |
| Postgres checkpointer · auth/RBAC | D-01 §13 | لاحقاً عند Assisted software | ✓ | — | — | — |
| telemetry · correlation IDs | D-189 | ربط الأدلّة | ✓ | — | — | — |
| fitness gates · GATE_LEDGER · CONSTITUTION_REGISTRY | C-13 | **انضباط الادّعاء** للحزم والوثائق | ✓ | — | — | — |
| `tools/hard_currency_engine/*` | C-14 | أوراكل مجالٍ محدّد؛ إضافات لاحقة | ✓ | — | ✓ من قلب MVP | — |
| `OFFER_CATALOG.json` (7 خطوط) | D-06 | أرشيف فرضيات؛ **ليس** واجهة بيع | ✓ | — | ✓ من GTM | — |
| Engagement/Contract/Scenario/Evidence/Verdict كنماذج أعمال | غير موجودة | **BUILD** | — | — | — | — |
| readback probe · n8n execution export adapter | غير موجودة | **BUILD** | — | — | — | — |
| `attest` CLI + packet generator + re-verify | غير موجودة | **BUILD** (المخرَج المدفوع) | — | — | — | — |
| economic event ledger (quote/deposit/delivery/settlement) | غير موجود | **BUILD MINIMAL** (ملفّ خاصّ يدوي) | — | — | — | — |

**قاعدة إعادة الاستعمال:** لا يُعاد استعمال مكوّنٍ إلا إن كان له سطرٌ في هذا الجدول بدورٍ في النظام الجديد. ما وُسم Delete يبقى في المستودع لخطّه الأصلي (التعليم) ولا يدخل سلسلة نداء الحزمة.

## 5. التدفّق المقترح (بعد أوّل عربون؛ اليوم يُنفَّذ يدوياً)

```text
interview (human) → contract.yaml
                      ↓
grant.yaml (read-only scope, TTL, forbidden) ← signed by acceptance authority
                      ↓
evidence pull: builder runs scenarios in staging  →  we read: execution export + system-of-record readback (GET only)
                      ↓
Trajectory build (adapter)  →  ConstraintSet (from contract)  →  verify()  →  Verdict per dimension
                      ↓
human judgments (named, rubric) only for Ambiguous assertions
                      ↓
ledger.jsonl (hash chain) + verdict.json + ReportPin + packet.md + manifest.sha256
                      ↓
client: `attest verify ./packet` → signs acceptance → builder invoice releases
                      ↓
regression asset (fixture + oracle + env assumptions) — with usage rights
```

**القرارات الإلزامية (لا تُفاوَض):** لا production mutation · قراءة فقط بصلاحيةٍ قصيرة العمر · لا أسرار في الحزمة · `UNVERIFIED` مخرَج من الدرجة الأولى · LLM يقترح ويشرح ولا يحكم · graph جديد؟ **لا** — CLI خطّي يكفي (D-01 §12.5 قالت 7–9 عقد؛ هنا **صفر عقد** حتى يظهر تفرّع حقيقي).

## 6. Service → Product — بوّابات التحوّل

| المرحلة | بوّابة الدخول | ما يُبنى |
|---|---|---|
| Manual | — | قوالب + النواة القائمة + scripts |
| Semi-automated | 1 عربون + عملٌ متكرّر يدوي | `attest` CLI (schema · append · hash · packet) |
| Productized | 3 حزمٍ مدفوعة متشابهة | مكتبة أوراكل + n8n adapter + قالب عقد |
| Software | 5+ مدفوعة، 2 مشترٍ متكرّر، صنفٌ واحد | بوابة re-verify + engagement table |
| Infrastructure | مستهلكٌ ثانٍ للسجلّ يطلب الصيغة (H-05) | مواصفة سجلٍّ منشورة |

## 7. Build Boundary

| **BUILD NOW** (لإثبات الدفع) | **AFTER FIRST PAYMENT** (للتكرار) | **AFTER REPEATABILITY** (للتوسّع) | **NEVER BUILD YET** (مغرٍ ولا يثبت الفرضية) |
|---|---|---|---|
| `contract.yaml` schema متوافق مع `ConstraintSet` | `attest` CLI كامل + re-verify للدافع | بوابة re-verify مُستضافة | دردشة/Outcome Interviewer |
| 3 أوراكل: count · field · idempotency (readback GET) | n8n execution export adapter | مكتبة بنود × أوراكل × توقيعات فشل | graph LangGraph جديد |
| `grant.yaml` + قالب تفويض | INCONCLUSIVE budget policy في العقد | period attestation (OBP) | SaaS متعدّد المستأجرين · billing |
| packet: `ledger.jsonl · verdict.json · packet.md · manifest.sha256` (يدوياً بالنواة القائمة) | timing/async oracle | engagement state table | حزمة موصلات (Make/Zapier/CRMs) |
| سجلّ تجاري خاصّ يدوي (quote/deposit/delivery/settlement) | سياسة retest (نمط C-10) | مواصفة سجلّ للمكتتب/المدقّق | LLM judge في مسار الحكم · monitoring مستمرّ · خرائط امتثال · تنفيذ إنتاجي مستقلّ · تكامل تأمين |

**التقدير النسبي للتغيير:** إعادة استعمال مباشرة للنواة (صفر كود جديد للحكم)؛ بناءٌ جديد صغير (أوراكل + adapter + packet — بضع مئات الأسطر)؛ صفر خدمة جديدة، صفر قاعدة بيانات جديدة، صفر graph.
