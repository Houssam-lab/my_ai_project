# MASTER INDEX CONSTITUTION — النص الدستوري المُلزِم (حرف بحرف)

> **السلطة / Authority:** هذا النصّ جزءٌ من دستور المشروع. وهو **مُلزِم بلا استثناء** لكل وكيل ذكاء اصطناعي برمجي، ولكل إنسان، ولكل أداة، في كل الأحوال: قراءة المستودع، مطالعة الكود، التوثيق، إضافة حرف، حذف حرف، إعادة تسمية، إعداد، ترحيل، اختبار، نشر. لا يجوز تجاوزه إطلاقًا، ولا تخفيفه، ولا تحويل فشله إلى تحذير، ولا الاستشهاد بالسرعة أو الراحة أو طلب المستخدم لتعطيله.
>
> **بروتوكول الدخول:** قبل أي عمل، يجب المرور على هذا النصّ كاملًا وتطبيقه. المرور عليه ليس شكليًّا: القاعدة العليا والبوابات أدناه شروطُ انتقالٍ، لا قائمة مهامّ.
>
> **علاقة النصّ بغيره:** يُقرأ مع [`ENGINEERING_CONSTITUTION.md`](../../ENGINEERING_CONSTITUTION.md)، و[`docs/architecture/VIBE_CODING_PREVENTION_CONSTITUTION.md`](../architecture/VIBE_CODING_PREVENTION_CONSTITUTION.md)، و[`docs/architecture/CODE_ACCEPTANCE_CONSTITUTION.md`](../architecture/CODE_ACCEPTANCE_CONSTITUTION.md)، و`CLAUDE.md`، و`AGENTS.md`. عند التعارض الظاهري، لا يُستعمل هذا النصّ لإضعاف بوابةٍ قائمة، ولا تُستعمل بوابةٌ قائمة لإلغاء شرطٍ من شروطه؛ يُطبَّق الأشدّ.
>
> **التعديل:** تعديل هذا الملفّ تعديلٌ دستوريّ: يتطلّب سجلّ تعديلٍ تحت `docs/governance/amendments/` ومراجعةً بشريةً مستقلّة. لا وكيل يُصادق على تعديله بنفسه.

---

## النصّ الدستوري — منقولٌ حرفًا بحرف كما ورد

نعم. لكن حتى يكون الفهرس بمستوى مشروع يريد الوصول إلى **سلاسة Claude واتساقه وانسجامه**، لا ينبغي أن يكون مجرد قائمة Features أو Tech Stack.

المنتج العظيم يمر من:

> **لماذا؟ → لمن؟ → ماذا؟ → كيف؟ → لماذا هذا التصميم؟ → كيف نثبت صحته؟ → كيف نجعله سلسًا؟ → كيف يتحمل الفشل؟ → كيف يتطور؟ → كيف يصبح منتجًا لا مجرد كود؟**

ولا أستطيع أن أقدّم لك "البنية الداخلية الخاصة بـClaude" لأنها غير معلنة بالكامل، لكن يمكن بناء **فهرس هندسي مستقل** يستهدف نفس الصفات التي يلاحظها المستخدم: الاتساق، السلاسة، الاعتمادية، جودة التفاعل، قوة الأدوات، الذاكرة، الأمان، والقدرة على التطور.

MASTER INDEX

من أول حرف إلى آخر حرف لبناء منتج AI من الطراز العالمي

القاعدة العليا

```text
NO FEATURE BEFORE FOUNDATION
NO ARCHITECTURE BEFORE UNDERSTANDING
NO IMPLEMENTATION BEFORE CONTRACT
NO CLAIM BEFORE EVIDENCE
NO SCALE BEFORE RELIABILITY
NO AUTONOMY BEFORE CONTROL
NO COMPLEXITY WITHOUT JUSTIFICATION
NO "DONE" WITHOUT VERIFICATION

```

00 — ORIGIN

لماذا يوجد المنتج؟

00.01 المشكلة الإنسانية  
00.02 المستخدم الحقيقي  
00.03 الألم الحقيقي  
00.04 البديل الحالي  
00.05 لماذا البدائل غير كافية؟  
00.06 الوعد الأساسي  
00.07 القيمة الجوهرية  
00.08 ما الذي لن نبنيه؟  
00.09 حدود المنتج  
00.10 تعريف النجاح  
00.11 تعريف الفشل  
00.12 North Star Metric  
00.13 Product Thesis  
00.14 Product Constitution

