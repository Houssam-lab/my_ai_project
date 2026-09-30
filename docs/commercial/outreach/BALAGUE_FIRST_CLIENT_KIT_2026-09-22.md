# حزمة أول اتصال — Balagué Expertise (Castelginest)

> **الهدف:** CABINET D'EXPERTISE COMPTABLE BALAGUE · SIREN 501 058 812 · SIRET 501 058 812 00030 · TVA FR40501058812
> **صاحب القرار:** Philippe Balagué (Gérant منذ 28/04/2017)
> **الهاتف:** 05 61 37 66 45 (ثابت) · **البريد:** philippe-balague@balague-expertise.fr
> **العنوان:** 11 chemin de Naucou, 31780 Castelginest (+ Saint-Girons)
> **حجم المكتب:** SARL رأسمال 400,000 € · 10–19 موظفًا · نتيجة صافية 68.3K€ (2025) · خزينة 272K€ · صفر إجراءات جماعية
> **إشارة الشراء:** صفحة "facturation électronique" على الموقع + عبارة «Le cabinet prend les devants et vous accompagne» + أداة MEG iSuite + زر ردّ اتصال "ON VOUS APPELLE" (3 فروع)
> **تحقق التاريخ:** 2026-09-22 (Pappers: لا يظهر علم رفض التسويق · الموقع: الصفحة حيّة)
>
> ⛔ **الحالة:** `QUALIFIED_PROSPECT_HYPOTHESIS` — ليست "عميلة مضمونة". المضمون الوحيد هو تنفيذ التسلسل وقياسه.
>
> 📌 **ما حدث فعلاً (`CONTACT_LEDGER.csv`):** البريد D1 أُرسل 2026-09-22؛ المكالمة لم تُجرَ؛ لا ردّ حتى 2026-09-28.
> تواريخ §0 تجاوزها الزمن — الخطوة التالية هي المكالمة (§2)، ثم المتابعة (§4) بنفس المحادثة.

---

## 0) الجدول المؤرَّخ (ابدأ غدًا الثلاثاء — لا اتصال يوم الاثنين)

| اليوم | التاريخ | الفعل | التوقيت |
|---|---|---|---|
| D0 | الثلاثاء **23/09/2026** | ☎ مكالمة أولى | **10:35 فرنسا = 9:35 الجزائر** |
| D1 | الأربعاء 24/09 | ✉ بريد «عيّنة 20 سجلًا مجانًا» (إن لم يجري الاتصال: أرسله صباح اليوم نفسه) | 10:30–11:30 فرنسا |
| D+3 | الجمعة 26/09 صباحًا فقط | ☎ متابعة هاتفية إن لم يرد | 10:30–12:00 فرنسا |
| D6 | الاثنين 29/09 | 🔗 دعوة LinkedIn + تعليق قصير | أي وقت |
| D+5 من البريد | الثلاثاء 30/09 | ✉ متابعة قصيرة (Follow-up 2) | 10:30 فرنسا |
| D12 | الثلاثاء 07/10 | ✉ بريد إغلاق أخير (Closing) | 10:30 فرنسا |

⛔ بعد بريد الإغلاق بلا ردّ: الهدف يُعلَّم `SANS_REPONSE` ويُحذف من المداولات (قاعدة الاحتفاظ 3 سنوات).

---

## 1) قبل رفع السماعة (5 دقائق إلزامية)

1. ✅ Pappers: تحققتُ اليوم — لا علم اعتراض. (إن أعدت الفحص وظهر «s'est opposée à l'utilisation de ses données à des fins de prospection» ⇒ أوقف فورًا).
2. جهّز ورقة وقلم: اسم من يرد + تاريخ + ما قيل.
3. افتح `demo/RAPPORT_DIAGNOSTIC_DEMO.md` على الشاشة — إن سأل «كيف يبدو تقريركم؟» اقرأ له البنود الأربعة فقط.
4. لا تذكر أنك بالخارج إلا **إن سأل**. تعريفك: «consultant en fiabilité des données pour la facturation électronique». الصدق عند السؤال إلزامي، والاستباق لا.

## 2) سيناريو المكالمة D0

### 2.1 إذا ردّ Philippe Balagué شخصيًا (احتمال معقول في مكتب 10–19 موظفًا)

> «Bonjour Monsieur Balagué. Je m'appelle [الاسم الكامل], consultant en fiabilité des données pour la facturation électronique. Je vous appelle parce que votre cabinet affiche qu'il prend les devants sur la réforme — et depuis le 1er septembre, une facture électronique peut être rejetée quand le référentiel client est incomplet : SIREN erroné, doublon, identifiant de routage manquant. Concrètement, je propose un test sans engagement : vous m'envoyez 20 fiches clients, je vous rends un diagnostic d'erreurs sous 24 h, gratuitement. Ça vous intéresse que je vous l'envoie par mail ?»

