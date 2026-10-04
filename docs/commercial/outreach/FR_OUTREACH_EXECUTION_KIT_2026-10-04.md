# حزمة تنفيذ حملة الـ30 اتصالًا — الفوترة الإلكترونية الفرنسية (المرحلة اليدوية)

> **التاريخ:** 2026-10-04 · **الغرض:** تحويل التوصية التنفيذية للتقرير المستقل ([`../INDEPENDENT_OPPORTUNITY_RESEARCH_2026-10-04.md`](../INDEPENDENT_OPPORTUNITY_RESEARCH_2026-10-04.md) §10) إلى مواد قابلة للتنفيذ فورًا: قائمة أهداف بمسمّين، تسلسل اتصال موحد، نصوص جاهزة، بروتوكول تسجيل، وعتبات قتل.
>
> **الحالة التجارية الحاكمة:** `GATE_C = ABSENT` — صفر دفعات. كل هدف في هذه الحزمة هو `QUALIFIED_PROSPECT_HYPOTHESIS` وليس عميلًا. **لا تُغيَّر أي حالة في أي قائمة إلا بسطر جديد في [`CONTACT_LEDGER.csv`](CONTACT_LEDGER.csv)** — السجل هو مصدر الحقيقة الوحيد (D-270/D-299).
>
> **قاعدة الفرضية الممنوعة:** لا تُذكر أي نسبة رفض أو نتائج مقيسة في أي رسالة أو مكالمة (`OFFER_CATALOG.json` → `claims_forbidden_ar`). الوعد الوحيد المسموح: تشخيص 20 سجلًا خلال 48 ساعة، مجانًا، بلا التزام.

---

## 0) قائمة الملفات — ماذا يُستخدم ومتى

| الملف | الدور |
|---|---|
| [`../FR_EINVOICING_TARGETS_V2_2026-10-04.csv`](../FR_EINVOICING_TARGETS_V2_2026-10-04.csv) | **قائمة العمل التشغيلية**: 34 سطرًا (30 هدفًا نشطًا + 4 مستبعدين)، بأعمدة `contact_nomme` / `contact_role` / `contact_source` / `contact_verifie_le`. تُطبع وتُشطب يدويًا. |
| [`BALAGUE_FIRST_CLIENT_KIT_2026-09-22.md`](BALAGUE_FIRST_CLIENT_KIT_2026-09-22.md) | **الأولوية صفر** — الهدف الوحيد الذي سبق أن أُرسل له بريد (2026-09-22، بلا رد حتى 2026-09-28، والمكالمة المقررة 2026-09-24 لم تُجرَ). الحزمة كاملة: سيناريو المكالمة، ردود الاعتراضات، جدول المتابعات المؤرَّخ. |
| [`demo/DEMO_20_FICHES.csv`](demo/DEMO_20_FICHES.csv) + `demo/DEMO_20_FICHES_ASSAINI.csv` + `demo/RAPPORT_DIAGNOSTIC_DEMO.md` | عيّنة العرض: ما يُرسل للعميل عند أول اهتمام. |
| [`CONTACT_LEDGER.csv`](CONTACT_LEDGER.csv) | المكان الوحيد الذي يُسجَّل فيه كل فعل تواصل. |

---

## 1) الخطة: 30 اتصالًا في 14 يومًا

**الأسبوع 1 (الأيام 1–7):**
- **الأولوية صفر (اليوم 1):** تنفيذ مكالمة Balagué المتأخرة (الحزمة المخصصة §2) — هدف واحد، جاهز بالكامل، لا يحتاج أي إعداد.
- **الأيام 1–4:** 10 رسائل بريد أولى لمسمّين (الترتيب أدناه) — 3 رسائل/يوم كحد أقصى حتى تبقى المساحة للمتابعات.
- **الأيام 3–7:** 5 مكالمات هاتفية (مكالمة لكل هدف مضى على بريده ≥48 ساعة).

**الأسبوع 2 (الأيام 8–14):**
- 20 اتصالًا إضافيًا (بريد/هاتف حسب `canal_1` في القائمة) + كل متابعات J+3 وJ+5 للأسبوع الأول.
- آخر اليوم 14: عدّ الأسطر الجديدة في السجل — قرار §4 أدناه.