**Gate 00:** لا ننتقل قبل أن نستطيع شرح المنتج في جملة واحدة بدون مصطلحات تقنية.

01 — USER

من هو الإنسان الذي نخدمه؟

01.01 Personas  
01.02 Jobs-to-be-Done  
01.03 User journeys  
01.04 Contexts  
01.05 Friction  
01.06 Expectations  
01.07 Accessibility  
01.08 Language  
01.09 Culture  
01.10 Trust  
01.11 Emotional state  
01.12 Failure tolerance  
01.13 User intent taxonomy  
01.14 Power users  
01.15 New users  
01.16 Expert users

**Gate 01:** لا نبني ميزة لا نعرف أي مشكلة مستخدم تحلها.

02 — DOMAIN

فهم المجال

02.01 Domain vocabulary  
02.02 Entities  
02.03 Relationships  
02.04 Events  
02.05 States  
02.06 State transitions  
02.07 Business rules  
02.08 Constraints  
02.09 Invariants  
02.10 Exceptions  
02.11 Edge cases  
02.12 Domain boundaries  
02.13 Source of truth

03 — PRODUCT EXPERIENCE

كيف يجب أن يشعر المنتج؟

03.01 First impression  
03.02 Onboarding  
03.03 Empty states  
03.04 Loading states  
03.05 Streaming  
03.06 Feedback  
03.07 Error states  
03.08 Recovery  
03.09 Navigation  
03.10 Consistency  
03.11 Accessibility  
03.12 Mobile  
03.13 Desktop  
03.14 Keyboard interaction  
03.15 Visual hierarchy  
03.16 Micro-interactions  
03.17 Response timing  
03.18 Perceived latency  
03.19 Delight  
03.20 Trust

هنا نبدأ الاقتراب من **السلاسة**.

04 — INTERACTION MODEL

كيف يتعامل المستخدم مع الذكاء الاصطناعي؟

04.01 Conversation model  
04.02 Message lifecycle  
04.03 Streaming lifecycle  
04.04 Regeneration  
04.05 Editing  
04.06 Branching  
04.07 Attachments  
04.08 Context  
04.09 Memory  
04.10 Interruptions  
04.11 Long tasks  
04.12 Clarification  
04.13 Uncertainty  
04.14 Citations/evidence  
04.15 Follow-up  
04.16 Multimodality  
04.17 Tool visibility  
04.18 User control

05 — PRODUCT CONTRACT

ماذا يتعهد المنتج أن يفعل؟

05.01 API contract  
05.02 UI contract  
05.03 Conversation contract  
05.04 Error contract  
05.05 Latency contract  
05.06 Availability contract  
05.07 Data contract  
05.08 Privacy contract  
05.09 Model behavior contract  
05.10 Tool contract

06 — SYSTEM ARCHITECTURE

الهيكل الأساسي

06.01 System boundaries  
06.02 Frontend  
06.03 Backend  
06.04 Domain layer  
06.05 Application layer  
06.06 Infrastructure  
06.07 APIs  
06.08 Events  
06.09 Queues  
06.10 Workers  
06.11 Database  
06.12 Cache  
06.13 Object storage  
06.14 Search  
06.15 AI orchestration  
06.16 Observability  
06.17 Security boundary

**قاعدة:** لا نضيف Microservice إلا عندما توجد مشكلة حقيقية تتطلبه.

07 — STATE ARCHITECTURE

أين تعيش الحقيقة؟

07.01 Session state  
07.02 User state  
07.03 Conversation state  
07.04 Agent state  
07.05 Persistent state  
07.06 Cache state  
07.07 Derived state  
07.08 Temporary state  
07.09 Ownership  
07.10 Synchronization  
07.11 Concurrency  
07.12 Recovery

**Gate:** كل state مهم يجب أن يكون له owner واحد واضح.

08 — DATA ARCHITECTURE

08.01 Data model  
08.02 Schema  
08.03 Constraints  
08.04 Indexes  
08.05 Transactions  
08.06 Consistency  
08.07 Migrations  
08.08 Versioning  
08.09 Retention  
08.10 Deletion  
08.11 Backup  
08.12 Recovery  
08.13 Privacy  
08.14 Data lineage

09 — AI CORE

عقل المنتج

09.01 Model selection  
09.02 Model abstraction  
09.03 Provider abstraction  
09.04 Prompt architecture  
09.05 Context assembly  
09.06 System instructions  
09.07 Conversation state  
09.08 Context compression  
09.09 Retrieval  
09.10 Memory  
09.11 Structured outputs  
09.12 Validation  
09.13 Model routing  
09.14 Model fallback  
09.15 Cost control  
09.16 Latency control  
09.17 Token budgeting  
09.18 Model versioning  
09.19 Model regression  
09.20 Model observability