**لماذا هذه الصيغة:** 3 جمل — مصداقية (صفحتهم هم) + ألمٌ قابل للتحقّق (آلية الرفض عند خطأ المعرّف) + طلب صغير محدد بلا مقابل.
⛔ لا تذكر أيّ نسبة رفض: لا نسبة مقيسة عندنا (`OFFER_CATALOG.json` — `claims_forbidden_ar`).

### 2.2 إذا ردّ موظف استقبال

> «Bonjour, [الاسم], consultant en fiabilité des données pour la facturation électronique. Monsieur Balagué a publié que le cabinet accompagne la réforme — je lui propose un test de qualité de référentiels sans engagement. Qui pourrait en parler avec lui, ou quelle est la meilleure adresse pour lui adresser ça ?»

(هدفك: اسم صاحب المهمة + بريد — ثم ودّع بأدب.)

### 2.3 الردود الجاهزة

| ما يقوله | ما تقوله أنت |
|---|---|
| «Envoyez-nous un mail» | ✅ نجاح: «Avec plaisir — à quelle adresse exactement, et à l'attention de qui ?» (اسم + بريد قبل الإنهاء) |
| «On gère ça en interne» | «Très bien. Le test ne coûte rien et prend 24 h : s'il y a des erreurs, vous le savez avant la vague de septembre 2027 ; s'il n'y en a pas, vous êtes tranquille. Je vous l'envoie ?» |
| «Pas le temps» | «Je vous envoie le mail aujourd'hui, vous y répondrez quand vous voulez. C'est noté pour [الاسم] ?» |
| «C'est quoi exactement votre service ?» | «Je vérifie et nettoie les données clients/fournisseurs avant migration facturation électronique : SIREN/SIRET contre SIRENE, numéros de TVA, dédoublonnage, identifiants de routage. Je livre un fichier prêt à importer + un rapport avant/après. Je ne touche ni à la comptabilité ni au fiscal — vous gardez la main. » |
| «Vous êtes basés où ?» | الصدق الكامل: «En Algérie — c'est justement ce qui rend le tarif très compétitif, avec un diagnostic livré en 24 h ; avant tout envoi de fichier réel, nous signons un accord de traitement des données. Le test de 20 fiches vous permettra de juger la qualité avant toute engagement.» (إن اعترض على خارج-EU: «Le test peut se faire sans données personnelles — seulement identifiants légaux. Et pour la suite, traitement dans votre environnement si vous préférez : je n'héberge rien.») |
| «Non merci» | «Merci Monsieur pour votre temps, très bonne journée.» ⇒ علّم الهدف `STOP` في الـCSV فورًا. لا عودة. |

### 2.4 إذا لم يرد (الصندوق الصوتي)

رسالة قصيرة واحدة (لا تعيد الاتصال بنفس اليوم):

> «Bonjour Monsieur Balagué, [الاسم], consultant en fiabilité des données pour la facturation électronique. Je vous appelle au sujet des référentiels clients avant la vague de septembre 2027 — je vous envoie un mail avec une proposition de test gratuit sur 20 fiches, résultat sous 24 h. Merci et bonne journée.»

ثم انتقل إلى البريد (القسم 3) في نفس النافذة.

---

## 3) البريد 1 — D1 (نسخة نهائية للنسخ)

**À :** philippe-balague@balague-expertise.fr
**Objet :** Diagnostic gratuit de vos référentiels clients — résultat sous 24 h

> Bonjour Monsieur Balagué,
>
> Je vous ai appelé hier au sujet de la qualité des référentiels clients dans le cadre de la facturation électronique. Depuis le 1er septembre, les rejets de factures pour cause de SIREN erronés, de numéros de TVA manquants ou d'identifiants de routage incomplets ont fortement augmenté — et la vague d'émission obligatoire pour vos clients PME/TPE arrive en septembre 2027.
>
> **Ma proposition, sans aucun engagement :**
> Vous m'envoyez 20 fiches clients (identifiants légaux uniquement : SIREN/SIRET, raison sociale, adresse — sans e-mails personnels), et je vous rends **sous 24 h** un diagnostic précis :
>
> - SIREN/SIRET invalides ou incohérents (vérification contre SIRENE) ;
> - numéros de TVA intracommunautaire manquants ou mal formés ;
> - doublons et quasi-doublons ;
> - champs obligatoires manquants pour le routage des factures ;
> - un score de qualité avant/après et une liste de correction priorisée.
>
> Vos données restent les vôtres : traitement ponctuel, aucune conservation au-delà de la livraison, aucune sous-traitance, suppression confirmée par écrit après livraison.
>
> Si le diagnostic vous est utile, nous verrons ensemble — seulement ensuite — s'il est pertinent d'étendre le travail au reste de votre base.
>
> Cordialement,
> [الاسم الكامل]
> Consultant — fiabilité des données & facturation électronique
> [بريدك] · [هاتفك مع +213]
>
> *PS : Cet envoi fait suite à notre appel téléphonique de ce matin. Si vous souhaitez ne plus être contacté, répondez simplement « STOP ».*