**ترتيب أول 10 أهداف (المسمّون أولًا — أعلى احتمال رد):**

| # | id في V2 | الهدف | المسمّى | القناة |
|---|---|---|---|---|
| 0 | 7 | Balagué Expertise | Philippe Balagué | **مكالمة فورًا** (بريد سبق 2026-09-22) |
| 1 | 2 | ARCOEX | Mickaël Amblard (Président) | tel_puis_mail |
| 2 | 4 | Finot & Associés | Gérald Finot | mail (ثم tel J+3) |
| 3 | 5 | RYDGE Montpellier | Cédric Lafond | tel_puis_linkedin |
| 4 | 6 | JF Occitanie | Franck de David-Beauregard | mail (ثم tel J+3) |
| 5 | 1 | Groupe T2F | Thibault Faure | mail_puis_tel |
| 6 | 11 | Nexco | Raphaël Berguig | mail |
| 7 | 3 | Cabinet Archipel | Gaël Gente | mail |
| 8 | 8 | Exco FSO (Toulouse-Feuillants) | Philippe Lafargue / David Brettes | mail_puis_linkedin |
| 9 | 9 | In Extenso Midi-Pyrénées | Frédéric Fenech | tel_puis_linkedin |
| 10 | 10 | Groupe CF Toulouse | Yann Benchora / Bertrand Enjalbert | mail |

بقية القائمة (المؤسسات، المنصات، إشارات التوظيف): الأيام 8–14 حسب `canal_1`.

---

## 2) نص البريد الأول (قالب عام — يُخصَّص بسطر واحد لكل هدف)

**Objet :** Diagnostic gratuit de vos référentiels clients — résultat sous 48 h

> Bonjour {Prénom Nom},
>
> {سطر الخطّاف الخاص بالهدف — يُنسخ من عمود `hook_fr` في قائمة V2 كما هو، بلا إعادة صياغة}
>
> Depuis le 1er septembre 2026, une facture électronique peut être rejetée au routage quand le référentiel client est incomplet : SIREN erroné ou radié, numéro de TVA invalide, doublon, identifiant de routage manquant. La vague suivante — l'émission obligatoire pour vos clients PME — arrive le 1er septembre 2027.
>
> Je propose un test sans engagement : vous m'envoyez 20 fiches clients (un simple export), je vous rends sous 48 h un diagnostic d'erreurs — SIREN contre la base SIRENE, TVA, doublons — avec le taux avant/après. Gratuitement. Si rien ne cloche, vous le savez ; si quelque chose cloche, vous le savez avant la plateforme agréée.
>
> Je ne touche ni à la comptabilité ni au fiscal : uniquement la qualité des données de routage. Le test peut se faire sur des identifiants légaux seuls, sans données personnelles.
>
> Souhaitez-vous que je vous envoie la marche à suivre pour l'export ?
>
> {Nom complet} — consultant en fiabilité des données pour la facturation électronique

**قواعد إلزامية:** (1) سطر الخطّاف من عمود `hook_fr` دون تعديل — هو ما يثبت أن الرسالة مكتوبة للمكتب تحديدًا. (2) بلا أي نسبة أو رقم مقيس. (3) الصدق عند السؤال عن الموقع: «En Algérie — c'est justement ce qui rend le tarif très compétitif» (ردّ Balagué kit §2.3 يسري هنا حرفيًا). (4) 90 ثانية قراءة كحد أقصى.

**متابعة J+3 (هاتف — 90 ثانية):** نفس سيناريو حزمة Balagué §2.1 مع استبدال الجملة الأولى: «Je vous avais envoyé un mail mardi au sujet du test gratuit sur 20 fiches — je voulais m'assurer qu'il vous est bien parvenu.»

**متابعة J+5 (بريد، سطران):** «Bonjour {Prénom}, je reviens une seule fois sur le test gratuit de 20 fiches (résultat sous 48 h). Si ce n'est pas le moment, dites-le-moi simplement et je ne reviendrai pas avant la rentrée.»

**بريد الإغلاق J+12:** «Bonjour {Prénom}, je clos mon fichier concernant le test de référentiels. Si la question devient urgente à l'approche de septembre 2027, ma porte reste ouverte. Bonne continuation.» ⇒ ثم `SANS_REPONSE` في القائمة + سطر في السجل. **لا عودة إلى الهدف.**