10 — REASONING / ORCHESTRATION

10.01 Task decomposition  
10.02 Planning  
10.03 Routing  
10.04 State machine  
10.05 Workflow execution  
10.06 Conditional paths  
10.07 Parallelism  
10.08 Cancellation  
10.09 Retry  
10.10 Timeout  
10.11 Recovery  
10.12 Termination  
10.13 Human escalation  
10.14 Long-running tasks

11 — AGENT SYSTEM

11.01 Agent identity  
11.02 Agent role  
11.03 Agent capabilities  
11.04 Tool permissions  
11.05 Tool selection  
11.06 Tool execution  
11.07 Tool validation  
11.08 Action authorization  
11.09 Agent memory  
11.10 Agent state  
11.11 Agent planning  
11.12 Agent observation  
11.13 Agent correction  
11.14 Agent termination  
11.15 Agent audit trail  
11.16 Agent cost limits  
11.17 Agent failure containment

**مبدأ:** Intelligence ≠ authority.

12 — TOOLS

12.01 Tool registry  
12.02 Tool schemas  
12.03 Input validation  
12.04 Output validation  
12.05 Permission model  
12.06 Timeouts  
12.07 Retries  
12.08 Idempotency  
12.09 Side effects  
12.10 Auditability  
12.11 Versioning  
12.12 Tool failure semantics

13 — KNOWLEDGE / MEMORY

13.01 Conversation memory  
13.02 User memory  
13.03 Semantic memory  
13.04 Episodic memory  
13.05 Working context  
13.06 Retrieval  
13.07 Relevance  
13.08 Freshness  
13.09 Contradiction handling  
13.10 Memory deletion  
13.11 Privacy  
13.12 Memory confidence

14 — MULTIMODALITY

14.01 Text  
14.02 Image  
14.03 Audio  
14.04 Video  
14.05 Documents  
14.06 OCR  
14.07 Vision reasoning  
14.08 Cross-modal context  
14.09 Input normalization  
14.10 Output rendering

15 — SAFETY

15.01 Threat model  
15.02 Abuse model  
15.03 Prompt injection  
15.04 Tool injection  
15.05 Data exfiltration  
15.06 Authorization  
15.07 Tenant isolation  
15.08 Secret handling  
15.09 Malicious files  
15.10 Unsafe automation  
15.11 Output safety  
15.12 Human override  
15.13 Incident response

16 — SECURITY

16.01 Identity  
16.02 Authentication  
16.03 Authorization  
16.04 Session security  
16.05 Secrets  
16.06 Encryption  
16.07 Network isolation  
16.08 Dependency security  
16.09 Supply chain  
16.10 Sandboxing  
16.11 Audit logs  
16.12 Vulnerability management

17 — RELIABILITY

17.01 Failure taxonomy  
17.02 Timeouts  
17.03 Retries  
17.04 Circuit breakers  
17.05 Idempotency  
17.06 Graceful degradation  
17.07 Backpressure  
17.08 Recovery  
17.09 Disaster recovery  
17.10 Chaos testing  
17.11 Fault injection  
17.12 Data recovery

18 — PERFORMANCE

18.01 Latency budget  
18.02 Throughput  
18.03 Concurrency  
18.04 CPU  
18.05 Memory  
18.06 Network  
18.07 Database  
18.08 Cache  
18.09 Model latency  
18.10 Tool latency  
18.11 Streaming latency  
18.12 Cost per request

19 — OBSERVABILITY

19.01 Structured logs  
19.02 Metrics  
19.03 Traces  
19.04 Correlation IDs  
19.05 User journey tracing  
19.06 Model telemetry  
19.07 Agent telemetry  
19.08 Tool telemetry  
19.09 Error classification  
19.10 Alerts  
19.11 Dashboards  
19.12 Incident reconstruction

20 — EVALUATION

هنا الفرق بين منتج AI حقيقي وواجهة فوق API.

20.01 Golden datasets  
20.02 User scenarios  
20.03 Regression suite  
20.04 Adversarial suite  
20.05 Tool-use evaluation  
20.06 Long-context evaluation  
20.07 Memory evaluation  
20.08 Instruction following  
20.09 Factuality  
20.10 Consistency  
20.11 Safety  
20.12 Latency  
20.13 Cost  
20.14 Human evaluation  
20.15 Automated evaluation  
20.16 Model comparison