⚠️ **هذا النصّ أُرسل 2026-09-22 ويبقى كما هو سجلّاً.** عبارة «ont fortement augmenté» غير مقيسة — لا تُعَد في أيّ رسالة لاحقة (المتابعة في §4 والإغلاق في §6 لا تحملانها).

**ملحق اختياري قوي:** أرفق `RAPPORT_DIAGNOSTIC_DEMO.md` (النسخة التجريبية الوهمية) ليسترصد شكل التقرير — مع سطر: «Ci-joint un exemple (données 100 % fictives) du rapport que vous recevriez.»

## 4) Follow-up 2 — D+5 (ثلاثاء 30/09)

**Objet : RE: Diagnostic gratuit de vos référentiels clients**

> Bonjour Monsieur Balagué,
>
> Je me permets un petit rappel concernant la proposition de diagnostic gratuit (20 fiches, résultat sous 24 h).
> Si le moment n'est pas bon, dites-le-moi simplement et je ne reviendrai plus vers vous.
> Si c'est pertinent, envoyez-moi le fichier et vous aurez le rapport demain à cette heure.
>
> Cordialement,
> [التوقيع نفسه]

## 5) LinkedIn — D6 (الاثنين 29/09)

دعوة إلى ملف Philippe Balagué مع ملاحظة:

> «Bonjour Monsieur Balagué, je viens vers vous au sujet de la fiabilité des référentiels clients pour la facturation électronique (test gratuit 20 fiches, 24 h). Ravi de connecter.»

سقفك اليومي: 20–25 دعوة (لعدة أهداف معًا، لا له وحده).

## 6) بريد الإغلاق — D12 (الثلاثاء 07/10)

**Objet : Dernier message — référentiels clients**

> Bonjour Monsieur Balagué,
>
> Je n'ai pas eu de retour à ma proposition de diagnostic gratuit — je comprends, la période est chargée.
> Je clos donc ce sujet de mon côté. Si le besoin se présente d'ici la vague de septembre 2027 (rejets de factures, migration de fichiers clients), vous pouvez me joindre directement à [بريدك] / [هاتفك].
>
> Je reste à disposition, et belle continuation pour le cabinet.
>
> Cordialement, [الاسم]

---

## 7) إن قال «نعم» — تنفيذ الـ24 ساعة (بروتوكول العيّنة)

1. **استلم الملف** (CSV/XLSX). تأكد من خلوّه من بيانات شخصية (بريدات أشخاص) — إن وُجدت: احذفها فورًا وأخبره.
2. **تحقق عبر `recherche-entreprises.api.gouv.fr`** (مجاني بلا مفتاح): وجود الكيان، SIRET نشط، مطابقة الاسم، الرفض (`diffusionCommerciale` لا يخص العملاء هنا)، الشطب.
3. **TVA:** فحص الصيغة FR + 2 + 9 (الصيغة = SIREN)؛ VIES فقط عند الحاجة وبإشارة.
4. **المكررات:** مطابقة تامة + تقريبية (اسم/عنوان/CP).
5. **المخرجات** (نفس بنية التقرير التجريبي): ملف مصحح + تقرير قبل/بعد + قائمة نواقص + سجل تغييرات + مذكرة حدود. كل تعديل موسوم «تقرير → قرار المكتب» — لا تحذف شيئًا نهائيًا بنفسك.
6. **رسالة التسليم** تُنهي بسؤال الإغلاق: «Souhaitez-vous que nous chiffrions ensemble le nettoyage du reste de la base ?» → العرض بعد العيّنة: **290 € HT حتى 200 سجلّ** (السعر الواحد — قرار المالك 2026-09-30 · `PRICING HYPOTHESIS`)؛ ما فوق 200 سجلّ يُسعَّر بعد العيّنة. الدفع **باليورو** عبر Malt أو فاتورة SWIFT إلى حساب العملة الصعبة — ⛔ لا تقبل طلباً مدفوعاً قبل جواب البنك الكتابي وتسجيل ANAE ومراجعة DPA (`OFFER_CATALOG.json` — `activation_gate_ar`).

## 8) تحديث التتبع (الصف 7 في `FR_EINVOICING_TARGETS_2026-09-21.csv`)

بعد كل فعل، عدّل الأعمدة: `statut` → `APPELE_23-09` / `MAIL_ENVOYE_24-09` / `REPONSE_OUI` / `STOP` · `date_contact` · `objection` · `prochaine_action` · `date_action`.

## 9) قاعدة النجاح بعد أول 8 أهداف

لا تحكم على Balagué وحده — الحكم على الدفعة: 30 اتصالًا ⇒ ≥3 محادثات حقيقية. Balagué هو المكالمة رقم 1 من 30.