---

## 3) بروتوكول ما قبل كل مكالمة (إلزامي — 5 دقائق)

1. **Pappers للشركة:** إن ظهر «s'est opposée à l'utilisation de ses données à des fins de prospection» ⇒ إلغاء الاتصال فورًا وتعليم الهدف `OPPOSITION`. (الأعلام محترمة أصلًا في القائمة: X1–X4 مستبعدون لهذا السبب تحديدًا.)
2. تجهيز: اسم من يرد + الوقت + الملاحظة — تُنقل إلى السجل في نفس اليوم.
3. «Non merci» قاطع ⇒ `STOP` في القائمة + سطر سجل. **لا إعادة اتصال أبدًا.**
4. ساعة الاتصال: 10:00–12:00 بتوقيت فرنسا (= 9:00–11:00 الجزائر). لا اتصال يوم الاثنين.

---

## 4) التسجيل وعتبات القرار

**كل فعل يُسجَّل في [`CONTACT_LEDGER.csv`](CONTACT_LEDGER.csv) في يومه** — الأعمدة كما هي: `date,target_ref,entity,country,channel,action,amount_eur,evidence_ref,note` حيث `target_ref` = `FR_EINVOICING_TARGETS_V2_2026-10-04.csv#id=N`. مثال:

```csv
2026-10-06,FR_EINVOICING_TARGETS_V2_2026-10-04.csv#id=4,Cabinet Finot & Associés,FR,email,EMAIL_SENT,,docs/commercial/FR_EINVOICING_TARGETS_V2_2026-10-04.csv:5,"Mail 1 (diagnostic gratuit 20 fiches) a l'attention de Gerald Finot"
```

**عتبات القرار (من التقرير المستقل §10 — تُطبق كما هي):**

| النتيجة بعد 30 اتصالًا موثقًا | القرار |
|---|---|
| ≥ 1 محادثة جادة (تشخيص مطلوب أو نقاش سعر) | الأطروحة حية → تسليم كل تشخيص خلال 48 ساعة + فتح بلجيكا (قاعدة H15: بعد 3 محادثات فرنسية) |
| 1–2 ردود فاترة بلا اهتمام | تعديل الرسالة/القناة (الهاتف أولًا) وجولة 30 ثانية |
| صفر ردود | **قتل موثّق** للأطروحة في السجل، وتحويل الجهد إلى مسارَي البطاقتين 2 و12 في التقرير المستقل |

**قيد زمني ملازم:** لا بحث تجاري جديد قبل اكتمال الـ30 اتصالًا (بوابة منع البحث بلا اتصال). هذه الحزمة آخر مخرج تحضيري.

---

## 5) حدود هذه الحزمة (صراحة كاملة)

- كل الأسماء والأدوار من مصادر مهنية عامة (مواقع المكاتب، السجل التجاري/السجلات القانونية الفرنسية، أدلة المهنة، LinkedIn الرسمي للشركات)، مُوثّقة بتاريخ التحقق في أعمدة `contact_source`/`contact_verifie_le`. الصف 17 (Cerfrance DP) رابطته بالإدارة الرقمية لفرع Ardèche **غير مؤكدة** — `A VERIFIER` قبل أي استخدام (موثّق داخل السطر نفسه).
- لا بيانات شخصية خاصة (لا عناوين منازل ولا بريد شخصي خارج نطاق العمل) — بيانات مهنية لأصحاب صفات رسمية في شركات، وهو النطاق الذي يجيزه القانون الفرنسي للتسويق B2B (المادة L.34-5 لقانون البريد والمواصلات: حق الاعتراض يُحترم عبر §3).
- هذه الحزمة **تحضير** — لا تدّعي أي نشاط: عدد أسطر السجل يوم 2026-10-04 لا يزال 1 (`GATE_C = ABSENT`).
- ما لا تستطيع هذه الحزمة فعله نيابةً عن المالك: المكالمة نفسها، تقديم Mercor، والسؤال المصرفي المكتوب عن SWIFT (التقرير المستقل §10، اليوم 1).