21 — TESTING

21.01 Unit  
21.02 Integration  
21.03 Contract  
21.04 Workflow  
21.05 End-to-end  
21.06 Regression  
21.07 Property-based  
21.08 Fuzzing  
21.09 Mutation testing  
21.10 Failure testing  
21.11 Load testing  
21.12 Security testing  
21.13 Recovery testing

22 — SOFTWARE QUALITY

22.01 Formatting  
22.02 Lint  
22.03 Type safety  
22.04 Dependency hygiene  
22.05 Complexity  
22.06 Duplication  
22.07 Dead code  
22.08 API stability  
22.09 Documentation  
22.10 Maintainability

23 — ARCHITECTURAL GOVERNANCE

23.01 Constitution  
23.02 Invariants  
23.03 Architecture Decision Records  
23.04 Dependency rules  
23.05 Forbidden imports  
23.06 Ownership rules  
23.07 Change protocol  
23.08 Exception protocol  
23.09 Protected files  
23.10 Self-audit  
23.11 Agent entry protocol  
23.12 Constitutional amendment

24 — ZERO-VIBE-CODING LAYER

24.01 Pre-modification gate  
24.02 Old-problems frontier  
24.03 Root-cause analysis  
24.04 Evidence ledger  
24.05 Change hypothesis  
24.06 Smallest experiment  
24.07 Baseline  
24.08 Regression verification  
24.09 Complexity budget  
24.10 No silent exceptions

**قاعدة مطلقة:**

```text
OLD PROBLEM
    ↓
UNDERSTAND
    ↓
REPAIR
    ↓
VERIFY
    ↓
NEW CHANGE

```

وليس:

```text
NEW FEATURE
↓
PATCH
↓
PATCH
↓
TECHNICAL DEBT

```

25 — CI/CD

25.01 Build  
25.02 Lint  
25.03 Type-check  
25.04 Test  
25.05 Security  
25.06 Architecture gates  
25.07 Migration checks  
25.08 Dependency checks  
25.09 Artifact generation  
25.10 Deployment  
25.11 Rollback  
25.12 Environment parity

26 — INFRASTRUCTURE

26.01 Containers  
26.02 Networking  
26.03 Compute  
26.04 Storage  
26.05 Database  
26.06 Queue  
26.07 Cache  
26.08 Secrets  
26.09 DNS  
26.10 CDN  
26.11 Scaling  
26.12 Disaster recovery

27 — DEPLOYMENT ENGINEERING

27.01 Development  
27.02 Test  
27.03 Staging  
27.04 Production  
27.05 Feature flags  
27.06 Canary  
27.07 Blue/green  
27.08 Rollback  
27.09 Migration sequencing  
27.10 Release verification

28 — PRODUCT OPERATIONS

28.01 Support  
28.02 Incident response  
28.03 User feedback  
28.04 Bug triage  
28.05 Feature requests  
28.06 Product analytics  
28.07 Retention  
28.08 Activation  
28.09 Churn  
28.10 Cost monitoring

29 — HUMAN FACTOR

29.01 UX research  
29.02 Cognitive load  
29.03 Trust  
29.04 Explainability  
29.05 Error recovery  
29.06 Accessibility  
29.07 User control  
29.08 User expectations  
29.09 Human-in-the-loop  
29.10 Human override

30 — CONSISTENCY ENGINE

وهذه من أهم طبقات "السلاسة" التي تراها في المنتجات الكبيرة.

30.01 Naming consistency  
30.02 Visual consistency  
30.03 Interaction consistency  
30.04 Error consistency  
30.05 API consistency  
30.06 State consistency  
30.07 Model consistency  
30.08 Tool consistency  
30.09 Documentation consistency  
30.10 Behavior consistency

أي:

> نفس المفهوم يجب ألا يتصرف بخمس طرق في خمسة أماكن.

31 — PRODUCT COHERENCE

31.01 Features support the core thesis  
31.02 UX supports the user journey  
31.03 Architecture supports UX  
31.04 AI supports product purpose  
31.05 Safety supports trust  
31.06 Analytics support decisions  
31.07 Infrastructure supports reliability  
31.08 Economics support sustainability

كل طبقة يجب أن تدعم الطبقات الأخرى.

32 — DEBT MANAGEMENT

32.01 Technical debt  
32.02 Architectural debt  
32.03 Test debt  
32.04 Documentation debt  
32.05 Security debt  
32.06 Operational debt  
32.07 Dependency debt  
32.08 UX debt  
32.09 Model debt  
32.10 Data debt

لكل دين:

```text
CAUSE
IMPACT
RISK
OWNER
PRIORITY
REPAIR
VERIFICATION

```

33 — CHANGE MANAGEMENT

33.01 Why change?  
33.02 What changes?  
33.03 What breaks?  
33.04 Migration  
33.05 Compatibility  
33.06 Rollback  
33.07 Verification  
33.08 Communication  
33.09 Post-change review

34 — LEARNING SYSTEM

34.01 Incident → lesson  
34.02 Failure → test  
34.03 Test → invariant  
34.04 Invariant → architecture  
34.05 Architecture → documentation  
34.06 Documentation → agent knowledge  
34.07 Knowledge → future prevention

هنا يصبح المشروع **يتعلم من تاريخه**.

35 — EXPERIMENTATION

35.01 Hypothesis  
35.02 Experiment  
35.03 Prediction  
35.04 Falsifier  
35.05 Measurement  
35.06 Result  
35.07 Model update  
35.08 Promotion / rejection

36 — EVOLUTION

36.01 Architecture v1  
36.02 Evidence  
36.03 Architecture v2  
36.04 Deprecation  
36.05 Migration  
36.06 Replacement  
36.07 Compatibility  
36.08 Historical knowledge preservation

37 — LONG-TERM DESIGN

37.01 6 months  
37.02 1 year  
37.03 2 years  
37.04 5 years  
37.05 10 years  
37.06 Team turnover  
37.07 Provider changes  
37.08 Technology extinction  
37.09 Scale changes  
37.10 Regulatory changes

38 — FINANCIAL ENGINEERING

لأن المنتج العظيم ليس مجرد نظام تقني.

38.01 Unit economics  
38.02 Inference cost  
38.03 Infrastructure cost  
38.04 Customer acquisition  
38.05 Gross margin  
38.06 Pricing  
38.07 Usage limits  
38.08 Cost protection  
38.09 Abuse economics  
38.10 Revenue model

39 — MARKET

39.01 Target market  
39.02 Competitive alternatives  
39.03 Differentiation  
39.04 Positioning  
39.05 Switching cost  
39.06 Distribution  
39.07 Feedback loops  
39.08 Moat  
39.09 Internationalization

40 — TRUST

40.01 Reliability  
40.02 Transparency  
40.03 Privacy  
40.04 Security  
40.05 Error honesty  
40.06 Uncertainty disclosure  
40.07 Data ownership  
40.08 User control

المنتج العظيم لا يجعل المستخدم يقول:

> "إنه ذكي."

فقط.

بل:

> **"أستطيع الاعتماد عليه."**

41 — PRODUCT READINESS

41.01 Functional readiness  
41.02 UX readiness  
41.03 Reliability readiness  
41.04 Security readiness  
41.05 Performance readiness  
41.06 Operational readiness  
41.07 Financial readiness  
41.08 Support readiness  
41.09 Legal/compliance readiness

42 — LAUNCH

42.01 Internal alpha  
42.02 Controlled alpha  
42.03 Beta  
42.04 Limited release  
42.05 General availability  
42.06 Monitoring  
42.07 Rollback  
42.08 Incident response

43 — POST-LAUNCH

43.01 Observe  
43.02 Measure  
43.03 Listen  
43.04 Diagnose  
43.05 Prioritize  
43.06 Improve  
43.07 Re-evaluate  
43.08 Repeat

44 — MATURITY

كل capability تمر:

```text
UNKNOWN
↓
CONCEPT
↓
DESIGNED
↓
IMPLEMENTED
↓
TESTED
↓
INTEGRATED
↓
RUNTIME VERIFIED
↓
FAILURE TESTED
↓
OPERATIONALLY PROVEN
↓
EVOLVABLE
↓
INSTITUTIONALIZED

```

45 — FINAL SYSTEM AUDIT

45.01 Can we explain it?  
45.02 Can we test it?  
45.03 Can we observe it?  
45.04 Can we recover it?  
45.05 Can we secure it?  
45.06 Can we scale it?  
45.07 Can we modify it safely?  
45.08 Can a new engineer understand it?  
45.09 Can the original developer disappear?  
45.10 Can the system survive its own success?

46 — THE LAST QUESTION

في النهاية لا نسأل:

> **"هل بنيناه؟"**

بل:

> **"هل بنيناه بطريقة تجعل الإصدار القادم أكثر سهولة، وأكثر معرفة، وأقل خطورة من الإصدار السابق؟"**

إذا كانت الإجابة نعم، فالنظام يتطور.

إذا كانت الإجابة لا، فنحن فقط نراكم الكود.

47 — FINAL PRODUCT LOOP

```text
VISION
  ↓
USER
  ↓
DOMAIN
  ↓
PRODUCT
  ↓
UX
  ↓
CONTRACTS
  ↓
ARCHITECTURE
  ↓
STATE
  ↓
DATA
  ↓
AI
  ↓
ORCHESTRATION
  ↓
AGENTS
  ↓
TOOLS
  ↓
MEMORY
  ↓
SAFETY
  ↓
SECURITY
  ↓
RELIABILITY
  ↓
PERFORMANCE
  ↓
OBSERVABILITY
  ↓
EVALUATION
  ↓
TESTING
  ↓
CI/CD
  ↓
OPERATIONS
  ↓
REAL USERS
  ↓
REAL FAILURES
  ↓
LEARNING
  ↓
ARCHITECTURAL EVOLUTION
  ↓
PRODUCT EVOLUTION
  ↓
NEXT GENERATION

```

والأهم: هذا الفهرس ليس To-Do List

لا ينبغي أن يقول الوكيل:

> "حسنًا، سأمر على 47 قسمًا وأضع ملفات لكل قسم."

هذا يعيدنا إلى Vibe Coding بشكل أكثر أناقة.

يجب تحويله إلى **نظام بوابات**:

```text
GATE 00
هل المشكلة صحيحة؟

GATE 01
هل المستخدم مفهوم؟

GATE 02
هل المجال مفهوم؟

GATE 03
هل العقد واضحة؟

GATE 04
هل المعمارية مبررة؟

GATE 05
هل الحالة مملوكة بوضوح؟

GATE 06
هل البيانات سليمة؟

GATE 07
هل AI قابل للضبط والتقييم؟

GATE 08
هل الأدوات آمنة؟

GATE 09
هل الفشل معروف؟

GATE 10
هل الأداء مقاس؟

GATE 11
هل المنتج قابل للاستخدام؟

GATE 12
هل الواقع يثبت الادعاءات؟

GATE 13
هل النظام قابل للتطور؟

GATE 14
هل يمكن لفريق آخر فهمه وتشغيله؟

GATE 15
هل يستحق التوسع؟

```

**ولا يجوز للوكيل القفز من Gate إلى Gate لمجرد أن الكود موجود.**

هذا هو الجزء الذي يجعل الفهرس مختلفًا جذريًا عن "خارطة تطوير".

> **الفهرس يحدد ماذا يجب أن تعرفه.**  
> **الدستور يحدد ماذا يُسمح لك أن تفعل.**  
> **البوابات تحدد متى يُسمح لك بالانتقال.**  
> **الأدلة تحدد هل ما فعلته صحيح.**  
> **والتجارب تحدد ما الذي يجب أن تتعلمه بعد ذلك.**

بهذه البنية يصبح هدفك ليس مجرد **بناء تطبيق يشبه Claude في الشكل**، بل بناء **منظومة هندسية قادرة على الوصول تدريجيًا إلى مستوى السلاسة والاتساق والاعتمادية الذي يجعل المنتجات العظيمة تبدو بسيطة رغم تعقيد ما تحتها**.

---

## نهاية النصّ المنقول — ملحق الإلزام

1. النصّ أعلاه مُلزِم بحرفه. أيّ عملٍ في هذا المستودع — قراءة، تحليل، توثيق، إضافة حرف، حذف حرف — يمرّ عليه أوّلًا ويُطبَّق.
2. لا وكيل ولا إنسان يتجاوز القاعدة العليا الثمانية ولا البوابات `GATE 00..15`.
3. لا يجوز تحويل هذا النصّ إلى To-Do List، ولا توليد 47 ملفًّا تمثيلًا له؛ فذلك Vibe Coding أنيق وهو محظور بنصّه.
4. لا يجوز حذف هذا الملفّ ولا تعديل نصّه المنقول إلا بسجلّ تعديلٍ دستوريّ تحت `docs/governance/amendments/` ومراجعةٍ بشريةٍ مستقلّة.
5. عند تعذّر إثبات بوّابة، الحالة `UNKNOWN` ويُبلَّغ العائق ويُتوقَّف — لا تُصنَّع يقينًا، ولا تُضعَّف بوّابة، ولا يُحذف اختبار.
